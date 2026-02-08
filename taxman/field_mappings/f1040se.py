"""Field mapping for Schedule E (Supplemental Income and Loss)."""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_e_data(se_result, profile=None) -> dict:
    """Build field data dict for Schedule E.

    Args:
        se_result: ScheduleEResult from calculator
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02"] = format_ssn(profile.ssn)

    # Part II: Income from partnerships, S corps, estates, trusts
    if se_result.net_rental_income != 0:
        data["f1_line28a"] = format_currency_for_pdf(se_result.net_rental_income)

    if se_result.ordinary_business_income != 0:
        data["f1_line28b"] = format_currency_for_pdf(se_result.ordinary_business_income)

    if se_result.guaranteed_payments != 0:
        data["f1_line28c"] = format_currency_for_pdf(se_result.guaranteed_payments)

    if se_result.interest_income != 0:
        data["f1_line28d"] = format_currency_for_pdf(se_result.interest_income)

    if se_result.capital_gains != 0:
        data["f1_line28e"] = format_currency_for_pdf(se_result.capital_gains)

    data["f1_line26"] = format_currency_for_pdf(se_result.total_schedule_e_income)

    # K-1 partnership details
    if profile:
        for i, k1 in enumerate(profile.schedule_k1s):
            prefix = f"f1_k1_{i+1}"
            data[f"{prefix}_name"] = k1.partnership_name
            if k1.partnership_ein:
                data[f"{prefix}_ein"] = k1.partnership_ein

    return data
