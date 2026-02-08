"""PDF document parser for tax documents.

Extracts structured data from:
- 1099-NEC forms
- Schedule K-1 (Form 1065)
- W-2 forms
- 1098 Mortgage Interest
- 1095-A Health Insurance Marketplace
- Charity receipts
- Prior year tax returns (1040 + all schedules)
- Estimated payment confirmations
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from taxman.models import (
    CharityReceipt,
    Form1095A,
    Form1098,
    Form1099NEC,
    FormW2,
    ScheduleK1,
    EstimatedPayment,
)


# =============================================================================
# ParseResult wrapper (Phase 3)
# =============================================================================

@dataclass
class ParseResult:
    """Wrapper for parsed document data with confidence and validation info."""
    data: Any = None
    confidence: float = 0.0  # 0.0 to 1.0
    warnings: list[str] = field(default_factory=list)
    needs_manual_review: bool = False
    source_file: str = ""
    document_type: str = ""

    def add_warning(self, msg: str):
        self.warnings.append(msg)
        self.needs_manual_review = True


# =============================================================================
# Core PDF Extraction
# =============================================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text


def extract_pages_from_pdf(pdf_path: str) -> list[str]:
    """Extract text from each page separately."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            pages.append(page_text or "")
    return pages


def extract_tables_from_pdf(pdf_path: str) -> list[list]:
    """Extract tables from a PDF file."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def find_amount(text: str, pattern: str) -> float:
    """Find a dollar amount near a label pattern in text.

    Handles negative amounts in parentheses like (1,234.56).
    """
    # Try with parenthetical negatives first
    match = re.search(
        pattern + r'[\s.:$]*\(?\$?([\d,]+\.?\d*)\)?',
        text, re.IGNORECASE
    )
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str)
            # Check if the match includes parentheses (negative)
            full_match = match.group(0)
            if '(' in full_match and ')' in full_match:
                amount = -amount
            return amount
        except ValueError:
            return 0.0
    return 0.0


# =============================================================================
# Document Parsers
# =============================================================================

def parse_1099_nec(pdf_path: str) -> ParseResult:
    """Parse a 1099-NEC PDF into structured data.

    Bug 5 fix: Uses labeled regex patterns for TINs instead of positional.
    Multi-strategy extraction: regex + table + positional fallback.
    """
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="1099-NEC",
    )

    form = Form1099NEC()
    confidence_factors = []

    # Try to extract payer name
    payer_match = re.search(r"PAYER'?S?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if payer_match:
        form.payer_name = payer_match.group(1).strip()
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.0)
        result.add_warning("Could not extract payer name")

    # Recipient name
    recip_match = re.search(r"RECIPIENT'?S?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if recip_match:
        form.recipient_name = recip_match.group(1).strip()

    # Box 1: Nonemployee compensation — multi-strategy
    box1 = find_amount(text, r'(?:box\s*1|nonemployee\s+compensation)')
    if box1 == 0:
        # Try table extraction as fallback
        tables = extract_tables_from_pdf(str(pdf_path))
        for table in tables:
            for row in table:
                if row and any('nonemployee' in str(c).lower() for c in row if c):
                    for cell in row:
                        if cell and re.match(r'[\d,]+\.?\d*', str(cell).strip()):
                            try:
                                box1 = float(str(cell).replace(',', ''))
                                break
                            except ValueError:
                                pass
    form.nonemployee_compensation = box1
    if box1 > 0:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.0)
        result.add_warning("Box 1 (nonemployee compensation) is $0 — verify manually")

    # Box 4: Federal income tax withheld
    form.federal_tax_withheld = find_amount(text, r'(?:box\s*4|federal.*tax.*withheld)')

    # Bug 5 fix: Use labeled regex patterns for TINs
    payer_tin_match = re.search(
        r"PAYER'?S?\s+TIN[:\s]*(\d{2}-\d{7})", text, re.IGNORECASE
    )
    if payer_tin_match:
        form.payer_tin = payer_tin_match.group(1)
    else:
        # Fallback: first EIN found
        ein_matches = re.findall(r'\b(\d{2}-\d{7})\b', text)
        if ein_matches:
            form.payer_tin = ein_matches[0]

    recip_tin_match = re.search(
        r"RECIPIENT'?S?\s+TIN[:\s]*(\d{3}-\d{2}-\d{4})", text, re.IGNORECASE
    )
    if recip_tin_match:
        form.recipient_tin = recip_tin_match.group(1)
    else:
        ssn_matches = re.findall(r'\b(\d{3}-\d{2}-\d{4})\b', text)
        if ssn_matches:
            form.recipient_tin = ssn_matches[0]
        elif not payer_tin_match:
            # Fallback to positional EIN for recipient
            ein_matches = re.findall(r'\b(\d{2}-\d{7})\b', text)
            if len(ein_matches) >= 2:
                form.recipient_tin = ein_matches[1]

    # Validate
    if box1 > 0:
        _validate_amount(result, box1, "compensation", max_reasonable=10_000_000)

    result.data = form
    result.confidence = (
        sum(confidence_factors) / len(confidence_factors)
        if confidence_factors else 0.0
    )
    return result


def parse_k1_1065(pdf_path: str) -> ParseResult:
    """Parse a Schedule K-1 (Form 1065) PDF into structured data.

    Bug 6 fix: Extracts Box 14 (SE earnings), Box 11 (other income),
    Box 13 (other deductions). Handles negative numbers in parentheses.
    """
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="K-1",
    )

    k1 = ScheduleK1()
    confidence_factors = []

    # Partnership info
    name_match = re.search(r"partnership'?s?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if name_match:
        k1.partnership_name = name_match.group(1).strip()
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.0)
        result.add_warning("Could not extract partnership name")

    ein_matches = re.findall(r'\b(\d{2}-\d{7})\b', text)
    if ein_matches:
        k1.partnership_ein = ein_matches[0]

    # Key boxes
    k1.ordinary_business_income = find_amount(text, r'(?:box\s*1|ordinary\s+business\s+income)')
    k1.net_rental_income = find_amount(text, r'(?:box\s*2|net\s+rental.*income)')
    k1.guaranteed_payments = find_amount(text, r'(?:box\s*4|guaranteed\s+payments)')
    k1.interest_income = find_amount(text, r'(?:box\s*5|interest\s+income)')
    k1.net_long_term_capital_gain = find_amount(text, r'(?:box\s*9a|net.*long.*term.*capital)')
    k1.section_179_deduction = find_amount(text, r'(?:box\s*12|section\s*179)')

    # Bug 6 fix: Box 11 (other income), Box 13 (other deductions), Box 14 (SE earnings)
    k1.other_income = find_amount(text, r'(?:box\s*11|other\s+income)')
    k1.other_deductions = find_amount(text, r'(?:box\s*13|other\s+deductions)')
    k1.self_employment_earnings = find_amount(
        text, r'(?:box\s*14|self[- ]?employment\s+earnings)'
    )

    # Partner share percentages
    profit_match = re.search(r'profit.*?(\d+\.?\d*)%', text, re.IGNORECASE)
    if profit_match:
        k1.partner_share_profit = float(profit_match.group(1))

    loss_match = re.search(r'loss.*?(\d+\.?\d*)%', text, re.IGNORECASE)
    if loss_match:
        k1.partner_share_loss = float(loss_match.group(1))

    capital_match = re.search(r'capital.*?(\d+\.?\d*)%', text, re.IGNORECASE)
    if capital_match:
        k1.partner_share_capital = float(capital_match.group(1))

    # Confidence: at least partnership name and one income box
    has_income = any([
        k1.ordinary_business_income, k1.net_rental_income,
        k1.guaranteed_payments, k1.interest_income,
    ])
    if has_income:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.3)
        result.add_warning("No income boxes found — verify K-1 data manually")

    result.data = k1
    result.confidence = (
        sum(confidence_factors) / len(confidence_factors)
        if confidence_factors else 0.0
    )
    return result


def parse_w2(pdf_path: str) -> ParseResult:
    """Parse a W-2 PDF into structured data."""
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="W-2",
    )

    w2 = FormW2()

    # Employer info
    emp_match = re.search(r"employer'?s?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if emp_match:
        w2.employer_name = emp_match.group(1).strip()

    ein_match = re.search(r"employer'?s?\s+(?:EIN|identification)[:\s]*(\d{2}-\d{7})",
                          text, re.IGNORECASE)
    if ein_match:
        w2.employer_ein = ein_match.group(1)

    # Key boxes
    w2.wages = find_amount(text, r'(?:box\s*1|wages.*tips.*compensation)')
    w2.federal_tax_withheld = find_amount(text, r'(?:box\s*2|federal.*tax.*withheld)')
    w2.ss_wages = find_amount(text, r'(?:box\s*3|social\s+security\s+wages)')
    w2.ss_tax_withheld = find_amount(text, r'(?:box\s*4|social\s+security\s+tax)')
    w2.medicare_wages = find_amount(text, r'(?:box\s*5|medicare\s+wages)')
    w2.medicare_tax_withheld = find_amount(text, r'(?:box\s*6|medicare\s+tax\s+withheld)')
    w2.state_wages = find_amount(text, r'(?:box\s*16|state\s+wages)')
    w2.state_tax_withheld = find_amount(text, r'(?:box\s*17|state.*income.*tax)')

    if w2.wages == 0:
        result.add_warning("Box 1 (wages) is $0 — verify manually")

    result.data = w2
    result.confidence = 0.7 if w2.wages > 0 else 0.3
    return result


def parse_1098_mortgage(pdf_path: str) -> ParseResult:
    """Parse a 1098 Mortgage Interest Statement."""
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="1098",
    )

    form = Form1098()

    # Lender info
    lender_match = re.search(r"(?:lender|recipient)(?:'s)?\s+name[:\s]+(.+)",
                             text, re.IGNORECASE)
    if lender_match:
        form.lender_name = lender_match.group(1).strip()

    ein_matches = re.findall(r'\b(\d{2}-\d{7})\b', text)
    if ein_matches:
        form.lender_ein = ein_matches[0]

    # Box 1: Mortgage interest
    form.mortgage_interest = find_amount(text, r'(?:box\s*1|mortgage\s+interest\s+received)')
    # Box 6: Points paid
    form.points_paid = find_amount(text, r'(?:box\s*6|points\s+paid)')
    # Box 2: Outstanding principal
    form.outstanding_principal = find_amount(
        text, r'(?:box\s*2|outstanding\s+mortgage\s+principal)'
    )

    if form.mortgage_interest == 0:
        result.add_warning("Box 1 (mortgage interest) is $0 — verify manually")

    result.data = form
    result.confidence = 0.7 if form.mortgage_interest > 0 else 0.3
    return result


def parse_1095_a(pdf_path: str) -> ParseResult:
    """Parse a 1095-A Health Insurance Marketplace Statement."""
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="1095-A",
    )

    form = Form1095A()

    # Try to extract monthly data from tables
    tables = extract_tables_from_pdf(str(pdf_path))
    for table in tables:
        for row in table:
            if not row or len(row) < 4:
                continue
            # Look for rows with month names or numbers
            month_match = re.match(
                r'(january|february|march|april|may|june|july|august|'
                r'september|october|november|december|\d{1,2})',
                str(row[0]).strip().lower()
            )
            if month_match:
                month_str = month_match.group(1)
                month_map = {
                    'january': 0, 'february': 1, 'march': 2, 'april': 3,
                    'may': 4, 'june': 5, 'july': 6, 'august': 7,
                    'september': 8, 'october': 9, 'november': 10, 'december': 11,
                }
                if month_str in month_map:
                    idx = month_map[month_str]
                else:
                    try:
                        idx = int(month_str) - 1
                    except ValueError:
                        continue
                if 0 <= idx < 12:
                    try:
                        if row[1]:
                            form.monthly_premiums[idx] = float(
                                str(row[1]).replace(',', '').replace('$', '')
                            )
                        if len(row) > 2 and row[2]:
                            form.monthly_slcsp[idx] = float(
                                str(row[2]).replace(',', '').replace('$', '')
                            )
                        if len(row) > 3 and row[3]:
                            form.monthly_aptc[idx] = float(
                                str(row[3]).replace(',', '').replace('$', '')
                            )
                    except (ValueError, IndexError):
                        pass

    if form.total_premiums == 0:
        result.add_warning("No monthly premiums found — verify manually")
        result.confidence = 0.3
    else:
        result.confidence = 0.6

    result.data = form
    return result


def parse_charity_receipt(pdf_path: str) -> ParseResult:
    """Parse a charitable contribution receipt."""
    text = extract_text_from_pdf(pdf_path)
    result = ParseResult(
        source_file=str(pdf_path),
        document_type="Charity Receipt",
    )

    receipt = CharityReceipt()

    # Organization name — first line or near "organization" label
    org_match = re.search(r"(?:organization|from)[:\s]+(.+)", text, re.IGNORECASE)
    if org_match:
        receipt.organization_name = org_match.group(1).strip()

    # Amount
    amount_match = re.search(
        r'(?:amount|donation|contribution|total)[:\s$]*\$?([\d,]+\.?\d*)',
        text, re.IGNORECASE
    )
    if amount_match:
        receipt.amount = float(amount_match.group(1).replace(',', ''))

    # Date
    date_match = re.search(
        r'(?:date|received)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        text, re.IGNORECASE
    )
    if date_match:
        receipt.date = date_match.group(1)

    # EIN
    ein_match = re.search(r'\b(\d{2}-\d{7})\b', text)
    if ein_match:
        receipt.organization_ein = ein_match.group(1)

    if receipt.amount == 0:
        result.add_warning("Donation amount is $0 — verify manually")

    result.data = receipt
    result.confidence = 0.5 if receipt.amount > 0 else 0.2
    return result


# =============================================================================
# Document Validation
# =============================================================================

def validate_parsed_document(parse_result: ParseResult) -> ParseResult:
    """Post-parse validation: warn on suspicious values."""
    data = parse_result.data
    if data is None:
        return parse_result

    # Check for $0 compensation on income forms
    if isinstance(data, Form1099NEC) and data.nonemployee_compensation == 0:
        parse_result.add_warning("1099-NEC has $0 compensation")

    if isinstance(data, FormW2) and data.wages == 0:
        parse_result.add_warning("W-2 has $0 wages")

    # Check for unusually high values
    if isinstance(data, Form1099NEC) and data.nonemployee_compensation > 10_000_000:
        parse_result.add_warning(
            f"Unusually high compensation: ${data.nonemployee_compensation:,.2f}"
        )

    if isinstance(data, FormW2) and data.wages > 10_000_000:
        parse_result.add_warning(f"Unusually high wages: ${data.wages:,.2f}")

    # Check for missing payer/employer name
    if isinstance(data, Form1099NEC) and not data.payer_name:
        parse_result.add_warning("Missing payer name on 1099-NEC")

    if isinstance(data, FormW2) and not data.employer_name:
        parse_result.add_warning("Missing employer name on W-2")

    if isinstance(data, ScheduleK1) and not data.partnership_name:
        parse_result.add_warning("Missing partnership name on K-1")

    return parse_result


def _validate_amount(result: ParseResult, amount: float, label: str,
                     max_reasonable: float = 10_000_000):
    """Add warning if amount seems unreasonable."""
    if amount > max_reasonable:
        result.add_warning(f"Unusually high {label}: ${amount:,.2f}")


# =============================================================================
# Prior Return Parsing
# =============================================================================

def parse_prior_return(pdf_path: str) -> dict:
    """Parse a prior year tax return PDF into structured line-item data.

    Returns a dict organized by form/schedule with line numbers and values.
    This handles the full return package (1040 + all schedules in one PDF).
    """
    pages = extract_pages_from_pdf(pdf_path)
    result = {
        "source_file": os.path.basename(pdf_path),
        "pages": len(pages),
        "forms_detected": [],
        "data": {},
        "raw_text": {},
    }

    current_form = None
    for i, page_text in enumerate(pages):
        # Detect which form this page belongs to
        form_name = _detect_form(page_text)
        if form_name:
            current_form = form_name
            if form_name not in result["forms_detected"]:
                result["forms_detected"].append(form_name)

        if current_form:
            if current_form not in result["data"]:
                result["data"][current_form] = {}
                result["raw_text"][current_form] = ""
            result["raw_text"][current_form] += page_text + "\n"

            # Extract line items (Line X ... amount pattern)
            lines = _extract_line_items(page_text)
            result["data"][current_form].update(lines)

    return result


def _detect_form(text: str) -> str | None:
    """Detect which IRS form a page of text belongs to."""
    form_patterns = [
        (r'Form\s+1040\b(?!\s*-)', "Form 1040"),
        (r'Schedule\s+C\b.*(?:Profit|Loss|Business)', "Schedule C"),
        (r'Schedule\s+SE\b.*Self-Employment', "Schedule SE"),
        (r'Schedule\s+E\b.*Supplemental', "Schedule E"),
        (r'Schedule\s+1\b.*Additional\s+Income', "Schedule 1"),
        (r'Schedule\s+2\b.*Additional\s+Tax', "Schedule 2"),
        (r'Schedule\s+3\b.*Additional\s+Credits', "Schedule 3"),
        (r'Schedule\s+A\b.*Itemized', "Schedule A"),
        (r'Schedule\s+B\b.*Interest', "Schedule B"),
        (r'Schedule\s+D\b.*Capital\s+Gains', "Schedule D"),
        (r'Form\s+2555\b.*Foreign\s+Earned', "Form 2555"),
        (r'Form\s+8995\b.*Qualified\s+Business', "Form 8995"),
        (r'Form\s+8829\b.*Business\s+Use.*Home', "Form 8829"),
        (r'Form\s+4562\b.*Depreciation', "Form 4562"),
        (r'Schedule\s+SE\b', "Schedule SE"),
        (r'Self-Employment\s+Tax', "Schedule SE"),
        (r'Qualified\s+Dividends.*Capital\s+Gain\s+Tax\s+Worksheet', "QDCG Worksheet"),
        (r'Form\s+W-?2\b', "W-2"),
        (r'Form\s+1098\b', "Form 1098"),
        (r'Form\s+1095-?A\b', "Form 1095-A"),
    ]
    for pattern, name in form_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


def _extract_line_items(text: str) -> dict[str, str | float]:
    """Extract line numbers and their values from form text."""
    items = {}
    for match in re.finditer(
        r'(?:^|\n)\s*(\d{1,2}[a-z]?)\s+(.+?)[\s.]+\$?\s*([\d,]+\.?\d*)\s*$',
        text, re.MULTILINE
    ):
        line_num = match.group(1)
        description = match.group(2).strip()
        amount_str = match.group(3).replace(',', '')
        try:
            amount = float(amount_str)
            items[f"line_{line_num}"] = amount
            items[f"line_{line_num}_desc"] = description
        except ValueError:
            pass
    return items


# =============================================================================
# Document Scanning & Classification
# =============================================================================

def scan_documents_folder(folder_path: str) -> dict:
    """Scan a folder for tax documents and classify them.

    Returns a summary of what was found and what's parseable.
    """
    folder = Path(folder_path)
    if not folder.exists():
        return {"error": f"Folder not found: {folder_path}"}

    results = {
        "folder": str(folder),
        "documents": [],
        "summary": {
            "total_files": 0,
            "pdf_files": 0,
            "classified": {},
            "unclassified": [],
        }
    }

    for f in sorted(folder.rglob("*")):
        if f.is_file():
            results["summary"]["total_files"] += 1
            doc_info = {
                "path": str(f),
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "type": f.suffix.lower(),
            }

            if f.suffix.lower() == ".pdf":
                results["summary"]["pdf_files"] += 1
                try:
                    text = extract_text_from_pdf(str(f))
                    doc_type = _classify_document(text, f.name)
                    doc_info["classification"] = doc_type
                    doc_info["text_preview"] = text[:500]

                    if doc_type != "unknown":
                        results["summary"]["classified"][doc_type] = (
                            results["summary"]["classified"].get(doc_type, 0) + 1
                        )
                    else:
                        results["summary"]["unclassified"].append(f.name)
                except Exception as e:
                    doc_info["classification"] = "error"
                    doc_info["error"] = str(e)
            else:
                doc_info["classification"] = f"non-pdf ({f.suffix})"

            results["documents"].append(doc_info)

    return results


def _classify_document(text: str, filename: str) -> str:
    """Classify a tax document based on its content and filename."""
    text_lower = text.lower()
    fname_lower = filename.lower()

    if "1099-nec" in text_lower or "1099nec" in fname_lower or "1099-nec" in fname_lower:
        return "1099-NEC"
    if "nonemployee compensation" in text_lower:
        return "1099-NEC"
    if "w-2" in text_lower or "w2" in fname_lower or "w-2" in fname_lower:
        return "W-2"
    if "wage and tax statement" in text_lower:
        return "W-2"
    if "schedule k-1" in text_lower or "k-1" in fname_lower or "k1" in fname_lower:
        return "K-1"
    if "form 1098" in text_lower or "1098" in fname_lower:
        if "1098-t" in text_lower or "1098t" in fname_lower:
            return "1098-T"
        return "1098"
    if "mortgage interest" in text_lower:
        return "1098"
    if "1095-a" in text_lower or "1095a" in fname_lower or "1095-a" in fname_lower:
        return "1095-A"
    if "health insurance marketplace" in text_lower:
        return "1095-A"
    if "form 1040" in text_lower or "individual income tax" in text_lower:
        if "estimated" in text_lower or "1040-es" in text_lower:
            return "1040-ES"
        return "Prior Return"
    if "estimated tax payment" in text_lower or "1040-es" in fname_lower:
        return "1040-ES"
    if "health insurance" in text_lower or "premium" in text_lower:
        return "Health Insurance"
    if "charitable" in text_lower or "donation" in text_lower or "contribution" in text_lower:
        return "Charity Receipt"
    if "receipt" in fname_lower or "expense" in fname_lower or "invoice" in fname_lower:
        return "Expense Record"

    return "unknown"


def save_parsed_data(data: dict, output_path: str):
    """Save parsed data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved parsed data to {output_path}")
