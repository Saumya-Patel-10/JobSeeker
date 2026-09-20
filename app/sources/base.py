"""Base contract for job source discovery adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.config.schema import JobSource

SourceHealthStatus = Literal[
    "healthy",
    "degraded",
    "unauthenticated",
    "rate_limited",
    "not_implemented",
    "error",
]


class SourceHealth(BaseModel):
    status: SourceHealthStatus = "healthy"
    message: str = ""
    authenticated: bool | None = None
    rate_limit_until: str | None = None


class DiscoveryContext(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    limit: int = 25
    remote_preference: str = "no_preference"


class JobSourceAdapter(ABC):
    """Discover job posting URLs from a configured source."""

    name: str = "base"

    def __init__(self, source: JobSource) -> None:
        self.source = source

    @abstractmethod
    async def health(self) -> SourceHealth:
        """Probe reachability, auth, and rate-limit state."""

    @abstractmethod
    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        """Return job posting URLs to ingest."""
