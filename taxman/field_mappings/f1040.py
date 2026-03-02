"""Field mapping for Form 1040 (2025).

Field names discovered via diagnostic fill against the 2025 IRS fillable PDF
(downloaded from irs.gov/pub/irs-pdf/f1040.pdf, Created 9/5/25).

Page 1 header: f1_01..f1_30 (name, address, filing status, dependents)
Page 1 income: f1_47..f1_75 (Lines 1a through 11a)
Page 2: f2_01..f2_51 (Lines 11b through signature block)
"""

from taxman.field_mappings.common import (
    checkbox,
    format_currency_for_pdf,
    format_ssn,
)


def build_1040_data(result, profile) -> dict:
    """Build field data dict for Form 1040.

    Args:
        result: Form1040Result
        profile: TaxpayerProfile

    Returns:
        Dict mapping PDF field names to values.
    """
    data = {}

    # ── Page 1 Header ──
    # f1_14: Your first name and middle initial
    data["f1_14[0]"] = profile.first_name
    # f1_15: Your last name
    data["f1_15[0]"] = profile.last_name
    # f1_16: Your social security number
    data["f1_16[0]"] = profile.ssn.replace("-", "")

    # Spouse info (for MFS/MFJ)
    if profile.spouse_name:
        # f1_17: Spouse first name
        # f1_18: Spouse last name
        parts = profile.spouse_name.split(None, 1)
        if len(parts) == 2:
            data["f1_17[0]"] = parts[0]
            data["f1_18[0]"] = parts[1]
        else:
            data["f1_17[0]"] = profile.spouse_name
    if profile.spouse_ssn:
        # f1_19: Spouse's social security number
        data["f1_19[0]"] = profile.spouse_ssn.replace("-", "")

    # Address
    # f1_20: Home address (street)
    data["f1_20[0]"] = profile.street_address
    # f1_21: Apt. no.
    # f1_22: City, town, or post office
    data["f1_22[0]"] = profile.city
    # f1_23: State
    data["f1_23[0]"] = profile.state
    # f1_24: ZIP code
    data["f1_24[0]"] = profile.zip_code
    # Foreign address
    if profile.foreign_address:
        # f1_25: Foreign country name
        data["f1_25[0]"] = profile.country
        # f1_26: Foreign province/state/county
        # f1_27: Foreign postal code

    # Do NOT set c1_6[0] (Deceased) or c1_7[0] (Spouse deceased).
    # The source PDF is pre-patched with /AP/N/Off appearances so PyPDFForm
    # leaves them unchecked when omitted from the data dict.

    # Filing status checkboxes
    # c1_1[0]=Single, c1_2[0]=MFJ, c1_3[0]=MFS, c1_4[0]=HOH, c1_5[0]=QSS
    fs_map = {
        "single": "c1_1[0]",
        "mfj": "c1_2[0]",
        "mfs": "c1_3[0]",
        "hoh": "c1_4[0]",
        "qss": "c1_5[0]",
    }
    fs_field = fs_map.get(profile.filing_status.value)
    if fs_field:
        data[fs_field] = True

    # MFS spouse full name on line below checkbox
    if profile.filing_status.value == "mfs" and profile.spouse_name:
        data["f1_28[0]"] = profile.spouse_name

    # ── Page 1 Income (f1_47..f1_75) ──
    # f1_47: Line 1a — Wages (W-2 box 1)
    if result.wage_income > 0:
        data["f1_47[0]"] = format_currency_for_pdf(result.wage_income)
    # f1_57: Line 1z — Add lines 1a through 1h
    if result.wage_income > 0:
        data["f1_57[0]"] = format_currency_for_pdf(result.wage_income)
    # f1_58: Line 2a — Tax-exempt interest
    if result.tax_exempt_interest > 0:
        data["f1_58[0]"] = format_currency_for_pdf(result.tax_exempt_interest)
    # f1_59: Line 2b — Taxable interest
    if result.taxable_interest > 0:
        data["f1_59[0]"] = format_currency_for_pdf(result.taxable_interest)
    # f1_60: Line 3a — Qualified dividends
    if result.qualified_dividends > 0:
        data["f1_60[0]"] = format_currency_for_pdf(result.qualified_dividends)
    # f1_61: Line 3b — Ordinary dividends
    if result.ordinary_dividends > 0:
        data["f1_61[0]"] = format_currency_for_pdf(result.ordinary_dividends)
    # f1_62: Line 4a — IRA distributions (gross)
    if result.ira_distributions > 0:
        data["f1_62[0]"] = format_currency_for_pdf(result.ira_distributions)
    # f1_63: Line 4b — Taxable IRA amount
    if result.ira_distributions > 0:
        data["f1_63[0]"] = format_currency_for_pdf(result.ira_distributions)
    # f1_65: Line 5a — Pensions and annuities (skip, not used)
    # f1_66: Line 5b — Taxable pensions (skip, not used)
    # f1_68: Line 6a — Social security benefits (skip, not used)
    # f1_69: Line 6b — Taxable SS (skip, not used)
    # f1_70: Line 7a — Capital gain or (loss)
    if result.capital_gain_loss != 0:
        data["f1_70[0]"] = format_currency_for_pdf(result.capital_gain_loss)
    # f1_72: Line 8 — Additional income from Schedule 1
    sched1_income = (result.total_income - result.wage_income
                     - result.taxable_interest - result.ordinary_dividends
                     - result.capital_gain_loss - result.ira_distributions)
    if sched1_income != 0:
        data["f1_72[0]"] = format_currency_for_pdf(sched1_income)
    # f1_73: Line 9 — Total income
    data["f1_73[0]"] = format_currency_for_pdf(result.total_income)
    # f1_74: Line 10 — Adjustments to income (Schedule 1)
    if result.adjustments > 0:
        data["f1_74[0]"] = format_currency_for_pdf(result.adjustments)
    # f1_75: Line 11a — AGI
    data["f1_75[0]"] = format_currency_for_pdf(result.agi)

    # ── Page 2 (f2_xx fields) ──
    # f2_01: Line 11b — AGI repeated
    data["f2_01[0]"] = format_currency_for_pdf(result.agi)
    # f2_02: Line 12e — Standard deduction or itemized
    data["f2_02[0]"] = format_currency_for_pdf(result.deduction)
    # f2_03: Line 13a — QBI deduction
    if result.qbi_deduction > 0:
        data["f2_03[0]"] = format_currency_for_pdf(result.qbi_deduction)
    # f2_04: Line 13b — Additional deductions (Schedule 1-A)
    # f2_05: Line 14 — Total deductions (12e + 13a + 13b)
    total_deductions = result.deduction + result.qbi_deduction
    data["f2_05[0]"] = format_currency_for_pdf(total_deductions)
    # f2_06: Line 15 — Taxable income
    data["f2_06[0]"] = format_currency_for_pdf(result.taxable_income)
    # f2_08: Line 16 — Tax
    data["f2_08[0]"] = format_currency_for_pdf(result.tax)
    # f2_09: Line 17 — Amount from Schedule 2, line 3 (AMT + excess premium tax credit)
    if result.amt > 0:
        data["f2_09[0]"] = format_currency_for_pdf(result.amt)
    # f2_10: Line 18 — Add lines 16 and 17
    data["f2_10[0]"] = format_currency_for_pdf(result.tax + result.amt)
    # f2_11: Line 19 — Child tax credit / credit for other dependents
    if result.nonrefundable_credits > 0:
        data["f2_11[0]"] = format_currency_for_pdf(result.nonrefundable_credits)
    # f2_12: Line 20 — Amount from Schedule 3, line 8
    # f2_13: Line 21 — Add lines 19 and 20
    if result.nonrefundable_credits > 0:
        data["f2_13[0]"] = format_currency_for_pdf(result.nonrefundable_credits)
    # f2_14: Line 22 — Subtract line 21 from line 18
    tax_less_credits = max(result.tax + result.amt - result.nonrefundable_credits, 0)
    data["f2_14[0]"] = format_currency_for_pdf(tax_less_credits)
    # f2_15: Line 23 — Other taxes (SE tax, Addl Medicare, NIIT from Schedule 2)
    other_taxes = result.se_tax + result.additional_medicare + result.niit + result.early_withdrawal_penalty
    data["f2_15[0]"] = format_currency_for_pdf(other_taxes)
    # f2_16: Line 24 — Total tax
    data["f2_16[0]"] = format_currency_for_pdf(result.total_tax)

    # Payments
    # f2_17: Line 25a — W-2 withholding
    if result.withholding > 0:
        data["f2_17[0]"] = format_currency_for_pdf(result.withholding)
    # f2_18: Line 25b — 1099 withholding
    # f2_19: Line 25c — Other withholding
    # f2_20: Line 25d — Total withholding
    if result.withholding > 0:
        data["f2_20[0]"] = format_currency_for_pdf(result.withholding)
    # f2_21: Line 26 — Estimated tax payments
    if result.estimated_payments > 0:
        data["f2_21[0]"] = format_currency_for_pdf(result.estimated_payments)

    # f2_28: Line 32 — Total other payments and refundable credits
    # f2_29: Line 33 — Total payments
    data["f2_29[0]"] = format_currency_for_pdf(result.total_payments)

    # Refund / amount owed
    if result.overpayment > 0:
        # f2_30: Line 34 — Overpaid
        data["f2_30[0]"] = format_currency_for_pdf(result.overpayment)
        # f2_31: Line 35a — Refunded to you
        data["f2_31[0]"] = format_currency_for_pdf(result.overpayment)
    if result.amount_owed > 0:
        # f2_35: Line 37 — Amount you owe
        data["f2_35[0]"] = format_currency_for_pdf(result.amount_owed)

    # Note: f2_22 is "former spouse SSN for estimated tax" — no page 2 SSN header exists

    return data
