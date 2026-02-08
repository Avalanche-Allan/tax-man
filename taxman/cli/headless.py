"""Headless wizard mode for Claude Code copilot integration.

Non-interactive CLI commands that accept JSON and return JSON,
allowing Claude Code to drive the tax wizard step-by-step.

Commands:
  taxman headless start [--session-id ID] [--docs-dir PATH]
  taxman headless step <session-id> <step-name> [--answers JSON]
  taxman headless status <session-id>
"""

import json
import sys
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import typer

from taxman.cli.config import TaxManConfig
from taxman.cli.serialization import (
    deserialize_profile,
    deserialize_result,
    serialize_profile,
    serialize_result,
)
from taxman.cli.state import SessionState
from taxman.models import (
    BusinessExpenses,
    BusinessType,
    EstimatedPayment,
    FilingStatus,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)

headless_app = typer.Typer(
    name="headless",
    help="Non-interactive headless mode for Claude Code copilot integration.",
    add_completion=False,
)


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class FieldSpec:
    """Describes one input field for a step."""
    name: str
    field_type: str  # "text" | "select" | "confirm" | "number" | "path"
    prompt: str
    required: bool = False
    default: Any = None
    choices: list = field(default_factory=list)
    condition: str = ""
    help_text: str = ""


@dataclass
class StepSpec:
    """Describes a wizard step's inputs and metadata."""
    name: str
    title: str
    description: str
    fields: list[FieldSpec] = field(default_factory=list)


# =============================================================================
# Step Ordering
# =============================================================================

STEP_ORDER = [
    "welcome",
    "filing_status",
    "document_scan",
    "document_review",
    "personal_info",
    "income_review",
    "business_expenses",
    "deductions",
    "foreign_income",
    "calculate",
    "optimization",
    "generate_forms",
    "filing_checklist",
]


def _next_step(current: str) -> Optional[str]:
    """Return the next step name after current, or None if done."""
    try:
        idx = STEP_ORDER.index(current)
        if idx + 1 < len(STEP_ORDER):
            return STEP_ORDER[idx + 1]
    except ValueError:
        pass
    return None


# =============================================================================
# Step Specs — define what each step asks
# =============================================================================

