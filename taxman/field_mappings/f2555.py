"""Field mapping for Form 2555 (Foreign Earned Income Exclusion).

Field names discovered via diagnostic fill against 2025 IRS PDF
(irs.gov/pub/irs-pdf/f2555.pdf, Created 5/14/25).

Page 1: f1_1..f1_54 (Parts I-II: General info, bona fide residence)
  f1_1=Name, f1_2=SSN, f1_3=Line 1 foreign address, f1_4=Line 2 occupation
  f1_5=Line 3 employer name, f1_8=Line 5e other specify
  f1_9=Line 6a last year filed, f1_10=Line 6d revocation info
  f1_11=Line 7 citizenship, f1_12=Line 8b separate residence
  f1_13=Line 9 tax home, f1_14=Line 9 dates
  f1_15=Line 10 begin date, f1_16=Line 10 end date
  f1_17=Line 12b family period
  Checkboxes: c1_1..c1_5 (employer type), c1_6/c1_7 (Line 6b/6c)

Page 2: f2_1..f2_53 (Part III physical presence, Part IV income)
  f2_1=Line 16 from date, f2_2=Line 16 through date
  f2_3=Line 17 country of employment
  f2_4=Line 18 row 1 country name, f2_5..f2_9=row 1 cols b-f
  f2_29=Line 20a business income, f2_51=Line 24, f2_53=Line 26

Page 3: f3_1..f3_27 (Parts V-IX: exclusion calculation)
  f3_1=Line 27, f3_13=Line 37 ($130,000), f3_14=Line 38 days
  f3_17=Line 40, f3_18=Line 41, f3_19=Line 42 exclusion
  f3_20=Line 43, f3_21=Line 44 allocable deductions, f3_22=Line 45
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
        # f1_1: Name shown on Form 1040
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        # f1_2: Your social security number
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

        # Part I: General Information
        # f1_3: Line 1 — Your foreign address (including country)
        data["f1_3[0]"] = profile.foreign_country or ""
        # f1_4: Line 2 — Your occupation
        data["f1_4[0]"] = profile.occupation or "Self-employed"
        # f1_5: Line 3 — Employer's name (self-employed = business name)
        if profile.businesses:
            data["f1_5[0]"] = profile.businesses[0].business_name
        else:
            data["f1_5[0]"] = "Self-employed"

        # Line 5 employer type checkboxes:
        # c1_1=a foreign entity, c1_2=b US company, c1_3=c Self,
        # c1_4=d foreign affiliate of US company
        data["c1_3[0]"] = True  # Self-employed

        # f1_11: Line 7 — Of what country are you a citizen/national?
        data["f1_11[0]"] = "United States"

        # Part III: Physical Presence Test (page 2)
        # f2_1: Line 16 — 12-month period from
        data["f2_1[0]"] = "01/01/2025"
        # f2_2: Line 16 — through
        data["f2_2[0]"] = "12/31/2025"
        # f2_3: Line 17 — Principal country of employment
        data["f2_3[0]"] = profile.foreign_country or ""

        # Line 18 table — row 1: country name in column (a)
        # f2_4: (a) Name of country
        data["f2_4[0]"] = profile.foreign_country or ""
        # f2_7: (d) Full days present in country
        days = profile.days_in_foreign_country_2025 or 0
        data["f2_7[0]"] = str(days)

    # ── Page 2: Part IV — Foreign Earned Income ──
    # f2_29: Line 20a — Allowable share of income in a business/profession
    data["f2_29[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)
    # f2_51: Line 24 — Add lines 19 through 21d, line 22g, and line 23
    data["f2_51[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)
    # f2_53: Line 26 — 2025 foreign earned income
    data["f2_53[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)

    # ── Page 3: Part V — All Taxpayers ──
    # f3_1: Line 27 — Enter the amount from line 26
    data["f3_1[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)

    # Part VII: Foreign Earned Income Exclusion
    # f3_13: Line 37 — Maximum exclusion ($130,000)
    data["f3_13[0]"] = "130,000"
    # f3_14: Line 38 — Number of days in qualifying period
    if profile:
        days = profile.days_in_foreign_country_2025 or 365
        data["f3_14[0]"] = str(days)

    # f3_15: Line 39 — Decimal (days/365)
    if profile:
        days = profile.days_in_foreign_country_2025 or 365
        ratio = days / 365.0
        if ratio >= 1.0:
            data["f3_15[0]"] = "1.000"
        else:
            data["f3_15[0]"] = f"{ratio:.3f}"

    # f3_17: Line 40 — Multiply line 37 by line 39
    if profile:
        days = profile.days_in_foreign_country_2025 or 365
        max_exclusion = round(130000 * min(days / 365.0, 1.0))
        data["f3_17[0]"] = format_currency_for_pdf(max_exclusion)
    else:
        max_exclusion = 130000

    # f3_18: Line 41 — Subtract line 36 from line 27 (no housing exclusion)
    data["f3_18[0]"] = format_currency_for_pdf(feie_result.foreign_earned_income)

    # f3_19: Line 42 — Foreign earned income exclusion (lesser of line 40 or 41)
    data["f3_19[0]"] = format_currency_for_pdf(feie_result.exclusion_amount)

    # Part VIII: Combined exclusion
    # f3_20: Line 43 — Add lines 36 and 42 (no housing = just line 42)
    data["f3_20[0]"] = format_currency_for_pdf(feie_result.exclusion_amount)

    # f3_21: Line 44 — Deductions allocable to excluded income
    allocable_deductions = getattr(feie_result, 'allocable_deductions', 0) or 0
    if allocable_deductions > 0:
        data["f3_21[0]"] = format_currency_for_pdf(allocable_deductions)

    # f3_22: Line 45 — Subtract line 44 from line 43 (goes to Schedule 1, line 8d)
    data["f3_22[0]"] = format_currency_for_pdf(
        feie_result.exclusion_amount - allocable_deductions
    )

    return data
