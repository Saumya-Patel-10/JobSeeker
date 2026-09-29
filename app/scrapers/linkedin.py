"""
LinkedIn Job Scraper
Scrapes recent job postings from LinkedIn using httpx + BeautifulSoup.
Note: LinkedIn requires authentication cookies for full access.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"


class LinkedInScraper:
    """Scrapes LinkedIn job postings."""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def fetch_jobs(
        self,
        keywords: str = "software engineer OR developer OR data scientist",
        location: str = "United States",
        limit: int = 25,
    ) -> list[dict]:
        """
        Fetch job postings from LinkedIn public search.
        Returns a list of job dicts compatible with the Job model.
        """
        params = {
            "keywords": keywords,
            "location": location,
            "f_TPR": "r1800",   # posted in last 30 minutes
            "start": 0,
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=30, follow_redirects=True) as client:
            response = await client.get(LINKEDIN_JOBS_URL, params=params)
            if response.status_code != 200:
                logger.warning(f"LinkedIn returned {response.status_code}")
                return []

        soup = BeautifulSoup(response.text, "lxml")
        job_cards = soup.find_all("div", class_="base-card")[:limit]

        jobs = []
        for card in job_cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"LinkedIn card parse error: {e}")

        logger.info(f"LinkedIn: found {len(jobs)} jobs")
        return jobs

    def _parse_card(self, card) -> Optional[dict]:
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        location_el = card.find("span", class_="job-search-card__location")
        link_el = card.find("a", class_="base-card__full-link")

        if not title_el or not link_el:
            return None

        url = link_el.get("href", "").split("?")[0]
        if not url:
            return None

        return {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else None,
            "description": None,   # fetched on demand by the matching engine
            "source": "linkedin",
            "source_url": url,
            "posted_at": datetime.now(timezone.utc),
        }
