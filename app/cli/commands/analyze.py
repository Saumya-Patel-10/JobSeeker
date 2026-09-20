"""``jobassist analyze`` — score a previously ingested job."""

from __future__ import annotations

import typer
from rich.table import Table

from app.cli._common import console, run_async, setup
from app.pipelines.score_pipeline import score_existing_job


def analyze(
    job_id: int = typer.Argument(..., help="ID of an ingested job"),
) -> None:
    """Compute and persist a fit score using the local LLM."""
    setup()
    try:
        score = run_async(score_existing_job(job_id))
    except Exception as exc:
        console.print(f"[red]analyze failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    table = Table(title=f"Score for job #{job_id}", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("fit_score", f"{score.fit_score:.2f}")
    table.add_row("skill_overlap", f"{score.skill_overlap:.2f}")
    table.add_row("seniority_alignment", f"{score.seniority_alignment:.2f}")
    table.add_row("salary_fit", f"{score.salary_fit:.2f}")
    table.add_row("location_compatibility", f"{score.location_compatibility:.2f}")
    table.add_row("confidence", f"{score.confidence:.2f}")
    table.add_row("matched_skills", ", ".join(score.matched_skills[:12]))
    table.add_row("missing_skills", ", ".join(score.missing_skills[:12]))
    table.add_row("rationale", score.rationale)
    console.print(table)
