"""Blacklist service: company / keyword / domain filtering."""

from __future__ import annotations

from urllib.parse import urlparse

from app.config.schema import BlacklistConfig
from app.models.job import Job


class Blacklist:
    """Match jobs against the user-configured blacklist."""

    def __init__(self, config: BlacklistConfig) -> None:
        self.companies = {c.strip().lower() for c in config.companies if c.strip()}
        self.keywords = [k.strip().lower() for k in config.keywords if k.strip()]
        self.domains = [d.strip().lower() for d in config.domains if d.strip()]

    def is_blocked(self, job: Job) -> tuple[bool, str | None]:
        """Return ``(blocked, reason)``."""
        if job.company.strip().lower() in self.companies:
            return True, f"company '{job.company}' is blacklisted"

        haystack = f"{job.title}\n{job.description_text}".lower()
        for kw in self.keywords:
            if kw and kw in haystack:
                return True, f"keyword '{kw}' matched"

        try:
            host = urlparse(job.source_url).netloc.lower()
        except (ValueError, AttributeError):
            host = ""
        for domain in self.domains:
            if domain and domain in host:
                return True, f"domain '{domain}' matched ({host})"

        return False, None