def _get_step_spec(step_name: str) -> StepSpec:
    """Return the spec for a given step."""
    specs = {
        "welcome": StepSpec(
            name="welcome",
            title="Welcome",
            description="Start your 2025 federal tax return preparation.",
            fields=[],
        ),
        "filing_status": StepSpec(
            name="filing_status",
            title="Filing Status",
            description="Select your filing status for 2025.",
            fields=[
                FieldSpec(
                    name="filing_status",
                    field_type="select",
                    prompt="Select your filing status",
                    required=True,
                    default="mfs",
                    choices=["single", "mfj", "mfs", "hoh", "qss"],
                    help_text="MFS (Married Filing Separately) is common for expats with NRA spouses. "
                              "MFJ requires both spouses to report worldwide income.",
                ),
                FieldSpec(
                    name="spouse_name",
                    field_type="text",
                    prompt="Spouse's full name",
                    condition="filing_status in ['mfs', 'mfj']",
                    help_text="Required for MFS/MFJ filings.",
                ),
                FieldSpec(
                    name="spouse_ssn",
                    field_type="text",
                    prompt="Spouse's SSN or ITIN (or leave blank)",
                    condition="filing_status in ['mfs', 'mfj']",
                    help_text="If your spouse is an NRA without an ITIN, leave blank and write 'NRA' on the return.",
                ),
                FieldSpec(
                    name="spouse_is_nra",
                    field_type="confirm",
                    prompt="Is your spouse a nonresident alien?",
                    default=True,
                    condition="filing_status == 'mfs'",
                    help_text="If yes, you can still file MFS. NRA spouses are not required to have an ITIN.",
                ),
            ],
        ),
        "document_scan": StepSpec(
            name="document_scan",
            title="Document Scan",
            description="Scan a folder of tax documents (PDFs) to auto-classify them.",
            fields=[
                FieldSpec(
                    name="documents_dir",
                    field_type="path",
                    prompt="Path to your tax documents folder",
                    help_text="Point to a folder containing PDF tax documents (W-2s, 1099s, K-1s, etc.). "
                              "The scanner will classify each document by type.",
                ),
            ],
        ),
        "document_review": StepSpec(
            name="document_review",
            title="Document Review",
            description="Review scanned documents and select which to parse.",
            fields=[
                FieldSpec(
                    name="accepted_documents",
                    field_type="text",
                    prompt="Comma-separated indices of documents to accept (0-based), or 'all'",
                    default="all",
                    help_text="After scanning, each document gets an index. Accept the ones you want parsed. "
                              "Example: '0,1,3' or 'all'.",
                ),
            ],
        ),
        "personal_info": StepSpec(
            name="personal_info",
            title="Personal Information",
            description="Enter your personal details for the return.",
            fields=[
                FieldSpec(name="first_name", field_type="text", prompt="First name", required=True),
                FieldSpec(name="last_name", field_type="text", prompt="Last name", required=True),
                FieldSpec(name="ssn", field_type="text", prompt="SSN (123-45-6789)", required=True,
                          help_text="Your Social Security Number. Format: 123-45-6789."),
                FieldSpec(name="occupation", field_type="text", prompt="Occupation"),
                FieldSpec(name="street_address", field_type="text", prompt="Street address"),
                FieldSpec(name="city", field_type="text", prompt="City"),
                FieldSpec(name="state", field_type="text", prompt="State (2-letter code)"),
                FieldSpec(name="zip_code", field_type="text", prompt="ZIP code"),
                FieldSpec(name="foreign_address", field_type="confirm", prompt="Do you have a foreign address?",
                          default=True, help_text="If you live abroad, say yes."),
                FieldSpec(name="country", field_type="text", prompt="Country",
                          default="Mexico", condition="foreign_address == true"),
            ],
        ),
        "income_review": StepSpec(
            name="income_review",
            title="Income Review",
            description="Review parsed income and add/modify Schedule C businesses and K-1s.",
            fields=[
                FieldSpec(
                    name="businesses",
                    field_type="text",
                    prompt="List of businesses as JSON array",
                    help_text="Each business: {\"business_name\": \"...\", \"gross_receipts\": 50000, "
                              "\"business_type\": \"single_member_llc\"}. business_type can be "
                              "'single_member_llc' or 'sole_proprietorship'.",
                ),
                FieldSpec(
                    name="keep_parsed_k1s",
                    field_type="confirm",
                    prompt="Keep K-1s imported from documents?",
                    default=True,
                    help_text="If documents were parsed, K-1 data was extracted. Keep it or start fresh.",
                ),
                FieldSpec(
                    name="additional_k1s",
                    field_type="text",
                    prompt="Additional K-1s as JSON array",
                    help_text="Each K-1: {\"partnership_name\": \"...\", \"net_rental_income\": 5000, "
                              "\"ordinary_business_income\": 0, \"guaranteed_payments\": 0, \"is_sstb\": false}.",
                ),
            ],
        ),
        "business_expenses": StepSpec(
            name="business_expenses",
            title="Business Expenses",
            description="Enter expenses and home office deductions for each business.",
            fields=[
                FieldSpec(
                    name="expenses",
                    field_type="text",
                    prompt="Expenses per business as JSON object keyed by business name",
                    help_text="Example: {\"My LLC\": {\"office_expense\": 500, \"supplies\": 200, "
                              "\"travel\": 1000, \"meals\": 800, \"advertising\": 300, "
                              "\"insurance\": 1200, \"contract_labor\": 5000}}. "
                              "Available categories: advertising, car_and_truck, commissions_and_fees, "
                              "contract_labor, depreciation, insurance, legal_and_professional, "
                              "office_expense, supplies, taxes_licenses, travel, meals (50% deductible), "
                              "utilities, other_expenses.",
                ),
                FieldSpec(
                    name="home_office",
                    field_type="text",
                    prompt="Home office per business as JSON object keyed by business name",
                    help_text="Example: {\"My LLC\": {\"method\": \"simplified\", \"square_footage\": 200}} "
                              "or {\"My LLC\": {\"method\": \"regular\", \"total_home_sqft\": 1000, "
                              "\"office_sqft\": 200, \"rent\": 1500, \"utilities\": 200, "
                              "\"internet\": 80, \"internet_business_pct\": 50}}. "
                              "Monthly amounts for rent/utilities/internet — will be annualized.",
                ),
            ],
        ),
        "deductions": StepSpec(
            name="deductions",
            title="Deductions",
            description="Health insurance, estimated payments, and prior year tax.",
            fields=[
                FieldSpec(
                    name="has_health_insurance",
                    field_type="confirm",
                    prompt="Do you have self-employed health insurance?",
                    default=False,
                    help_text="Self-employed health insurance premiums are an above-the-line deduction.",
                ),
                FieldSpec(
                    name="health_insurance_provider",
                    field_type="text",
                    prompt="Insurance provider name",
                    condition="has_health_insurance == true",
                ),
                FieldSpec(
                    name="health_insurance_premiums",
                    field_type="number",
                    prompt="Annual premiums ($)",
                    default=0,
                    condition="has_health_insurance == true",
                ),
                FieldSpec(
                    name="estimated_payments",
                    field_type="text",
                    prompt="Estimated payments as JSON array of {quarter, amount}",
                    help_text="Example: [{\"quarter\": 1, \"amount\": 5000}, {\"quarter\": 2, \"amount\": 5000}]",
                ),
                FieldSpec(
                    name="prior_year_tax",
                    field_type="number",
                    prompt="Prior year total tax (Line 24 of last year's 1040)",
                    default=0,
                    help_text="Used for estimated payment safe harbor calculation. "
                              "If AGI > $150K (or $75K MFS), you need 110% of prior year tax.",
                ),
            ],
        ),
        "foreign_income": StepSpec(
            name="foreign_income",
            title="Foreign Income",
            description="Foreign residency details for FEIE eligibility.",
            fields=[
                FieldSpec(
                    name="lived_abroad",
                    field_type="confirm",
                    prompt="Did you live abroad during 2025?",
                    default=True,
                    help_text="If yes, you may qualify for the Foreign Earned Income Exclusion (FEIE). "
                              "Requires 330+ days in a foreign country to pass the Physical Presence Test.",
                ),
                FieldSpec(
                    name="foreign_country",
                    field_type="text",
                    prompt="Foreign country of residence",
                    default="Mexico",
                    condition="lived_abroad == true",
                ),
                FieldSpec(
                    name="days_abroad",
                    field_type="number",
                    prompt="Days physically present in the foreign country",
                    default=330,
                    condition="lived_abroad == true",
                    help_text="Must be 330+ for Physical Presence Test. Count carefully.",
                ),
                FieldSpec(
                    name="days_us",
                    field_type="number",
                    prompt="Days in the US during 2025",
                    default=0,
                    condition="lived_abroad == true",
                ),
            ],
        ),
        "calculate": StepSpec(
            name="calculate",
            title="Tax Calculation",
            description="Run the full tax calculation engine. No input needed.",
            fields=[],
        ),
        "optimization": StepSpec(
            name="optimization",
            title="Optimization",
            description="Run FEIE comparison and optimization recommendations. No input needed.",
            fields=[],
        ),
        "generate_forms": StepSpec(
            name="generate_forms",
            title="Generate Forms",
            description="Generate PDF forms and text reports.",
            fields=[
                FieldSpec(
                    name="output_dir",
                    field_type="path",
                    prompt="Output directory for generated forms",
                    default="output",
                ),
            ],
        ),
        "filing_checklist": StepSpec(
            name="filing_checklist",
            title="Filing Checklist",
            description="Generate filing checklist and estimated quarterly payments. No input needed.",
            fields=[],
        ),
    }
    return specs.get(step_name)


