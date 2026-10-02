"""Ashby ATS job discovery — public GraphQL API, no auth required.

Ashby exposes a public non-user GraphQL endpoint at:
  POST https://jobs.ashbyhq.com/api/non-user-graphql

Used by: Linear, Vanta, Arc, Descript, Brex, Luma, Hex, Warp, and many others.
"""

from __future__ import annotations

import httpx

from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.utils.logging import get_logger

log = get_logger(__name__)

ASHBY_GRAPHQL_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"

# GraphQL query to fetch all job postings for a company
_JOB_POSTING_QUERY = """
query ApiJobPostingIndex($organizationHostedJobsPageName: String!) {
  jobPostings(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
    where: { isListed: { eq: true }, status: { eq: Published } }
    orderBy: { direction: desc, field: publishedDate }
  ) {
    id
    title
    locationName
    employmentType
    externalLink
    publishedDate
    departmentName
    teamName
    isRemote
  }
}
"""


class AshbySourceAdapter(JobSourceAdapter):
    """Discover jobs from a single company using Ashby ATS via their public GraphQL API."""

    name = "ashby"

    async def health(self) -> SourceHealth:
        org = self._org_name()
        if not org:
            return SourceHealth(status="error", message="No org_name configured")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    ASHBY_GRAPHQL_URL,
                    json={
                        "operationName": "ApiJobPostingIndex",
                        "query": _JOB_POSTING_QUERY,
                        "variables": {"organizationHostedJobsPageName": org},
                    },
                )
            if resp.status_code == 200:
                return SourceHealth(
                    status="healthy",
                    message=f"Ashby API reachable for '{org}'",
                    authenticated=True,
                )
            return SourceHealth(
                status="error",
                message=f"Ashby API returned HTTP {resp.status_code} for '{org}'",
            )
        except Exception as exc:
            return SourceHealth(status="error", message=str(exc))

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        org = self._org_name()
        if not org:
            log.info("ashby.discover_skipped", reason="no_org_name")
            return []

        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    ASHBY_GRAPHQL_URL,
                    json={
                        "operationName": "ApiJobPostingIndex",
                        "query": _JOB_POSTING_QUERY,
                        "variables": {"organizationHostedJobsPageName": org},
                    },
                )
            if resp.status_code != 200:
                log.warning("ashby.api_failed", org=org, status=resp.status_code)
                return []

            data = resp.json()
            postings = (data.get("data") or {}).get("jobPostings") or []

            for posting in postings:
                if len(urls) >= ctx.limit:
                    break
                title = (posting.get("title") or "").lower()
                if keywords and not any(k in title for k in keywords):
                    continue
                link = posting.get("externalLink") or f"https://jobs.ashbyhq.com/{org}/{posting.get('id')}"
                if link and link not in urls:
                    urls.append(link)

        except Exception as exc:
            log.warning("ashby.discover_failed", org=org, error=str(exc))

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("ashby.discover_complete", org=org, urls=len(urls))
        return urls[: ctx.limit]

    def _org_name(self) -> str:
        return str(self.source.config.get("org_name", ""))

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []


class AshbyMultiSourceAdapter(JobSourceAdapter):
    """Discover jobs from MULTIPLE Ashby companies in a single source entry.

    Configure with a list of org_names in config:
      config:
        orgs:
          - linear
          - vanta
          - descript
        keywords:
          - engineer
          - software
    """

    name = "ashby_multi"

    async def health(self) -> SourceHealth:
        orgs = self._orgs()
        if not orgs:
            return SourceHealth(status="error", message="No orgs configured")
        return SourceHealth(
            status="healthy",
            message=f"Ashby multi-org ready: {len(orgs)} companies",
            authenticated=True,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        orgs = self._orgs()
        if not orgs:
            log.info("ashby_multi.discover_skipped", reason="no_orgs")
            return []

        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []
        per_org_limit = max(5, ctx.limit // max(len(orgs), 1))

        async with httpx.AsyncClient(timeout=30.0) as client:
            for org in orgs:
                if len(urls) >= ctx.limit:
                    break
                try:
                    resp = await client.post(
                        ASHBY_GRAPHQL_URL,
                        json={
                            "operationName": "ApiJobPostingIndex",
                            "query": _JOB_POSTING_QUERY,
                            "variables": {"organizationHostedJobsPageName": org},
                        },
                    )
                    if resp.status_code != 200:
                        log.warning("ashby_multi.org_failed", org=org, status=resp.status_code)
                        continue

                    data = resp.json()
                    postings = (data.get("data") or {}).get("jobPostings") or []
                    org_count = 0
                    for posting in postings:
                        if org_count >= per_org_limit or len(urls) >= ctx.limit:
                            break
                        title = (posting.get("title") or "").lower()
                        if keywords and not any(k in title for k in keywords):
                            continue
                        link = posting.get("externalLink") or f"https://jobs.ashbyhq.com/{org}/{posting.get('id')}"
                        if link and link not in urls:
                            urls.append(link)
                            org_count += 1
                except Exception as exc:
                    log.warning("ashby_multi.org_error", org=org, error=str(exc))

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("ashby_multi.discover_complete", orgs=len(orgs), urls=len(urls))
        return urls[: ctx.limit]

    def _orgs(self) -> list[str]:
        raw = self.source.config.get("orgs", [])
        return [str(o) for o in raw] if isinstance(raw, list) else []

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []
