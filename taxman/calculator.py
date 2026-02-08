"""Tax calculation engine for 2025 federal return.

Computes all form line items from a TaxpayerProfile.
Each calculation includes the IRS form/line reference and reasoning.
"""

from dataclasses import dataclass, field
from typing import Optional

from taxman.constants import (
    ADDITIONAL_MEDICARE_RATE,
    ADDITIONAL_MEDICARE_THRESHOLD_MFS,
    ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    AMT_BREAKPOINT_MFS,
    AMT_BREAKPOINT_OTHER,
    AMT_EXEMPTION_MFJ,
    AMT_EXEMPTION_MFS,
    AMT_EXEMPTION_SINGLE,
    AMT_EXEMPTION_HOH,
    AMT_PHASEOUT_MFJ,
    AMT_PHASEOUT_MFS,
    AMT_PHASEOUT_SINGLE,
    AMT_PHASEOUT_HOH,
    AMT_PHASEOUT_RATE,
    AMT_RATE_HIGH,
    AMT_RATE_LOW,
    ACTC_EARNED_INCOME_RATE,
    ACTC_EARNED_INCOME_THRESHOLD,
    ACTC_REFUNDABLE_PER_CHILD,
    CAPITAL_LOSS_LIMIT_MFS,
    CAPITAL_LOSS_LIMIT_OTHER,
    CTC_AMOUNT_PER_CHILD,
    CTC_PHASEOUT_MFJ,
    CTC_PHASEOUT_OTHER,
    CTC_PHASEOUT_RATE,
    ODC_AMOUNT,
    ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS,
    ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_SINGLE,
    ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFJ,
    ESTIMATED_TAX_PRIOR_YEAR_HIGH_INCOME_PCT,
    ESTIMATED_TAX_PRIOR_YEAR_PCT,
    ESTIMATED_TAX_SAFE_HARBOR_PCT,
    FEIE_EXCLUSION_LIMIT,
    LTCG_FIFTEEN_PCT_HOH,
    LTCG_FIFTEEN_PCT_MFJ,
    LTCG_FIFTEEN_PCT_MFS,
    LTCG_FIFTEEN_PCT_SINGLE,
    LTCG_ZERO_PCT_HOH,
    LTCG_ZERO_PCT_MFJ,
    LTCG_ZERO_PCT_MFS,
    LTCG_ZERO_PCT_SINGLE,
    MEALS_DEDUCTION_PCT,
    MFS_BRACKETS,
    MFJ_BRACKETS,
    SINGLE_BRACKETS,
    HOH_BRACKETS,
    NIIT_RATE,
    NIIT_THRESHOLD_MFS,
    NIIT_THRESHOLD_SINGLE,
    NIIT_THRESHOLD_MFJ,
    QBI_DEDUCTION_RATE,
    QBI_PHASEOUT_MFS,
    QBI_PHASEOUT_MFJ,
    QBI_THRESHOLD_MFS,
    QBI_THRESHOLD_MFJ,
    QBI_THRESHOLD_SINGLE,
    SE_DEDUCTIBLE_FRACTION,
    SE_INCOME_FACTOR,
    SE_MINIMUM_INCOME,
    SS_TAX_RATE,
    SS_WAGE_BASE,
    MEDICARE_TAX_RATE,
    STANDARD_DEDUCTION,
)
from taxman.models import TaxpayerProfile, ScheduleCData, FilingStatus


# =============================================================================
# Filing status helper lookups
# =============================================================================

BRACKETS_BY_STATUS = {
    FilingStatus.SINGLE: SINGLE_BRACKETS,
    FilingStatus.MFJ: MFJ_BRACKETS,
    FilingStatus.MFS: MFS_BRACKETS,
    FilingStatus.HOH: HOH_BRACKETS,
    FilingStatus.QSS: MFJ_BRACKETS,
}

QBI_THRESHOLDS = {
    FilingStatus.SINGLE: (QBI_THRESHOLD_SINGLE, QBI_PHASEOUT_MFS),
    FilingStatus.MFS: (QBI_THRESHOLD_MFS, QBI_PHASEOUT_MFS),
    FilingStatus.MFJ: (QBI_THRESHOLD_MFJ, QBI_PHASEOUT_MFJ),
    FilingStatus.HOH: (QBI_THRESHOLD_SINGLE, QBI_PHASEOUT_MFS),
    FilingStatus.QSS: (QBI_THRESHOLD_MFJ, QBI_PHASEOUT_MFJ),
}

ADDITIONAL_MEDICARE_THRESHOLDS = {
    FilingStatus.SINGLE: ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    FilingStatus.MFS: ADDITIONAL_MEDICARE_THRESHOLD_MFS,
    FilingStatus.MFJ: ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
    FilingStatus.HOH: ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    FilingStatus.QSS: ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
}

# Bug 1 fix: NIIT thresholds by filing status
NIIT_THRESHOLDS = {
    FilingStatus.SINGLE: NIIT_THRESHOLD_SINGLE,
    FilingStatus.MFS: NIIT_THRESHOLD_MFS,
    FilingStatus.MFJ: NIIT_THRESHOLD_MFJ,
    FilingStatus.HOH: NIIT_THRESHOLD_SINGLE,
    FilingStatus.QSS: NIIT_THRESHOLD_MFJ,
}

# Bug 4 fix: Estimated tax high-income thresholds by filing status
ESTIMATED_TAX_HIGH_INCOME_THRESHOLDS = {
    FilingStatus.SINGLE: ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_SINGLE,
    FilingStatus.MFS: ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS,
    FilingStatus.MFJ: ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFJ,
    FilingStatus.HOH: ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_SINGLE,
    FilingStatus.QSS: ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFJ,
}


AMT_EXEMPTIONS = {
    FilingStatus.SINGLE: AMT_EXEMPTION_SINGLE,
    FilingStatus.MFS: AMT_EXEMPTION_MFS,
    FilingStatus.MFJ: AMT_EXEMPTION_MFJ,
    FilingStatus.HOH: AMT_EXEMPTION_HOH,
    FilingStatus.QSS: AMT_EXEMPTION_MFJ,
}

AMT_PHASEOUTS = {
    FilingStatus.SINGLE: AMT_PHASEOUT_SINGLE,
    FilingStatus.MFS: AMT_PHASEOUT_MFS,
    FilingStatus.MFJ: AMT_PHASEOUT_MFJ,
    FilingStatus.HOH: AMT_PHASEOUT_HOH,
    FilingStatus.QSS: AMT_PHASEOUT_MFJ,
}

AMT_BREAKPOINTS = {
    FilingStatus.SINGLE: AMT_BREAKPOINT_OTHER,
    FilingStatus.MFS: AMT_BREAKPOINT_MFS,
    FilingStatus.MFJ: AMT_BREAKPOINT_OTHER,
    FilingStatus.HOH: AMT_BREAKPOINT_OTHER,
    FilingStatus.QSS: AMT_BREAKPOINT_OTHER,
}

CAPITAL_LOSS_LIMITS = {
    FilingStatus.SINGLE: CAPITAL_LOSS_LIMIT_OTHER,
    FilingStatus.MFS: CAPITAL_LOSS_LIMIT_MFS,
    FilingStatus.MFJ: CAPITAL_LOSS_LIMIT_OTHER,
    FilingStatus.HOH: CAPITAL_LOSS_LIMIT_OTHER,
    FilingStatus.QSS: CAPITAL_LOSS_LIMIT_OTHER,
}

LTCG_ZERO_THRESHOLDS = {
    FilingStatus.SINGLE: LTCG_ZERO_PCT_SINGLE,
    FilingStatus.MFS: LTCG_ZERO_PCT_MFS,
    FilingStatus.MFJ: LTCG_ZERO_PCT_MFJ,
    FilingStatus.HOH: LTCG_ZERO_PCT_HOH,
    FilingStatus.QSS: LTCG_ZERO_PCT_MFJ,
}

LTCG_FIFTEEN_THRESHOLDS = {
    FilingStatus.SINGLE: LTCG_FIFTEEN_PCT_SINGLE,
    FilingStatus.MFS: LTCG_FIFTEEN_PCT_MFS,
    FilingStatus.MFJ: LTCG_FIFTEEN_PCT_MFJ,
    FilingStatus.HOH: LTCG_FIFTEEN_PCT_HOH,
    FilingStatus.QSS: LTCG_FIFTEEN_PCT_MFJ,
}

# =============================================================================
# Calculation Result Containers
# =============================================================================

@dataclass
class LineItem:
    """A single calculated line on a tax form."""
    form: str
    line: str
    description: str
    amount: float
    explanation: str = ""
    irs_reference: str = ""


