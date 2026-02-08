"""Field mapping for Form 2555 (Foreign Earned Income Exclusion)."""

from taxman.field_mappings.common import (
    checkbox,
    format_currency_for_pdf,
    format_ssn,
)


def build_2555_data(feie_result, profile=None) -> dict:
    """Build field data dict for Form 2555.

    Args:
        feie_result: Form2555Result from calculator
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02"] = format_ssn(profile.ssn)

        # Part I: General Information
        data["f1_03"] = profile.foreign_country
        data["f1_04"] = profile.street_address
        data["f1_05"] = profile.city

        # Foreign address
        if profile.foreign_address:
            data["f1_06"] = profile.country

        # Physical presence test
        data["f1_physical_presence"] = checkbox(True)
        data["f1_days_abroad"] = str(profile.days_in_foreign_country_2025)

    # Part IV: Foreign Earned Income
    data["f1_line19"] = format_currency_for_pdf(feie_result.foreign_earned_income)

    # Part V: Exclusion
    data["f1_line42"] = format_currency_for_pdf(feie_result.exclusion_amount)

    # Analysis
    data["f1_tax_with"] = format_currency_for_pdf(feie_result.tax_with_feie)
    data["f1_tax_without"] = format_currency_for_pdf(feie_result.tax_without_feie)
    data["f1_savings"] = format_currency_for_pdf(feie_result.savings)

    return data
