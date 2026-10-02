"""Multi-company Greenhouse and Lever adapters.

These adapters fan out a single job_sources.yaml entry to dozens of companies,
providing Jobright-style breadth of coverage with zero extra config per company.

Greenhouse API:  https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
Lever API:       https://api.lever.co/v0/postings/{site}?mode=json
"""

from __future__ import annotations

import asyncio

import httpx

from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.utils.logging import get_logger

log = get_logger(__name__)

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
LEVER_API = "https://api.lever.co/v0/postings/{site}?mode=json"

# ─── Curated Greenhouse company list ────────────────────────────────────────
# These are the board slugs used in the Greenhouse API URL.
# Source: each company's careers page (e.g. https://boards.greenhouse.io/<slug>)
GREENHOUSE_TECH_COMPANIES: list[str] = [
    # AI / ML
    "openai", "anthropic", "mistral", "cohere", "huggingface",
    "perplexity", "characterai", "stability-ai", "inflectionai",
    # Dev Tools / Cloud Infrastructure
    "stripe", "vercel", "supabase", "planetscale", "neon",
    "cloudflare", "fastly", "tailscale", "hashicorp", "pulumi",
    "railway", "render", "fly", "dagster-labs",
    # Product / Collaboration
    "notion", "figma", "loom", "miro", "coda", "craft-docs",
    "airtable", "asana", "linear",
    # Fintech
    "coinbase", "robinhood", "plaid", "mercury", "brex",
    "chime", "gusto", "rippling", "deel", "remote",
    # Data / Analytics
    "databricks", "dbt-labs", "amplitude", "mixpanel", "segment",
    "fivetran", "airbyte", "motherduck", "starburst",
    # Cybersecurity
    "lacework", "orca-security", "abnormal-security", "wiz-io",
    # Infrastructure / Observability
    "datadog", "grafana-labs", "honeycomb-io", "sentry",
    "incident-io",
    # Consumer / Social
    "reddit", "discord", "roblox", "spotify",
    # Enterprise SaaS
    "hubspot", "intercom", "zendesk", "mongodb", "elastic",
    "twilio", "sendgrid", "okta",
    # Defense / Aerospace
    "anduril", "shield-ai", "joby-aviation", "zipline",
]

# ─── Curated Lever company list ────────────────────────────────────────────
# These are the site IDs used in the Lever API URL.
LEVER_TECH_COMPANIES: list[str] = [
    # Fintech
    "ramp", "deel", "brex-2", "mercury-bank", "wise",
    # AI / ML
    "scale-ai", "weights-and-biases", "runway",
    # Dev Tools
    "netlify", "retool", "coda-hq", "descript",
    # Data
    "hex-technologies",
    # Infrastructure
    "chronosphere", "camunda",
    # Consumer
    "duolingo", "calm",
    # Enterprise
    "lattice", "leapsome", "rippling-people-center",
    # Crypto / Web3
    "chainalysis", "consensys",
    # Health Tech
    "headway", "cityblock",
]


class GreenhouseMultiSourceAdapter(JobSourceAdapter):
    """Poll multiple Greenhouse-powered job boards in a single adapter.

    Uses the curated GREENHOUSE_TECH_COMPANIES list by default, or a custom
    list from config:
      config:
        slugs:
          - stripe
          - openai
          - anthropic
        keywords:
          - engineer
          - software
    """

    name = "greenhouse_multi"

    async def health(self) -> SourceHealth:
        slugs = self._slugs()
        return SourceHealth(
            status="healthy",
            message=f"Greenhouse multi ready: {len(slugs)} companies",
            authenticated=True,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        slugs = self._slugs()
        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []
        per_slug_limit = max(3, ctx.limit // max(len(slugs), 1))

        # Use concurrency for speed — Greenhouse API is very fast
        semaphore = asyncio.Semaphore(10)

        async def fetch_slug(slug: str) -> list[str]:
            async with semaphore:
                return await _fetch_greenhouse_slug(slug, keywords, per_slug_limit)

        results = await asyncio.gather(*[fetch_slug(s) for s in slugs], return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                for url in result:
                    if url not in urls:
                        urls.append(url)
                    if len(urls) >= ctx.limit:
                        break
            if len(urls) >= ctx.limit:
                break

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("greenhouse_multi.discover_complete", slugs=len(slugs), urls=len(urls))
        return urls[: ctx.limit]

    def _slugs(self) -> list[str]:
        raw = self.source.config.get("slugs", [])
        if isinstance(raw, list) and raw:
            return [str(s) for s in raw]
        return GREENHOUSE_TECH_COMPANIES

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []


class LeverMultiSourceAdapter(JobSourceAdapter):
    """Poll multiple Lever-powered job boards in a single adapter.

    Uses the curated LEVER_TECH_COMPANIES list by default, or a custom
    list from config:
      config:
        sites:
          - ramp
          - scale-ai
        keywords:
          - engineer
    """

    name = "lever_multi"

    async def health(self) -> SourceHealth:
        sites = self._sites()
        return SourceHealth(
            status="healthy",
            message=f"Lever multi ready: {len(sites)} companies",
            authenticated=True,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        sites = self._sites()
        keywords = [k.lower() for k in (ctx.keywords or self._config_keywords())]
        urls: list[str] = []
        per_site_limit = max(3, ctx.limit // max(len(sites), 1))

        semaphore = asyncio.Semaphore(8)

        async def fetch_site(site: str) -> list[str]:
            async with semaphore:
                return await _fetch_lever_site(site, keywords, per_site_limit)

        results = await asyncio.gather(*[fetch_site(s) for s in sites], return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                for url in result:
                    if url not in urls:
                        urls.append(url)
                    if len(urls) >= ctx.limit:
                        break
            if len(urls) >= ctx.limit:
                break

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        log.info("lever_multi.discover_complete", sites=len(sites), urls=len(urls))
        return urls[: ctx.limit]

    def _sites(self) -> list[str]:
        raw = self.source.config.get("sites", [])
        if isinstance(raw, list) and raw:
            return [str(s) for s in raw]
        return LEVER_TECH_COMPANIES

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        return [str(k) for k in raw] if isinstance(raw, list) else []


# ─── Shared fetch helpers ────────────────────────────────────────────────────

async def _fetch_greenhouse_slug(slug: str, keywords: list[str], limit: int) -> list[str]:
    """Fetch job URLs from a single Greenhouse board."""
    url = GREENHOUSE_API.format(slug=slug)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        jobs = data.get("jobs") or []
        result: list[str] = []
        for job in jobs:
            if len(result) >= limit:
                break
            title = (job.get("title") or "").lower()
            if keywords and not any(k in title for k in keywords):
                continue
            abs_url = job.get("absolute_url")
            if abs_url and abs_url not in result:
                result.append(abs_url)
        return result
    except Exception as exc:
        log.warning("greenhouse_multi.slug_failed", slug=slug, error=str(exc))
        return []


async def _fetch_lever_site(site: str, keywords: list[str], limit: int) -> list[str]:
    """Fetch job URLs from a single Lever job board."""
    url = LEVER_API.format(site=site)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return []
        postings = resp.json()
        if not isinstance(postings, list):
            return []
        result: list[str] = []
        for posting in postings:
            if len(result) >= limit:
                break
            title = (posting.get("text") or "").lower()
            if keywords and not any(k in title for k in keywords):
                continue
            hosted_url = posting.get("hostedUrl")
            if hosted_url and hosted_url not in result:
                result.append(hosted_url)
        return result
    except Exception as exc:
        log.warning("lever_multi.site_failed", site=site, error=str(exc))
        return []
