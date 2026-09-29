"""
Indeed Job Scraper
Scrapes job postings from Indeed using httpx + BeautifulSoup.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

INDEED_SEARCH_URL = "https://www.indeed.com/jobs"


class IndeedScraper:
    """Scrapes Indeed job postings."""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def fetch_jobs(
        self,
        query: str = "software developer",
        location: str = "United States",
        limit: int = 25,
    ) -> list[dict]:
        params = {
            "q": query,
            "l": location,
            "fromage": 1,    # last 1 day
            "sort": "date",
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=30, follow_redirects=True) as client:
            response = await client.get(INDEED_SEARCH_URL, params=params)
            if response.status_code != 200:
                logger.warning(f"Indeed returned {response.status_code}")
                return []

        soup = BeautifulSoup(response.text, "lxml")
        job_cards = soup.find_all("div", class_="job_seen_beacon")[:limit]

        jobs = []
        for card in job_cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Indeed card parse error: {e}")

        logger.info(f"Indeed: found {len(jobs)} jobs")
        return jobs

    def _parse_card(self, card) -> Optional[dict]:
        title_el = card.find("span", attrs={"id": lambda x: x and "jobTitle" in x})
        company_el = card.find("span", class_="companyName")
        location_el = card.find("div", class_="companyLocation")
        link_el = card.find("a", class_="jcs-JobTitle")

        if not title_el or not link_el:
            return None

        job_id = link_el.get("data-jk", "")
        url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else None
        if not url:
            return None

        snippet_el = card.find("div", class_="job-snippet")
        description = snippet_el.get_text(strip=True) if snippet_el else None

        return {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else None,
            "description": description,
            "source": "indeed",
            "source_url": url,
            "external_id": job_id,
            "posted_at": datetime.now(timezone.utc),
        }
