"""``jobassist ingest-url`` — single URL ingestion."""

from __future__ import annotations

import typer

from app.cli._common import console, run_async, setup
from app.pipelines.ingest_pipeline import ingest_url as ingest_pipeline


def ingest_url(
    url: str = typer.Argument(..., help="Public job posting URL (Greenhouse/Lever/LinkedIn/other)"),
) -> None:
    """Fetch, normalize, and persist a single job posting."""
    setup()
    try:
        job = run_async(ingest_pipeline(url))
    except Exception as exc:
        console.print(f"[red]ingest failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(
        f"[green]OK[/green] job [cyan]#{job.id}[/cyan] — {job.title} @ {job.company} "
        f"([dim]{job.ats_source.value}[/dim])"
    )
