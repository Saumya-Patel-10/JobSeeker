"""Lever Jobs adapter.

Scraping uses the public ``api.lever.co/v0/postings/<site>/<id>?mode=json``
endpoint. Form filling targets ``jobs.lever.co/<site>/<id>/apply``.
"""

from __future__ import annotations

import contextlib
import re
from datetime import UTC, datetime
from typing import ClassVar

import httpx
from bs4 import BeautifulSoup

from app.ats.base import ATSAdapter
from app.automation import selectors
from app.models.application import (
    ApplicationContext,
    FillReport,
    SubmitReport,
)
from app.models.enums import ATSSource
from app.models.job import Job
from app.utils.errors import ScrapeError
from app.utils.hashing import url_hash
from app.utils.logging import get_logger

log = get_logger(__name__)

_URL_RE = re.compile(r"https?://jobs\.lever\.co/(?P<site>[^/]+)/(?P<id>[a-zA-Z0-9-]+)")


class LeverAdapter(ATSAdapter):
    name: ClassVar[str] = "lever"

    @classmethod
    def detect(cls, url: str, html: str | None = None) -> bool:
        if not url:
            return False
        if "lever.co" in url.lower():
            return True
        return bool(html and "jobs.lever.co" in html.lower())

    @classmethod
    def parse_url(cls, url: str) -> tuple[str, str] | None:
        match = _URL_RE.search(url)
        if match is None:
            return None
        return match.group("site"), match.group("id")

    async def scrape_job(self, url: str) -> Job:
        parsed = self.parse_url(url)
        if parsed is None:
            raise ScrapeError(f"Could not parse Lever URL: {url}")
        site, job_id = parsed
        api_url = f"https://api.lever.co/v0/postings/{site}/{job_id}?mode=json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(api_url)
            except httpx.RequestError as exc:
                raise ScrapeError(f"Lever API unreachable: {exc}") from exc
        if resp.status_code != 200:
            raise ScrapeError(f"Lever API returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()

        title = str(data.get("text", "Unknown"))
        company = site.replace("-", " ").title()
        categories = data.get("categories") or {}
        location = categories.get("location") if isinstance(categories, dict) else None

        description_html = str(data.get("descriptionHtml") or data.get("description", "") or "")
        description_text = BeautifulSoup(description_html, "lxml").get_text("\n", strip=True)

        posted_at: datetime | None = None
        created_at = data.get("createdAt")
        if isinstance(created_at, (int, float)):
            try:
                posted_at = datetime.fromtimestamp(int(created_at) / 1000, tz=UTC)
            except (OSError, ValueError, OverflowError):
                posted_at = None

        return Job(
            external_id=str(data.get("id", job_id)),
            title=title,
            company=company,
            location=location,
            description_text=description_text,
            description_html=description_html,
            source_url=url,
            ats_source=ATSSource.lever,
            url_hash=url_hash(url),
            posted_at=posted_at,
            scraped_at=datetime.now(UTC),
            raw_payload=data,
        )

    async def fill_application(self, ctx: ApplicationContext) -> FillReport:
        if self.session is None:
            raise ScrapeError("Browser session required for Lever fill_application")
        apply_url = ctx.job.source_url.rstrip("/") + "/apply"
        page = await self.session.new_page()
        try:
            await page.goto(apply_url, wait_until="domcontentloaded")
            filled = 0
            skipped = 0
            failed = 0
            notes: list[str] = []

            mapping: list[tuple[str, str | None]] = [
                ('input[name="name"]', ctx.profile.personal.full_name),
                (selectors.EMAIL, ctx.profile.personal.email),
                (selectors.PHONE, ctx.profile.personal.phone),
                (
                    'input[name="org"]',
                    ctx.profile.employment[0].company if ctx.profile.employment else None,
                ),
                (
                    selectors.LINKEDIN,
                    str(ctx.profile.links.linkedin) if ctx.profile.links.linkedin else None,
                ),
                (
                    selectors.GITHUB,
                    str(ctx.profile.links.github) if ctx.profile.links.github else None,
                ),
            ]
            for selector, value in mapping:
                if not value:
                    skipped += 1
                    continue
                try:
                    await page.locator(selector).first.fill(value, timeout=4000)
                    filled += 1
                except Exception as exc:
                    failed += 1
                    notes.append(f"{selector[:40]}: {exc}")

            if ctx.resume_pdf_path:
                try:
                    await page.locator(selectors.RESUME_UPLOAD).first.set_input_files(
                        ctx.resume_pdf_path
                    )
                    filled += 1
                except Exception as exc:
                    failed += 1
                    notes.append(f"resume upload: {exc}")

            ss = await self.session.screenshot(page, f"lever_{ctx.job.url_hash[:8]}_filled")
            return FillReport(
                fields_filled=filled,
                fields_skipped=skipped,
                fields_failed=failed,
                screenshots=[str(ss)],
                notes=notes,
            )
        finally:
            await page.close()

    async def submit(self, ctx: ApplicationContext) -> SubmitReport:
        if self.session is None:
            raise ScrapeError("Browser session required for Lever submit")
        apply_url = ctx.job.source_url.rstrip("/") + "/apply"
        page = await self.session.new_page()
        try:
            await page.goto(apply_url, wait_until="domcontentloaded")
            await self.fill_application(ctx)
            ss_before = await self.session.screenshot(
                page, f"lever_{ctx.job.url_hash[:8]}_pre_submit"
            )
            try:
                await page.locator(selectors.SUBMIT).first.click(timeout=8000)
            except Exception as exc:
                return SubmitReport(
                    submitted=False,
                    error=f"submit click failed: {exc}",
                    screenshot=str(ss_before),
                )
            with contextlib.suppress(Exception):
                await page.wait_for_load_state("networkidle", timeout=15000)
            ss_after = await self.session.screenshot(
                page, f"lever_{ctx.job.url_hash[:8]}_post_submit"
            )
            text = (await page.content()).lower()
            ok = "thank" in text or "received your application" in text
            return SubmitReport(
                submitted=ok,
                confirmation_text="Application received" if ok else None,
                screenshot=str(ss_after),
                submitted_at=datetime.now(UTC) if ok else None,
            )
        finally:
            await page.close()
