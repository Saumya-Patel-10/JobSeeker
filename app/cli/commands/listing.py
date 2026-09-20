"""``jobassist list-applications`` — show all applications."""

from __future__ import annotations

import typer
from rich.table import Table

from app.cli._common import console, run_async, setup
from app.database.dao import applications as apps_dao
from app.database.session import session_scope
from app.models.enums import ApplicationStatus


def list_applications(
    status: str | None = typer.Option(None, "--status", help="Filter by status name"),
    limit: int = typer.Option(50, "--limit", "-n"),
) -> None:
    """List recent applications, newest first."""
    setup()
    status_enum: ApplicationStatus | None = None
    if status:
        try:
            status_enum = ApplicationStatus(status)
        except ValueError as exc:
            console.print(f"[red]Invalid status:[/red] {status}")
            raise typer.Exit(1) from exc
    run_async(_run(status_enum, limit))


async def _run(status: ApplicationStatus | None, limit: int) -> None:
    async with session_scope() as db:
        rows = await apps_dao.list_applications(db, status=status, limit=limit)
    if not rows:
        console.print("[dim]No applications recorded yet.[/dim]")
        return
    table = Table(title="Applications")
    table.add_column("ID")
    table.add_column("Job")
    table.add_column("Status")
    table.add_column("Mode")
    table.add_column("Submitted")
    for row in rows:
        table.add_row(
            str(row.id),
            row.job.title if row.job else f"#{row.job_id}",
            row.status,
            row.mode,
            row.submitted_at.isoformat(timespec="minutes") if row.submitted_at else "-",
        )
    console.print(table)
