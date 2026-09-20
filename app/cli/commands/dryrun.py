"""``jobassist dry-run`` — inspect an application page without filling."""

from __future__ import annotations

import typer

from app.cli._common import console, run_async, setup
from app.models.enums import ApplicationMode
from app.pipelines.apply_pipeline import apply_to_job


def dry_run(
    job_id: int = typer.Argument(..., help="ID of an ingested job"),
) -> None:
    """Open the application page in the browser and inspect form fields."""
    setup()
    try:
        result = run_async(apply_to_job(job_id, mode=ApplicationMode.dry_run))
    except Exception as exc:
        console.print(f"[red]dry-run failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    if result.dry_run is None:
        console.print("[yellow]No dry-run report returned.[/yellow]")
        return
    console.print(
        f"[green]OK[/green] dry-run for job #{job_id} via adapter [bold]{result.dry_run.adapter}[/bold]"
    )
    console.print(f"  fields detected: {len(result.dry_run.fields_detected)}")
    console.print(f"  answers prepared: {len(result.dry_run.answers_prepared)}")
    for note in result.dry_run.notes[:8]:
        console.print(f"  • {note}")
    for ss in result.dry_run.screenshots:
        console.print(f"  screenshot: [cyan]{ss}[/cyan]")