@dataclass
class ScheduleCResult:
    """Calculated Schedule C for one business."""
    business_name: str
    gross_receipts: float = 0.0       # Line 1
    returns_allowances: float = 0.0    # Line 2
    cost_of_goods_sold: float = 0.0    # Line 4
    gross_profit: float = 0.0          # Line 5
    other_income: float = 0.0          # Line 6
    gross_income: float = 0.0          # Line 7
    total_expenses: float = 0.0        # Line 28
    net_profit_loss: float = 0.0       # Line 31
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class ScheduleSEResult:
    """Calculated Schedule SE."""
    net_se_earnings: float = 0.0       # Line 3
    taxable_se_earnings: float = 0.0   # Line 4 (92.35% of net)
    se_tax: float = 0.0               # Line 12
    deductible_se_tax: float = 0.0    # 50% of SE tax
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class ScheduleEResult:
    """Calculated Schedule E (rental/K-1 income)."""
    net_rental_income: float = 0.0      # Box 2 + Box 3 rental income
    ordinary_business_income: float = 0.0  # Box 1
    guaranteed_payments: float = 0.0    # Box 4
    interest_income: float = 0.0        # Box 5
    dividends: float = 0.0             # Box 6a
    qualified_dividends: float = 0.0   # Box 6b
    royalties: float = 0.0            # Box 7
    net_st_capital_gain: float = 0.0   # Box 8
    capital_gains: float = 0.0          # Box 9a
    net_section_1231_gain: float = 0.0 # Box 10
    other_income: float = 0.0         # Box 11
    section_179_deduction: float = 0.0 # Box 12
    other_deductions: float = 0.0     # Box 13
    se_earnings_from_k1: float = 0.0    # Box 14 (subject to SE tax)
    total_schedule_e_income: float = 0.0  # All K-1 income for Schedule 1
    warnings: list[str] = field(default_factory=list)
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class Form8995Result:
    """Calculated QBI deduction."""
    total_qbi: float = 0.0
    qbi_deduction: float = 0.0
    is_limited: bool = False
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class ScheduleDResult:
    """Calculated Schedule D (Capital Gains and Losses)."""
    net_st_gain_loss: float = 0.0
    net_lt_gain_loss: float = 0.0
    net_capital_gain_loss: float = 0.0
    capital_gain_for_1040: float = 0.0  # Loss limited by filing status
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class Form6251Result:
    """Calculated AMT (Form 6251)."""
    amti: float = 0.0                    # Alternative minimum taxable income
    exemption: float = 0.0               # AMT exemption (after phaseout)
    tentative_minimum_tax: float = 0.0   # TMT
    amt: float = 0.0                     # AMT = max(TMT - regular tax, 0)
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class TaxCreditsResult:
    """Calculated tax credits (CTC, ACTC, ODC)."""
    ctc_per_child: float = 0.0
    num_qualifying_children: int = 0
    num_other_dependents: int = 0
    gross_ctc: float = 0.0            # Before phaseout
    gross_odc: float = 0.0
    phaseout_reduction: float = 0.0
    total_credit_after_phaseout: float = 0.0
    nonrefundable_credit: float = 0.0  # Limited to tax liability
    refundable_actc: float = 0.0       # Additional Child Tax Credit
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class Form2555Result:
    """Calculated FEIE."""
    foreign_earned_income: float = 0.0
    exclusion_amount: float = 0.0
    is_beneficial: bool = False
    tax_with_feie: float = 0.0
    tax_without_feie: float = 0.0
    savings: float = 0.0
    lines: list[LineItem] = field(default_factory=list)


@dataclass
class Form1040Result:
    """Complete calculated Form 1040."""
    # Income
    wage_income: float = 0.0           # Line 1a (W-2 wages)
    tax_exempt_interest: float = 0.0   # Line 2a (informational)
    taxable_interest: float = 0.0      # Line 2b
    qualified_dividends: float = 0.0   # Line 3a
    ordinary_dividends: float = 0.0    # Line 3b
    capital_gain_loss: float = 0.0     # Line 7
    total_income: float = 0.0          # Line 9
    adjustments: float = 0.0           # Line 10
    agi: float = 0.0                   # Line 11
    deduction: float = 0.0             # Line 13
    qbi_deduction: float = 0.0        # Line 13, QBI portion
    taxable_income: float = 0.0        # Line 15
    # Tax
    tax: float = 0.0                   # Line 16
    se_tax: float = 0.0               # Schedule 2
    additional_medicare: float = 0.0   # Schedule 2
    niit: float = 0.0                  # Schedule 2 (Net Investment Income Tax)
    amt: float = 0.0                  # Schedule 2 (Alternative Minimum Tax)
    nonrefundable_credits: float = 0.0  # Line 21 (CTC + ODC nonrefundable)
    total_tax: float = 0.0            # Line 24
    # Payments
    total_payments: float = 0.0        # Line 33
    estimated_payments: float = 0.0
    withholding: float = 0.0           # Line 25a (W-2 federal withholding)
    # Result
    overpayment: float = 0.0          # Line 34
    amount_owed: float = 0.0          # Line 37
    # Components
    schedule_c_results: list[ScheduleCResult] = field(default_factory=list)
    schedule_se: Optional[ScheduleSEResult] = None
    schedule_e: Optional[ScheduleEResult] = None
    schedule_d: Optional[ScheduleDResult] = None
    form_6251: Optional[Form6251Result] = None
    tax_credits: Optional[TaxCreditsResult] = None
    qbi: Optional[Form8995Result] = None
    feie: Optional[Form2555Result] = None
    lines: list[LineItem] = field(default_factory=list)


# =============================================================================
# Core Calculation Functions
# =============================================================================

def calculate_schedule_c(biz: ScheduleCData) -> ScheduleCResult:
    """Calculate Schedule C (Profit or Loss From Business).

    IRS Instructions: https://www.irs.gov/instructions/i1040sc
    """
    result = ScheduleCResult(business_name=biz.business_name)
    lines = []

    # Part I: Income
    # IRS Schedule C flow: Line 1 (gross receipts) - Line 2 (returns)
    # = Line 3 (net receipts) - Line 4 (COGS) = Line 5 (gross profit)
    # + Line 6 (other income) = Line 7 (gross income)
    result.gross_receipts = biz.gross_receipts
    lines.append(LineItem("Schedule C", "1", "Gross receipts or sales",
                          biz.gross_receipts))

    result.returns_allowances = biz.returns_and_allowances
    lines.append(LineItem("Schedule C", "2", "Returns and allowances",
                          biz.returns_and_allowances))

    result.cost_of_goods_sold = biz.cost_of_goods_sold
    if biz.cost_of_goods_sold > 0:
        lines.append(LineItem("Schedule C", "4", "Cost of goods sold",
                              biz.cost_of_goods_sold))

    gross_profit = biz.gross_profit  # receipts - returns - COGS
    result.gross_profit = gross_profit
    lines.append(LineItem("Schedule C", "5", "Gross profit",
                          gross_profit,
                          "Line 1 minus Line 2 minus Line 4"))

    result.other_income = biz.other_income
    if biz.other_income > 0:
        lines.append(LineItem("Schedule C", "6", "Other income",
                              biz.other_income))

    gross_income = gross_profit + biz.other_income
    result.gross_income = gross_income
    lines.append(LineItem("Schedule C", "7", "Gross income",
                          gross_income,
                          "Line 5 plus Line 6"))

    # Part II: Expenses
    exp = biz.expenses
    expense_lines = [
        ("8", "Advertising", exp.advertising),
        ("9", "Car and truck expenses", exp.car_and_truck),
        ("10", "Commissions and fees", exp.commissions_and_fees),
        ("11", "Contract labor", exp.contract_labor),
        ("13", "Depreciation", exp.depreciation),
        ("14", "Employee benefit programs", exp.employee_benefit_programs),
        ("15", "Insurance (other than health)", exp.insurance),
        ("16a", "Interest: mortgage", exp.interest_mortgage),
        ("16b", "Interest: other", exp.interest_other),
        ("17", "Legal and professional services", exp.legal_and_professional),
        ("18", "Office expense", exp.office_expense),
        ("19", "Pension and profit-sharing plans", exp.pension_profit_sharing),
        ("20a", "Rent: vehicles/equipment", exp.rent_vehicles_equipment),
        ("20b", "Rent: other", exp.rent_other),
        ("21", "Repairs and maintenance", exp.repairs_maintenance),
        ("22", "Supplies", exp.supplies),
        ("23", "Taxes and licenses", exp.taxes_licenses),
        ("24a", "Travel", exp.travel),
        ("24b", "Meals (50%)", round(exp.meals * MEALS_DEDUCTION_PCT, 2)),
        ("25", "Utilities", exp.utilities),
        ("26", "Wages", exp.wages),
        ("27a", "Other expenses", exp.other_expenses),
    ]

    total_expenses = 0.0
    for line_num, desc, amount in expense_lines:
        if amount > 0:
            lines.append(LineItem("Schedule C", line_num, desc, round(amount, 2)))
            total_expenses += amount

    # Home office deduction
    home_office_deduction = 0.0
    if biz.home_office:
        if biz.home_office.use_simplified_method:
            home_office_deduction = biz.home_office.simplified_deduction
            lines.append(LineItem("Schedule C", "30",
                                  "Business use of home (simplified method)",
                                  round(home_office_deduction, 2),
                                  f"{min(biz.home_office.square_footage, 300):.0f} sqft × $5/sqft"))
        else:
            home_office_deduction = biz.home_office.regular_deduction
            lines.append(LineItem("Schedule C", "30",
                                  "Business use of home (regular method, Form 8829)",
                                  round(home_office_deduction, 2),
                                  f"{biz.home_office.business_percentage:.1%} business use"))
        total_expenses += home_office_deduction

    result.total_expenses = round(total_expenses, 2)
    lines.append(LineItem("Schedule C", "28", "Total expenses before home office",
                          round(total_expenses - home_office_deduction, 2)))

    # Net profit or loss
    net_profit = round(gross_income - total_expenses, 2)
    result.net_profit_loss = net_profit
    lines.append(LineItem("Schedule C", "31", "Net profit or (loss)",
                          net_profit,
                          "Line 7 minus Line 28 minus Line 30"))

    result.lines = lines
    return result


