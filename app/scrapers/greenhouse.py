"""
Greenhouse Job Scraper
Greenhouse exposes a public JSON API — no scraping needed!
Endpoint: https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Add more company slugs as you grow
GREENHOUSE_COMPANIES = [
    "stripe", "openai", "anthropic", "notion", "figma",
    "vercel", "supabase", "planetscale", "linear", "loom",
]

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper:
    """Uses the public Greenhouse Jobs API to fetch postings."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def fetch_jobs(self, limit_per_company: int = 10) -> list[dict]:
        all_jobs = []

        async with httpx.AsyncClient(timeout=30) as client:
            for slug in GREENHOUSE_COMPANIES:
                try:
                    jobs = await self._fetch_company_jobs(client, slug, limit_per_company)
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.debug(f"Greenhouse {slug} error: {e}")

        logger.info(f"Greenhouse: found {len(all_jobs)} jobs across {len(GREENHOUSE_COMPANIES)} companies")
        return all_jobs

    async def _fetch_company_jobs(
        self, client: httpx.AsyncClient, slug: str, limit: int
    ) -> list[dict]:
        url = f"{GREENHOUSE_API_BASE}/{slug}/jobs?content=true"
        response = await client.get(url)
        if response.status_code != 200:
            return []

        data = response.json()
        raw_jobs = data.get("jobs", [])[:limit]

        jobs = []
        for job in raw_jobs:
            parsed = self._parse_job(job, slug)
            if parsed:
                jobs.append(parsed)
        return jobs

    def _parse_job(self, job: dict, company_slug: str) -> Optional[dict]:
        job_id = job.get("id")
        title = job.get("title")
        if not job_id or not title:
            return None

        # Extract location
        offices = job.get("offices", [])
        location = offices[0].get("name") if offices else None

        # Job content (HTML stripped)
        content_html = job.get("content", "")
        description = _strip_html(content_html)[:5000]

        url = f"https://boards.greenhouse.io/{company_slug}/jobs/{job_id}"

        updated_at = job.get("updated_at")
        posted_at = None
        if updated_at:
            try:
                posted_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except Exception:
                posted_at = datetime.now(timezone.utc)

        return {
            "title": title,
            "company": company_slug.capitalize(),
            "location": location,
            "description": description,
            "source": "greenhouse",
            "source_url": url,
            "external_id": str(job_id),
            "posted_at": posted_at,
        }


def _strip_html(html: str) -> str:
    """Remove HTML tags from Greenhouse job description."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)
