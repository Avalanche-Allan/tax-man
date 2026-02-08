"""Field mapping for Form 1040.

NOTE: Actual PDF field names must be discovered via
inspect_form_fields_raw('f1040') against 2025 IRS PDFs.
The field names below are placeholders based on common conventions.
"""

from taxman.field_mappings.common import (
    checkbox,
    format_currency_for_pdf,
    format_ssn,
)


def build_1040_data(result, profile) -> dict:
    """Build field data dict for Form 1040.

    Args:
        result: Form1040Result
        profile: TaxpayerProfile

    Returns:
        Dict mapping PDF field names to values.
    """
    data = {}

    # Header
    data["f1_01"] = profile.first_name
    data["f1_02"] = profile.last_name
    data["f1_03"] = format_ssn(profile.ssn)

    # Filing status checkboxes
    fs_map = {
        "single": "f1_04",
        "mfj": "f1_05",
        "mfs": "f1_06",
        "hoh": "f1_07",
        "qss": "f1_08",
    }
    fs_field = fs_map.get(profile.filing_status.value)
    if fs_field:
        data[fs_field] = checkbox(True)

    # Spouse info (MFS)
    if profile.spouse_name:
        data["f1_09"] = profile.spouse_name
    if profile.spouse_ssn:
        data["f1_10"] = format_ssn(profile.spouse_ssn)

    # Address
    data["f1_11"] = profile.street_address
    data["f1_12"] = f"{profile.city}, {profile.state} {profile.zip_code}"
    if profile.foreign_address:
        data["f1_13"] = profile.country

    # Income
    data["f1_line8"] = format_currency_for_pdf(result.total_income)  # Line 8/9
    data["f1_line9"] = format_currency_for_pdf(result.total_income)
    data["f1_line10"] = format_currency_for_pdf(result.adjustments)
    data["f1_line11"] = format_currency_for_pdf(result.agi)

    # Deductions
    data["f1_line13a"] = format_currency_for_pdf(result.deduction)
    data["f1_line13b"] = format_currency_for_pdf(result.qbi_deduction)
    data["f1_line15"] = format_currency_for_pdf(result.taxable_income)

    # Tax
    data["f1_line16"] = format_currency_for_pdf(result.tax)
    data["f1_line24"] = format_currency_for_pdf(result.total_tax)

    # Payments
    data["f1_line26"] = format_currency_for_pdf(result.estimated_payments)
    data["f1_line33"] = format_currency_for_pdf(result.total_payments)

    # Refund / owed
    if result.overpayment > 0:
        data["f1_line34"] = format_currency_for_pdf(result.overpayment)
    if result.amount_owed > 0:
        data["f1_line37"] = format_currency_for_pdf(result.amount_owed)

    return data
