"""Scaffolded adapters — health + telemetry only until fully implemented."""

from __future__ import annotations

from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth


class ScaffoldSourceAdapter(JobSourceAdapter):
    display_name: str = "Source"

    async def health(self) -> SourceHealth:
        return SourceHealth(
            status="not_implemented",
            message=f"{self.display_name} discovery is not yet implemented",
            authenticated=None,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        return []
