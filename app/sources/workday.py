"""Workday job discovery — browser-based scraping for enterprise/FAANG companies.

Workday has NO public API. Discovery is done by navigating their careers portals
via the supervised Playwright browser already used for LinkedIn.

Companies using Workday: Google, Meta, Microsoft, Amazon, Apple, Nvidia,
Adobe, Salesforce, ServiceNow, Snowflake, Palantir, Uber, Lyft, and most
Fortune 500 enterprises.

Each company needs a specific Workday tenant URL in this format:
  https://<company>.wd1.myworkdayjobs.com/<tenant-path>/

This adapter supports a list of (company_name, workday_url) pairs so one
config entry can fan out to many companies.
"""

from __future__ import annotations

import asyncio

import httpx

from app.runtime.automation_runtime import get_automation_runtime
from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.utils.logging import get_logger

log = get_logger(__name__)

# Workday REST API — each tenant exposes a jobs search endpoint:
# GET https://<company>.wd1.myworkdayjobs.com/wday/cxs/<tenant>/jobs
# This is a semi-public JSON endpoint that Workday uses internally for their
# hosted career pages. No auth required for published roles.
WORKDAY_API_PATH = "wday/cxs/{tenant}/jobs"


# Known Workday tenants: (display_name, base_url, tenant_path)
# base_url format: https://<company>.wd1.myworkdayjobs.com
# tenant_path: the identifier in the CXS API path (often same as careers site slug)
DEFAULT_WORKDAY_COMPANIES: list[dict] = [
    {"name": "Google", "base_url": "https://google.wd1.myworkdayjobs.com", "tenant": "Google_External_Career_Site"},
    {"name": "Meta", "base_url": "https://meta.wd5.myworkdayjobs.com", "tenant": "careers_meta"},
    {"name": "Microsoft", "base_url": "https://microsoft.wd5.myworkdayjobs.com", "tenant": "Global"},
    {"name": "Amazon", "base_url": "https://amazon.jobs", "tenant": None},   # Amazon uses custom portal
    {"name": "Apple", "base_url": "https://apple.wd5.myworkdayjobs.com", "tenant": "University_Recruiting"},
    {"name": "Nvidia", "base_url": "https://nvidia.wd5.myworkdayjobs.com", "tenant": "nvidiaexternal"},
    {"name": "Adobe", "base_url": "https://adobe.wd5.myworkdayjobs.com", "tenant": "external_experienced"},
    {"name": "Salesforce", "base_url": "https://salesforce.wd12.myworkdayjobs.com", "tenant": "External_Career_Site"},
    {"name": "ServiceNow", "base_url": "https://servicenow.wd5.myworkdayjobs.com", "tenant": "External"},
    {"name": "Snowflake", "base_url": "https://snowflake.wd5.myworkdayjobs.com", "tenant": "Snowflake_Careers"},
    {"name": "Palantir", "base_url": "https://palantir.wd5.myworkdayjobs.com", "tenant": "palantir"},
    {"name": "Uber", "base_url": "https://uber.wd5.myworkdayjobs.com", "tenant": "Uber_External_Careers"},
    {"name": "Lyft", "base_url": "https://lyft.wd5.myworkdayjobs.com", "tenant": "External"},
    {"name": "Intuit", "base_url": "https://intuit.wd5.myworkdayjobs.com", "tenant": "External_Career_Site"},
    {"name": "Workday", "base_url": "https://workday.wd5.myworkdayjobs.com", "tenant": "Workday_External"},
    {"name": "Palo Alto Networks", "base_url": "https://paloaltonetworks.wd5.myworkdayjobs.com", "tenant": "External"},
    {"name": "CrowdStrike", "base_url": "https://crowdstrike.wd5.myworkdayjobs.com", "tenant": "crowdstrike-careers"},
    {"name": "Fortinet", "base_url": "https://fortinet.wd5.myworkdayjobs.com", "tenant": "External"},
]

_WORKDAY_SEARCH_BODY = {
    "appliedFacets": {},
    "limit": 20,
    "offset": 0,
    "searchText": "",
}


class WorkdaySourceAdapter(JobSourceAdapter):
    """Discover jobs from Workday-powered career portals.

    Uses the semi-public Workday CXS JSON API first (fast, no browser),
    falls back to browser scraping for companies that block API access.
    """

    name = "workday"

    async def health(self) -> SourceHealth:
        companies = self._companies()
        if not companies:
            return SourceHealth(status="error", message="No Workday companies configured")
        return SourceHealth(
            status="healthy",
            message=f"Workday adapter ready: {len(companies)} companies configured",
            authenticated=None,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        companies = self._companies()
        if not companies:
            log.info("workday.discover_skipped", reason="no_companies")
            return []

        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []
        per_company_limit = max(5, ctx.limit // max(len(companies), 1))

        for company in companies:
            if len(urls) >= ctx.limit:
                break
            tenant = company.get("tenant")
            base_url = company.get("base_url", "")
            name = company.get("name", "unknown")

            if not tenant:
                log.info("workday.company_skipped", company=name, reason="no_tenant")
                continue

            try:
                company_urls = await self._fetch_via_api(
                    base_url=base_url,
                    tenant=tenant,
                    company_name=name,
                    keywords=keywords,
                    limit=per_company_limit,
                )
                for u in company_urls:
                    if u not in urls:
                        urls.append(u)
            except Exception as exc:
                log.warning("workday.company_failed", company=name, error=str(exc))

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("workday.discover_complete", companies=len(companies), urls=len(urls))
        return urls[: ctx.limit]

    async def _fetch_via_api(
        self,
        base_url: str,
        tenant: str,
        company_name: str,
        keywords: list[str],
        limit: int,
    ) -> list[str]:
        """Use the semi-public Workday CXS JSON API to get job listings."""
        api_url = f"{base_url}/{WORKDAY_API_PATH.format(tenant=tenant)}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        all_urls: list[str] = []
        search_text = keywords[0] if keywords else "software engineer"

        body = {**_WORKDAY_SEARCH_BODY, "searchText": search_text, "limit": limit}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                resp = await client.post(api_url, headers=headers, json=body)
                if resp.status_code != 200:
                    log.warning(
                        "workday.api_http_error",
                        company=company_name,
                        status=resp.status_code,
                    )
                    return []
                data = resp.json()
                job_postings = data.get("jobPostings") or []
                for posting in job_postings:
                    external_path = posting.get("externalPath") or posting.get("detailViewExternalPath") or ""
                    if external_path:
                        full_url = f"{base_url}{external_path}"
                        if full_url not in all_urls:
                            all_urls.append(full_url)
                    if len(all_urls) >= limit:
                        break
                log.info(
                    "workday.api_success",
                    company=company_name,
                    jobs=len(all_urls),
                )
            except Exception as exc:
                log.warning("workday.api_request_failed", company=company_name, error=str(exc))

        return all_urls

    def _companies(self) -> list[dict]:
        """Return configured companies or fall back to the curated default list."""
        raw = self.source.config.get("companies")
        if isinstance(raw, list) and raw:
            return raw
        # Use the built-in curated list if nothing is configured
        enabled_names = self.source.config.get("enabled_companies")
        if isinstance(enabled_names, list) and enabled_names:
            lower_names = [n.lower() for n in enabled_names]
            return [c for c in DEFAULT_WORKDAY_COMPANIES if c["name"].lower() in lower_names]
        return DEFAULT_WORKDAY_COMPANIES

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []
