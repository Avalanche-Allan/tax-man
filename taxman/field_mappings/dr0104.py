"""Field mappings for Colorado DR 0104 and DR 0104PN (2025).

Unlike IRS forms, Colorado PDFs use human-readable field names
("Form Question 13" = DR 0104 line 13, "Federal Infomation Line 4" =
DR 0104PN line 4 federal column — note the DOR's "Infomation" typo).
Field names verified by widget dump + visual render of the 2025 PDFs
(DR 0104 10/03/25, DR 0104PN 09/24/25).

DR 0104 residency buttons: RB1=Full-Year, RB2=Part-Year/Nonresident,
RB3=Abroad on due date. Page 7: RB9/RB10 = third-party designee No/Yes.

DR 0104PN taxpayer status: RB1=Full-Year Nonresident, RB2=Full-Year
Resident, RB3=Military, RB4=Part-Year. RB9..RB12 = federal form filed
(1040 / 1040NR / 1040SR / Other).

Limitations: additions lines 2-9 only carry the SALT addback (line 2);
the QBI and standard-deduction addbacks (lines 3-4, AGI > $300k/$500k)
are not modeled. Subtractions (line 11) would require the DR 0104AD
schedule, which is not generated.
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def _line_amount(result, form: str, line: str) -> float:
    return sum(
        li.amount for li in result.lines
        if li.form == form and li.line == line
    )


def _co_withholding(profile) -> float:
    """Colorado tax withheld from W-2s and 1099s."""
    if not profile:
        return 0.0
    return sum(
        w2.state_tax_withheld for w2 in profile.forms_w2
        if w2.state == "CO"
    )


def build_dr0104_data(co_result, federal_result, profile) -> dict:
    """Build field data dict for Colorado DR 0104.

    Args:
        co_result: ColoradoForm104Result
        federal_result: Form1040Result
        profile: TaxpayerProfile
    """
    data = {}

    # ── Page 1: Residency status and taxpayer info ──
    if co_result.is_nonresident:
        data["widget:RB2"] = True  # Part-Year or Nonresident (attach DR 0104PN)
    else:
        data["widget:RB1"] = True  # Full-Year
    if profile.foreign_address:
        data["widget:RB3"] = True  # Abroad on due date

    data["Last Name"] = profile.last_name
    data["First Name"] = profile.first_name
    if profile.date_of_birth:
        data["Date of Birth"] = profile.date_of_birth
    data["Social Security Number"] = format_ssn(profile.ssn) if profile.ssn else ""

    # ── Page 2: Contact information ──
    if profile.street_address:
        data["Physical Street Address 2"] = profile.street_address
    if profile.phone:
        data["Phone Number 3"] = profile.phone
    if profile.city:
        data["City 4"] = profile.city
    if profile.state:
        data["State 5"] = profile.state
    if profile.zip_code:
        data["ZIP Code 4"] = profile.zip_code
    if profile.foreign_address and profile.country:
        data["Foreign Country"] = profile.country

    # ── Page 3: Line 1 + additions ──
    # Line 1: Federal taxable income (1040 line 15)
    data["Form Question 1"] = (
        format_currency_for_pdf(co_result.federal_taxable_income) or "0"
    )
    # Line 2: State income tax addback (itemizers only)
    if co_result.co_additions > 0:
        data["Form Question 2"] = format_currency_for_pdf(co_result.co_additions)
    # Line 10: Subtotal of lines 1-7 and 9
    line10 = co_result.federal_taxable_income + co_result.co_additions
    data["Form Question 10"] = format_currency_for_pdf(line10) or "0"

    # ── Page 4: Subtractions, tax ──
    # Line 11: Subtractions (DR 0104AD — not generated; engine total)
    if co_result.co_subtractions > 0:
        data["Form Question 11"] = format_currency_for_pdf(
            co_result.co_subtractions
        )
    # Line 12: Colorado taxable income
    data["Form Question 12"] = (
        format_currency_for_pdf(co_result.co_taxable_income) or "0"
    )
    # Line 13: Colorado tax (from DR 0104PN line 36 for nonresidents)
    data["Form Question 13"] = format_currency_for_pdf(co_result.co_tax) or "0"
    # Line 16: Subtotal lines 13-15 (no AMT/recapture modeled)
    data["Form Question 16"] = format_currency_for_pdf(co_result.co_tax) or "0"
    # Line 21: Net income tax (no nonrefundable credits modeled)
    data["Form Question 21"] = format_currency_for_pdf(co_result.co_tax) or "0"
    # Line 23: Net tax and required repayment
    data["Form Question 23"] = format_currency_for_pdf(co_result.co_tax) or "0"

    # ── Page 5: Prepayments ──
    withholding = _co_withholding(profile)
    if withholding > 0:
        data["Form Question 24"] = format_currency_for_pdf(withholding)
    # Line 33: Subtotal of lines 24-32
    data["Form Question 33"] = format_currency_for_pdf(withholding) or "0"

    # ── Page 6: TABOR (full-year residents only) + balance ──
    # Line 39: Sum of lines 33 and 38 (38 = 0 for nonresidents)
    data["Form Question 39"] = format_currency_for_pdf(withholding) or "0"

    net_tax = co_result.co_tax
    if withholding > net_tax:
        # Line 40: Overpayment / Line 42: Refund
        overpaid = round(withholding - net_tax, 2)
        data["Form Question 40"] = format_currency_for_pdf(overpaid)
        data["Form Question 42"] = format_currency_for_pdf(overpaid)
    else:
        # Line 43: Net tax due / Line 47: Amount you owe
        owed = round(net_tax - withholding, 2)
        data["Form Question 43"] = format_currency_for_pdf(owed) or "0"
        data["Form Question 47"] = format_currency_for_pdf(owed) or "0"

    # ── Page 7: Third-party designee — No ──
    data["widget:RB9"] = True

    return data


def build_dr0104pn_data(co_result, federal_result, profile) -> dict:
    """Build field data dict for Colorado DR 0104PN (nonresident
    apportionment schedule).

    Federal column comes from the federal return; Colorado column
    places all CO-source income on line 17 (supplemental income /
    Schedule E), which covers both direct CO rentals and CO
    partnership K-1 income.
    """
    data = {}

    data["Name"] = f"{profile.first_name} {profile.last_name}"
    data["SSN or ITIN"] = format_ssn(profile.ssn) if profile.ssn else ""

    # Taxpayer is: Full-Year Nonresident
    data["widget:RB1"] = True
    # Federal form filed: 1040
    data["widget:RB9"] = True

    fed = format_currency_for_pdf  # alias for brevity

    # Line 4: Wages (1040 line 1z)
    if federal_result.wage_income != 0:
        data["Federal Infomation Line 4"] = fed(federal_result.wage_income)
    # Line 6: Taxable interest + ordinary dividends
    interest_div = (federal_result.taxable_interest
                    + federal_result.ordinary_dividends)
    if interest_div != 0:
        data["Federal Infomation Line 6"] = fed(interest_div)
    # Line 10: Capital gains (1040 line 7)
    if federal_result.capital_gain_loss != 0:
        data["Federal Infomation Line 10"] = fed(federal_result.capital_gain_loss)
    # Line 12: 1040 lines 4b, 5b, 6b
    if federal_result.ira_distributions != 0:
        data["Federal Infomation Line 12"] = fed(federal_result.ira_distributions)
    # Line 14: Business income (Schedule C)
    business = sum(sc.net_profit_loss for sc in federal_result.schedule_c_results)
    if business != 0:
        data["Federal Infomation Line 14"] = fed(business)
    # Line 16: Supplemental income (Schedule 1 line 5 / Schedule E)
    sch_e = _line_amount(federal_result, "Schedule 1", "5")
    if sch_e != 0:
        data["Federal Infomation Line 16"] = fed(sch_e)
    # Line 18: Other income (Schedule 1 lines 1, 2a, and 9)
    other = round(federal_result.schedule_1_income - business - sch_e, 2)
    if other != 0:
        data["Federal Infomation Line 18"] = fed(other)
        descriptions = []
        if federal_result.feie:
            descriptions.append("Foreign earned income exclusion (Form 2555)")
        if profile.nol_carryforward > 0:
            descriptions.append("Net operating loss deduction")
        data["List Type - Line 18"] = "; ".join(descriptions)
    # Line 20: Total income (1040 line 9)
    data["Federal Infomation Line 20"] = fed(federal_result.total_income) or "0"
    # Line 22: Federal adjustments (1040 line 10)
    if federal_result.adjustments != 0:
        data["Federal Infomation Line 22"] = fed(federal_result.adjustments)
        data["List Type - Line 22"] = (
            "Deductible SE tax; SE health insurance"
        )
    # Line 24: Federal AGI
    data["Federal Infomation Line 24"] = fed(federal_result.agi) or "0"
    # Line 26: Additions (DR 0104 lines 5-7 and 9 — none modeled)
    # Line 28: Total of lines 24 and 26
    data["Federal Infomation Line 28"] = fed(federal_result.agi) or "0"
    # Line 30: Subtractions (DR 0104 line 11)
    if co_result.co_subtractions > 0:
        data["Federal Infomation Line 30"] = fed(co_result.co_subtractions)
    # Line 32: Modified federal AGI
    data["Federal Infomation Line 32"] = (
        fed(co_result.federal_modified_agi) or "0"
    )

    # ── Colorado column ──
    co_income = co_result.co_source_income
    # Line 17: CO-source supplemental income (rentals, K-1s)
    if co_income != 0:
        data["Colorado Information Line 17"] = fed(co_income)
    # Line 21: Total Colorado income
    data["Colorado Information Line 21"] = fed(co_income) or "0"
    # Line 23: CO share of federal adjustments (0 — SE income not CO-source)
    # Line 25: Colorado AGI
    data["Colorado Information Line 25"] = fed(co_income) or "0"
    # Line 29: Total of lines 25 and 27
    data["Colorado Information Line 29"] = fed(co_income) or "0"
    # Line 33: Modified Colorado AGI
    data["Colorado Information Line 33"] = fed(co_result.co_modified_agi) or "0"

    # Line 34: Percentage (federal column field, xxx.xxxx)
    data["Federal Infomation Line 34"] = (
        f"{co_result.apportionment_pct * 100:.4f}"
    )
    # Line 35: Tax on DR 0104 line 12 amount (Colorado column field)
    data["Colorado Information Line 35"] = (
        fed(co_result.co_tax_before_apportion) or "0"
    )
    # Line 36: Apportioned tax → DR 0104 line 13 (federal column field)
    data["Federal Infomation Line 36"] = fed(co_result.co_tax) or "0"

    return data
