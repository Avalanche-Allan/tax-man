"""Field mapping for Form 8995 (Qualified Business Income Deduction — Simplified).

Field names from inspect_form_fields('f8995') against 2025 IRS PDF.
Single page: f1_01..f1_33
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_8995_data(qbi_result, form1040_result=None, profile=None) -> dict:
    """Build field data dict for Form 8995.

    Args:
        qbi_result: Form8995Result from calculator
        form1040_result: Form1040Result (for taxable income)
        profile: TaxpayerProfile
    """
    data = {}

    # Header
    if profile:
        data["f1_01[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # Lines 1-5: QBI from each business (up to 5 rows)
    # Each row: f1_03 = business name/EIN, f1_05 = QBI amount
    if form1040_result:
        field_idx = 3  # Starting field index for business rows
        for i, sc in enumerate(form1040_result.schedule_c_results[:5]):
            data[f"f1_{field_idx:02d}[0]"] = sc.business_name
            data[f"f1_{field_idx + 2:02d}[0]"] = format_currency_for_pdf(sc.net_profit_loss)
            field_idx += 3  # Each row uses 3 fields (name, EIN, amount)

    # f1_18: Line 6 — Total QBI
    data["f1_18[0]"] = format_currency_for_pdf(qbi_result.total_qbi)

    # f1_19: Line 7 — QBI component (20% of Line 6)
    data["f1_19[0]"] = format_currency_for_pdf(qbi_result.total_qbi * 0.20)

    # f1_20: Line 8 — Qualified REIT dividends/PTP (if any)
    # f1_21: Line 9 — Total QBI deduction before limit

    # f1_22: Line 10 — Taxable income before QBI
    if form1040_result:
        data["f1_22[0]"] = format_currency_for_pdf(
            form1040_result.taxable_income + qbi_result.qbi_deduction
        )

    # f1_23: Line 11 — Net capital gain
    # f1_24: Line 12 — Subtract line 11 from line 10
    # f1_25: Line 13 — Income limitation (20% of line 12)

    # f1_26: Line 14 — QBI deduction (lesser of lines 9 and 13)
    data["f1_26[0]"] = format_currency_for_pdf(qbi_result.qbi_deduction)

    # f1_27: Line 15 — Total QBI deduction
    data["f1_27[0]"] = format_currency_for_pdf(qbi_result.qbi_deduction)

    return data
