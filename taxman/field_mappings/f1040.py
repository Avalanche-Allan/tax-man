"""Field mapping for Form 1040 (2025).

Field names discovered via inspect_form_fields('f1040') against
the 2025 IRS fillable PDF (downloaded from irs.gov/pub/irs-pdf/f1040.pdf).

PyPDFForm field key format: f{page}_{seq}[0] for text, c{page}_{seq}[0] for checkboxes.
Page 1: f1_01..f1_75, c1_1..c1_44
Page 2: f2_01..f2_51, c2_1..c2_18
"""

from taxman.field_mappings.common import (
    checkbox,
    format_currency_for_pdf,
    format_ssn,
    split_ssn,
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
    # f1_01: Your first name and middle initial
    data["f1_01[0]"] = profile.first_name
    # f1_02: Your last name
    data["f1_02[0]"] = profile.last_name
    # f1_03: SSN (first 2 digits — maxLength 2)
    # f1_04: Spouse first name
    # f1_05-f1_10: SSN split fields (maxLength 2/4 pattern for xxx-xx-xxxx)
    ssn1, ssn2, ssn3 = split_ssn(profile.ssn)
    if ssn1:
        data["f1_03[0]"] = ssn1[:2]
        data["f1_05[0]"] = ssn1[2:] + ssn2[:1]  # This is a guess; IRS fields vary by year
    # Full SSN in the dedicated field
    data["f1_16[0]"] = profile.ssn.replace("-", "")

    # Filing status checkboxes (c1_1..c1_5 = Single, MFJ, MFS, HOH, QSS)
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

    # Spouse info
    if profile.spouse_name:
        data["f1_04[0]"] = profile.spouse_name
    if profile.spouse_ssn:
        data["f1_19[0]"] = profile.spouse_ssn.replace("-", "")

    # Address fields (f1_20..f1_27 are address block)
    data["f1_20[0]"] = profile.street_address
    data["f1_21[0]"] = profile.city
    data["f1_22[0]"] = profile.state
    data["f1_23[0]"] = profile.zip_code
    if profile.foreign_address:
        data["f1_24[0]"] = profile.country
        data["f1_25[0]"] = profile.foreign_country

    # Occupation
    data["f1_11[0]"] = profile.occupation

    # ── Income lines (f1_47+ on Page 1) ──
    # The income fields start after the header/dependents section
    # f1_47: Line 1a — Wages
    data["f1_47[0]"] = format_currency_for_pdf(result.wage_income)
    # f1_48: Line 1z — Total from additional income
    # f1_49: Line 1 — Total (add 1a through 1z)
    # f1_50: Line 2a — Tax-exempt interest
    data["f1_50[0]"] = format_currency_for_pdf(result.tax_exempt_interest)
    # f1_51: Line 2b — Taxable interest
    data["f1_51[0]"] = format_currency_for_pdf(result.taxable_interest)
    # f1_52: Line 3a — Qualified dividends
    data["f1_52[0]"] = format_currency_for_pdf(result.qualified_dividends)
    # f1_53: Line 3b — Ordinary dividends
    data["f1_53[0]"] = format_currency_for_pdf(result.ordinary_dividends)
    # f1_54: Line 4a — IRA distributions
    # f1_55: Line 4b — Taxable IRA
    # f1_56: Line 5a — Pensions/annuities
    # f1_57: Line 5b — Taxable pensions
    # f1_58: Line 6a — SS benefits
    # f1_59: Line 6b — Taxable SS
    # f1_60: Line 6c — Election checkbox
    # f1_61: Line 7 — Capital gain or (loss)
    data["f1_61[0]"] = format_currency_for_pdf(result.capital_gain_loss)
    # f1_62: Line 8 — Other income (Schedule 1)
    data["f1_62[0]"] = format_currency_for_pdf(result.total_income - result.wage_income
                                                 - result.taxable_interest - result.ordinary_dividends
                                                 - result.capital_gain_loss)
    # f1_63: Line 9 — Total income
    data["f1_63[0]"] = format_currency_for_pdf(result.total_income)
    # f1_64: Line 10 — Adjustments (Schedule 1)
    data["f1_64[0]"] = format_currency_for_pdf(result.adjustments)
    # f1_65: Line 11 — AGI
    data["f1_65[0]"] = format_currency_for_pdf(result.agi)
    # f1_66: Line 12 — Standard deduction or itemized
    data["f1_66[0]"] = format_currency_for_pdf(result.deduction)
    # f1_67: Line 13 — Qualified business income deduction
    data["f1_67[0]"] = format_currency_for_pdf(result.qbi_deduction)
    # f1_68: Line 14 — Total deductions (12 + 13)
    data["f1_68[0]"] = format_currency_for_pdf(result.deduction + result.qbi_deduction)
    # f1_69: Line 15 — Taxable income
    data["f1_69[0]"] = format_currency_for_pdf(result.taxable_income)

    # ── Page 2 (f2_xx fields) ──
    # f2_01: Line 16 — Tax
    data["f2_01[0]"] = format_currency_for_pdf(result.tax)
    # f2_02-f2_06: Lines 17-21 (credits etc.)
    if result.nonrefundable_credits > 0:
        data["f2_06[0]"] = format_currency_for_pdf(result.nonrefundable_credits)
    # f2_07: Line 22 — Tax less credits
    data["f2_07[0]"] = format_currency_for_pdf(max(result.tax - result.nonrefundable_credits, 0))
    # f2_08: Line 23 — Other taxes (SE, Addl Medicare, NIIT, AMT from Schedule 2)
    other_taxes = result.se_tax + result.additional_medicare + result.niit + result.amt
    data["f2_08[0]"] = format_currency_for_pdf(other_taxes)
    # f2_09: Line 24 — Total tax
    data["f2_09[0]"] = format_currency_for_pdf(result.total_tax)

    # Payments
    # f2_10: Line 25a — W-2/1099 withholding
    data["f2_10[0]"] = format_currency_for_pdf(result.withholding)
    # f2_13: Line 26 — Estimated tax payments
    data["f2_13[0]"] = format_currency_for_pdf(result.estimated_payments)
    # f2_18: Line 33 — Total payments
    data["f2_18[0]"] = format_currency_for_pdf(result.total_payments)

    # Refund / amount owed
    if result.overpayment > 0:
        # f2_19: Line 34 — Overpaid
        data["f2_19[0]"] = format_currency_for_pdf(result.overpayment)
        # f2_20: Line 35a — Refunded to you
        data["f2_20[0]"] = format_currency_for_pdf(result.overpayment)
    if result.amount_owed > 0:
        # f2_24: Line 37 — Amount you owe
        data["f2_24[0]"] = format_currency_for_pdf(result.amount_owed)

    # SSN on page 2 header
    data["f2_22[0]"] = profile.ssn.replace("-", "")

    return data
