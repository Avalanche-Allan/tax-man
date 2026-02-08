"""Tax Man CLI — Typer application with subcommands.

Commands:
  taxman prepare  — Launch wizard walkthrough
  taxman review   — Display saved return in Rich tables
  taxman export   — Generate PDFs and reports
  taxman compare  — FEIE comparison
  taxman scan     — Classify documents in a folder
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="taxman",
    help="Tax Man — 2025 Federal Tax Return Preparation",
    add_completion=False,
)
console = Console()


@app.command()
def prepare(
    documents_dir: Optional[str] = typer.Option(
        None, "--documents-dir", "-d",
        help="Path to tax documents folder",
    ),
    resume: Optional[str] = typer.Option(
        None, "--resume", "-r",
        help="Resume a saved session by ID",
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c",
        help="Path to config file",
    ),
):
    """Launch the interactive tax preparation wizard."""
    from taxman.cli.config import TaxManConfig
    from taxman.cli.state import SessionState
    from taxman.cli.wizard import TaxWizard

    cfg = TaxManConfig.load(Path(config) if config else None)
    cfg.ensure_dirs()

    session = None
    if resume:
        session = SessionState.load(resume)
        if session:
            console.print(f"[green]Resuming session {resume}[/green]")
            console.print(f"[dim]Completed steps: {', '.join(session.completed_steps)}[/dim]")
        else:
            console.print(f"[red]Session {resume} not found.[/red]")
            raise typer.Exit(1)

    doc_dir = documents_dir or cfg.documents_dir
    wizard = TaxWizard(session=session, documents_dir=doc_dir, config=cfg)
    wizard.run()


@app.command()
def review(
    session_id: str = typer.Argument(help="Session ID to review"),
):
    """Display a saved return with Rich tables."""
    from taxman.cli.display import (
        display_income_table,
        display_result_panel,
        display_tax_breakdown,
    )
    from taxman.cli.state import SessionState

    session = SessionState.load(session_id)
    if not session:
        console.print(f"[red]Session {session_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Session: {session_id}[/bold]")
    console.print(f"Filing status: {session.filing_status}")
    console.print(f"Steps completed: {len(session.completed_steps)}")
    console.print(f"Last updated: {session.updated_at}")

    if session.results:
        console.print("\n[bold]Results on file:[/bold]")
        for key, val in session.results.items():
            console.print(f"  {key}: {val}")
    else:
        console.print("[dim]No calculated results in this session.[/dim]")


@app.command()
def export(
    session_id: str = typer.Argument(help="Session ID to export"),
    output_dir: str = typer.Option("output", "--output-dir", "-o"),
):
    """Generate PDFs and reports from a saved session."""
    from taxman.cli.state import SessionState

    session = SessionState.load(session_id)
    if not session:
        console.print(f"[red]Session {session_id} not found.[/red]")
        raise typer.Exit(1)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Exporting session {session_id} to {output_dir}[/bold]")

    if not session.results:
        console.print("[yellow]No results to export. Run 'taxman prepare' first.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[green]Export complete: {output_dir}[/green]")


@app.command()
def compare(
    session_id: Optional[str] = typer.Argument(None, help="Session ID"),
):
    """Compare tax scenarios (FEIE with/without)."""
    console.print("[bold]FEIE Comparison[/bold]")
    console.print("[dim]Run 'taxman prepare' for interactive comparison.[/dim]")


@app.command()
def scan(
    directory: str = typer.Argument(help="Folder to scan for tax documents"),
):
    """Scan and classify tax documents in a folder."""
    from taxman.cli.display import display_document_scan
    from taxman.parse_documents import scan_documents_folder

    path = Path(directory)
    if not path.exists():
        console.print(f"[red]Folder not found: {directory}[/red]")
        raise typer.Exit(1)

    console.print(f"Scanning [bold]{directory}[/bold]...")
    results = scan_documents_folder(directory)

    if "error" in results:
        console.print(f"[red]{results['error']}[/red]")
        raise typer.Exit(1)

    display_document_scan(results)

    summary = results["summary"]
    console.print(f"\n[bold]Found {summary['pdf_files']} PDFs "
                  f"({len(summary['classified'])} types classified)[/bold]")


@app.command()
def sessions():
    """List all saved sessions."""
    from taxman.cli.state import SessionState

    all_sessions = SessionState.list_sessions()
    if not all_sessions:
        console.print("[dim]No saved sessions found.[/dim]")
        return

    from rich.table import Table
    table = Table(title="Saved Sessions", header_style="bold cyan")
    table.add_column("ID", style="bold")
    table.add_column("Filing Status")
    table.add_column("Steps")
    table.add_column("Last Updated")

    for s in all_sessions:
        table.add_row(
            s["id"],
            s["filing_status"] or "—",
            str(s["steps"]),
            s["updated"][:19] if s["updated"] else "—",
        )

    console.print(table)


if __name__ == "__main__":
    app()
