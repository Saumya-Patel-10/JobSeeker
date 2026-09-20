"""``jobassist search`` — unified discovery via SourceOrchestrator."""

from __future__ import annotations

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.cli._common import console, run_async, setup
from app.config.loader import load_config
from app.services.discovery_config import JobDiscoveryConfig
from app.services.job_application_orchestrator import get_job_application_orchestrator


def search(
    limit: int = typer.Option(25, "--limit", "-n", help="Max postings per source"),
) -> None:
    """Discover and ingest from all enabled sources (unified orchestrator)."""
    setup()
    run_async(_search_async(limit))


async def _search_async(limit: int) -> None:
    config = load_config()
    sources = [s for s in config.job_sources.sources if s.enabled]
    if not sources:
        console.print("[yellow]No enabled sources in config/job_sources.yaml[/yellow]")
        return

    discovery = JobDiscoveryConfig(
        keywords=config.preferences.role_keywords,
        companies=config.preferences.target_companies,
        locations=config.preferences.locations,
        remote_preference=config.preferences.remote_preference,
        limit_per_source=limit,
        run_search=True,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        TextColumn("{task.fields[status]}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Unified discovery", status="")
        orch = get_job_application_orchestrator()
        result = await orch.discover(discovery, ingest=True)
        progress.update(
            task,
            status=f"{result.get('urls_found', 0)} urls, {result.get('ingested', 0)} ingested",
        )

    console.print(
        f"[green]OK[/green] ingested [bold]{result.get('ingested', 0)}[/bold] "
        f"([red]{result.get('failed', 0)}[/red] failed, "
        f"[bold]{result.get('urls_found', 0)}[/bold] urls seen)"
    )
