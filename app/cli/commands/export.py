"""``jobassist export`` — dump applications to JSON or CSV for record keeping."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import typer

from app.cli._common import console, run_async, setup
from app.config.paths import APPLICATIONS_DIR
from app.database.dao import applications as apps_dao
from app.database.session import session_scope


def export(
    format: str = typer.Option("json", "--format", "-f", help="json | csv"),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file. Default: data/applications/applications-<timestamp>.<ext>",
    ),
) -> None:
    """Export every application row to disk."""
    setup()
    fmt = format.lower()
    if fmt not in ("json", "csv"):
        console.print(f"[red]Unsupported format:[/red] {format}")
        raise typer.Exit(1)
    if output is None:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        output = APPLICATIONS_DIR / f"applications-{ts}.{fmt}"
    run_async(_run(fmt, output))
    console.print(f"[green]OK[/green] wrote [cyan]{output}[/cyan]")


async def _run(fmt: str, path: Path) -> None:
    async with session_scope() as db:
        rows = await apps_dao.list_applications(db, limit=10_000)

    records = [
        {
            "id": row.id,
            "job_id": row.job_id,
            "job_title": row.job.title if row.job else None,
            "status": row.status,
            "mode": row.mode,
            "source": row.source,
            "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
            "notes": row.notes,
            "recruiter_name": row.recruiter_name,
            "recruiter_email": row.recruiter_email,
        }
        for row in rows
    ]

    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        return

    columns = (
        list(records[0].keys())
        if records
        else [
            "id",
            "job_id",
            "job_title",
            "status",
            "mode",
            "source",
            "submitted_at",
            "created_at",
            "updated_at",
            "notes",
            "recruiter_name",
            "recruiter_email",
        ]
    )
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
