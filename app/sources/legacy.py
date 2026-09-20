"""Adapters delegating to existing job_sources.py HTTP resolvers."""

from __future__ import annotations

from app.services.job_sources import resolve_urls_for_source
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth


class LegacyHttpSourceAdapter(JobSourceAdapter):
    """Greenhouse, Lever, url_list sources."""

    async def health(self) -> SourceHealth:
        urls = self.source.config.get("urls", [])
        if self.source.type == "url_list" and isinstance(urls, list) and len(urls) == 0:
            return SourceHealth(status="degraded", message="No URLs configured")
        return SourceHealth(status="healthy", message="HTTP/API source ready")

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        return await resolve_urls_for_source(self.source, ctx.limit)
