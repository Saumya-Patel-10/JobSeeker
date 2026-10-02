"""SmartRecruiters job discovery — public REST API, no auth required.

SmartRecruiters exposes a completely open REST API at:
  GET https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings

Used by: Zoom, Visa, Bosch, McDonald's, KPMG, Sephora, Médecins Sans Frontières,
and many large enterprises.
"""

from __future__ import annotations

import httpx

from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.utils.logging import get_logger

log = get_logger(__name__)

SMARTRECRUITERS_API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"

# Curated list of companies using SmartRecruiters
DEFAULT_SR_COMPANIES: list[str] = [
    "zoom",
    "visa",
    "bosch",
    "sephora",
    "kpmg",
    "decathlon",
    "lidl",
    "klarna",
    "delivery-hero",
    "trivago",
    "siemens",
    "continental",
    "hellofresh",
    "n26",
    "celonis",
]


class SmartRecruitersSourceAdapter(JobSourceAdapter):
    """Discover jobs from companies using SmartRecruiters ATS via their public REST API."""

    name = "smartrecruiters"

    async def health(self) -> SourceHealth:
        companies = self._companies()
        if not companies:
            return SourceHealth(status="error", message="No SmartRecruiters companies configured")
        return SourceHealth(
            status="healthy",
            message=f"SmartRecruiters adapter ready: {len(companies)} companies",
            authenticated=True,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        companies = self._companies()
        if not companies:
            log.info("smartrecruiters.discover_skipped", reason="no_companies")
            return []

        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []
        per_company_limit = max(5, ctx.limit // max(len(companies), 1))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for company in companies:
                if len(urls) >= ctx.limit:
                    break
                try:
                    params: dict = {"limit": per_company_limit}
                    if keywords:
                        params["q"] = keywords[0]

                    resp = await client.get(
                        SMARTRECRUITERS_API.format(company=company),
                        params=params,
                    )
                    if resp.status_code == 404:
                        log.info("smartrecruiters.company_not_found", company=company)
                        continue
                    if resp.status_code != 200:
                        log.warning("smartrecruiters.http_error", company=company, status=resp.status_code)
                        continue

                    data = resp.json()
                    for posting in data.get("content") or []:
                        if len(urls) >= ctx.limit:
                            break
                        title = (posting.get("name") or "").lower()
                        if keywords and not any(k in title for k in keywords):
                            continue
                        ref_number = posting.get("refNumber") or posting.get("id") or ""
                        job_url = f"https://careers.smartrecruiters.com/{company}/{ref_number}" if ref_number else None
                        if job_url and job_url not in urls:
                            urls.append(job_url)
                except Exception as exc:
                    log.warning("smartrecruiters.company_failed", company=company, error=str(exc))

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("smartrecruiters.discover_complete", companies=len(companies), urls=len(urls))
        return urls[: ctx.limit]

    def _companies(self) -> list[str]:
        raw = self.source.config.get("companies", [])
        if isinstance(raw, list) and raw:
            return [str(c) for c in raw]
        return DEFAULT_SR_COMPANIES

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []
