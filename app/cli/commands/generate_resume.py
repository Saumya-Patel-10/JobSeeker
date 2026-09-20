"""``jobassist generate-resume`` — tailor + render the master resume."""

from __future__ import annotations

import typer

from app.cli._common import console, run_async, setup
from app.pipelines.tailor_pipeline import tailor_existing_job


def generate_resume(
    job_id: int = typer.Argument(..., help="ID of an ingested job"),
    no_cover_letter: bool = typer.Option(
        False, "--no-cover-letter", help="Skip cover letter generation"
    ),
) -> None:
    """Generate a tailored DOCX + PDF resume for a job."""
    setup()
    try:
        result = run_async(tailor_existing_job(job_id, write_cover_letter=not no_cover_letter))
    except Exception as exc:
        console.print(f"[red]generate-resume failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(
        f"[green]OK[/green] resume #{result.resume_version_id} for job #{job_id}\n"
        f"  DOCX: [cyan]{result.docx_path}[/cyan]\n"
        f"  PDF:  [cyan]{result.pdf_path}[/cyan]"
    )
    if result.cover_letter:
        console.print("  Cover letter saved alongside resume.")
