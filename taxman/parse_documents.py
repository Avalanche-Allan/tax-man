"""PDF document parser for tax documents.

Extracts structured data from:
- 1099-NEC forms
- Schedule K-1 (Form 1065)
- Prior year tax returns (1040 + all schedules)
- Estimated payment confirmations
"""

import json
import os
import re
from pathlib import Path

import pdfplumber

from taxman.models import (
    Form1099NEC,
    ScheduleK1,
    EstimatedPayment,
)


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
    """Find a dollar amount near a label pattern in text."""
    match = re.search(pattern + r'[\s.:$]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    return 0.0


def parse_1099_nec(pdf_path: str) -> Form1099NEC:
    """Parse a 1099-NEC PDF into structured data."""
    text = extract_text_from_pdf(pdf_path)

    form = Form1099NEC()

    # Try to extract payer name (usually near top)
    payer_match = re.search(r"PAYER'?S?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if payer_match:
        form.payer_name = payer_match.group(1).strip()

    # Box 1: Nonemployee compensation
    form.nonemployee_compensation = find_amount(text, r'(?:box\s*1|nonemployee\s+compensation)')

    # Box 4: Federal income tax withheld
    form.federal_tax_withheld = find_amount(text, r'(?:box\s*4|federal.*tax.*withheld)')

    # TINs
    tin_matches = re.findall(r'\b(\d{2}-\d{7})\b', text)
    if len(tin_matches) >= 1:
        form.payer_tin = tin_matches[0]
    if len(tin_matches) >= 2:
        form.recipient_tin = tin_matches[1]

    ssn_matches = re.findall(r'\b(\d{3}-\d{2}-\d{4})\b', text)
    if ssn_matches:
        form.recipient_tin = ssn_matches[0]

    return form


def parse_k1_1065(pdf_path: str) -> ScheduleK1:
    """Parse a Schedule K-1 (Form 1065) PDF into structured data."""
    text = extract_text_from_pdf(pdf_path)

    k1 = ScheduleK1()

    # Partnership info
    name_match = re.search(r"partnership'?s?\s+name[:\s]+(.+)", text, re.IGNORECASE)
    if name_match:
        k1.partnership_name = name_match.group(1).strip()

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

    # Partner share percentages
    profit_match = re.search(r'profit.*?(\d+\.?\d*)%', text, re.IGNORECASE)
    if profit_match:
        k1.partner_share_profit = float(profit_match.group(1))

    return k1


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
    ]
    for pattern, name in form_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


def _extract_line_items(text: str) -> dict[str, str | float]:
    """Extract line numbers and their values from form text."""
    items = {}
    # Match patterns like "7  Wages..." or "Line 7" followed by amounts
    # This is deliberately broad - we refine per-form later
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
                # Try to classify the PDF
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
    if "schedule k-1" in text_lower or "k-1" in fname_lower or "k1" in fname_lower:
        return "K-1"
    if "form 1040" in text_lower or "individual income tax" in text_lower:
        if "estimated" in text_lower or "1040-es" in text_lower:
            return "1040-ES"
        return "Prior Return"
    if "estimated tax payment" in text_lower or "1040-es" in fname_lower:
        return "1040-ES"
    if "health insurance" in text_lower or "premium" in text_lower:
        return "Health Insurance"
    if "receipt" in fname_lower or "expense" in fname_lower or "invoice" in fname_lower:
        return "Expense Record"

    return "unknown"


def save_parsed_data(data: dict, output_path: str):
    """Save parsed data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved parsed data to {output_path}")