# =============================================================================
# JSON Helpers
# =============================================================================

def _json_response(data: dict) -> str:
    """Serialize a dict to pretty JSON."""
    return json.dumps(data, indent=2, default=str)


def _error_response(message: str, error_type: str = "error", step: str = "") -> str:
    """Return a structured JSON error."""
    return _json_response({
        "error": True,
        "error_type": error_type,
        "message": message,
        "step": step,
    })


def _spec_to_dict(spec: StepSpec) -> dict:
    """Convert a StepSpec to a JSON-serializable dict."""
    return {
        "name": spec.name,
        "title": spec.title,
        "description": spec.description,
        "fields": [asdict(f) for f in spec.fields],
    }


# =============================================================================
# Step Processors
# =============================================================================

def _load_profile(session: SessionState) -> TaxpayerProfile:
    """Load profile from session, or create a new one."""
    if session.profile_data:
        return deserialize_profile(session.profile_data)
    return TaxpayerProfile()


def _save_profile(session: SessionState, profile: TaxpayerProfile):
    """Save profile to session."""
    session.profile_data = serialize_profile(profile)
    session.save()


def _process_welcome(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    return {"message": "Session started. Proceed to filing_status."}


def _process_filing_status(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    fs = answers.get("filing_status", "mfs")
    valid = {"single", "mfj", "mfs", "hoh", "qss"}
    if fs not in valid:
        return {"error": True, "error_type": "validation_error",
                "message": f"Invalid filing_status '{fs}'. Must be one of: {', '.join(sorted(valid))}"}

    profile.filing_status = FilingStatus(fs)
    session.filing_status = fs

    if fs in ("mfs", "mfj"):
        profile.spouse_name = answers.get("spouse_name", "")
        profile.spouse_ssn = answers.get("spouse_ssn", "")
        if fs == "mfs":
            profile.spouse_is_nra = answers.get("spouse_is_nra", True)

    _save_profile(session, profile)
    return {
        "filing_status": fs,
        "spouse_name": profile.spouse_name,
        "spouse_is_nra": profile.spouse_is_nra if fs == "mfs" else None,
    }


def _process_document_scan(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from taxman.parse_documents import scan_documents_folder

    doc_dir = answers.get("documents_dir", "")
    if not doc_dir:
        return {"message": "No documents directory provided. Skipping scan.", "documents": []}

    path = Path(doc_dir)
    if not path.exists():
        return {"error": True, "error_type": "validation_error",
                "message": f"Directory not found: {doc_dir}"}

    session.documents_dir = doc_dir
    results = scan_documents_folder(doc_dir)

    if "error" in results:
        return {"error": True, "error_type": "scan_error", "message": results["error"]}

    session.scan_results = results
    session.save()

    documents = []
    for i, doc in enumerate(results.get("documents", [])):
        documents.append({
            "index": i,
            "name": doc.get("name", ""),
            "classification": doc.get("classification", "unknown"),
            "path": doc.get("path", ""),
            "text_preview": doc.get("text_preview", "")[:200],
        })

    return {
        "summary": results.get("summary", {}),
        "documents": documents,
    }


def _process_document_review(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from dataclasses import asdict as _asdict

    from taxman.models import (
        CharityReceipt,
        Form1095A,
        Form1098,
        Form1099NEC,
        FormW2,
        ScheduleK1,
    )
    from taxman.parse_documents import (
        parse_1095_a,
        parse_1098_mortgage,
        parse_1099_nec,
        parse_charity_receipt,
        parse_k1_1065,
        parse_prior_return,
        parse_w2,
    )

    scan_results = session.scan_results
    if not scan_results or not scan_results.get("documents"):
        return {"message": "No documents to review.", "parsed": []}

    PARSERS = {
        "1099-NEC": parse_1099_nec,
        "W-2": parse_w2,
        "K-1": parse_k1_1065,
        "1098": parse_1098_mortgage,
        "1095-A": parse_1095_a,
        "Charity Receipt": parse_charity_receipt,
    }
    parseable_types = set(PARSERS.keys()) | {"Prior Return"}

    accepted_raw = answers.get("accepted_documents", "all")
    all_docs = scan_results["documents"]

    # Filter to parseable
    parseable_docs = [
        (i, doc) for i, doc in enumerate(all_docs)
        if doc.get("classification", "unknown") in parseable_types
    ]

    if accepted_raw == "all":
        accepted_indices = {i for i, _ in parseable_docs}
    else:
        try:
            accepted_indices = {int(x.strip()) for x in str(accepted_raw).split(",") if x.strip()}
        except ValueError:
            return {"error": True, "error_type": "validation_error",
                    "message": "accepted_documents must be 'all' or comma-separated indices"}

    parsed_results = []
    prior_year_tax_updated = False

    for i, doc in parseable_docs:
        if i not in accepted_indices:
            continue

        classification = doc.get("classification", "unknown")

        if classification == "Prior Return":
            try:
                prior_data = parse_prior_return(doc["path"])
                prior_tax = prior_data.get("data", {}).get("Form 1040", {}).get("line_24")
                if prior_tax is not None:
                    try:
                        prior_val = float(str(prior_tax).replace(",", "").replace("$", ""))
                    except (TypeError, ValueError):
                        prior_val = 0.0
                    profile.prior_year_tax = prior_val
                    prior_year_tax_updated = True
                    parsed_results.append({
                        "index": i,
                        "type": "Prior Return",
                        "prior_year_tax": prior_val,
                    })
            except Exception as e:
                parsed_results.append({
                    "index": i, "type": "Prior Return",
                    "error": str(e),
                })
            continue

        parser = PARSERS.get(classification)
        if not parser:
            continue

        try:
            pr = parser(doc["path"])
            entry = {
                "type": pr.document_type,
                "file": pr.source_file,
                "confidence": pr.confidence,
                "warnings": pr.warnings,
                "needs_manual_review": pr.needs_manual_review,
                "data": _asdict(pr.data) if pr.data else None,
            }
            parsed_results.append({"index": i, **entry})

            # Also store in session.parsed_documents for later rehydration
            if not session.parsed_documents:
                session.parsed_documents = []
            session.parsed_documents.append(entry)

        except Exception as e:
            parsed_results.append({
                "index": i, "type": classification,
                "error": str(e),
            })

    if prior_year_tax_updated:
        _save_profile(session, profile)
    session.save()

    return {"parsed": parsed_results}


def _process_personal_info(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    for attr in ["first_name", "last_name", "ssn", "occupation",
                 "street_address", "city", "state", "zip_code"]:
        val = answers.get(attr)
        if val is not None:
            setattr(profile, attr, val)

    foreign_address = answers.get("foreign_address", profile.foreign_address)
    if isinstance(foreign_address, str):
        foreign_address = foreign_address.lower() in ("true", "yes", "1")
    profile.foreign_address = foreign_address

    if foreign_address:
        profile.country = answers.get("country", profile.country or "Mexico")
        profile.foreign_country = profile.country

    session.personal_info = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
    }
    _save_profile(session, profile)
    return {"personal_info": session.personal_info}


def _process_income_review(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    # Rehydrate parsed documents into profile
    _apply_parsed_results(session, profile)

    # Process businesses
    businesses_raw = answers.get("businesses", [])
    if isinstance(businesses_raw, str):
        try:
            businesses_raw = json.loads(businesses_raw)
        except json.JSONDecodeError:
            businesses_raw = []

    if businesses_raw:
        profile.businesses = []
        for biz in businesses_raw:
            btype = biz.get("business_type", "single_member_llc")
            try:
                btype_enum = BusinessType(btype)
            except ValueError:
                btype_enum = BusinessType.SINGLE_MEMBER_LLC
            profile.businesses.append(ScheduleCData(
                business_name=biz.get("business_name", "Business"),
                gross_receipts=float(biz.get("gross_receipts", 0)),
                business_type=btype_enum,
            ))

    # K-1s
    keep_parsed = answers.get("keep_parsed_k1s", True)
    if isinstance(keep_parsed, str):
        keep_parsed = keep_parsed.lower() in ("true", "yes", "1")

    if not keep_parsed:
        profile.schedule_k1s = []

    additional_k1s = answers.get("additional_k1s", [])
    if isinstance(additional_k1s, str):
        try:
            additional_k1s = json.loads(additional_k1s)
        except json.JSONDecodeError:
            additional_k1s = []

    for k1 in additional_k1s:
        profile.schedule_k1s.append(ScheduleK1(
            partnership_name=k1.get("partnership_name", "Partnership"),
            net_rental_income=float(k1.get("net_rental_income", 0)),
            ordinary_business_income=float(k1.get("ordinary_business_income", 0)),
            guaranteed_payments=float(k1.get("guaranteed_payments", 0)),
            interest_income=float(k1.get("interest_income", 0)),
            dividends=float(k1.get("dividends", 0)),
            qualified_dividends=float(k1.get("qualified_dividends", 0)),
            net_long_term_capital_gain=float(k1.get("net_long_term_capital_gain", 0)),
            net_short_term_capital_gain=float(k1.get("net_short_term_capital_gain", 0)),
            self_employment_earnings=float(k1.get("self_employment_earnings", 0)),
            qbi_amount=float(k1.get("qbi_amount", 0)),
            is_sstb=k1.get("is_sstb", False),
        ))

    _save_profile(session, profile)

    return {
        "businesses": [
            {"name": b.business_name, "gross_receipts": b.gross_receipts}
            for b in profile.businesses
        ],
        "k1s": [
            {"partnership_name": k.partnership_name,
             "net_rental_income": k.net_rental_income,
             "ordinary_business_income": k.ordinary_business_income}
            for k in profile.schedule_k1s
        ],
    }


def _apply_parsed_results(session: SessionState, profile: TaxpayerProfile):
    """Populate profile from parsed document results."""
    from taxman.models import (
        CharityReceipt,
        Form1095A,
        Form1098,
        Form1099NEC,
        FormW2,
        ScheduleK1,
    )

    TYPE_MAP = {
        "W-2": FormW2,
        "1099-NEC": Form1099NEC,
        "K-1": ScheduleK1,
        "1098": Form1098,
        "1095-A": Form1095A,
        "Charity Receipt": CharityReceipt,
    }

    for entry in session.parsed_documents:
        doc_type = entry.get("type", "")
        model_cls = TYPE_MAP.get(doc_type)
        data_dict = entry.get("data")
        if not model_cls or not isinstance(data_dict, dict):
            continue

        try:
            obj = model_cls(**data_dict)
        except Exception:
            continue

        if isinstance(obj, FormW2):
            profile.forms_w2.append(obj)
        elif isinstance(obj, Form1099NEC):
            profile.forms_1099_nec.append(obj)
        elif isinstance(obj, ScheduleK1):
            profile.schedule_k1s.append(obj)
        elif isinstance(obj, Form1098):
            profile.forms_1098.append(obj)


def _process_business_expenses(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    expenses_raw = answers.get("expenses", {})
    if isinstance(expenses_raw, str):
        try:
            expenses_raw = json.loads(expenses_raw)
        except json.JSONDecodeError:
            expenses_raw = {}

    home_office_raw = answers.get("home_office", {})
    if isinstance(home_office_raw, str):
        try:
            home_office_raw = json.loads(home_office_raw)
        except json.JSONDecodeError:
            home_office_raw = {}

    results = []
    for biz in profile.businesses:
        biz_expenses = expenses_raw.get(biz.business_name, {})
        if biz_expenses:
            expenses = BusinessExpenses()
            expense_fields = [
                "advertising", "car_and_truck", "commissions_and_fees",
                "contract_labor", "depreciation", "employee_benefit_programs",
                "insurance", "interest_mortgage", "interest_other",
                "legal_and_professional", "office_expense", "pension_profit_sharing",
                "rent_vehicles_equipment", "rent_other", "repairs_maintenance",
                "supplies", "taxes_licenses", "travel", "meals", "utilities",
                "wages", "other_expenses",
            ]
            for ef in expense_fields:
                val = biz_expenses.get(ef, 0)
                try:
                    setattr(expenses, ef, float(val))
                except (ValueError, TypeError):
                    pass
            if biz_expenses.get("other_expenses_description"):
                expenses.other_expenses_description = biz_expenses["other_expenses_description"]
            biz.expenses = expenses

        # Home office
        ho_data = home_office_raw.get(biz.business_name, {})
        if ho_data:
            method = ho_data.get("method", "simplified")
            if method == "simplified":
                biz.home_office = HomeOffice(
                    use_simplified_method=True,
                    square_footage=float(ho_data.get("square_footage", 0)),
                )
            else:
                biz.home_office = HomeOffice(
                    use_simplified_method=False,
                    total_home_sqft=float(ho_data.get("total_home_sqft", 0)),
                    office_sqft=float(ho_data.get("office_sqft", 0)),
                    rent=float(ho_data.get("rent", 0)) * 12,
                    utilities=float(ho_data.get("utilities", 0)) * 12,
                    internet=float(ho_data.get("internet", 0)) * 12,
                    internet_business_pct=float(ho_data.get("internet_business_pct", 50)),
                    mortgage_interest=float(ho_data.get("mortgage_interest", 0)),
                    real_estate_taxes=float(ho_data.get("real_estate_taxes", 0)),
                )

        results.append({
            "business": biz.business_name,
            "total_expenses": biz.expenses.total,
            "home_office": (
                biz.home_office.simplified_deduction if biz.home_office and biz.home_office.use_simplified_method
                else biz.home_office.regular_deduction if biz.home_office
                else 0
            ),
            "net_profit": biz.net_profit,
        })

    _save_profile(session, profile)
    return {"businesses": results}


def _process_deductions(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    # Health insurance
    has_health = answers.get("has_health_insurance", False)
    if isinstance(has_health, str):
        has_health = has_health.lower() in ("true", "yes", "1")

    if has_health:
        profile.health_insurance = HealthInsurance(
            provider=answers.get("health_insurance_provider", ""),
            total_premiums=float(answers.get("health_insurance_premiums", 0)),
        )

    # Estimated payments
    est_raw = answers.get("estimated_payments", [])
    if isinstance(est_raw, str):
        try:
            est_raw = json.loads(est_raw)
        except json.JSONDecodeError:
            est_raw = []

    if est_raw:
        profile.estimated_payments = []
        for p in est_raw:
            amt = float(p.get("amount", 0))
            if amt > 0:
                profile.estimated_payments.append(
                    EstimatedPayment(quarter=int(p.get("quarter", 0)), amount=amt)
                )

    # Prior year tax
    prior = answers.get("prior_year_tax", None)
    if prior is not None:
        try:
            profile.prior_year_tax = float(str(prior).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            pass

    _save_profile(session, profile)
    return {
        "health_insurance": profile.health_insurance is not None,
        "estimated_payments_total": profile.total_estimated_payments,
        "prior_year_tax": profile.prior_year_tax,
    }


def _process_foreign_income(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    lived_abroad = answers.get("lived_abroad", True)
    if isinstance(lived_abroad, str):
        lived_abroad = lived_abroad.lower() in ("true", "yes", "1")

    if not lived_abroad:
        profile.foreign_address = False
        profile.days_in_foreign_country_2025 = 0
        _save_profile(session, profile)
        return {"lived_abroad": False, "feie_eligible": False}

    profile.foreign_address = True
    profile.foreign_country = answers.get("foreign_country", profile.foreign_country or "Mexico")
    profile.days_in_foreign_country_2025 = int(answers.get("days_abroad", 330))
    profile.days_in_us_2025 = int(answers.get("days_us", 0))

    feie_eligible = profile.days_in_foreign_country_2025 >= 330

    _save_profile(session, profile)
    return {
        "lived_abroad": True,
        "foreign_country": profile.foreign_country,
        "days_abroad": profile.days_in_foreign_country_2025,
        "days_us": profile.days_in_us_2025,
        "feie_eligible": feie_eligible,
        "feie_note": (
            "You meet the Physical Presence Test for FEIE."
            if feie_eligible
            else f"You may not meet the Physical Presence Test "
                 f"({profile.days_in_foreign_country_2025}/330 days)."
        ),
    }


def _process_calculate(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from taxman.calculator import calculate_return

    result = calculate_return(profile)
    session.results = serialize_result(result)
    session.save()

    return {
        "wage_income": result.wage_income,
        "total_income": result.total_income,
        "agi": result.agi,
        "deduction": result.deduction,
        "qbi_deduction": result.qbi_deduction,
        "taxable_income": result.taxable_income,
        "income_tax": result.tax,
        "se_tax": result.se_tax,
        "additional_medicare": result.additional_medicare,
        "niit": result.niit,
        "amt": result.amt,
        "nonrefundable_credits": result.nonrefundable_credits,
        "total_tax": result.total_tax,
        "total_payments": result.total_payments,
        "estimated_payments": result.estimated_payments,
        "withholding": result.withholding,
        "overpayment": result.overpayment,
        "amount_owed": result.amount_owed,
        "schedule_c": [
            {"business": sc.business_name, "gross": sc.gross_receipts,
             "expenses": sc.total_expenses, "net": sc.net_profit_loss}
            for sc in result.schedule_c_results
        ],
    }


def _process_optimization(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from taxman.calculator import (
        compare_feie_scenarios,
        generate_optimization_recommendations,
    )

    if not session.results:
        return {"error": True, "error_type": "state_error",
                "message": "No calculation results. Run 'calculate' step first."}

    result = deserialize_result(session.results)
    response = {}

    # FEIE comparison
    if profile.days_in_foreign_country_2025 >= 330:
        scenarios = compare_feie_scenarios(profile)
        response["feie"] = {
            "without_feie": scenarios["without_feie"],
            "feie_evaluation": scenarios["feie_evaluation"],
            "recommendation": scenarios["recommendation"],
        }

        feie_result = scenarios.get("feie_result")
        if feie_result and feie_result.is_beneficial:
            result.feie = feie_result
            session.results = serialize_result(result)
            session.save()

    # Optimization recommendations
    recs = generate_optimization_recommendations(result, profile)
    response["recommendations"] = recs

    return response


def _process_generate_forms(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from taxman.reports import (
        generate_filing_checklist,
        generate_tax_summary,
    )

    if not session.results:
        return {"error": True, "error_type": "state_error",
                "message": "No calculation results. Run 'calculate' step first."}

    result = deserialize_result(session.results)
    output_dir = answers.get("output_dir", "output")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Text reports
    summary = generate_tax_summary(result, profile)
    summary_path = output_path / "tax_summary.txt"
    summary_path.write_text(summary)
    generated_files.append(str(summary_path))

    checklist = generate_filing_checklist(result, profile)
    checklist_path = output_path / "filing_checklist.txt"
    checklist_path.write_text(checklist)
    generated_files.append(str(checklist_path))

    # PDF generation
    try:
        from taxman.fill_forms import generate_all_forms
        forms = generate_all_forms(result, profile, output_dir)
        for f in forms:
            generated_files.append(str(f))
    except Exception as e:
        pass  # PDFs are optional; text reports still generated

    session.generated_forms = generated_files
    session.save()

    return {"generated_files": generated_files, "output_dir": output_dir}


def _process_filing_checklist(session: SessionState, profile: TaxpayerProfile, answers: dict) -> dict:
    from taxman.calculator import estimate_quarterly_payments
    from taxman.reports import generate_filing_checklist

    if not session.results:
        return {"error": True, "error_type": "state_error",
                "message": "No calculation results. Run 'calculate' step first."}

    result = deserialize_result(session.results)
    checklist = generate_filing_checklist(result, profile)

    response = {"checklist": checklist}

    # Quarterly payment plan
    quarterly = estimate_quarterly_payments(
        result.total_tax, profile.prior_year_tax, result.agi,
        filing_status=profile.filing_status,
    )
    response["quarterly_payments"] = quarterly

    return response


# Processor dispatch
PROCESSORS = {
    "welcome": _process_welcome,
    "filing_status": _process_filing_status,
    "document_scan": _process_document_scan,
    "document_review": _process_document_review,
    "personal_info": _process_personal_info,
    "income_review": _process_income_review,
    "business_expenses": _process_business_expenses,
    "deductions": _process_deductions,
    "foreign_income": _process_foreign_income,
    "calculate": _process_calculate,
    "optimization": _process_optimization,
    "generate_forms": _process_generate_forms,
    "filing_checklist": _process_filing_checklist,
}


# =============================================================================
# Typer Commands
# =============================================================================

@headless_app.command("start")
def start(
    session_id: Optional[str] = typer.Option(None, "--session-id", "-s",
                                             help="Resume an existing session"),
    docs_dir: Optional[str] = typer.Option(None, "--docs-dir", "-d",
                                           help="Path to tax documents folder"),
):
    """Start or resume a headless session. Returns JSON."""
    try:
        config = TaxManConfig.load()
        config.ensure_dirs()

        if session_id:
            session = SessionState.load(session_id)
            if not session:
                print(_error_response(f"Session {session_id} not found.", "not_found"))
                raise typer.Exit(1)
        else:
            session = SessionState.create()

        if docs_dir:
            session.documents_dir = docs_dir
        session.save()

        # Determine next step
        if session.completed_steps:
            last = session.completed_steps[-1]
            next_step = _next_step(last)
        else:
            next_step = "welcome"

        next_spec = _get_step_spec(next_step) if next_step else None

        response = {
            "session_id": session.session_id,
            "resumed": session_id is not None,
            "completed_steps": session.completed_steps,
            "next_step": next_step,
            "next_spec": _spec_to_dict(next_spec) if next_spec else None,
        }
        print(_json_response(response))

    except typer.Exit:
        raise
    except Exception as e:
        print(_error_response(str(e), "internal_error"))
        raise typer.Exit(1)


@headless_app.command("step")
def step(
    session_id: str = typer.Argument(help="Session ID"),
    step_name: str = typer.Argument(help="Step name to process"),
    answers: Optional[str] = typer.Option(None, "--answers", "-a",
                                          help="JSON string with answers"),
):
    """Process a step or return its spec. Returns JSON."""
    try:
        session = SessionState.load(session_id)
        if not session:
            print(_error_response(f"Session {session_id} not found.", "not_found"))
            raise typer.Exit(1)

        if step_name not in STEP_ORDER:
            print(_error_response(
                f"Unknown step '{step_name}'. Valid: {', '.join(STEP_ORDER)}",
                "validation_error", step_name,
            ))
            raise typer.Exit(1)

        # No answers → return the step spec
        if answers is None:
            spec = _get_step_spec(step_name)
            response = {
                "session_id": session_id,
                "step": step_name,
                "spec": _spec_to_dict(spec),
            }
            print(_json_response(response))
            return

        # Parse answers JSON
        try:
            answers_dict = json.loads(answers)
        except json.JSONDecodeError as e:
            print(_error_response(f"Invalid JSON in --answers: {e}", "json_error", step_name))
            raise typer.Exit(1)

        # Process the step
        profile = _load_profile(session)
        processor = PROCESSORS.get(step_name)
        if not processor:
            print(_error_response(f"No processor for step '{step_name}'", "internal_error", step_name))
            raise typer.Exit(1)

        result = processor(session, profile, answers_dict)

        # Check if processor returned an error
        if isinstance(result, dict) and result.get("error"):
            print(_json_response(result))
            raise typer.Exit(1)

        # Mark step completed
        session.current_step = step_name
        session.complete_step(step_name)

        # Determine next step
        next_step_name = _next_step(step_name)
        next_spec = _get_step_spec(next_step_name) if next_step_name else None

        response = {
            "session_id": session_id,
            "step": step_name,
            "result": result,
            "next_step": next_step_name,
            "next_spec": _spec_to_dict(next_spec) if next_spec else None,
            "completed": next_step_name is None,
        }
        print(_json_response(response))

    except typer.Exit:
        raise
    except Exception as e:
        print(_error_response(f"{type(e).__name__}: {e}", "internal_error", step_name))
        raise typer.Exit(1)


@headless_app.command("status")
def status(
    session_id: str = typer.Argument(help="Session ID"),
):
    """Return session status as JSON."""
    try:
        session = SessionState.load(session_id)
        if not session:
            print(_error_response(f"Session {session_id} not found.", "not_found"))
            raise typer.Exit(1)

        profile_summary = {}
        if session.profile_data:
            profile = deserialize_profile(session.profile_data)
            profile_summary = {
                "name": f"{profile.first_name} {profile.last_name}".strip(),
                "filing_status": profile.filing_status.value,
                "businesses": len(profile.businesses),
                "k1s": len(profile.schedule_k1s),
                "w2s": len(profile.forms_w2),
                "foreign_address": profile.foreign_address,
                "days_abroad": profile.days_in_foreign_country_2025,
            }

        results_summary = {}
        if session.results:
            result = deserialize_result(session.results)
            results_summary = {
                "total_income": result.total_income,
                "agi": result.agi,
                "taxable_income": result.taxable_income,
                "total_tax": result.total_tax,
                "amount_owed": result.amount_owed,
                "overpayment": result.overpayment,
            }

        response = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "completed_steps": session.completed_steps,
            "current_step": session.current_step,
            "total_steps": len(STEP_ORDER),
            "progress_pct": round(len(session.completed_steps) / len(STEP_ORDER) * 100),
            "profile_summary": profile_summary,
            "results_summary": results_summary,
            "generated_forms": session.generated_forms,
        }
        print(_json_response(response))

    except typer.Exit:
        raise
    except Exception as e:
        print(_error_response(str(e), "internal_error"))
        raise typer.Exit(1)
