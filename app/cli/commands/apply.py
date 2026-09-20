"""``jobassist apply`` — prepare application via unified pipeline (no direct submit)."""

from __future__ import annotations

import typer

from app.cli._common import console, run_async, setup
from app.models.enums import ApplicationMode
from app.pipelines.apply_pipeline import prepare_application
from app.services.submission import SubmissionNotAllowedError, submit_application_if_approved


def apply(
    job_id: int = typer.Argument(..., help="ID of an ingested job"),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Request auto-submit after prepare (requires approved checkpoint + allow_auto_submit).",
    ),
    mode: str = typer.Option(
        "human_review",
        "--mode",
        help="dry_run | human_review | auto. Overridden by --auto if passed.",
    ),
    submit: bool = typer.Option(
        False,
        "--submit",
        help="After prepare, submit only if checkpoint is approved (use review --approve first).",
    ),
) -> None:
    """Prepare an application (fill form + approval checkpoint). Submission is never bypassed."""
    setup()
    if auto:
        resolved = ApplicationMode.auto
    else:
        try:
            resolved = ApplicationMode(mode)
        except ValueError as exc:
            console.print(f"[red]Invalid mode:[/red] {mode}")
            raise typer.Exit(1) from exc
    try:
        result = run_async(
            prepare_application(job_id, mode=resolved, allow_auto=auto)
        )
    except Exception as exc:
        console.print(f"[red]prepare failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(
        f"[green]OK[/green] application #{result.application_id} for job #{job_id} "
        f"({result.mode.value})"
    )
    if result.approval_checkpoint_id:
        console.print(
            f"  [yellow]Awaiting approval[/yellow] checkpoint #{result.approval_checkpoint_id}"
        )
        console.print(
            "  Approve in Control Center or: jobassist review --approve <checkpoint_id>"
        )
    if result.fill:
        console.print(
            f"  filled={result.fill.fields_filled} skipped={result.fill.fields_skipped} "
            f"failed={result.fill.fields_failed}"
        )
        for ss in result.fill.screenshots:
            console.print(f"  screenshot: [cyan]{ss}[/cyan]")
    if result.dry_run:
        console.print(
            f"  dry-run fields detected: {len(result.dry_run.fields_detected)} "
            f"answers prepared: {len(result.dry_run.answers_prepared)}"
        )

    if submit and result.application_id and result.approval_checkpoint_id:
        try:
            report = run_async(
                submit_application_if_approved(
                    result.application_id,
                    checkpoint_id=result.approval_checkpoint_id,
                )
            )
            if report.submitted:
                console.print("  [green]submitted[/green]")
            else:
                console.print(f"  [red]NOT submitted[/red]: {report.error or 'see logs'}")
        except SubmissionNotAllowedError as exc:
            console.print(f"  [yellow]Submit blocked:[/yellow] {exc}")