def calculate_schedule_se(
    net_se_income: float, w2_ss_wages: float = 0.0
) -> ScheduleSEResult:
    """Calculate Schedule SE (Self-Employment Tax).

    IRS Instructions: https://www.irs.gov/instructions/i1040sse

    SE tax applies to net self-employment earnings of $400 or more.
    Rate is 15.3% (12.4% Social Security + 2.9% Medicare).
    Social Security portion caps at the wage base ($176,100 for 2025),
    reduced by any W-2 SS wages already subject to SS tax.
    """
    result = ScheduleSEResult()
    lines = []

    result.net_se_earnings = net_se_income
    lines.append(LineItem("Schedule SE", "3", "Net SE earnings",
                          round(net_se_income, 2),
                          "Combined net profit from Schedule C + K-1 SE earnings"))

    if net_se_income < SE_MINIMUM_INCOME:
        lines.append(LineItem("Schedule SE", "4", "No SE tax required",
                              0.0, f"Net SE earnings under ${SE_MINIMUM_INCOME}"))
        result.lines = lines
        return result

    # Line 4a: 92.35% of net SE earnings
    taxable_se = round(net_se_income * SE_INCOME_FACTOR, 2)
    result.taxable_se_earnings = taxable_se
    lines.append(LineItem("Schedule SE", "4a",
                          "Multiply Line 3 by 92.35%",
                          taxable_se,
                          f"${net_se_income:,.2f} × 0.9235 = ${taxable_se:,.2f}"))

    # Calculate SS and Medicare portions separately
    # SS wage base is reduced by W-2 SS wages (Line 8a-8b on Schedule SE)
    remaining_ss_base = max(SS_WAGE_BASE - w2_ss_wages, 0)
    ss_earnings = min(taxable_se, remaining_ss_base)
    ss_tax = round(ss_earnings * SS_TAX_RATE, 2)
    medicare_tax = round(taxable_se * MEDICARE_TAX_RATE, 2)
    se_tax = round(ss_tax + medicare_tax, 2)

    lines.append(LineItem("Schedule SE", "10",
                          "Social Security tax",
                          ss_tax,
                          f"min(${taxable_se:,.2f}, ${remaining_ss_base:,.2f}) × {SS_TAX_RATE}"))
    lines.append(LineItem("Schedule SE", "11",
                          "Medicare tax",
                          medicare_tax,
                          f"${taxable_se:,.2f} × {MEDICARE_TAX_RATE}"))

    result.se_tax = se_tax
    lines.append(LineItem("Schedule SE", "12",
                          "Self-employment tax",
                          se_tax,
                          f"SS tax ${ss_tax:,.2f} + Medicare ${medicare_tax:,.2f}"))

    # Deductible half
    result.deductible_se_tax = round(se_tax * SE_DEDUCTIBLE_FRACTION, 2)
    lines.append(LineItem("Schedule SE", "13",
                          "Deductible part of SE tax",
                          result.deductible_se_tax,
                          f"50% of ${se_tax:,.2f} — this goes to Schedule 1, Line 15"))

    result.lines = lines
    return result


def calculate_schedule_e(profile: TaxpayerProfile) -> ScheduleEResult:
    """Calculate Schedule E (Supplemental Income and Loss).

    Handles all K-1 income boxes and flows them to the correct places:
    - Box 1: Ordinary business income → Schedule E Part II
    - Box 2: Net rental income → Schedule E Part II
    - Box 4: Guaranteed payments → Schedule E Part II (also subject to SE tax)
    - Box 5: Interest income → flows to Schedule B / Form 1040
    - Box 9a: Net LTCG → flows to Schedule D / Form 1040
    - Box 14: Self-employment earnings → used for Schedule SE

    For MFS filers: passive rental losses cannot offset non-passive income
    (IRC §469(i)(5)(B) — the $25K special allowance is $0 for MFS).
    """
    result = ScheduleEResult()
    lines = []

    for k1 in profile.schedule_k1s:
        # Box 2: Net rental income (passive)
        rental = k1.net_rental_income
        if rental < 0 and profile.filing_status == FilingStatus.MFS:
            lines.append(LineItem("Schedule E", "Part II",
                                  f"K-1 rental loss from {k1.partnership_name} (SUSPENDED)",
                                  0.0,
                                  f"Actual loss: ${rental:,.2f}. MFS filers get $0 passive "
                                  f"loss allowance (IRC §469(i)(5)(B)). Loss is suspended "
                                  f"and carries forward."))
        else:
            result.net_rental_income += rental
            lines.append(LineItem("Schedule E", "Part II",
                                  f"K-1 rental income from {k1.partnership_name}",
                                  round(rental, 2),
                                  "Net rental income from partnership K-1, Box 2"))

        # Box 3: Other net rental income
        rental3 = k1.other_net_rental_income
        if rental3 < 0 and profile.filing_status == FilingStatus.MFS:
            pass  # Suspended same as Box 2
        elif rental3 != 0:
            result.net_rental_income += rental3
            lines.append(LineItem("Schedule E", "K-1 Box 3",
                                  f"Other net rental income from {k1.partnership_name}",
                                  round(rental3, 2)))

        # Box 1: Ordinary business income
        if k1.ordinary_business_income != 0:
            result.ordinary_business_income += k1.ordinary_business_income
            lines.append(LineItem("Schedule E", "K-1 Box 1",
                                  f"Ordinary business income from {k1.partnership_name}",
                                  round(k1.ordinary_business_income, 2)))

        # Box 4: Guaranteed payments
        if k1.guaranteed_payments != 0:
            result.guaranteed_payments += k1.guaranteed_payments
            lines.append(LineItem("Schedule E", "K-1 Box 4",
                                  f"Guaranteed payments from {k1.partnership_name}",
                                  round(k1.guaranteed_payments, 2),
                                  "Subject to self-employment tax"))

        # Box 5: Interest income (flows to Line 2b)
        if k1.interest_income > 0:
            result.interest_income += k1.interest_income
            lines.append(LineItem("Schedule E", "K-1 Box 5",
                                  f"Interest income from {k1.partnership_name}",
                                  round(k1.interest_income, 2),
                                  "Flows to Form 1040 Line 2b"))

        # Box 6a: Dividends (flows to Line 3b)
        if k1.dividends != 0:
            result.dividends += k1.dividends
            lines.append(LineItem("Schedule E", "K-1 Box 6a",
                                  f"Dividends from {k1.partnership_name}",
                                  round(k1.dividends, 2),
                                  "Flows to Form 1040 Line 3b"))

        # Box 6b: Qualified dividends (flows to Line 3a)
        if hasattr(k1, 'qualified_dividends') and k1.qualified_dividends != 0:
            result.qualified_dividends += k1.qualified_dividends
            lines.append(LineItem("Schedule E", "K-1 Box 6b",
                                  f"Qualified dividends from {k1.partnership_name}",
                                  round(k1.qualified_dividends, 2),
                                  "Flows to Form 1040 Line 3a"))

        # Box 7: Royalties (Schedule E + NII)
        if k1.royalties != 0:
            result.royalties += k1.royalties
            lines.append(LineItem("Schedule E", "K-1 Box 7",
                                  f"Royalties from {k1.partnership_name}",
                                  round(k1.royalties, 2)))

        # Box 8: Net short-term capital gain (flows to Schedule D)
        if k1.net_short_term_capital_gain != 0:
            result.net_st_capital_gain += k1.net_short_term_capital_gain
            lines.append(LineItem("Schedule E", "K-1 Box 8",
                                  f"Net ST capital gain from {k1.partnership_name}",
                                  round(k1.net_short_term_capital_gain, 2),
                                  "Flows to Schedule D"))

        # Box 9a: Net long-term capital gain (flows to Schedule D)
        if k1.net_long_term_capital_gain != 0:
            result.capital_gains += k1.net_long_term_capital_gain
            lines.append(LineItem("Schedule E", "K-1 Box 9a",
                                  f"Net long-term capital gain from {k1.partnership_name}",
                                  round(k1.net_long_term_capital_gain, 2),
                                  "Flows to Schedule D"))

        # Box 10: Net section 1231 gain (treated as LTCG for Schedule D)
        if k1.net_section_1231_gain != 0:
            result.net_section_1231_gain += k1.net_section_1231_gain
            lines.append(LineItem("Schedule E", "K-1 Box 10",
                                  f"Net §1231 gain from {k1.partnership_name}",
                                  round(k1.net_section_1231_gain, 2),
                                  "Treated as LTCG, flows to Schedule D"))

        # Box 11: Other income
        if k1.other_income != 0:
            result.other_income += k1.other_income
            lines.append(LineItem("Schedule E", "K-1 Box 11",
                                  f"Other income from {k1.partnership_name}",
                                  round(k1.other_income, 2)))

        # Box 12: Section 179 deduction
        if k1.section_179_deduction != 0:
            result.section_179_deduction += k1.section_179_deduction
            lines.append(LineItem("Schedule E", "K-1 Box 12",
                                  f"§179 deduction from {k1.partnership_name}",
                                  round(k1.section_179_deduction, 2)))

        # Box 13: Other deductions
        if k1.other_deductions != 0:
            result.other_deductions += k1.other_deductions
            lines.append(LineItem("Schedule E", "K-1 Box 13",
                                  f"Other deductions from {k1.partnership_name}",
                                  round(k1.other_deductions, 2)))

        # Box 14: Self-employment earnings
        if k1.self_employment_earnings != 0:
            result.se_earnings_from_k1 += k1.self_employment_earnings
            lines.append(LineItem("Schedule E", "K-1 Box 14",
                                  f"SE earnings from {k1.partnership_name}",
                                  round(k1.self_employment_earnings, 2),
                                  "Added to Schedule SE calculation"))

    # Total Schedule E income for Schedule 1
    # Excludes dividends/cap gains (they flow to Lines 3b/7 directly)
    result.total_schedule_e_income = round(
        result.net_rental_income + result.ordinary_business_income
        + result.guaranteed_payments + result.interest_income
        + result.capital_gains + result.royalties + result.other_income
        - result.section_179_deduction - result.other_deductions, 2
    )
    lines.append(LineItem("Schedule E", "26",
                          "Total Schedule E income",
                          result.total_schedule_e_income))

    result.lines = lines
    return result


