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


def generate_tax_summary(result: Form1040Result) -> str:
    """Generate a plain-English summary of the tax return."""
    lines = []
    lines.append("=" * 60)
    lines.append("2025 FEDERAL TAX RETURN SUMMARY")
    lines.append("Filing Status: Married Filing Separately")
    lines.append("=" * 60)
    lines.append("")

    # Income
    lines.append("INCOME")
    lines.append("-" * 40)
    for sc in result.schedule_c_results:
        lines.append(f"  {sc.business_name}:")
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


def generate_filing_checklist() -> str:
    """Generate filing checklist with deadlines and instructions."""
    return f"""
FILING CHECKLIST — 2025 Federal Tax Return
{'=' * 50}

FORMS TO FILE:
  [ ] Form 1040 — U.S. Individual Income Tax Return
  [ ] Schedule 1 — Additional Income and Adjustments
  [ ] Schedule 2 — Additional Taxes (SE tax, Addl Medicare)
  [ ] Schedule C — Profit or Loss From Business (Law Firm LLC)
  [ ] Schedule C — Profit or Loss From Business (DocSherpa LLC)
  [ ] Schedule SE — Self-Employment Tax
  [ ] Schedule E — Supplemental Income (K-1 rental)
  [ ] Form 8995 — Qualified Business Income Deduction
  [ ] Form 2555 — Foreign Earned Income Exclusion (if beneficial)
  [ ] Form 8959 — Additional Medicare Tax (if applicable)
  [ ] Form 8960 — Net Investment Income Tax (if applicable)

DEADLINES:
  Regular deadline:     {FILING_DEADLINE}
  Abroad auto-extend:  June 15, 2026 (attach statement)
  Extension (Form 4868): {EXTENSION_DEADLINE}

FILING METHOD:
  Since you're MFS with foreign address and self-employment,
  e-filing via tax software is the easiest option.
  MeF-approved software can e-file 1040 with all schedules.

  If paper filing:
    Mail to: Department of the Treasury
             Internal Revenue Service
             Austin, TX 73301-0215 (if amount owed)
             Austin, TX 73301-0002 (if refund)

IMPORTANT NOTES:
  - As a US citizen abroad, you get an automatic 2-month
    extension to June 15, 2026 (attach statement to return)
  - Interest still accrues from April 15 on any amount owed
  - Consider Form 4868 for extension to October 15 if needed
  - Estimated payments for 2026 are separate — see quarterly plan

COLORADO STATE FILING:
  - Evaluate obligation based on rental property income
  - CO requires filing if you have CO-source income
  - File Form 104 (Colorado Individual Income Tax Return)
  - Deadline: April 15, 2026
"""


def generate_quarterly_plan(total_tax: float, prior_year_tax: float,
                            agi: float) -> str:
    """Generate 2026 estimated tax payment plan."""
    est = estimate_quarterly_payments(total_tax, prior_year_tax, agi)

    return f"""
2026 ESTIMATED TAX PAYMENT PLAN
{'=' * 50}

Based on 2025 return:
  Total 2025 tax:          ${total_tax:>12,.2f}
  2025 AGI:                ${agi:>12,.2f}

Safe harbor calculation:
  90% of 2025 tax:         ${est['safe_harbor_current_year']:>12,.2f}
  {'110' if agi > ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS else '100'}% of 2024 tax:         ${est['safe_harbor_prior_year']:>12,.2f}
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
