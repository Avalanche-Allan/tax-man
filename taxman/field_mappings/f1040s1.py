"""Field mapping for Schedule 1 (Additional Income and Adjustments).

Field names discovered via widget-position dump against the 2025 IRS PDF
(irs.gov/pub/irs-pdf/f1040s1.pdf, Created 7/25/25).

Page 1 (Part I — Additional Income):
  f1_01=Name, f1_02=SSN, f1_03=1099-K error amount
  f1_04=1, f1_05=2a, f1_06=2b date, f1_07=3 (business income),
  f1_08=4, f1_09=5 (Schedule E), f1_10=6, f1_12=7,
  f1_13=8a NOL (pre-parenthesized — enter positive),
  f1_16=8d FEIE (pre-parenthesized — enter positive),
  f1_35/f1_36=8z description/amount, f1_37=9, f1_38=10

Page 2 (Part II — Adjustments):
  f2_05=15 (deductible SE tax), f2_06=16, f2_07=17 (SE health
  insurance), f2_29=25, f2_30=26 (total adjustments)
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def _line_amount(result, form: str, line: str) -> float:
    """Sum of LineItem amounts for a given form/line."""
    return sum(
        li.amount for li in result.lines
        if li.form == form and li.line == line
    )


def build_schedule_1_data(result, profile=None) -> dict:
    """Build field data dict for Schedule 1.

    Args:
        result: Form1040Result
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02[0]"] = format_ssn(profile.ssn) if profile.ssn else ""

    # ── Part I: Additional Income ──
    # Line 3: Business income from Schedule C
    line3 = sum(sc.net_profit_loss for sc in result.schedule_c_results)
    if line3 != 0:
        data["f1_07[0]"] = format_currency_for_pdf(line3)

    # Line 5: Rental real estate, partnerships, S corps (Schedule E)
    line5 = _line_amount(result, "Schedule 1", "5")
    if line5 != 0:
        data["f1_09[0]"] = format_currency_for_pdf(line5)

    # Line 8a: Net operating loss (pre-parenthesized field — positive)
    nol = profile.nol_carryforward if profile else 0.0
    if nol > 0:
        data["f1_13[0]"] = format_currency_for_pdf(nol)

    # Line 8d: Foreign earned income exclusion (pre-parenthesized)
    feie_exclusion = (
        result.feie.net_exclusion
        if result.feie and result.feie.net_exclusion > 0 else 0.0
    )
    if feie_exclusion > 0:
        data["f1_16[0]"] = format_currency_for_pdf(feie_exclusion)

    # Line 9: Total other income (8a through 8z)
    line9 = -nol - feie_exclusion
    if line9 != 0:
        data["f1_37[0]"] = format_currency_for_pdf(line9)

    # Line 10: Additional income → Form 1040 Line 8
    data["f1_38[0]"] = format_currency_for_pdf(result.schedule_1_income)

    # ── Part II: Adjustments to Income ──
    # Line 15: Deductible part of SE tax
    if result.schedule_se and result.schedule_se.deductible_se_tax > 0:
        data["f2_05[0]"] = format_currency_for_pdf(
            result.schedule_se.deductible_se_tax
        )

    # Line 17: Self-employed health insurance deduction
    line17 = _line_amount(result, "Schedule 1", "17")
    if line17 > 0:
        data["f2_07[0]"] = format_currency_for_pdf(line17)

    # Line 26: Total adjustments → Form 1040 Line 10
    if result.adjustments > 0:
        data["f2_30[0]"] = format_currency_for_pdf(result.adjustments)

    return data