def calculate_schedule_d(profile: TaxpayerProfile,
                         filing_status: FilingStatus) -> ScheduleDResult:
    """Calculate Schedule D (Capital Gains and Losses).

    Aggregates capital gains/losses from 1099-B, K-1 Boxes 8/9a/10,
    and 1099-DIV Box 2a (capital gain distributions).
    Applies capital loss limitation ($1,500 MFS / $3,000 other).
    """
    result = ScheduleDResult()
    lines = []

    net_st = 0.0
    net_lt = 0.0

    # 1099-B: broker transactions
    for b in profile.forms_1099_b:
        net_st += b.net_st_gain_loss
        net_lt += b.net_lt_gain_loss

    # K-1 boxes
    for k1 in profile.schedule_k1s:
        net_st += k1.net_short_term_capital_gain     # Box 8
        net_lt += k1.net_long_term_capital_gain       # Box 9a
        net_lt += k1.net_section_1231_gain            # Box 10 → treated as LTCG

    # 1099-DIV Box 2a: capital gain distributions → LT
    for div in profile.forms_1099_div:
        net_lt += div.capital_gain_distributions

    result.net_st_gain_loss = round(net_st, 2)
    result.net_lt_gain_loss = round(net_lt, 2)
    result.net_capital_gain_loss = round(net_st + net_lt, 2)

    if net_st != 0:
        lines.append(LineItem("Schedule D", "7", "Net short-term capital gain/loss",
                              result.net_st_gain_loss))
    if net_lt != 0:
        lines.append(LineItem("Schedule D", "15", "Net long-term capital gain/loss",
                              result.net_lt_gain_loss))

    # Apply capital loss limitation
    net = result.net_capital_gain_loss
    if net >= 0:
        result.capital_gain_for_1040 = net
    else:
        loss_limit = CAPITAL_LOSS_LIMITS.get(filing_status, CAPITAL_LOSS_LIMIT_OTHER)
        result.capital_gain_for_1040 = round(max(net, -loss_limit), 2)

    lines.append(LineItem("Schedule D", "21", "Capital gain/loss for 1040 Line 7",
                          result.capital_gain_for_1040))

    result.lines = lines
    return result


def calculate_qbi_deduction(
    taxable_income_before_qbi: float,
    schedule_c_results: list[ScheduleCResult],
    filing_status: FilingStatus = FilingStatus.MFS,
    w2_wages: float = 0.0,
    ubia: float = 0.0,
    k1_qbi: float = 0.0,
    k1_w2_wages: float = 0.0,
    k1_ubia: float = 0.0,
    net_capital_gain: float = 0.0,
) -> Form8995Result:
    """Calculate QBI deduction (Form 8995/8995-A).

    Section 199A: 20% deduction on qualified business income.

    For MFS, the threshold where limitations begin is $197,300 (2025).
    Below threshold: simple 20% of QBI (Form 8995).
    Above threshold: W-2 wage / capital limitations apply (Form 8995-A).

    QBI sources: Schedule C net profit + K-1 Box 20 Code Z (non-SSTB).
    """
    result = Form8995Result()
    lines = []

    schedule_c_qbi = sum(r.net_profit_loss for r in schedule_c_results)
    total_qbi = schedule_c_qbi + k1_qbi
    total_w2_wages = w2_wages + k1_w2_wages
    total_ubia = ubia + k1_ubia
    result.total_qbi = total_qbi

    qbi_source = "Schedule C businesses"
    if k1_qbi > 0:
        qbi_source += f" + K-1 QBI (${k1_qbi:,.2f})"
    lines.append(LineItem("Form 8995", "1-3",
                          "Total qualified business income",
                          round(total_qbi, 2),
                          f"Sum of net profit from {qbi_source}"))

    if total_qbi <= 0:
        lines.append(LineItem("Form 8995", "—",
                              "No QBI deduction (QBI is zero or negative)",
                              0.0))
        result.lines = lines
        return result

    # Look up thresholds by filing status
    threshold, phaseout_range = QBI_THRESHOLDS.get(
        filing_status, (QBI_THRESHOLD_MFS, QBI_PHASEOUT_MFS)
    )

    if taxable_income_before_qbi <= threshold:
        # Simple: 20% of QBI, capped at 20% of (taxable income - net capital gain)
        # IRC §199A(a): net capital gain includes qualified dividends
        qbi_deduction = total_qbi * QBI_DEDUCTION_RATE
        taxable_for_qbi_cap = max(taxable_income_before_qbi - net_capital_gain, 0)
        max_deduction = taxable_for_qbi_cap * QBI_DEDUCTION_RATE
        qbi_deduction = min(qbi_deduction, max_deduction)
        result.qbi_deduction = round(qbi_deduction, 2)
        result.is_limited = False

        lines.append(LineItem("Form 8995", "10",
                              "QBI deduction (20% of QBI)",
                              result.qbi_deduction,
                              f"Below {filing_status.value.upper()} threshold of "
                              f"${threshold:,}. 20% × ${total_qbi:,.2f} = "
                              f"${total_qbi * QBI_DEDUCTION_RATE:,.2f}"))
    else:
        # Above threshold — W-2 wage / UBIA limitations (Bug 2 fix)
        result.is_limited = True
        excess = taxable_income_before_qbi - threshold
        phase_out_pct = min(excess / phaseout_range, 1.0)

        # W-2/UBIA limitation: greater of (50% of W-2 wages) or
        # (25% of W-2 wages + 2.5% of UBIA)
        # Uses combined W-2 wages and UBIA from all QBI sources
        wage_limit = max(
            total_w2_wages * 0.50,
            total_w2_wages * 0.25 + total_ubia * 0.025,
        )
        limited_amount = min(total_qbi * QBI_DEDUCTION_RATE, wage_limit)
        full_amount = total_qbi * QBI_DEDUCTION_RATE
        qbi_deduction = full_amount - (full_amount - limited_amount) * phase_out_pct

        result.qbi_deduction = round(max(qbi_deduction, 0.0), 2)
        lines.append(LineItem("Form 8995-A", "16",
                              "QBI deduction (limited)",
                              result.qbi_deduction,
                              f"Above threshold. Taxable income "
                              f"${taxable_income_before_qbi:,.2f} exceeds "
                              f"${threshold:,} by ${excess:,.2f}. "
                              f"Phase-out: {phase_out_pct:.1%}. "
                              f"W-2 wages: ${total_w2_wages:,.2f}, "
                              f"UBIA: ${total_ubia:,.2f}, "
                              f"Wage limit: ${wage_limit:,.2f}."))

    result.lines = lines
    return result


