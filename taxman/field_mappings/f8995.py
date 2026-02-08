"""Field mapping for Form 8995 (Qualified Business Income Deduction)."""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_8995_data(qbi_result, form1040_result=None, profile=None) -> dict:
    """Build field data dict for Form 8995.

    Args:
        qbi_result: Form8995Result from calculator
        form1040_result: Form1040Result (for taxable income)
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02"] = format_ssn(profile.ssn)

    # QBI from each business
    if form1040_result:
        for i, sc in enumerate(form1040_result.schedule_c_results):
            prefix = f"f1_biz{i+1}"
            data[f"{prefix}_name"] = sc.business_name
            data[f"{prefix}_qbi"] = format_currency_for_pdf(sc.net_profit_loss)

    data["f1_total_qbi"] = format_currency_for_pdf(qbi_result.total_qbi)
    data["f1_qbi_deduction"] = format_currency_for_pdf(qbi_result.qbi_deduction)

    if form1040_result:
        data["f1_taxable_income"] = format_currency_for_pdf(
            form1040_result.taxable_income + qbi_result.qbi_deduction
        )

    return data
