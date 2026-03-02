"""Field mapping for Schedule SE (Self-Employment Tax).

Field names discovered via diagnostic fill against 2025 IRS PDF
(irs.gov/pub/irs-pdf/f1040sse.pdf, Created 5/7/25).

Page 1: f1_1..f1_22, c1_1
Page 2: f2_1..f2_4
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
        # f1_1: Name of person with self-employment income
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        # f1_2: Social security number
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # Part I — Self-Employment Tax
    # f1_3: Line 1a — Net farm profit (skip)
    # f1_4: Line 1b — Conservation Reserve Program (skip)

    # f1_5: Line 2 — Net profit from Schedule C, line 31
    data["f1_5[0]"] = format_currency_for_pdf(se_result.net_se_earnings)
    # f1_6: Line 3 — Combine lines 1a, 1b, and 2
    data["f1_6[0]"] = format_currency_for_pdf(se_result.net_se_earnings)
    # f1_7: Line 4a — Multiply line 3 by 92.35%
    data["f1_7[0]"] = format_currency_for_pdf(se_result.taxable_se_earnings)
    # f1_8: Line 4b — Optional methods total (skip)
    # f1_9: Line 4c — Combine lines 4a and 4b
    data["f1_9[0]"] = format_currency_for_pdf(se_result.taxable_se_earnings)
    # f1_10: Line 5a — Church employee income (skip)
    # f1_11: Line 5b — Church employee × 92.35% (skip)
    # f1_12: Line 6 — Add lines 4c and 5b
    data["f1_12[0]"] = format_currency_for_pdf(se_result.taxable_se_earnings)

    # Line 7 ($176,100) is pre-printed

    # f1_14: Line 8a — W-2 social security wages
    w2_ss = getattr(se_result, 'w2_ss_wages', 0) or 0
    if w2_ss > 0:
        data["f1_14[0]"] = format_currency_for_pdf(w2_ss)
    # f1_15: Line 8b — Unreported tips (skip)
    # f1_16: Line 8c — Form 8919 wages (skip)
    # f1_17: Line 8d — Add lines 8a, 8b, 8c
    if w2_ss > 0:
        data["f1_17[0]"] = format_currency_for_pdf(w2_ss)

    # f1_18: Line 9 — Subtract line 8d from line 7
    ss_wage_base = 176100
    remaining_base = max(ss_wage_base - w2_ss, 0)
    data["f1_18[0]"] = format_currency_for_pdf(remaining_base)

    # f1_19: Line 10 — Multiply smaller of line 6 or line 9 by 12.4%
    ss_portion = min(se_result.taxable_se_earnings, remaining_base) * 0.124
    data["f1_19[0]"] = format_currency_for_pdf(round(ss_portion))

    # f1_20: Line 11 — Multiply line 6 by 2.9%
    medicare_portion = se_result.taxable_se_earnings * 0.029
    data["f1_20[0]"] = format_currency_for_pdf(round(medicare_portion))

    # f1_21: Line 12 — Self-employment tax (add lines 10 and 11)
    data["f1_21[0]"] = format_currency_for_pdf(se_result.se_tax)

    # f1_22: Line 13 — Deductible part (50% of SE tax)
    data["f1_22[0]"] = format_currency_for_pdf(se_result.deductible_se_tax)

    return data