def calculate_income_tax(taxable_income: float,
                         brackets: Optional[list[tuple]] = None) -> float:
    """Calculate federal income tax using progressive brackets."""
    if brackets is None:
        brackets = MFS_BRACKETS

    tax = 0.0
    prev_bound = 0

    for upper_bound, rate in brackets:
        if taxable_income <= prev_bound:
            break
        taxable_in_bracket = min(taxable_income, upper_bound) - prev_bound
        tax += taxable_in_bracket * rate
        prev_bound = upper_bound

    return round(tax, 2)


def calculate_tax_with_qdcg_worksheet(
    taxable_income: float,
    qualified_dividends: float,
    net_lt_gain: float,
    net_st_gain: float,
    filing_status: FilingStatus,
) -> float:
    """Qualified Dividends and Capital Gain Tax Worksheet.

    Computes tax using preferential 0%/15%/20% rates for qualified dividends
    and net long-term capital gains, then returns the lesser of worksheet tax
    or regular tax (IRS safety check).

    Based on IRS Form 1040 Instructions, "Qualified Dividends and Capital
    Gain Tax Worksheet" (line 16).
    """
    brackets = BRACKETS_BY_STATUS.get(filing_status, MFS_BRACKETS)
    regular_tax = calculate_income_tax(taxable_income, brackets)

    if taxable_income <= 0:
        return 0.0

    # Net capital gain = net LTCG reduced by any net STCL (but not below 0)
    net_st_loss = min(net_st_gain, 0)  # negative or zero
    net_cap_gain = max(net_lt_gain + net_st_loss, 0)

    # Preferential income: qualified dividends + net capital gain,
    # but cannot exceed taxable income
    preferential_income = min(qualified_dividends + net_cap_gain, taxable_income)

    if preferential_income <= 0:
        return regular_tax

    # Ordinary income portion (taxed at regular brackets)
    ordinary_portion = max(taxable_income - preferential_income, 0)
    ordinary_tax = calculate_income_tax(ordinary_portion, brackets)

    # Stack preferential income on top of ordinary income
    # and apply 0%/15%/20% rates based on total taxable income thresholds
    zero_threshold = LTCG_ZERO_THRESHOLDS.get(filing_status, LTCG_ZERO_PCT_MFS)
    fifteen_threshold = LTCG_FIFTEEN_THRESHOLDS.get(filing_status, LTCG_FIFTEEN_PCT_MFS)

    # How much room in the 0% bracket (above ordinary income)?
    zero_room = max(zero_threshold - ordinary_portion, 0)
    at_zero_pct = min(preferential_income, zero_room)
    remaining = preferential_income - at_zero_pct

    # How much room in the 15% bracket?
    fifteen_room = max(fifteen_threshold - ordinary_portion - at_zero_pct, 0)
    at_fifteen_pct = min(remaining, fifteen_room)
    at_twenty_pct = remaining - at_fifteen_pct

    preferential_tax = round(
        at_zero_pct * 0.0
        + at_fifteen_pct * 0.15
        + at_twenty_pct * 0.20, 2
    )

    worksheet_tax = round(ordinary_tax + preferential_tax, 2)

    # IRS safety check: use the lesser of worksheet tax or regular tax
    return min(worksheet_tax, regular_tax)


def calculate_additional_medicare(
    se_earnings: float,
    filing_status: FilingStatus = FilingStatus.MFS,
) -> float:
    """Calculate Additional Medicare Tax (0.9%) on SE earnings above threshold.

    Form 8959. Threshold for MFS is $125,000.
    """
    threshold = ADDITIONAL_MEDICARE_THRESHOLDS.get(
        filing_status, ADDITIONAL_MEDICARE_THRESHOLD_MFS
    )
    excess = max(se_earnings - threshold, 0)
    return round(excess * ADDITIONAL_MEDICARE_RATE, 2)


def calculate_niit(
    net_investment_income: float,
    agi: float,
    filing_status: FilingStatus = FilingStatus.MFS,
) -> float:
    """Calculate Net Investment Income Tax (3.8%).

    IRC §1411. Applies to lesser of net investment income or
    AGI excess over threshold. Threshold for MFS is $125,000.
    """
    # Bug 1 fix: use filing-status-specific threshold
    threshold = NIIT_THRESHOLDS.get(filing_status, NIIT_THRESHOLD_MFS)
    agi_excess = max(agi - threshold, 0)
    taxable_nii = min(net_investment_income, agi_excess)
    return round(taxable_nii * NIIT_RATE, 2)


def calculate_amt(
    taxable_income: float,
    regular_tax: float,
    filing_status: FilingStatus,
    salt_deduction: float = 0.0,
    other_amt_adjustments: float = 0.0,
) -> Form6251Result:
    """Calculate Alternative Minimum Tax (Form 6251).

    AMTI = taxable income + SALT addback + other adjustments.
    Exemption phases out at 25 cents per dollar above threshold.
    TMT = 26% of first $239,100 ($119,550 MFS) + 28% of remainder.
    AMT = max(TMT - regular tax, 0).
    """
    result = Form6251Result()
    lines = []

    # AMTI
    amti = taxable_income + salt_deduction + other_amt_adjustments
    result.amti = round(amti, 2)
    lines.append(LineItem("Form 6251", "7", "AMTI",
                          result.amti))

    # Exemption with phaseout
    base_exemption = AMT_EXEMPTIONS.get(filing_status, AMT_EXEMPTION_MFS)
    phaseout_start = AMT_PHASEOUTS.get(filing_status, AMT_PHASEOUT_MFS)

    if amti <= phaseout_start:
        exemption = base_exemption
    else:
        reduction = (amti - phaseout_start) * AMT_PHASEOUT_RATE
        exemption = max(base_exemption - reduction, 0)

    result.exemption = round(exemption, 2)
    lines.append(LineItem("Form 6251", "13", "AMT exemption",
                          result.exemption))

    # AMT taxable excess
    amt_taxable = max(amti - exemption, 0)

    # TMT: 26%/28% rates
    breakpoint = AMT_BREAKPOINTS.get(filing_status, AMT_BREAKPOINT_OTHER)
    if amt_taxable <= breakpoint:
        tmt = amt_taxable * AMT_RATE_LOW
    else:
        tmt = breakpoint * AMT_RATE_LOW + (amt_taxable - breakpoint) * AMT_RATE_HIGH

    result.tentative_minimum_tax = round(tmt, 2)
    lines.append(LineItem("Form 6251", "14", "Tentative minimum tax",
                          result.tentative_minimum_tax))

    # AMT = max(TMT - regular tax, 0)
    result.amt = round(max(tmt - regular_tax, 0), 2)
    lines.append(LineItem("Form 6251", "15", "AMT",
                          result.amt))

    result.lines = lines
    return result


