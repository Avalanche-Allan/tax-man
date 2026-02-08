"""Report generation for tax return analysis.

Produces human-readable summaries, optimization analysis,
and filing checklists from calculated tax data.
"""

from taxman.calculator import (
    Form1040Result,
    estimate_quarterly_payments,
)
from taxman.constants import (
    ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS,
    FILING_DEADLINE,
    EXTENSION_DEADLINE,
)
from taxman.models import TaxpayerProfile, FilingStatus


def generate_tax_summary(result: Form1040Result,
                         profile: TaxpayerProfile = None) -> str:
    """Generate a plain-English summary of the tax return.

    Bug 8 fix: Derives filing status and situation from profile data.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("2025 FEDERAL TAX RETURN SUMMARY")

    if profile:
        fs_display = profile.filing_status.value.upper()
        lines.append(f"Filing Status: {fs_display}")
        if profile.first_name or profile.last_name:
            lines.append(f"Taxpayer: {profile.first_name} {profile.last_name}")
    else:
        lines.append("Filing Status: Married Filing Separately")

    lines.append("=" * 60)
    lines.append("")

    # Income
    lines.append("INCOME")
    lines.append("-" * 40)
    for i, sc in enumerate(result.schedule_c_results):
        biz_name = sc.business_name
        if profile and i < len(profile.businesses):
            biz_name = profile.businesses[i].business_name or biz_name
        lines.append(f"  {biz_name}:")
        lines.append(f"    Gross receipts:    ${sc.gross_receipts:>12,.2f}")
        lines.append(f"    Total expenses:    ${sc.total_expenses:>12,.2f}")
        lines.append(f"    Net profit/loss:   ${sc.net_profit_loss:>12,.2f}")
        lines.append("")

    if result.schedule_e:
        se = result.schedule_e
        lines.append("  Schedule E (K-1 income):")
        if se.net_rental_income != 0:
            lines.append(f"    Rental income:     ${se.net_rental_income:>12,.2f}")
        if se.ordinary_business_income != 0:
            lines.append(f"    Ordinary business: ${se.ordinary_business_income:>12,.2f}")
        if se.guaranteed_payments != 0:
            lines.append(f"    Guaranteed pmts:   ${se.guaranteed_payments:>12,.2f}")
        if se.interest_income != 0:
            lines.append(f"    Interest income:   ${se.interest_income:>12,.2f}")
        if se.capital_gains != 0:
            lines.append(f"    Capital gains:     ${se.capital_gains:>12,.2f}")
        lines.append(f"    Total K-1 income:  ${se.total_schedule_e_income:>12,.2f}")
        lines.append("")

    lines.append(f"  TOTAL INCOME:        ${result.total_income:>12,.2f}")
    lines.append("")

    # Adjustments
    lines.append("ADJUSTMENTS TO INCOME")
    lines.append("-" * 40)
    lines.append(f"  Total adjustments:   ${result.adjustments:>12,.2f}")
    lines.append(f"  AGI:                 ${result.agi:>12,.2f}")
    lines.append("")

    # Deductions
    lines.append("DEDUCTIONS")
    lines.append("-" * 40)
    lines.append(f"  Standard deduction:  ${result.deduction:>12,.2f}")
    lines.append(f"  QBI deduction:       ${result.qbi_deduction:>12,.2f}")
    lines.append(f"  TAXABLE INCOME:      ${result.taxable_income:>12,.2f}")
    lines.append("")

    # Tax
    lines.append("TAX")
    lines.append("-" * 40)
    lines.append(f"  Income tax:          ${result.tax:>12,.2f}")
    lines.append(f"  Self-employment tax: ${result.se_tax:>12,.2f}")
    if result.additional_medicare > 0:
        lines.append(f"  Addl Medicare tax:   ${result.additional_medicare:>12,.2f}")
    if result.niit > 0:
        lines.append(f"  Net invest inc tax:  ${result.niit:>12,.2f}")
    lines.append(f"  TOTAL TAX:           ${result.total_tax:>12,.2f}")
    lines.append("")

    # Payments
    lines.append("PAYMENTS")
    lines.append("-" * 40)
    lines.append(f"  Estimated payments:  ${result.estimated_payments:>12,.2f}")
    lines.append(f"  Total payments:      ${result.total_payments:>12,.2f}")
    lines.append("")

    # Result
    lines.append("=" * 60)
    if result.overpayment > 0:
        lines.append(f"  REFUND:              ${result.overpayment:>12,.2f}")
    else:
        lines.append(f"  AMOUNT OWED:         ${result.amount_owed:>12,.2f}")
    lines.append("=" * 60)
    lines.append("")

    # Effective rates
    if result.total_income > 0:
        effective_rate = result.total_tax / result.total_income * 100
        income_tax_rate = result.tax / result.total_income * 100
        se_tax_rate = result.se_tax / result.total_income * 100
        lines.append(f"  Effective tax rate:     {effective_rate:.1f}%")
        lines.append(f"    Income tax rate:      {income_tax_rate:.1f}%")
        lines.append(f"    SE tax rate:          {se_tax_rate:.1f}%")
        if result.additional_medicare > 0:
            addl_rate = result.additional_medicare / result.total_income * 100
            lines.append(f"    Addl Medicare rate:   {addl_rate:.1f}%")
        if result.niit > 0:
            niit_rate = result.niit / result.total_income * 100
            lines.append(f"    NIIT rate:            {niit_rate:.1f}%")

    return "\n".join(lines)


def generate_line_detail(result: Form1040Result) -> str:
    """Generate detailed line-by-line calculation report."""
    lines = []
    lines.append("DETAILED LINE-BY-LINE CALCULATIONS")
    lines.append("=" * 70)
    lines.append("")

    current_form = None
    for item in result.lines:
        if item.form != current_form:
            lines.append("")
            lines.append(f"── {item.form} {'─' * (60 - len(item.form))}")
            current_form = item.form

        amount_str = f"${item.amount:>12,.2f}" if item.amount != 0 else "         $0"
        lines.append(f"  Line {item.line:<6} {item.description:<35} {amount_str}")
        if item.explanation:
            for exp_line in item.explanation.split("\n"):
                lines.append(f"             {exp_line}")

    # Schedule C details
    for sc in result.schedule_c_results:
        lines.append("")
        lines.append(f"── Schedule C: {sc.business_name} {'─' * (45 - len(sc.business_name))}")
        for item in sc.lines:
            amount_str = f"${item.amount:>12,.2f}" if item.amount != 0 else "         $0"
            lines.append(f"  Line {item.line:<6} {item.description:<35} {amount_str}")

    # Schedule SE details
    if result.schedule_se:
        lines.append("")
        lines.append("── Schedule SE " + "─" * 50)
        for item in result.schedule_se.lines:
            amount_str = f"${item.amount:>12,.2f}"
            lines.append(f"  Line {item.line:<6} {item.description:<35} {amount_str}")
            if item.explanation:
                lines.append(f"             {item.explanation}")

    # Schedule E details
    if result.schedule_e:
        lines.append("")
        lines.append("── Schedule E (K-1 Income) " + "─" * 39)
        for item in result.schedule_e.lines:
            amount_str = f"${item.amount:>12,.2f}" if item.amount != 0 else "         $0"
            lines.append(f"  Line {item.line:<12} {item.description:<29} {amount_str}")
            if item.explanation:
                for exp_line in item.explanation.split("\n"):
                    lines.append(f"                   {exp_line}")

    # QBI details
    if result.qbi:
        lines.append("")
        lines.append("── Form 8995 (QBI Deduction) " + "─" * 37)
        for item in result.qbi.lines:
            amount_str = f"${item.amount:>12,.2f}"
            lines.append(f"  Line {item.line:<6} {item.description:<35} {amount_str}")
            if item.explanation:
                lines.append(f"             {item.explanation}")

    return "\n".join(lines)


def generate_filing_checklist(result: Form1040Result = None,
                              profile: TaxpayerProfile = None) -> str:
    """Generate filing checklist with deadlines and instructions.

    Bug 8 fix: Builds form list from actual result data; derives
    filing status and business info from profile.
    """
    # Determine filing situation from profile
    if profile:
        fs = profile.filing_status.value.upper()
        is_abroad = profile.foreign_address
        has_co = profile.has_colorado_filing_obligation
    else:
        fs = "MFS"
        is_abroad = True
        has_co = True

    forms = []
    forms.append("  [ ] Form 1040 — U.S. Individual Income Tax Return")
    forms.append("  [ ] Schedule 1 — Additional Income and Adjustments")

    # Schedule 2 if any additional taxes
    has_sched2 = False
    if result:
        if result.se_tax > 0 or result.additional_medicare > 0 or result.niit > 0:
            has_sched2 = True
    else:
        has_sched2 = True
    if has_sched2:
        forms.append("  [ ] Schedule 2 — Additional Taxes (SE tax, Addl Medicare)")

    # Schedule C — one per business
    if result and result.schedule_c_results:
        for sc in result.schedule_c_results:
            forms.append(f"  [ ] Schedule C — Profit or Loss ({sc.business_name})")
    elif profile and profile.businesses:
        for biz in profile.businesses:
            forms.append(f"  [ ] Schedule C — Profit or Loss ({biz.business_name})")
    else:
        forms.append("  [ ] Schedule C — Profit or Loss From Business")

    # Schedule SE
    if (result and result.se_tax > 0) or not result:
        forms.append("  [ ] Schedule SE — Self-Employment Tax")

    # Schedule E
    if (result and result.schedule_e) or (profile and profile.schedule_k1s):
        forms.append("  [ ] Schedule E — Supplemental Income (K-1)")

    # QBI
    if result and result.qbi and result.qbi.qbi_deduction > 0:
        form_num = "8995-A" if result.qbi.is_limited else "8995"
        forms.append(f"  [ ] Form {form_num} — Qualified Business Income Deduction")
    elif not result:
        forms.append("  [ ] Form 8995 — Qualified Business Income Deduction")

    # FEIE
    if result and result.feie and result.feie.is_beneficial:
        forms.append("  [ ] Form 2555 — Foreign Earned Income Exclusion")
    elif not result and is_abroad:
        forms.append("  [ ] Form 2555 — Foreign Earned Income Exclusion (if beneficial)")

    # Additional Medicare
    if (result and result.additional_medicare > 0) or not result:
        forms.append("  [ ] Form 8959 — Additional Medicare Tax (if applicable)")

    # NIIT
    if (result and result.niit > 0) or not result:
        forms.append("  [ ] Form 8960 — Net Investment Income Tax (if applicable)")

    forms_str = "\n".join(forms)

    abroad_note = ""
    if is_abroad:
        abroad_note = """
