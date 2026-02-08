"""Field mapping for Form 2555 (Foreign Earned Income Exclusion).

Field names from inspect_form_fields('f2555') against 2025 IRS PDF.
Page 1: f1_1..f1_54 (Parts I-III: General info, qualifying tests)
Page 2: f2_1..f2_53 (Parts IV-VI: Income, deductions, exclusion)
Page 3: f3_1..f3_27 (Parts VII-IX: Housing)
"""

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
        # Header
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

        # Part I: General Information
        # f1_3: Line 1 — Foreign country name
        data["f1_3[0]"] = profile.foreign_country
        # f1_4: Line 2 — Foreign address
        data["f1_4[0]"] = profile.street_address
        # f1_5: Line 3 — City
        data["f1_5[0]"] = profile.city
        # f1_6: Line 4a — Employer name
        # f1_7: Line 4b — Employer address

        # Part III: Physical Presence Test
        # c1_4: Checkbox for physical presence test
        data["c1_4[0]"] = True
        # f1_17: Line 16 — Days present in foreign country
        data["f1_17[0]"] = str(profile.days_in_foreign_country_2025)

    # ── Page 2: Parts IV-VI ──
    # Part IV: Foreign Earned Income
    # f2_1: Line 19 — Wages/salaries/tips
    # f2_2: Line 20 — Allowances, reimbursements, etc.
    # f2_3: Line 21 — Total foreign earned income
    # For self-employed, line 22 (Schedule C net profit):
    data["f2_4[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)
    # f2_5: Line 23 — Other foreign earned income
    # f2_6: Line 24 — Add lines 19-23
    data["f2_6[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)

    # Part V: Figuring the Foreign Earned Income Exclusion
    # f2_25: Line 42 — Foreign earned income exclusion
    data["f2_25[0]"] = format_currency_for_pdf(feie_result.exclusion_amount)

    # f2_26: Line 43 — Housing deduction
    # f2_27: Line 44 — Total exclusion
    data["f2_27[0]"] = format_currency_for_pdf(feie_result.exclusion_amount)

    return data