def calculate_tax_credits(
    profile: TaxpayerProfile,
    agi: float,
    tax_liability: float,
    earned_income: float,
) -> TaxCreditsResult:
    """Calculate CTC, ACTC, and ODC.

    CTC: $2,500 per qualifying child (OBBBA 2025).
    ODC: $500 per other dependent.
    Phaseout: $50 per $1,000 excess MAGI over threshold ($400K MFJ, $200K other).
    Nonrefundable portion limited to tax liability.
    ACTC refundable: min(unused CTC, $1,700/child, 15% of (earned income - $2,500)).
    EITC: $0 for MFS filers (disqualified).
    """
    result = TaxCreditsResult()
    lines = []

    qualifying_children = [d for d in profile.dependents if d.is_qualifying_child_ctc]
    other_dependents = [d for d in profile.dependents if not d.is_qualifying_child_ctc]
    result.num_qualifying_children = len(qualifying_children)
    result.num_other_dependents = len(other_dependents)

    if not profile.dependents:
        result.lines = lines
        return result

    # Gross credits
    result.ctc_per_child = CTC_AMOUNT_PER_CHILD
    result.gross_ctc = len(qualifying_children) * CTC_AMOUNT_PER_CHILD
    result.gross_odc = len(other_dependents) * ODC_AMOUNT
    gross_total = result.gross_ctc + result.gross_odc

    lines.append(LineItem("Schedule 8812", "4",
                          f"CTC: {len(qualifying_children)} children × ${CTC_AMOUNT_PER_CHILD:,}",
                          result.gross_ctc))
    if result.gross_odc > 0:
        lines.append(LineItem("Schedule 8812", "5",
                              f"ODC: {len(other_dependents)} dependents × ${ODC_AMOUNT}",
                              result.gross_odc))

    # Phaseout
    fs = profile.filing_status
    threshold = CTC_PHASEOUT_MFJ if fs in (FilingStatus.MFJ, FilingStatus.QSS) else CTC_PHASEOUT_OTHER
    excess = max(agi - threshold, 0)
    # Round up to next $1,000
    thousands_excess = -(-excess // 1_000)  # ceiling division
    result.phaseout_reduction = thousands_excess * CTC_PHASEOUT_RATE

    result.total_credit_after_phaseout = max(gross_total - result.phaseout_reduction, 0)

    # Nonrefundable portion: limited to tax liability
    result.nonrefundable_credit = min(result.total_credit_after_phaseout, tax_liability)
    lines.append(LineItem("Schedule 8812", "14",
                          "Nonrefundable credit",
                          result.nonrefundable_credit))

    # ACTC refundable: only for CTC (not ODC)
    unused_ctc = max(
        min(result.gross_ctc, result.total_credit_after_phaseout) - result.nonrefundable_credit,
        0,
    )
    if unused_ctc > 0 and len(qualifying_children) > 0:
        actc_per_child_cap = len(qualifying_children) * ACTC_REFUNDABLE_PER_CHILD
        earned_income_amount = max(earned_income - ACTC_EARNED_INCOME_THRESHOLD, 0) * ACTC_EARNED_INCOME_RATE
        result.refundable_actc = round(min(unused_ctc, actc_per_child_cap, earned_income_amount), 2)
        if result.refundable_actc > 0:
            lines.append(LineItem("Schedule 8812", "27",
                                  "Additional Child Tax Credit (refundable)",
                                  result.refundable_actc))

    result.lines = lines
    return result


def evaluate_feie(
    profile: TaxpayerProfile,
    taxable_income_no_feie: float,
    tax_without_feie: float,
    earned_income: float,
) -> Form2555Result:
    """Evaluate whether the Foreign Earned Income Exclusion is beneficial.

    Key: FEIE excludes income from income tax only, NOT from SE tax.
    Uses the stacking method per Form 2555 instructions:
    1. Compute tax on full taxable income (as if no exclusion)
    2. Compute tax on the excluded amount
    3. Tax with FEIE = (1) minus (2)

    Args:
        profile: Taxpayer profile
        taxable_income_no_feie: Actual taxable income without FEIE
        tax_without_feie: Income tax computed without FEIE
        earned_income: Total foreign earned income (Schedule C profits)
    """
    result = Form2555Result()
    lines = []

    result.foreign_earned_income = earned_income

    # Physical presence test (330 days in any consecutive 12-month period)
    days_abroad = profile.days_in_foreign_country_2025
    qualifies = days_abroad >= 330

    lines.append(LineItem("Form 2555", "Physical Presence",
                          f"Days in foreign country: {days_abroad}",
                          float(days_abroad),
                          f"Need 330 full days in 12-month period. "
                          f"{'QUALIFIES' if qualifies else 'DOES NOT QUALIFY'}. "
                          f"Note: test is any 12-month period overlapping the "
                          f"tax year, not just calendar year."))

    if not qualifies:
        result.is_beneficial = False
        result.lines = lines
        return result

    # Exclusion amount
    exclusion = min(earned_income, FEIE_EXCLUSION_LIMIT)
    result.exclusion_amount = exclusion
    lines.append(LineItem("Form 2555", "42",
                          "Foreign earned income exclusion",
                          round(exclusion, 2),
                          f"Lesser of earned income ${earned_income:,.2f} "
                          f"or limit ${FEIE_EXCLUSION_LIMIT:,}"))

    # Stacking method: use actual taxable income, not raw earned income
    # Tax on full taxable income (already computed as tax_without_feie)
    # Tax on excluded portion (at the bottom of the bracket stack)
    # Bug 3 fix: use correct brackets for filing status
    brackets = BRACKETS_BY_STATUS.get(profile.filing_status, MFS_BRACKETS)
    tax_on_excluded = calculate_income_tax(exclusion, brackets)
    tax_with_feie = max(tax_without_feie - tax_on_excluded, 0)

    result.tax_with_feie = round(tax_with_feie, 2)
    result.tax_without_feie = round(tax_without_feie, 2)
    result.savings = round(tax_without_feie - tax_with_feie, 2)
    result.is_beneficial = result.savings > 0

    lines.append(LineItem("Form 2555", "Analysis",
                          "Tax comparison",
                          result.savings,
                          f"Tax WITHOUT FEIE: ${tax_without_feie:,.2f}\n"
                          f"Tax WITH FEIE: ${tax_with_feie:,.2f}\n"
                          f"Income tax savings: ${result.savings:,.2f}\n"
                          f"Note: SE tax is UNCHANGED by FEIE.\n"
                          f"{'BENEFICIAL' if result.is_beneficial else 'NOT BENEFICIAL'}"))

    result.lines = lines
    return result


# =============================================================================
# Master Calculation — Builds the Full Return
# =============================================================================

def calculate_return(profile: TaxpayerProfile) -> Form1040Result:
    """Calculate the complete federal tax return.

    This is the main entry point. It computes all forms and schedules
    and produces a complete Form1040Result with every line item.
    """
    result = Form1040Result()
    lines = []
    fs = profile.filing_status

    # ─── SCHEDULE C (for each business) ─────────────────────────
    # Auto-create Schedule C from 1099-NEC if no businesses defined
    businesses = list(profile.businesses)
    if not businesses and profile.forms_1099_nec:
        nec_total = sum(f.nonemployee_compensation for f in profile.forms_1099_nec)
        if nec_total > 0:
            businesses.append(ScheduleCData(
                business_name="1099-NEC Income",
                gross_receipts=nec_total,
            ))

    total_business_income = 0.0
    for biz in businesses:
        sc = calculate_schedule_c(biz)
        result.schedule_c_results.append(sc)
        total_business_income += sc.net_profit_loss
        lines.append(LineItem("Schedule 1", "3",
                              f"Business income: {biz.business_name}",
                              sc.net_profit_loss,
                              "From Schedule C, Line 31"))

    # ─── SCHEDULE E (K-1 income) ───────────────────────────────
    sch_e = None
    k1_se_income = 0.0
    k1_other_income = 0.0
    net_investment_income = 0.0

    if profile.schedule_k1s:
        sch_e = calculate_schedule_e(profile)
        result.schedule_e = sch_e

        # K-1 SE earnings (Box 14 / guaranteed payments) feed into SE tax
        k1_se_income = sch_e.se_earnings_from_k1 + sch_e.guaranteed_payments

        # All K-1 income flows to Schedule 1 initially
        k1_other_income = sch_e.total_schedule_e_income
        # Subtract pieces that flow to Lines 2b/3b/7 instead of Schedule 1
        k1_other_income -= sch_e.interest_income
        # Note: capital_gains subtracted below only when Schedule D is computed

    # ─── INVESTMENT INCOME (Lines 2-7) ────────────────────────
    # Line 2a: Tax-exempt interest (informational)
    tax_exempt_interest = sum(f.tax_exempt_interest for f in profile.forms_1099_int)
    result.tax_exempt_interest = round(tax_exempt_interest, 2)

    # Line 2b: Taxable interest (1099-INT Box 1 + K-1 Box 5)
    taxable_interest = (
        sum(f.interest_income for f in profile.forms_1099_int)
        + (sch_e.interest_income if sch_e else 0.0)
    )
    result.taxable_interest = round(taxable_interest, 2)

    # Line 3a: Qualified dividends (1099-DIV Box 1b + K-1 Box 6b)
    qualified_dividends = (
        sum(f.qualified_dividends for f in profile.forms_1099_div)
        + (sch_e.qualified_dividends if sch_e else 0.0)
    )
    result.qualified_dividends = round(qualified_dividends, 2)

    # Line 3b: Ordinary dividends (1099-DIV Box 1a + K-1 Box 6a)
    ordinary_dividends = (
        sum(f.ordinary_dividends for f in profile.forms_1099_div)
        + (sch_e.dividends if sch_e else 0.0)
    )
    result.ordinary_dividends = round(ordinary_dividends, 2)
    # Subtract K-1 dividends from k1_other_income (they flow to Line 3b, not Sch 1)
    if sch_e:
        k1_other_income -= sch_e.dividends

    # Schedule D / Line 7: Capital gains and losses
    has_cap_activity = (
        profile.forms_1099_b
        or any(k1.net_short_term_capital_gain != 0 or k1.net_long_term_capital_gain != 0
               or k1.net_section_1231_gain != 0 for k1 in profile.schedule_k1s)
        or any(f.capital_gain_distributions > 0 for f in profile.forms_1099_div)
    )
    sch_d = None
    if has_cap_activity:
        sch_d = calculate_schedule_d(profile, fs)
        result.schedule_d = sch_d
        result.capital_gain_loss = sch_d.capital_gain_for_1040
        # Subtract K-1 capital gains from k1_other_income (they flow through Sch D)
        if sch_e:
            k1_other_income -= sch_e.capital_gains

    # Net investment income for NIIT
    net_investment_income += max(taxable_interest, 0)
    net_investment_income += max(ordinary_dividends, 0)
    if sch_d and sch_d.net_capital_gain_loss > 0:
        net_investment_income += sch_d.net_capital_gain_loss
    if sch_e:
        net_investment_income += max(sch_e.net_rental_income, 0)
        net_investment_income += max(sch_e.royalties, 0)

    # ─── SCHEDULE SE ───────────────────────────────────────────
    # SE income = Schedule C profits + K-1 SE earnings
    total_se_income = total_business_income + k1_se_income
    # W-2 SS wages reduce the remaining SS wage base for SE tax
    w2_ss_wages = sum(w2.ss_wages for w2 in profile.forms_w2)
    if total_se_income >= SE_MINIMUM_INCOME:
        se = calculate_schedule_se(total_se_income, w2_ss_wages=w2_ss_wages)
        result.schedule_se = se
        result.se_tax = se.se_tax

    # ─── FORM 1040: INCOME ─────────────────────────────────────
    # W-2 wage income (Line 1a)
    wages = sum(w2.wages for w2 in profile.forms_w2)
    result.wage_income = round(wages, 2)
    if wages > 0:
        lines.append(LineItem("Form 1040", "1a", "Wages, salaries, tips",
                              result.wage_income))

    # Lines 2a/2b
    if result.tax_exempt_interest > 0:
        lines.append(LineItem("Form 1040", "2a", "Tax-exempt interest",
                              result.tax_exempt_interest))
    if result.taxable_interest > 0:
        lines.append(LineItem("Form 1040", "2b", "Taxable interest",
                              result.taxable_interest))

    # Lines 3a/3b
    if result.qualified_dividends > 0:
        lines.append(LineItem("Form 1040", "3a", "Qualified dividends",
                              result.qualified_dividends))
    if result.ordinary_dividends > 0:
        lines.append(LineItem("Form 1040", "3b", "Ordinary dividends",
                              result.ordinary_dividends))

    # Line 7
    if result.capital_gain_loss != 0:
        lines.append(LineItem("Form 1040", "7", "Capital gain or (loss)",
                              result.capital_gain_loss))

    # Schedule 1 income: business + K-1 (non-investment portions)
    schedule_1_income = total_business_income + k1_other_income
    lines.append(LineItem("Form 1040", "8",
                          "Other income (Schedule 1)",
                          round(schedule_1_income, 2)))

    result.total_income = round(
        wages + taxable_interest + ordinary_dividends
        + result.capital_gain_loss + schedule_1_income, 2
    )
    lines.append(LineItem("Form 1040", "9", "Total income",
                          result.total_income))

    # ─── ADJUSTMENTS TO INCOME (Schedule 1, Part II) ───────────
    adjustments = 0.0

    # Deductible half of SE tax
    if result.schedule_se:
        adj_se = result.schedule_se.deductible_se_tax
        adjustments += adj_se
        lines.append(LineItem("Schedule 1", "15",
                              "Deductible part of self-employment tax",
                              adj_se))

    # Self-employed health insurance deduction
    # Per Form 7206 / Pub 535: limited to net profit from the business
    # under which the plan is established, minus the deductible SE tax
    if profile.health_insurance and profile.health_insurance.total_premiums > 0:
        se_tax_deduction = result.schedule_se.deductible_se_tax if result.schedule_se else 0
        max_health = max(total_business_income - se_tax_deduction, 0)
        health_deduction = round(min(
            profile.health_insurance.total_premiums,
            max_health,
        ), 2)
        adjustments += health_deduction
        lines.append(LineItem("Schedule 1", "17",
                              "Self-employed health insurance deduction",
                              health_deduction,
                              f"100% of premiums (${profile.health_insurance.total_premiums:,.2f}), "
                              f"limited to net SE income minus deductible SE tax "
                              f"(${max_health:,.2f})"))

    result.adjustments = round(adjustments, 2)
    lines.append(LineItem("Form 1040", "10",
                          "Adjustments to income",
                          result.adjustments))

    # ─── AGI ───────────────────────────────────────────────────
    result.agi = round(result.total_income - result.adjustments, 2)
    lines.append(LineItem("Form 1040", "11",
                          "Adjusted Gross Income (AGI)",
                          result.agi,
                          "Total income minus adjustments"))

    # ─── DEDUCTIONS ────────────────────────────────────────────
    result.deduction = STANDARD_DEDUCTION[fs.value]
    lines.append(LineItem("Form 1040", "13a",
                          f"Standard deduction ({fs.value.upper()})",
                          result.deduction))

    # ─── QBI DEDUCTION ─────────────────────────────────────────
    # Aggregate K-1 QBI (non-SSTB partnerships only)
    k1_qbi = sum(k1.qbi_amount for k1 in profile.schedule_k1s if not k1.is_sstb)
    k1_w2_wages = sum(k1.qbi_w2_wages for k1 in profile.schedule_k1s if not k1.is_sstb)
    k1_ubia = sum(k1.qbi_ubia for k1 in profile.schedule_k1s if not k1.is_sstb)

    taxable_before_qbi = max(result.agi - result.deduction, 0)
    # Net capital gain for §199A cap includes qualified dividends
    qbi_net_cap_gain = (
        max(result.schedule_d.net_capital_gain_loss, 0) if result.schedule_d else 0.0
    ) + qualified_dividends
    qbi_result = calculate_qbi_deduction(
        taxable_before_qbi, result.schedule_c_results, fs,
        k1_qbi=k1_qbi, k1_w2_wages=k1_w2_wages, k1_ubia=k1_ubia,
        net_capital_gain=qbi_net_cap_gain,
    )
    result.qbi = qbi_result
    result.qbi_deduction = qbi_result.qbi_deduction
    lines.append(LineItem("Form 1040", "13b",
                          "Qualified business income deduction",
                          result.qbi_deduction))

    # ─── TAXABLE INCOME ────────────────────────────────────────
    result.taxable_income = round(max(
        result.agi - result.deduction - result.qbi_deduction, 0
    ), 2)
    lines.append(LineItem("Form 1040", "15", "Taxable income",
                          result.taxable_income))

    # ─── TAX ───────────────────────────────────────────────────
    brackets = BRACKETS_BY_STATUS.get(fs, MFS_BRACKETS)
    # Use QDCG worksheet when there are qualified dividends or net LTCG
    net_lt_for_qdcg = sch_d.net_lt_gain_loss if sch_d else 0.0
    net_st_for_qdcg = sch_d.net_st_gain_loss if sch_d else 0.0
    if qualified_dividends > 0 or net_lt_for_qdcg > 0:
        result.tax = calculate_tax_with_qdcg_worksheet(
            result.taxable_income,
            qualified_dividends,
            net_lt_for_qdcg,
            net_st_for_qdcg,
            fs,
        )
        tax_method = "QDCG worksheet"
    else:
        result.tax = calculate_income_tax(result.taxable_income, brackets)
        tax_method = f"{fs.value.upper()} tax brackets"
    lines.append(LineItem("Form 1040", "16", "Tax",
                          result.tax,
                          f"From {tax_method}"))

    # Additional Medicare Tax (Form 8959)
    # Per Form 8959: applies to combined W-2 Medicare wages + SE earnings
    # exceeding the filing-status threshold
    w2_medicare_wages = sum(w2.medicare_wages for w2 in profile.forms_w2)
    se_medicare_earnings = (
        result.schedule_se.taxable_se_earnings if result.schedule_se else 0.0
    )
    combined_medicare_earnings = w2_medicare_wages + se_medicare_earnings
    if combined_medicare_earnings > 0:
        result.additional_medicare = calculate_additional_medicare(
            combined_medicare_earnings, fs
        )
        if result.additional_medicare > 0:
            lines.append(LineItem("Schedule 2", "23",
                                  "Additional Medicare Tax (0.9%)",
                                  result.additional_medicare,
                                  f"Combined Medicare earnings "
                                  f"${combined_medicare_earnings:,.2f} "
                                  f"exceeds {fs.value.upper()} threshold"))

    # Net Investment Income Tax (Form 8960)
    if net_investment_income > 0:
        result.niit = calculate_niit(net_investment_income, result.agi, fs)
        if result.niit > 0:
            lines.append(LineItem("Schedule 2", "18",
                                  "Net Investment Income Tax (3.8%)",
                                  result.niit,
                                  f"On ${net_investment_income:,.2f} net investment income"))

    # AMT (Form 6251) — only relevant for itemizers with SALT
    salt_for_amt = profile.state_local_tax_deduction if profile.uses_itemized_deductions else 0.0
    if salt_for_amt > 0:
        amt_result = calculate_amt(
            result.taxable_income, result.tax, fs,
            salt_deduction=salt_for_amt,
        )
        result.amt = amt_result.amt
        result.form_6251 = amt_result
        if result.amt > 0:
            lines.append(LineItem("Schedule 2", "1",
                                  "Alternative Minimum Tax",
                                  result.amt))

    # ─── TAX CREDITS ─────────────────────────────────────────
    # Earned income for ACTC: wages + SE income
    earned_income_for_credits = wages + max(total_business_income, 0)
    # Tax before credits = income tax + AMT (credits reduce this)
    tax_before_credits = result.tax + result.amt
    refundable_actc = 0.0

    if profile.dependents:
        credits_result = calculate_tax_credits(
            profile, result.agi, tax_before_credits, earned_income_for_credits,
        )
        result.tax_credits = credits_result
        result.nonrefundable_credits = credits_result.nonrefundable_credit
        refundable_actc = credits_result.refundable_actc
        if result.nonrefundable_credits > 0:
            lines.append(LineItem("Form 1040", "19",
                                  "Nonrefundable credits (CTC/ODC)",
                                  result.nonrefundable_credits))

    # ─── TOTAL TAX ─────────────────────────────────────────────
    result.total_tax = round(
        result.tax + result.se_tax + result.additional_medicare
        + result.niit + result.amt - result.nonrefundable_credits, 2
    )
    result.total_tax = max(result.total_tax, 0)
    lines.append(LineItem("Form 1040", "24", "Total tax",
                          result.total_tax,
                          f"Income tax ${result.tax:,.2f} + "
                          f"SE tax ${result.se_tax:,.2f} + "
                          f"Addl Medicare ${result.additional_medicare:,.2f}"
                          + (f" + NIIT ${result.niit:,.2f}" if result.niit else "")
                          + (f" + AMT ${result.amt:,.2f}" if result.amt else "")
                          + (f" - credits ${result.nonrefundable_credits:,.2f}"
                             if result.nonrefundable_credits else "")))

    # ─── PAYMENTS ──────────────────────────────────────────────
    # Federal income tax withheld (Line 25)
    w2_withholding = sum(w2.federal_tax_withheld for w2 in profile.forms_w2)
    form_1099_withholding = (
        sum(f.federal_tax_withheld for f in profile.forms_1099_int)
        + sum(f.federal_tax_withheld for f in profile.forms_1099_div)
        + sum(f.federal_tax_withheld for f in profile.forms_1099_b)
        + sum(f.federal_tax_withheld for f in profile.forms_1099_nec)
    )
    result.withholding = round(w2_withholding + form_1099_withholding, 2)
    if result.withholding > 0:
        lines.append(LineItem("Form 1040", "25a",
                              "Federal income tax withheld",
                              result.withholding))

    result.estimated_payments = profile.total_estimated_payments
    if result.estimated_payments > 0:
        lines.append(LineItem("Form 1040", "26",
                              "Estimated tax payments",
                              result.estimated_payments))

    result.total_payments = round(
        result.withholding + result.estimated_payments + refundable_actc, 2
    )
    if refundable_actc > 0:
        lines.append(LineItem("Form 1040", "28",
                              "Additional Child Tax Credit (refundable)",
                              refundable_actc))
    lines.append(LineItem("Form 1040", "33", "Total payments",
                          result.total_payments))

    # ─── REFUND OR AMOUNT OWED ─────────────────────────────────
    if result.total_payments > result.total_tax:
        result.overpayment = round(result.total_payments - result.total_tax, 2)
        lines.append(LineItem("Form 1040", "34", "Overpaid",
                              result.overpayment))
    else:
        result.amount_owed = round(result.total_tax - result.total_payments, 2)
        lines.append(LineItem("Form 1040", "37", "Amount you owe",
                              result.amount_owed))

    result.lines = lines
    return result


# =============================================================================
# Optimization Analysis
# =============================================================================

def compare_feie_scenarios(profile: TaxpayerProfile) -> dict:
    """Compare tax outcomes with and without FEIE."""
    # Calculate without FEIE
    result_no_feie = calculate_return(profile)

    # Total earned income from Schedule C businesses
    earned_income = sum(sc.net_profit_loss for sc in result_no_feie.schedule_c_results)

    # Evaluate FEIE using actual taxable income and computed tax
    feie_eval = evaluate_feie(
        profile,
        taxable_income_no_feie=result_no_feie.taxable_income,
        tax_without_feie=result_no_feie.tax,
        earned_income=max(earned_income, 0),
    )

    return {
        "without_feie": {
            "income_tax": result_no_feie.tax,
            "se_tax": result_no_feie.se_tax,
            "additional_medicare": result_no_feie.additional_medicare,
            "niit": result_no_feie.niit,
            "total_tax": result_no_feie.total_tax,
        },
        "feie_evaluation": {
            "qualifies": feie_eval.exclusion_amount > 0,
            "exclusion_amount": feie_eval.exclusion_amount,
            "income_tax_with_feie": feie_eval.tax_with_feie,
            "income_tax_savings": feie_eval.savings,
            "se_tax_unchanged": result_no_feie.se_tax,
            "is_beneficial": feie_eval.is_beneficial,
        },
        "feie_result": feie_eval,
        "recommendation": (
            f"Take the FEIE — saves ${feie_eval.savings:,.2f} in income tax"
            if feie_eval.is_beneficial
            else "Skip the FEIE — not beneficial for your situation"
        ),
    }


def estimate_quarterly_payments(
    total_tax: float,
    prior_year_tax: float,
    agi: float,
    filing_status: FilingStatus = FilingStatus.MFS,
) -> dict:
    """Estimate recommended quarterly payments for next year.

    Safe harbor: pay 100% of prior year tax (110% if AGI > threshold)
    or 90% of current year tax, whichever is less.
    Bug 4 fix: uses filing-status-specific high-income threshold.
    """
    threshold = ESTIMATED_TAX_HIGH_INCOME_THRESHOLDS.get(
        filing_status, ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS
    )
    prior_year_pct = (ESTIMATED_TAX_PRIOR_YEAR_HIGH_INCOME_PCT
                      if agi > threshold
                      else ESTIMATED_TAX_PRIOR_YEAR_PCT)

    safe_harbor_prior = round(prior_year_tax * prior_year_pct, 2)
    safe_harbor_current = round(total_tax * ESTIMATED_TAX_SAFE_HARBOR_PCT, 2)

    recommended_annual = min(safe_harbor_prior, safe_harbor_current)
    quarterly = round(recommended_annual / 4, 2)

    return {
        "safe_harbor_prior_year": safe_harbor_prior,
        "safe_harbor_current_year": safe_harbor_current,
        "recommended_annual": recommended_annual,
        "recommended_quarterly": quarterly,
        "method": (
            f"{'110' if agi > threshold else '100'}% of prior year tax"
            if safe_harbor_prior <= safe_harbor_current
            else "90% of current year tax"
        ),
    }


# =============================================================================
# Optimization Recommendations
# =============================================================================

def generate_optimization_recommendations(
    result: Form1040Result,
    profile: TaxpayerProfile,
) -> list[dict]:
    """Generate ranked optimization suggestions based on the return.

    Returns a list of dicts with 'title', 'description', 'estimated_savings'.
    """
    recommendations = []

    # Check FEIE benefit
    if profile.days_in_foreign_country_2025 >= 330:
        earned_income = sum(sc.net_profit_loss for sc in result.schedule_c_results)
        if earned_income > 0:
            feie_eval = evaluate_feie(
                profile,
                result.taxable_income,
                result.tax,
                max(earned_income, 0),
            )
            if feie_eval.is_beneficial:
                recommendations.append({
                    "title": "Claim Foreign Earned Income Exclusion",
                    "description": (
                        f"You qualify for FEIE with {profile.days_in_foreign_country_2025} "
                        f"days abroad. Excludes up to ${FEIE_EXCLUSION_LIMIT:,} from income tax."
                    ),
                    "estimated_savings": feie_eval.savings,
                })

    # Check retirement contributions
    se_income = sum(sc.net_profit_loss for sc in result.schedule_c_results)
    if se_income > 50_000:
        # SEP-IRA: 25% of net SE income (after deductible SE tax), max $69,000
        se_tax_ded = result.schedule_se.deductible_se_tax if result.schedule_se else 0
        sep_max = min((se_income - se_tax_ded) * 0.25, 69_000)
        if sep_max > 0:
            brackets = BRACKETS_BY_STATUS.get(profile.filing_status, MFS_BRACKETS)
            # Estimate marginal rate
            marginal_rate = 0.22
            for upper, rate in brackets:
                if result.taxable_income <= upper:
                    marginal_rate = rate
                    break
            est_savings = round(sep_max * marginal_rate, 2)
            recommendations.append({
                "title": "SEP-IRA Contribution",
                "description": (
                    f"Contribute up to ${sep_max:,.0f} to a SEP-IRA to reduce "
                    f"taxable income. Deadline is filing deadline (including extensions)."
                ),
                "estimated_savings": est_savings,
            })

    # Check home office optimization
    for biz in profile.businesses:
        if biz.home_office and biz.home_office.use_simplified_method:
            if biz.home_office.total_home_sqft > 0 and biz.home_office.office_sqft > 0:
                regular = biz.home_office.regular_deduction
                simplified = biz.home_office.simplified_deduction
                if regular > simplified:
                    recommendations.append({
                        "title": f"Switch {biz.business_name} to regular home office method",
                        "description": (
                            f"Regular method deduction: ${regular:,.2f} vs "
                            f"simplified: ${simplified:,.2f}."
                        ),
                        "estimated_savings": round(regular - simplified, 2),
                    })

    # Sort by estimated savings descending
    recommendations.sort(key=lambda r: r["estimated_savings"], reverse=True)
    return recommendations
