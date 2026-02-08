"""Field mapping for Schedule C (Profit or Loss From Business).

Field names from inspect_form_fields('f1040sc') against 2025 IRS PDF.
Page 1: f1_1..f1_46  Page 2: f2_1..f2_33
"""

from taxman.field_mappings.common import (
    checkbox,
    format_currency_for_pdf,
    format_ein,
    format_ssn,
)


def build_schedule_c_data(sc_result, biz_data=None, profile=None) -> dict:
    """Build field data dict for Schedule C.

    Args:
        sc_result: ScheduleCResult from calculator
        biz_data: ScheduleCData (optional, for business info)
        profile: TaxpayerProfile (optional, for SSN)
    """
    data = {}

    # Header
    if profile:
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    if biz_data:
        # f1_3: Business name (A)
        data["f1_3[0]"] = biz_data.business_name
        # f1_4: Principal business code (B) — maxLength 6
        data["f1_4[0]"] = biz_data.principal_business_code
        # f1_5: Business description (C)
        data["f1_5[0]"] = biz_data.business_description
        # f1_6: EIN (D) — maxLength 9
        if biz_data.business_ein:
            data["f1_6[0]"] = biz_data.business_ein.replace("-", "")
        # f1_7: Business address (E)
        # f1_8: City, state, ZIP (F)

        # Accounting method checkboxes: c1_1[0]=Cash, c1_1[1]=Accrual, c1_1[2]=Other
        if biz_data.accounting_method.value == "cash":
            data["c1_1[0]"] = True
        elif biz_data.accounting_method.value == "accrual":
            data["c1_1[1]"] = True

        # Material participation: c1_2[0]=Yes, c1_2[1]=No
        if biz_data.did_materially_participate:
            data["c1_2[0]"] = True
        else:
            data["c1_2[1]"] = True

    # Part I: Income
    # f1_10: Line 1 — Gross receipts
    data["f1_10[0]"] = format_currency_for_pdf(sc_result.gross_receipts)
    # f1_11: Line 2 — Returns and allowances
    data["f1_11[0]"] = format_currency_for_pdf(sc_result.returns_allowances)
    # f1_12: Line 3 — Subtract line 2 from line 1
    data["f1_12[0]"] = format_currency_for_pdf(sc_result.gross_receipts - sc_result.returns_allowances)
    # f1_13: Line 4 — Cost of goods sold
    data["f1_13[0]"] = format_currency_for_pdf(sc_result.cost_of_goods_sold)
    # f1_14: Line 5 — Gross profit
    data["f1_14[0]"] = format_currency_for_pdf(sc_result.gross_profit)
    # f1_15: Line 6 — Other income
    data["f1_15[0]"] = format_currency_for_pdf(sc_result.other_income)
    # f1_16: Line 7 — Gross income
    data["f1_16[0]"] = format_currency_for_pdf(sc_result.gross_income)

    # Part II: Expenses (f1_17..f1_38)
    expense_field_map = {
        "8": "f1_17[0]",    # Advertising
        "9": "f1_18[0]",    # Car and truck expenses
        "10": "f1_19[0]",   # Commissions and fees
        "11": "f1_20[0]",   # Contract labor
        "12": "f1_21[0]",   # Depletion
        "13": "f1_22[0]",   # Depreciation
        "14": "f1_23[0]",   # Employee benefit programs
        "15": "f1_24[0]",   # Insurance
        "16a": "f1_25[0]",  # Interest: mortgage
        "16b": "f1_26[0]",  # Interest: other
        "17": "f1_27[0]",   # Legal and professional services
        "18": "f1_28[0]",   # Office expense
        "19": "f1_29[0]",   # Pension and profit-sharing
        "20a": "f1_30[0]",  # Rent: vehicles/equipment
        "20b": "f1_31[0]",  # Rent: other
        "21": "f1_32[0]",   # Repairs and maintenance
        "22": "f1_33[0]",   # Supplies
        "23": "f1_34[0]",   # Taxes and licenses
        "24a": "f1_35[0]",  # Travel
        "24b": "f1_36[0]",  # Meals (deductible portion)
        "25": "f1_37[0]",   # Utilities
        "26": "f1_38[0]",   # Wages
    }

    for item in sc_result.lines:
        field = expense_field_map.get(item.line)
        if field and item.amount > 0:
            data[field] = format_currency_for_pdf(item.amount)

    # f1_39: Line 27a — Other expenses (from list)
    # f1_40: Line 27b — reserved
    # f1_43: Line 30 — Home office deduction (extract first to compute Line 28)
    home_office = 0.0
    for item in sc_result.lines:
        if item.line == "30":
            home_office = item.amount
            data["f1_43[0]"] = format_currency_for_pdf(item.amount)
            break
    # f1_41: Line 28 — Total expenses BEFORE home office
    expenses_before_ho = sc_result.total_expenses - home_office
    data["f1_41[0]"] = format_currency_for_pdf(expenses_before_ho)
    # f1_44: Line 31 — Net profit or (loss)
    data["f1_44[0]"] = format_currency_for_pdf(sc_result.net_profit_loss)

    return data
