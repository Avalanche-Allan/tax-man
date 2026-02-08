"""Rich rendering helpers for Tax Man CLI.

All terminal display logic is centralized here — tables, panels,
progress bars, and formatted output for financial data.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()


def format_currency(amount: float) -> str:
    """Format a float as a currency string."""
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def display_welcome():
    """Display welcome panel."""
    panel = Panel(
        "[bold]Tax Man[/bold] — 2025 Federal Tax Return Preparation\n\n"
        "This wizard will walk you through:\n"
        "  1. Document scanning and parsing\n"
        "  2. Personal and business information\n"
        "  3. Income review and expense entry\n"
        "  4. Deduction selection\n"
        "  5. Tax calculation and optimization\n"
        "  6. Form generation\n\n"
        "[dim]DISCLAIMER: This tool assists with tax preparation but does not\n"
        "constitute tax advice. Consult a qualified tax professional.[/dim]",
        title="Welcome",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def display_income_table(schedule_c_results: list, schedule_e_result=None):
    """Display income summary as a Rich table."""
    table = Table(title="Income Summary", show_header=True, header_style="bold cyan")
    table.add_column("Source", style="white")
    table.add_column("Gross Receipts", justify="right", style="green")
    table.add_column("Expenses", justify="right", style="red")
    table.add_column("Net Profit/Loss", justify="right", style="bold")

    total_net = 0.0
    for sc in schedule_c_results:
        net_style = "green" if sc.net_profit_loss >= 0 else "red"
        table.add_row(
            sc.business_name,
            format_currency(sc.gross_receipts),
            format_currency(sc.total_expenses),
            Text(format_currency(sc.net_profit_loss), style=net_style),
        )
        total_net += sc.net_profit_loss

    if schedule_e_result:
        se = schedule_e_result
        if se.total_schedule_e_income != 0:
            net_style = "green" if se.total_schedule_e_income >= 0 else "red"
            table.add_row(
                "K-1 Income",
                "—",
                "—",
                Text(format_currency(se.total_schedule_e_income), style=net_style),
            )
            total_net += se.total_schedule_e_income

    table.add_section()
    total_style = "bold green" if total_net >= 0 else "bold red"
    table.add_row("TOTAL", "", "", Text(format_currency(total_net), style=total_style))

    console.print(table)


def display_tax_breakdown(result):
    """Display tax breakdown as a Rich table."""
    table = Table(title="Tax Breakdown", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white")
    table.add_column("Amount", justify="right", style="bold")
    table.add_column("Effective Rate", justify="right", style="dim")

    total_income = result.total_income or 1  # Avoid division by zero

    rows = [
        ("Income Tax", result.tax),
        ("Self-Employment Tax", result.se_tax),
    ]
    if result.additional_medicare > 0:
        rows.append(("Additional Medicare Tax", result.additional_medicare))
    if result.niit > 0:
        rows.append(("Net Investment Income Tax", result.niit))

    for name, amount in rows:
        rate = f"{amount / total_income * 100:.1f}%" if amount > 0 else "—"
        table.add_row(name, format_currency(amount), rate)

    table.add_section()
    total_rate = f"{result.total_tax / total_income * 100:.1f}%"
    table.add_row(
        Text("TOTAL TAX", style="bold"),
        Text(format_currency(result.total_tax), style="bold"),
        Text(total_rate, style="bold"),
    )

    console.print(table)


def display_schedule_c(sc_result, biz_data=None):
    """Display a single Schedule C as a Rich panel."""
    lines = []
    lines.append(f"Gross Receipts:     {format_currency(sc_result.gross_receipts)}")
    lines.append(f"Total Expenses:     {format_currency(sc_result.total_expenses)}")
    lines.append(f"Net Profit/Loss:    {format_currency(sc_result.net_profit_loss)}")

    if biz_data and biz_data.home_office:
        ho = biz_data.home_office
        if ho.use_simplified_method:
            lines.append(f"Home Office:        {format_currency(ho.simplified_deduction)} (simplified)")
        else:
            lines.append(f"Home Office:        {format_currency(ho.regular_deduction)} (regular)")

    content = "\n".join(lines)
    panel = Panel(
        content,
        title=f"Schedule C: {sc_result.business_name}",
        border_style="green" if sc_result.net_profit_loss >= 0 else "red",
    )
    console.print(panel)


def display_feie_comparison(scenarios: dict):
    """Display FEIE comparison as side-by-side tables."""
    table = Table(title="FEIE Comparison", show_header=True, header_style="bold cyan")
    table.add_column("", style="white")
    table.add_column("Without FEIE", justify="right")
    table.add_column("With FEIE", justify="right")
    table.add_column("Savings", justify="right", style="green")

    wo = scenarios["without_feie"]
    fe = scenarios["feie_evaluation"]

    table.add_row(
        "Income Tax",
        format_currency(wo["income_tax"]),
        format_currency(fe["income_tax_with_feie"]),
        format_currency(fe["income_tax_savings"]),
    )
    table.add_row(
        "SE Tax",
        format_currency(wo["se_tax"]),
        format_currency(wo["se_tax"]),
        "—",
    )
    table.add_section()
    table.add_row(
        Text("Recommendation", style="bold"),
        "", "",
        Text(
            "Take FEIE" if fe["is_beneficial"] else "Skip FEIE",
            style="bold green" if fe["is_beneficial"] else "bold red",
        ),
    )

    console.print(table)


def display_document_scan(scan_results: dict):
    """Display document scan results as a Rich tree."""
    tree = Tree(f"[bold]{scan_results['folder']}[/bold]")

    classified = scan_results["summary"]["classified"]
    for doc_type, count in sorted(classified.items()):
        tree.add(f"[green]{doc_type}[/green]: {count} file(s)")

    unclassified = scan_results["summary"]["unclassified"]
    if unclassified:
        unc_branch = tree.add("[yellow]Unclassified[/yellow]")
        for name in unclassified:
            unc_branch.add(f"[dim]{name}[/dim]")

    summary = scan_results["summary"]
    tree.add(f"[dim]Total: {summary['total_files']} files, {summary['pdf_files']} PDFs[/dim]")

    console.print(tree)


def display_quarterly_plan(plan: dict):
    """Display quarterly payment plan."""
    table = Table(title="2026 Estimated Tax Payments", header_style="bold cyan")
    table.add_column("Quarter", style="white")
    table.add_column("Due Date", style="white")
    table.add_column("Amount", justify="right", style="bold green")

    quarterly = plan["recommended_quarterly"]
    quarters = [
        ("Q1", "April 15, 2026"),
        ("Q2", "June 15, 2026"),
        ("Q3", "September 15, 2026"),
        ("Q4", "January 15, 2027"),
    ]
    for q, due in quarters:
        table.add_row(q, due, format_currency(quarterly))

    table.add_section()
    table.add_row(
        Text("Annual Total", style="bold"), "",
        Text(format_currency(plan["recommended_annual"]), style="bold"),
    )

    console.print(table)
    console.print(f"[dim]Method: {plan['method']}[/dim]")


def display_line_items(items: list, title: str = "Line Items"):
    """Display a list of LineItem objects as a table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Form", style="dim", width=14)
    table.add_column("Line", width=8)
    table.add_column("Description", style="white")
    table.add_column("Amount", justify="right", style="bold")

    for item in items:
        table.add_row(
            item.form,
            str(item.line),
            item.description,
            format_currency(item.amount),
        )

    console.print(table)


def display_progress(description: str):
    """Return a Rich progress context manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def display_result_panel(result):
    """Display final result — refund or amount owed."""
    if result.overpayment > 0:
        panel = Panel(
            f"[bold green]REFUND: {format_currency(result.overpayment)}[/bold green]",
            title="Result",
            border_style="green",
        )
    else:
        panel = Panel(
            f"[bold red]AMOUNT OWED: {format_currency(result.amount_owed)}[/bold red]",
            title="Result",
            border_style="red",
        )
    console.print(panel)


def display_optimization_recommendations(recommendations: list):
    """Display optimization suggestions."""
    if not recommendations:
        console.print("[dim]No optimization suggestions found.[/dim]")
        return

    table = Table(title="Optimization Opportunities", header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Suggestion", style="white")
    table.add_column("Est. Savings", justify="right", style="bold green")

    for i, rec in enumerate(recommendations, 1):
        table.add_row(
            str(i),
            f"[bold]{rec['title']}[/bold]\n{rec['description']}",
            format_currency(rec["estimated_savings"]),
        )

    console.print(table)
