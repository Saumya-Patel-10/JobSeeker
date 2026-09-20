"""Abstract base class every ATS adapter must implement.

Detection is a classmethod so the registry can route a URL without
constructing every adapter. ``login`` defaults to no-op because most
adapters rely on the persistent browser profile.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.automation.browser import BrowserSession
from app.models.application import (
    ApplicationContext,
    DryRunReport,
    FillReport,
    SubmitReport,
)
from app.models.job import Job


class ATSAdapter(ABC):
    """Stateless adapter except for an optional :class:`BrowserSession`."""

    name: ClassVar[str]

    def __init__(self, session: BrowserSession | None = None) -> None:
        self.session = session

    @classmethod
    @abstractmethod
    def detect(cls, url: str, html: str | None = None) -> bool:
        """Return True if this adapter handles ``url``."""

    @abstractmethod
    async def scrape_job(self, url: str) -> Job:
        """Fetch and normalize a job posting from ``url``."""

    async def login(self, session: BrowserSession) -> None:
        """Optional. Default: rely on the persistent browser profile."""
        return None

    @abstractmethod
    async def fill_application(self, ctx: ApplicationContext) -> FillReport:
        """Fill the application form for ``ctx.job`` using ``ctx.profile``."""

    @abstractmethod
    async def submit(self, ctx: ApplicationContext) -> SubmitReport:
        """Submit a previously filled application. Honors ``ctx.mode``."""

    async def dry_run(self, ctx: ApplicationContext) -> DryRunReport:
        """Inspect the page and report what would happen, without filling."""
        return DryRunReport(
            job_id=ctx.job.id or 0,
            adapter=self.name,
            notes=["Default dry-run: adapter did not implement DOM inspection."],
        )
