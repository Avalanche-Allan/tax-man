"""Field mapping for Schedule SE (Self-Employment Tax).

Field names from inspect_form_fields('f1040sse') against 2025 IRS PDF.
Page 1: f1_1..f1_22 (Short Schedule SE, Section A)
Page 2: f2_1..f2_4 (Long Schedule SE, Section B — rarely needed)
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_se_data(se_result, profile=None) -> dict:
    """Build field data dict for Schedule SE.

    Args:
        se_result: ScheduleSEResult from calculator
        profile: TaxpayerProfile
    """
    data = {}

    # Header
    if profile:
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # Section A — Short Schedule SE
    # f1_3: Line 1a — Net farm profit
    # f1_4: Line 1b — Reserved
    # f1_5: Line 2 — Net SE income (from Schedule C, etc.)
    data["f1_5[0]"] = format_currency_for_pdf(se_result.net_se_earnings)
    # f1_6: Line 3 — Combine lines 1a, 1b, and 2
    data["f1_6[0]"] = format_currency_for_pdf(se_result.net_se_earnings)
    # f1_7: Line 4a — If line 3 > 0, multiply by 92.35%
    data["f1_7[0]"] = format_currency_for_pdf(se_result.taxable_se_earnings)
    # f1_8-f1_11: Lines 4b-7 (wages from W-2, SS base calc)
    # f1_12: Line 8a — Net SE earnings for SS (lesser of 4a/4b or wage base)
    # f1_13: Line 8b — SS tax rate
    # f1_14: Line 9 — SS tax portion
    # f1_15: Line 10 — Medicare tax (2.9% of line 4a)
    # f1_16: Line 11 — Sum of SS + Medicare
    # f1_17: Line 12 — Self-employment tax
    data["f1_17[0]"] = format_currency_for_pdf(se_result.se_tax)
    # f1_18: Line 13 — Deductible part (50%)
    data["f1_18[0]"] = format_currency_for_pdf(se_result.deductible_se_tax)

    return data
