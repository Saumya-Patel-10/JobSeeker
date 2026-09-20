"""Greenhouse Job Boards adapter.

Scraping uses the public ``boards-api.greenhouse.io`` JSON endpoint — no
login required and no Playwright needed. Form-filling/submission requires
the browser session because Greenhouse application pages are interactive.
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
    DryRunReport,
    FillReport,
    SubmitReport,
)
from app.models.enums import ATSSource
from app.models.job import Job
from app.utils.errors import ScrapeError
from app.utils.hashing import url_hash
from app.utils.logging import get_logger

log = get_logger(__name__)

_URL_RE = re.compile(
    r"https?://(?:boards|job-boards)\.greenhouse\.io/(?P<token>[^/]+)/jobs/(?P<id>\d+)"
)
_EMBED_RE = re.compile(
    r"https?://boards-api\.greenhouse\.io/v1/boards/(?P<token>[^/]+)/jobs/(?P<id>\d+)"
)


class GreenhouseAdapter(ATSAdapter):
    name: ClassVar[str] = "greenhouse"

    @classmethod
    def detect(cls, url: str, html: str | None = None) -> bool:
        if not url:
            return False
        lower = url.lower()
        if "greenhouse.io" in lower:
            return True
        return bool(html and "boards-api.greenhouse" in html.lower())

    @classmethod
    def parse_url(cls, url: str) -> tuple[str, str] | None:
        match = _URL_RE.search(url) or _EMBED_RE.search(url)
        if match is None:
            return None
        return match.group("token"), match.group("id")

    async def scrape_job(self, url: str) -> Job:
        parsed = self.parse_url(url)
        if parsed is None:
            raise ScrapeError(f"Could not parse Greenhouse URL: {url}")
        board_token, job_id = parsed
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(api_url, params={"questions": "true"})
            except httpx.RequestError as exc:
                raise ScrapeError(f"Greenhouse API unreachable: {exc}") from exc
        if resp.status_code != 200:
            raise ScrapeError(f"Greenhouse API returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()

        title = str(data.get("title", "Unknown"))
        company_obj = data.get("company") or {}
        company = (
            company_obj.get("name") if isinstance(company_obj, dict) else None
        ) or board_token.title()
        location_obj = data.get("location") or {}
        location = location_obj.get("name") if isinstance(location_obj, dict) else None
        description_html = str(data.get("content", "") or "")
        description_text = BeautifulSoup(description_html, "lxml").get_text("\n", strip=True)
        posted_at = _parse_iso(data.get("updated_at") or data.get("first_published"))

        return Job(
            external_id=str(data.get("id", job_id)),
            title=title,
            company=str(company),
            location=location,
            description_text=description_text,
            description_html=description_html,
            source_url=url,
            ats_source=ATSSource.greenhouse,
            url_hash=url_hash(url),
            posted_at=posted_at,
            scraped_at=datetime.now(UTC),
            raw_payload=data,
        )

    async def fill_application(self, ctx: ApplicationContext) -> FillReport:
        if self.session is None:
            raise ScrapeError("Browser session required for Greenhouse fill_application")
        page = await self.session.new_page()
        try:
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            filled = 0
            skipped = 0
            failed = 0
            notes: list[str] = []

            mapping: list[tuple[str, str | None]] = [
                (selectors.FIRST_NAME, ctx.profile.personal.first_name),
                (selectors.LAST_NAME, ctx.profile.personal.last_name),
                (selectors.EMAIL, ctx.profile.personal.email),
                (selectors.PHONE, ctx.profile.personal.phone),
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

            if ctx.cover_letter:
                try:
                    await page.locator(selectors.COVER_LETTER).first.fill(
                        ctx.cover_letter, timeout=4000
                    )
                    filled += 1
                except Exception:
                    skipped += 1

            screenshot = await self.session.screenshot(
                page, f"greenhouse_{ctx.job.url_hash[:8]}_filled"
            )
            return FillReport(
                fields_filled=filled,
                fields_skipped=skipped,
                fields_failed=failed,
                screenshots=[str(screenshot)],
                notes=notes,
            )
        finally:
            await page.close()

    async def submit(self, ctx: ApplicationContext) -> SubmitReport:
        if self.session is None:
            raise ScrapeError("Browser session required for Greenhouse submit")
        page = await self.session.new_page()
        try:
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            await self.fill_application(ctx)
            ss_before = await self.session.screenshot(
                page, f"greenhouse_{ctx.job.url_hash[:8]}_pre_submit"
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
                page, f"greenhouse_{ctx.job.url_hash[:8]}_post_submit"
            )
            text = (await page.content()).lower()
            ok = "thank" in text or "application received" in text or "successfully" in text
            return SubmitReport(
                submitted=ok,
                confirmation_text="Application received" if ok else None,
                screenshot=str(ss_after),
                submitted_at=datetime.now(UTC) if ok else None,
            )
        finally:
            await page.close()

    async def dry_run(self, ctx: ApplicationContext) -> DryRunReport:
        if self.session is None:
            return DryRunReport(
                job_id=ctx.job.id or 0,
                adapter=self.name,
                notes=["No browser session — DOM inspection skipped."],
            )
        page = await self.session.new_page()
        try:
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            labels = await page.eval_on_selector_all(
                "label",
                "elements => elements.map(el => (el.innerText || '').trim()).filter(Boolean)",
            )
            ss = await self.session.screenshot(page, f"greenhouse_{ctx.job.url_hash[:8]}_dryrun")
            return DryRunReport(
                job_id=ctx.job.id or 0,
                adapter=self.name,
                notes=[f"Detected {len(labels)} labels", *labels[:30]],
                screenshots=[str(ss)],
            )
        finally:
            await page.close()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