ABROAD EXTENSION:
  - As a US citizen abroad, you get an automatic 2-month
    extension to June 15, 2026 (attach statement to return)
  - Interest still accrues from April 15 on any amount owed"""

    co_note = ""
    if has_co:
        co_note = """
COLORADO STATE FILING:
  - Evaluate obligation based on rental property income
  - CO requires filing if you have CO-source income
  - File Form 104 (Colorado Individual Income Tax Return)
  - Deadline: April 15, 2026"""

    return f"""
FILING CHECKLIST — 2025 Federal Tax Return ({fs})
{'=' * 50}

FORMS TO FILE:
{forms_str}

DEADLINES:
  Regular deadline:      {FILING_DEADLINE}
  Extension (Form 4868): {EXTENSION_DEADLINE}
{abroad_note}

FILING METHOD:
  E-filing via tax software is the easiest option.
  MeF-approved software can e-file 1040 with all schedules.

  If paper filing:
    Mail to: Department of the Treasury
             Internal Revenue Service
             Austin, TX 73301-0215 (if amount owed)
             Austin, TX 73301-0002 (if refund)

IMPORTANT NOTES:
  - Consider Form 4868 for extension to October 15 if needed
  - Estimated payments for 2026 are separate — see quarterly plan
{co_note}
"""


def generate_quarterly_plan(total_tax: float, prior_year_tax: float,
                            agi: float,
                            filing_status: FilingStatus = FilingStatus.MFS) -> str:
    """Generate 2026 estimated tax payment plan.

    Bug 4/8 fix: passes filing_status to estimate_quarterly_payments.
    """
    est = estimate_quarterly_payments(
        total_tax, prior_year_tax, agi, filing_status=filing_status
    )

    threshold = ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS

    return f"""
