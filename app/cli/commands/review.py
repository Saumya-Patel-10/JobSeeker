"""``jobassist review`` — approval checkpoints (not direct status bypass)."""

from __future__ import annotations

import typer
from rich.table import Table

from app.cli._common import console, run_async, setup
from app.database.dao import approvals as approvals_dao
from app.database.session import session_scope
from app.services.approval_service import get_approval_service
from app.services.submission import SubmissionNotAllowedError, submit_application_if_approved


def review(
    approve: int | None = typer.Option(
        None, "--approve", help="Approve checkpoint id (not application id)"
    ),
    reject: int | None = typer.Option(None, "--reject", help="Reject checkpoint id"),
    submit: bool = typer.Option(
        False, "--submit", help="After approve, submit via submit_application_if_approved"
    ),
) -> None:
    """List or resolve approval checkpoints."""
    setup()
    if approve is not None:
        run_async(_approve(approve, submit=submit))
        return
    if reject is not None:
        run_async(_reject(reject))
        return
    run_async(_list_pending())


async def _list_pending() -> None:
    async with session_scope() as db:
        rows = await approvals_dao.list_pending(db, limit=50)
    if not rows:
        console.print("[dim]No pending approval checkpoints.[/dim]")
        return
    table = Table(title="Pending approval checkpoints")
    table.add_column("Checkpoint")
    table.add_column("Application")
    table.add_column("Job")
    table.add_column("Type")
    for row in rows:
        table.add_row(
            str(row.id),
            str(row.application_id),
            str(row.job_id),
            row.checkpoint_type,
        )
    console.print(table)


async def _approve(checkpoint_id: int, *, submit: bool) -> None:
    ok = await get_approval_service().approve(checkpoint_id)
    if not ok:
        console.print(f"[red]Checkpoint {checkpoint_id} not found[/red]")
        raise typer.Exit(1)
    console.print(f"[green]OK[/green] checkpoint #{checkpoint_id} approved")
    if submit:
        async with session_scope() as db:
            row = await approvals_dao.get_by_id(db, checkpoint_id)
        if row:
            try:
                report = await submit_application_if_approved(
                    row.application_id, checkpoint_id=checkpoint_id
                )
                if report.submitted:
                    console.print("[green]Application submitted via browser[/green]")
                else:
                    console.print(f"[yellow]Submit incomplete:[/yellow] {report.error}")
            except SubmissionNotAllowedError as exc:
                console.print(f"[yellow]{exc}[/yellow]")


async def _reject(checkpoint_id: int) -> None:
    ok = await get_approval_service().reject(checkpoint_id)
    if not ok:
        console.print(f"[red]Checkpoint {checkpoint_id} not found[/red]")
        raise typer.Exit(1)
    console.print(f"[yellow]OK[/yellow] checkpoint #{checkpoint_id} rejected")
