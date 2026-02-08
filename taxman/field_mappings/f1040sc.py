"""Field mapping for Schedule C (Profit or Loss From Business)."""

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

    # Taxpayer info
    if profile:
        data["f1_01"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02"] = format_ssn(profile.ssn)

    # Business info
    if biz_data:
        data["f1_03"] = biz_data.business_name
        data["f1_04"] = biz_data.principal_business_code
        if biz_data.business_ein:
            data["f1_05"] = format_ein(biz_data.business_ein)
        data["f1_06"] = biz_data.business_description

        # Accounting method
        if biz_data.accounting_method.value == "cash":
            data["f1_07"] = checkbox(True)
        elif biz_data.accounting_method.value == "accrual":
            data["f1_08"] = checkbox(True)

        # Material participation
        data["f1_09"] = checkbox(biz_data.did_materially_participate)

    # Part I: Income
    data["f1_line1"] = format_currency_for_pdf(sc_result.gross_receipts)
    data["f1_line2"] = format_currency_for_pdf(sc_result.returns_allowances)
    data["f1_line7"] = format_currency_for_pdf(sc_result.gross_income)

    # Part II: Expenses — map from line items
    for item in sc_result.lines:
        line = item.line
        if item.amount > 0 and line.isdigit() or (len(line) <= 3 and line[0].isdigit()):
            data[f"f1_line{line}"] = format_currency_for_pdf(item.amount)

    # Totals
    data["f1_line28"] = format_currency_for_pdf(sc_result.total_expenses)
    data["f1_line31"] = format_currency_for_pdf(sc_result.net_profit_loss)

    return data
