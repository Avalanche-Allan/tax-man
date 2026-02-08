"""Field mapping for Schedule SE (Self-Employment Tax)."""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_se_data(se_result, profile=None) -> dict:
    """Build field data dict for Schedule SE.

    Args:
        se_result: ScheduleSEResult from calculator
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02"] = format_ssn(profile.ssn)

    data["f1_line3"] = format_currency_for_pdf(se_result.net_se_earnings)
    data["f1_line4a"] = format_currency_for_pdf(se_result.taxable_se_earnings)
    data["f1_line12"] = format_currency_for_pdf(se_result.se_tax)
    data["f1_line13"] = format_currency_for_pdf(se_result.deductible_se_tax)

    return data
