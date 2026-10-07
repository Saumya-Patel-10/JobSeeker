"""Coordinates source adapters, ingest, and discovery telemetry."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.config.loader import load_config
from app.pipelines.ingest_pipeline import ingest_url
from app.runtime.automation_runtime import get_automation_runtime
from app.services.discovery_config import JobDiscoveryConfig
from app.services.event_bus import get_event_bus
from app.services.job_filters import matches_filters
from app.sources.base import DiscoveryContext
from app.sources.registry import get_adapter_for_source
from app.utils.logging import get_logger

log = get_logger(__name__)


class SourceOrchestrator:
    async def poll_source(self, source_name: str, discovery: JobDiscoveryConfig) -> dict[str, Any]:
        config = load_config()
        source = next((s for s in config.job_sources.sources if s.name == source_name), None)
        if source is None:
            return {"source": source_name, "error": "not_found", "urls": 0, "ingested": 0}
        if not source.enabled:
            return {"source": source_name, "skipped": True, "urls": 0, "ingested": 0}

        adapter = get_adapter_for_source(source)
        ctx = DiscoveryContext(
            keywords=discovery.keywords or config.preferences.role_keywords,
            companies=discovery.companies or config.preferences.target_companies,
            locations=discovery.locations or config.preferences.locations,
            limit=discovery.limit_per_source,
            remote_preference=discovery.remote_preference,
        )

        health = await adapter.health()
        status_row = {
            "name": source.name,
            "enabled": source.enabled,
            "last_poll_at": datetime.now(UTC).isoformat(),
            "jobs_discovered": 0,
            "ingestion_failures": 0,
            "auth_status": "authenticated" if health.authenticated else "unknown",
            "rate_limit_until": health.rate_limit_until,
            "health_status": health.status,
            "last_error": health.message if health.status == "error" else None,
        }

        if health.status == "not_implemented":
            return {
                "source": source_name,
                "urls_found": 0,
                "ingested": 0,
                "failed": 0,
                "sources": {source_name: status_row},
            }

        runtime = get_automation_runtime()
        if not await runtime.await_ready():
            return {"source": source_name, "stopped": True, "urls": 0, "ingested": 0}

        try:
            urls = await adapter.discover(ctx)
        except Exception as exc:
            log.warning("source_orchestrator.source_failed", source=source_name, error=str(exc))
            urls = []
        status_row["jobs_discovered"] = len(urls)
        ingested = 0
        failed = 0

        for url in urls:
            if not await runtime.await_ready():
                break
            try:
                job = await ingest_url(url)
                if matches_filters(job, discovery, config):
                    ingested += 1
                else:
                    log.info("source_orchestrator.filtered", url=url)
            except Exception as exc:
                failed += 1
                status_row["ingestion_failures"] = failed
                log.warning("source_orchestrator.ingest_failed", url=url, error=str(exc))

        status_row["ingestion_failures"] = failed
        status_row["ingested"] = ingested
        get_event_bus().emit(
            "discovery.source_polled",
            {"source": source_name, "urls": len(urls), "ingested": ingested, "failed": failed},
        )
        return {
            "source": source_name,
            "urls_found": len(urls),
            "ingested": ingested,
            "failed": failed,
            "sources": {source_name: status_row},
        }

    async def discover(self, discovery: JobDiscoveryConfig) -> dict[str, list[str]]:
        """Discover job URLs from all enabled sources (no ingest)."""
        return await self.discover_urls(discovery)

    async def discover_urls(self, discovery: JobDiscoveryConfig) -> dict[str, list[str]]:
        """Discover URLs from all enabled sources without ingesting."""
        config = load_config()
        enabled = [s for s in config.job_sources.sources if s.enabled]
        output: dict[str, list[str]] = {}
        for source in enabled:
            adapter = get_adapter_for_source(source)
            ctx = DiscoveryContext(
                keywords=discovery.keywords or config.preferences.role_keywords,
                companies=discovery.companies or config.preferences.target_companies,
                locations=discovery.locations or config.preferences.locations,
                limit=discovery.limit_per_source,
                remote_preference=discovery.remote_preference,
            )
            try:
                health = await adapter.health()
                if health.status == "not_implemented":
                    output[source.name] = []
                    continue
                urls = await adapter.discover(ctx)
                output[source.name] = urls
            except Exception as exc:
                log.warning("source_orchestrator.source_failed", source=source.name, error=str(exc))
                output[source.name] = []
        return output

    async def poll_all(self, discovery: JobDiscoveryConfig) -> dict[str, Any]:
        config = load_config()
        enabled = [s for s in config.job_sources.sources if s.enabled]
        total_urls = 0
        total_ingested = 0
        total_failed = 0
        all_sources: dict[str, Any] = {}

        for source in enabled:
            result = await self.poll_source(source.name, discovery)
            total_urls += result.get("urls_found", 0)
            total_ingested += result.get("ingested", 0)
            total_failed += result.get("failed", 0)
            all_sources.update(result.get("sources", {}))

        return {
            "urls_found": total_urls,
            "ingested": total_ingested,
            "failed": total_failed,
            "sources": all_sources,
        }

    async def health_all(self) -> list[dict[str, Any]]:
        config = load_config()
        rows: list[dict[str, Any]] = []
        for source in config.job_sources.sources:
            adapter = get_adapter_for_source(source)
            health = await adapter.health()
            rows.append(
                {
                    "name": source.name,
                    "type": source.type,
                    "enabled": source.enabled,
                    "health_status": health.status,
                    "message": health.message,
                    "authenticated": health.authenticated,
                    "rate_limit_until": health.rate_limit_until,
                }
            )
        return rows


_orchestrator: SourceOrchestrator | None = None


def get_source_orchestrator() -> SourceOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SourceOrchestrator()
    return _orchestrator
