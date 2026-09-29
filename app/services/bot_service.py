"""
Bot Service — Playwright browser automation.
Handles automated job application form submission for:
  - LinkedIn Easy Apply
  - Indeed Apply
  - Greenhouse application portal
"""
import asyncio
import logging
from typing import Optional, Tuple
import tempfile
import os
import httpx

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobApplicationBot:
    """Playwright-based automated job application bot."""

    def __init__(self):
        self.browser: Optional[Browser] = None

    async def apply(
        self,
        job_url: str,
        job_source: str,
        resume_url: str,
        cover_letter_url: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Main entry point. Routes to the correct platform handler.
        Returns (success: bool, error_message: str | None)
        """
        # Download resume to a temp file
        resume_path = await self._download_to_temp(resume_url, suffix=".docx")
        cl_path = None
        if cover_letter_url:
            cl_path = await self._download_to_temp(cover_letter_url, suffix=".docx")

        try:
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                context = await self.browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                page = await context.new_page()

                source_lower = job_source.lower()
                if source_lower == "linkedin":
                    return await self._apply_linkedin(page, job_url, resume_path, cl_path)
                elif source_lower == "indeed":
                    return await self._apply_indeed(page, job_url, resume_path, cl_path)
                elif source_lower == "greenhouse":
                    return await self._apply_greenhouse(page, job_url, resume_path, cl_path)
                else:
                    return await self._apply_generic(page, job_url, resume_path, cl_path)

        except Exception as e:
            logger.error(f"Bot error for {job_url}: {e}")
            return False, str(e)
        finally:
            # Cleanup temp files
            for path in [resume_path, cl_path]:
                if path and os.path.exists(path):
                    os.unlink(path)

    # ─────────────────────────────────────────────────────────────────────────
    # Platform-specific handlers
    # ─────────────────────────────────────────────────────────────────────────

    async def _apply_linkedin(
        self, page: Page, job_url: str, resume_path: str, cl_path: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """LinkedIn Easy Apply automation."""
        try:
            # Log in first
            await page.goto("https://www.linkedin.com/login", timeout=30000)
            await page.fill("#username", settings.LINKEDIN_EMAIL)
            await page.fill("#password", settings.LINKEDIN_PASSWORD)
            await page.click("[type=submit]")
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Navigate to job
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Click Easy Apply
            easy_apply_btn = await page.query_selector(".jobs-apply-button")
            if not easy_apply_btn:
                return False, "Easy Apply button not found — manual application required"
            await easy_apply_btn.click()
            await asyncio.sleep(2)

            # Handle multi-step modal
            max_steps = 10
            for step in range(max_steps):
                # Upload resume if file input exists
                file_input = await page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(1)

                # Fill cover letter textarea if present
                cl_area = await page.query_selector("textarea[id*='cover-letter']")
                if cl_area and cl_path:
                    # Read cover letter text and paste it
                    cl_text = await _read_docx_text(cl_path)
                    await cl_area.fill(cl_text[:3000])

                # Check for Next / Submit / Review
                next_btn = await page.query_selector("button[aria-label='Continue to next step']")
                submit_btn = await page.query_selector("button[aria-label='Submit application']")
                review_btn = await page.query_selector("button[aria-label='Review your application']")

                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(2)
                    return True, None
                elif review_btn:
                    await review_btn.click()
                    await asyncio.sleep(1)
                elif next_btn:
                    await next_btn.click()
                    await asyncio.sleep(1)
                else:
                    break

            return False, "Could not complete LinkedIn Easy Apply flow"

        except PlaywrightTimeout as e:
            return False, f"LinkedIn timeout: {e}"

    async def _apply_indeed(
        self, page: Page, job_url: str, resume_path: str, cl_path: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Indeed Apply automation."""
        try:
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Click Apply Now
            apply_btn = await page.query_selector("button#indeedApplyButton, a.indeed-apply-button")
            if not apply_btn:
                return False, "Indeed Apply button not found"
            await apply_btn.click()
            await asyncio.sleep(2)

            # Upload resume
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(resume_path)
                await asyncio.sleep(2)

            # Multi-step form navigation
            for _ in range(8):
                continue_btn = await page.query_selector("button[data-testid='IndeedApplyButtonV2']")
                submit_btn = await page.query_selector("button[data-testid='SubmitButton']")

                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(2)
                    return True, None
                elif continue_btn:
                    await continue_btn.click()
                    await asyncio.sleep(1)
                else:
                    break

            return False, "Could not complete Indeed apply flow"

        except PlaywrightTimeout as e:
            return False, f"Indeed timeout: {e}"

    async def _apply_greenhouse(
        self, page: Page, job_url: str, resume_path: str, cl_path: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Greenhouse application form automation."""
        try:
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Upload resume
            resume_input = await page.query_selector("input#resume")
            if resume_input:
                await resume_input.set_input_files(resume_path)
                await asyncio.sleep(1)

            # Upload cover letter
            if cl_path:
                cl_input = await page.query_selector("input#cover_letter")
                if cl_input:
                    await cl_input.set_input_files(cl_path)
                    await asyncio.sleep(1)

            # Submit
            submit_btn = await page.query_selector("input#submit_app")
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(3)
                return True, None

            return False, "Greenhouse submit button not found"

        except PlaywrightTimeout as e:
            return False, f"Greenhouse timeout: {e}"

    async def _apply_generic(
        self, page: Page, job_url: str, resume_path: str, cl_path: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Generic fallback handler — looks for common apply patterns."""
        try:
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Try to find a file upload
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(resume_path)
                await asyncio.sleep(1)

            # Look for a submit button
            for selector in ["button[type='submit']", "input[type='submit']", "button.apply"]:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await asyncio.sleep(2)
                    return True, None

            return False, "Generic handler: no recognizable apply form found"

        except PlaywrightTimeout as e:
            return False, f"Generic timeout: {e}"

    # ─── Utilities ────────────────────────────────────────────────────────────

    @staticmethod
    async def _download_to_temp(url: str, suffix: str = ".docx") -> str:
        """Download a file from URL to a temp file. Returns temp file path."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(resp.content)
            return f.name


async def _read_docx_text(path: str) -> str:
    """Read text from a DOCX file."""
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)