2026 ESTIMATED TAX PAYMENT PLAN
{'=' * 50}

Based on 2025 return:
  Total 2025 tax:          ${total_tax:>12,.2f}
  2025 AGI:                ${agi:>12,.2f}

Safe harbor calculation:
  90% of 2025 tax:         ${est['safe_harbor_current_year']:>12,.2f}
  {'110' if agi > threshold else '100'}% of 2024 tax:         ${est['safe_harbor_prior_year']:>12,.2f}
  Method used:             {est['method']}

RECOMMENDED QUARTERLY PAYMENTS:
  Annual total:            ${est['recommended_annual']:>12,.2f}
  Each quarter:            ${est['recommended_quarterly']:>12,.2f}

  Q1 due: April 15, 2026      ${est['recommended_quarterly']:>10,.2f}
  Q2 due: June 15, 2026       ${est['recommended_quarterly']:>10,.2f}
  Q3 due: September 15, 2026  ${est['recommended_quarterly']:>10,.2f}
  Q4 due: January 15, 2027    ${est['recommended_quarterly']:>10,.2f}

Pay via IRS Direct Pay: https://www.irs.gov/payments
Or EFTPS: https://www.eftps.gov
"""


def generate_feie_comparison_report(scenarios: dict) -> str:
    """Generate detailed FEIE comparison report."""
    wo = scenarios["without_feie"]
    fe = scenarios["feie_evaluation"]

    lines = []
    lines.append("FEIE COMPARISON ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("WITHOUT FEIE:")
    lines.append(f"  Income tax:          ${wo['income_tax']:>12,.2f}")
    lines.append(f"  SE tax:              ${wo['se_tax']:>12,.2f}")
    lines.append(f"  Addl Medicare:       ${wo['additional_medicare']:>12,.2f}")
    if wo['niit'] > 0:
        lines.append(f"  NIIT:                ${wo['niit']:>12,.2f}")
    lines.append(f"  Total tax:           ${wo['total_tax']:>12,.2f}")
    lines.append("")
    lines.append("WITH FEIE:")
    lines.append(f"  Exclusion:           ${fe['exclusion_amount']:>12,.2f}")
    lines.append(f"  Income tax:          ${fe['income_tax_with_feie']:>12,.2f}")
    lines.append(f"  SE tax (unchanged):  ${fe['se_tax_unchanged']:>12,.2f}")
    lines.append("")
    lines.append(f"  Income tax savings:  ${fe['income_tax_savings']:>12,.2f}")
    lines.append("")
    lines.append(f"  RECOMMENDATION: {scenarios['recommendation']}")

    return "\n".join(lines)


def generate_prior_year_comparison(current: Form1040Result,
                                   prior: dict) -> str:
    """Generate year-over-year comparison report.

    Args:
        current: Current year Form1040Result
        prior: Dict with prior year values (total_income, agi, total_tax, etc.)
    """
    lines = []
    lines.append("YEAR-OVER-YEAR COMPARISON")
    lines.append("=" * 60)
    lines.append(f"{'':>25} {'Prior Year':>12} {'Current':>12} {'Change':>12}")
    lines.append("-" * 60)

    comparisons = [
        ("Total Income", prior.get("total_income", 0), current.total_income),
        ("AGI", prior.get("agi", 0), current.agi),
        ("Taxable Income", prior.get("taxable_income", 0), current.taxable_income),
        ("Income Tax", prior.get("tax", 0), current.tax),
        ("SE Tax", prior.get("se_tax", 0), current.se_tax),
        ("Total Tax", prior.get("total_tax", 0), current.total_tax),
    ]

    for label, prior_val, current_val in comparisons:
        change = current_val - prior_val
        sign = "+" if change > 0 else ""
        lines.append(
            f"  {label:<23} ${prior_val:>11,.2f} ${current_val:>11,.2f} "
            f"{sign}${change:>10,.2f}"
        )

    return "\n".join(lines)
