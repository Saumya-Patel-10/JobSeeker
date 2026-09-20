"""LinkedIn adapter — ASSIST MODE ONLY.

LinkedIn's Terms of Service prohibit automated submission. This adapter
intentionally fills the form and stops at the final "Submit application"
button so the user can review and click submit themselves. Override at
your own risk in your local fork.

Login is delegated to the persistent browser profile: run with
``browser.headless: false`` once, log in manually, and subsequent runs
reuse the cookies under ``data/browser_profiles/<profile>``.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import ClassVar

from app.ats.base import ATSAdapter
from app.automation.browser import BrowserSession
from app.models.application import (
    ApplicationContext,
    DryRunReport,
    FillReport,
    SubmitReport,
)
from app.models.enums import ATSSource
from app.models.job import Job
from app.utils.errors import ScrapeError, SubmitError
from app.utils.hashing import url_hash
from app.utils.logging import get_logger

log = get_logger(__name__)

_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/(?P<id>\d+)")


class LinkedInAdapter(ATSAdapter):
    name: ClassVar[str] = "linkedin"

    @classmethod
    def detect(cls, url: str, html: str | None = None) -> bool:
        if not url:
            return False
        return "linkedin.com/jobs" in url.lower()

    @classmethod
    def parse_url(cls, url: str) -> str | None:
        match = _URL_RE.search(url)
        return match.group("id") if match else None

    async def login(self, session: BrowserSession) -> None:
        """Ensure the user is logged in. We do NOT enter credentials —
        instead we open ``/login`` headed and wait for the user."""
        if session.config.headless:
            log.warning(
                "linkedin.headless_login_skipped",
                hint="Run with browser.headless: false once to log in.",
            )
            return

    async def scrape_job(self, url: str) -> Job:
        if self.session is None:
            raise ScrapeError(
                "LinkedIn scraping requires a logged-in browser session. "
                "Set browser.headless: false and log in once."
            )
        page = await self.session.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await page.wait_for_selector(
                    "h1.top-card-layout__title, h1[data-test-id='job-title']",
                    timeout=10000,
                )
            except Exception as exc:
                raise ScrapeError(
                    f"LinkedIn page did not render job title (login required?): {exc}"
                ) from exc

            title = await _safe_text(
                page, "h1.top-card-layout__title, h1[data-test-id='job-title']"
            )
            company = await _safe_text(
                page,
                "a.topcard__org-name-link, span[data-test-id='employer-name'], "
                "div.job-details-jobs-unified-top-card__company-name a",
            )
            location = await _safe_text(
                page,
                "span.topcard__flavor--bullet, div.job-details-jobs-unified-top-card__primary-description-container",
            )
            description = await _safe_text(
                page, "div.description__text, div.jobs-description__content"
            )

            return Job(
                external_id=self.parse_url(url),
                title=title or "Unknown",
                company=company or "Unknown",
                location=location,
                description_text=description or "",
                description_html=None,
                source_url=url,
                ats_source=ATSSource.linkedin,
                url_hash=url_hash(url),
                scraped_at=datetime.now(UTC),
                raw_payload=None,
            )
        finally:
            await page.close()

    async def fill_application(self, ctx: ApplicationContext) -> FillReport:
        if self.session is None:
            raise ScrapeError("Browser session required for LinkedIn fill_application")
        page = await self.session.new_page()
        notes: list[str] = []
        try:
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            try:
                await page.locator(
                    "button.jobs-apply-button, button:has-text('Easy Apply')"
                ).first.click(timeout=8000)
            except Exception as exc:
                notes.append(f"Easy Apply button not found: {exc}")
                ss = await self.session.screenshot(
                    page, f"linkedin_{ctx.job.url_hash[:8]}_no_easy_apply"
                )
                return FillReport(
                    fields_filled=0,
                    fields_skipped=0,
                    fields_failed=1,
                    notes=notes,
                    screenshots=[str(ss)],
                )

            filled = 0
            skipped = 0
            failed = 0

            mapping = [
                (
                    "input[id*='phoneNumber'], input[id*='phone-number'], input[name*='phone' i]",
                    ctx.profile.personal.phone,
                ),
                ("input[id*='firstName' i]", ctx.profile.personal.first_name),
                ("input[id*='lastName' i]", ctx.profile.personal.last_name),
                ("input[type='email']", ctx.profile.personal.email),
            ]
            for selector, value in mapping:
                if not value:
                    skipped += 1
                    continue
                try:
                    await page.locator(selector).first.fill(value, timeout=3000)
                    filled += 1
                except Exception:
                    skipped += 1

            if ctx.resume_pdf_path:
                try:
                    await page.locator("input[type='file']").first.set_input_files(
                        ctx.resume_pdf_path
                    )
                    filled += 1
                except Exception as exc:
                    failed += 1
                    notes.append(f"resume upload: {exc}")

            notes.append(
                "ASSIST-MODE: stopped before Submit. Review the form and click Submit manually."
            )
            ss = await self.session.screenshot(page, f"linkedin_{ctx.job.url_hash[:8]}_assist_stop")
            return FillReport(
                fields_filled=filled,
                fields_skipped=skipped,
                fields_failed=failed,
                notes=notes,
                screenshots=[str(ss)],
            )
        finally:
            await page.close()

    async def submit(self, _ctx: ApplicationContext) -> SubmitReport:
        # Hard policy: never auto-submit on LinkedIn.
        raise SubmitError(
            "LinkedIn adapter operates in assist-only mode and refuses to submit. "
            "Click Submit manually after reviewing the prepared form."
        )

    async def dry_run(self, ctx: ApplicationContext) -> DryRunReport:
        if self.session is None:
            return DryRunReport(
                job_id=ctx.job.id or 0,
                adapter=self.name,
                notes=["No browser session — login + DOM inspection skipped."],
            )
        page = await self.session.new_page()
        try:
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            ss = await self.session.screenshot(page, f"linkedin_{ctx.job.url_hash[:8]}_dryrun")
            return DryRunReport(
                job_id=ctx.job.id or 0,
                adapter=self.name,
                notes=["LinkedIn opens the Easy Apply modal; no auto-submit."],
                screenshots=[str(ss)],
            )
        finally:
            await page.close()


async def _safe_text(page, selector: str) -> str | None:
    try:
        return (await page.locator(selector).first.inner_text(timeout=4000)).strip()
    except Exception:
        return None
