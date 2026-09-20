"""``jobassist runtime-check`` — consolidated runtime readiness report."""

from __future__ import annotations

import asyncio

from rich.table import Table

from app.cli._common import console, setup
from app.runtime.validator import run_runtime_validation


def runtime_check() -> None:
    setup()
    report = asyncio.run(run_runtime_validation())
    table = Table(title="Runtime Readiness")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    table.add_row(
        "Python",
        "[green]OK[/green]" if report.python_ok else "[red]FAIL[/red]",
        report.python_version,
    )
    table.add_row(
        "Config",
        "[green]OK[/green]" if report.config_ok else "[red]FAIL[/red]",
        report.config_error or "validated",
    )
    table.add_row(
        "Database",
        "[green]OK[/green]" if report.db_ok else "[red]FAIL[/red]",
        report.db_path,
    )
    table.add_row(
        "LLM",
        "[green]OK[/green]" if report.llm_reachable else "[yellow]WARN[/yellow]",
        f"{report.llm_provider or 'n/a'} @ {report.llm_base_url or 'n/a'}",
    )
    console.print(table)
