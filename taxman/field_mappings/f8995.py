"""Field mapping for Form 8995 (Qualified Business Income Deduction — Simplified).

Field names discovered via diagnostic fill against 2025 IRS PDF
(irs.gov/pub/irs-pdf/f8995.pdf, Created 9/12/25).

Single page: f1_01..f1_33
Row i:  f1_03 (name), f1_04 (EIN), f1_05 (QBI)
Row ii: f1_06 (name), f1_07 (EIN), f1_08 (QBI)
Row iii: f1_09 (name), f1_10 (EIN), f1_11 (QBI)
Row iv: f1_12 (name), f1_13 (EIN), f1_14 (QBI)
Row v:  f1_15 (name), f1_16 (EIN), f1_17 (QBI)
Line 2: f1_18, Line 3: f1_19, Line 4: f1_20
Line 5: f1_21, Line 6: f1_22, Line 7: f1_23
Line 8: f1_24, Line 9: f1_25, Line 10: f1_26
Line 11: f1_27, Line 12: f1_28, Line 13: f1_29
Line 14: f1_30, Line 15: f1_31, Line 16: f1_32, Line 17: f1_33
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_8995_data(qbi_result, form1040_result=None, profile=None) -> dict:
    """Build field data dict for Form 8995.

    Args:
        qbi_result: Form8995Result from calculator
        form1040_result: Form1040Result (for taxable income)
        profile: TaxpayerProfile
    """
    data = {}

    # Header
    if profile:
        data["f1_01[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # Lines 1i-1v: QBI from each business (up to 5 rows)
    # Each row: name, EIN, QBI amount
    row_fields = [
        ("f1_03[0]", "f1_04[0]", "f1_05[0]"),  # Row i
        ("f1_06[0]", "f1_07[0]", "f1_08[0]"),  # Row ii
        ("f1_09[0]", "f1_10[0]", "f1_11[0]"),  # Row iii
        ("f1_12[0]", "f1_13[0]", "f1_14[0]"),  # Row iv
        ("f1_15[0]", "f1_16[0]", "f1_17[0]"),  # Row v
    ]
    if form1040_result:
        for i, sc in enumerate(form1040_result.schedule_c_results[:5]):
            name_f, ein_f, qbi_f = row_fields[i]
            data[name_f] = sc.business_name
            data[qbi_f] = format_currency_for_pdf(sc.net_profit_loss)

    # f1_18: Line 2 — Total QBI
    data["f1_18[0]"] = format_currency_for_pdf(qbi_result.total_qbi)

    # f1_19: Line 3 — QBI net loss carryforward from prior year (skip if none)

    # f1_20: Line 4 — Total QBI (line 2 + line 3, if zero or less enter 0)
    data["f1_20[0]"] = format_currency_for_pdf(max(qbi_result.total_qbi, 0))

    # f1_21: Line 5 — QBI component (20% of line 4)
    qbi_component = max(qbi_result.total_qbi, 0) * 0.20
    data["f1_21[0]"] = format_currency_for_pdf(round(qbi_component))

    # f1_22: Line 6 — Qualified REIT dividends / PTP income
    # f1_23: Line 7 — REIT/PTP loss carryforward
    # f1_24: Line 8 — Total REIT/PTP income
    # f1_25: Line 9 — REIT/PTP component (20%)

    # f1_26: Line 10 — QBI deduction before income limitation (line 5 + line 9)
    data["f1_26[0]"] = format_currency_for_pdf(round(qbi_component))

    # f1_27: Line 11 — Taxable income before QBI deduction
    if form1040_result:
        taxable_before_qbi = form1040_result.taxable_income + qbi_result.qbi_deduction
        data["f1_27[0]"] = format_currency_for_pdf(taxable_before_qbi)

    # f1_28: Line 12 — Net capital gain + qualified dividends
    if form1040_result:
        net_cap_gain = max(form1040_result.capital_gain_loss, 0) + form1040_result.qualified_dividends
        if net_cap_gain > 0:
            data["f1_28[0]"] = format_currency_for_pdf(net_cap_gain)

    # f1_29: Line 13 — Subtract line 12 from line 11
    if form1040_result:
        line13 = max(taxable_before_qbi - net_cap_gain, 0)
        data["f1_29[0]"] = format_currency_for_pdf(line13)

    # f1_30: Line 14 — Income limitation (20% of line 13)
    if form1040_result:
        income_limit = round(line13 * 0.20)
        data["f1_30[0]"] = format_currency_for_pdf(income_limit)

    # f1_31: Line 15 — QBI deduction (lesser of line 10 and line 14)
    data["f1_31[0]"] = format_currency_for_pdf(qbi_result.qbi_deduction)

    # f1_32: Line 16 — Total QBI loss carryforward
    # f1_33: Line 17 — Total REIT/PTP loss carryforward

    return data
