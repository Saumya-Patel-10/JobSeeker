"""Generic fallback adapter.

Strategy:
1. Open the URL in Playwright.
2. Extract <input>, <textarea>, <select> nodes with their labels.
3. Ask the LLM to classify each field and propose an answer from the profile.
4. Deterministically fill the form using the LLM's suggestions.

This is the slowest path because every field touches the LLM, but it's the
correct catch-all for company-specific application pages.
"""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from typing import Any, ClassVar

from bs4 import BeautifulSoup

from app.ats.base import ATSAdapter
from app.automation import selectors
from app.llm.base import ChatMessage, LLMProvider
from app.llm.prompts import PromptRegistry
from app.models.application import (
    ApplicationContext,
    DryRunReport,
    FieldDescriptor,
    FillReport,
    SubmitReport,
)
from app.models.enums import AnswerSource, ATSSource, FieldType
from app.models.job import Job
from app.utils.errors import ScrapeError
from app.utils.hashing import url_hash
from app.utils.logging import get_logger

log = get_logger(__name__)


class GenericAdapter(ATSAdapter):
    """LLM-classified fallback that handles unknown application pages."""

    name: ClassVar[str] = "generic"

    def __init__(
        self,
        session: Any | None = None,
        *,
        llm: LLMProvider | None = None,
        prompts: PromptRegistry | None = None,
    ) -> None:
        super().__init__(session)
        self.llm = llm
        self.prompts = prompts

    @classmethod
    def detect(cls, _url: str, _html: str | None = None) -> bool:
        # Generic always returns False — the registry uses it as the final
        # fallback when no specific adapter matched.
        return False

    async def scrape_job(self, url: str) -> Job:
        html: str
        if self.session is not None:
            page = await self.session.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded")
                html = await page.content()
            finally:
                await page.close()
        else:
            try:
                import httpx

                async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                    resp = await client.get(
                        url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            )
                        },
                    )
                    resp.raise_for_status()
                    html = resp.text
            except Exception as exc:
                raise ScrapeError(f"Generic adapter scrape failed: {exc}") from exc

        soup = BeautifulSoup(html, "lxml")
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Unknown"
        description_text = soup.get_text("\n", strip=True)[:20000]
        return Job(
            title=title,
            company="Unknown",
            description_text=description_text,
            description_html=html,
            source_url=url,
            ats_source=ATSSource.generic,
            url_hash=url_hash(url),
            scraped_at=datetime.now(UTC),
        )

    async def _detect_fields(self, page: Any) -> list[FieldDescriptor]:
        raw = await page.evaluate(r"""
            () => {
                const out = [];
                const elements = document.querySelectorAll('input, select, textarea');
                elements.forEach((el) => {
                    if (el.type === 'hidden' || el.type === 'submit' || el.type === 'button') return;
                    let label = '';
                    if (el.id) {
                        const lab = document.querySelector(`label[for="${el.id}"]`);
                        if (lab) label = (lab.innerText || '').trim();
                    }
                    if (!label && el.closest('label')) {
                        label = (el.closest('label').innerText || '').trim();
                    }
                    if (!label) label = el.placeholder || el.name || el.id || '';
                    let selector = '';
                    if (el.id) selector = `#${el.id}`;
                    else if (el.name) selector = `${el.tagName.toLowerCase()}[name="${el.name}"]`;
                    else selector = el.tagName.toLowerCase();
                    out.push({
                        label,
                        selector,
                        tag: el.tagName.toLowerCase(),
                        type: el.type || 'text',
                        required: !!el.required,
                        options: el.tagName === 'SELECT'
                            ? Array.from(el.options).map(o => o.text)
                            : [],
                    });
                });
                return out;
            }
            """)
        descriptors: list[FieldDescriptor] = []
        for item in raw:
            field_type = _map_field_type(item.get("tag"), item.get("type"))
            descriptors.append(
                FieldDescriptor(
                    label=item.get("label", "")[:200] or "(no label)",
                    selector=item.get("selector", ""),
                    field_type=field_type,
                    required=bool(item.get("required", False)),
                    options=[str(o) for o in (item.get("options") or [])],
                )
            )
        return descriptors

    async def _classify(
        self, ctx: ApplicationContext, descriptors: list[FieldDescriptor]
    ) -> list[FieldDescriptor]:
        if not self.llm or not self.prompts:
            return descriptors
        if not descriptors:
            return descriptors
        rendered = self.prompts.render(
            "field_classify",
            profile_json=ctx.profile.model_dump_json(),
            standard_answers_json=json.dumps(
                [a.model_dump(mode="json") for a in ctx.profile.standard_answers]
            ),
            fields_json=json.dumps([d.model_dump(mode="json") for d in descriptors]),
        )
        try:
            response = await self.llm.chat_json(
                [
                    ChatMessage(
                        role="system",
                        content="You classify form fields and propose honest answers using only the candidate's profile.",
                    ),
                    ChatMessage(role="user", content=rendered),
                ]
            )
        except Exception as exc:
            log.warning("generic.classify_failed", error=str(exc))
            return descriptors

        items = response.get("fields", [])
        merged: list[FieldDescriptor] = []
        for original, suggested in zip(descriptors, items, strict=False):
            try:
                merged.append(
                    FieldDescriptor(
                        label=original.label,
                        selector=original.selector,
                        field_type=FieldType(
                            suggested.get("field_type", original.field_type.value)
                        ),
                        required=bool(suggested.get("required", original.required)),
                        options=original.options,
                        suggested_answer=suggested.get("suggested_answer"),
                        answered_from=_parse_source(suggested.get("answered_from")),
                    )
                )
            except Exception:
                merged.append(original)
        # Pad if the LLM dropped trailing items.
        if len(merged) < len(descriptors):
            merged.extend(descriptors[len(merged) :])
        return merged

    async def fill_application(self, ctx: ApplicationContext) -> FillReport:
        if self.session is None:
            raise ScrapeError("Generic adapter requires a browser session")
        page = await self.session.new_page()
        try:
            self.session.set_task(f"Navigating to application: {ctx.job.source_url}")
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            self.session.set_task("Detecting form fields")
            descriptors = await self._detect_fields(page)
            self.session.set_task("Classifying fields with AI")
            classified = await self._classify(ctx, descriptors)

            filled = 0
            skipped = 0
            failed = 0
            notes: list[str] = []
            self.session.set_task("Filling form fields")
            for field in classified:
                if not field.suggested_answer:
                    skipped += 1
                    continue
                try:
                    locator = page.locator(field.selector).first
                    if field.field_type in (FieldType.select, FieldType.multiselect):
                        await locator.select_option(label=field.suggested_answer, timeout=4000)
                    elif field.field_type == FieldType.checkbox:
                        if field.suggested_answer.lower() in ("yes", "true", "1"):
                            await locator.check(timeout=4000)
                    elif field.field_type == FieldType.file:
                        if ctx.resume_pdf_path:
                            await locator.set_input_files(ctx.resume_pdf_path)
                    else:
                        await locator.fill(field.suggested_answer, timeout=4000)
                    filled += 1
                except Exception as exc:
                    failed += 1
                    notes.append(f"{field.label[:40]}: {exc}")

            # Always also try the universal resume upload.
            if ctx.resume_pdf_path:
                with contextlib.suppress(Exception):
                    await page.locator(selectors.RESUME_UPLOAD).first.set_input_files(
                        ctx.resume_pdf_path
                    )

            ss = await self.session.screenshot(page, f"generic_{ctx.job.url_hash[:8]}_filled")
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
            raise ScrapeError("Generic adapter requires a browser session")
        page = await self.session.new_page()
        try:
            self.session.set_task(f"Navigating to application: {ctx.job.source_url}")
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            await self.fill_application(ctx)
            ss_before = await self.session.screenshot(
                page, f"generic_{ctx.job.url_hash[:8]}_pre_submit"
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
                page, f"generic_{ctx.job.url_hash[:8]}_post_submit"
            )
            text = (await page.content()).lower()
            ok = any(s in text for s in ("thank", "submitted", "received your"))
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
            self.session.set_task(f"Navigating to application: {ctx.job.source_url}")
            await page.goto(ctx.job.source_url, wait_until="domcontentloaded")
            self.session.set_task("Detecting form fields")
            descriptors = await self._detect_fields(page)
            self.session.set_task("Classifying fields with AI")
            classified = await self._classify(ctx, descriptors)
            ss = await self.session.screenshot(page, f"generic_{ctx.job.url_hash[:8]}_dryrun")
            answers = [_to_generated_answer(f) for f in classified if f.suggested_answer]
            return DryRunReport(
                job_id=ctx.job.id or 0,
                adapter=self.name,
                fields_detected=classified,
                answers_prepared=answers,
                notes=[f"Detected {len(classified)} fields"],
                screenshots=[str(ss)],
            )
        finally:
            await page.close()


def _map_field_type(tag: str | None, html_type: str | None) -> FieldType:
    tag = (tag or "").lower()
    html_type = (html_type or "").lower()
    if tag == "textarea":
        return FieldType.textarea
    if tag == "select":
        return FieldType.select
    return {
        "email": FieldType.email,
        "tel": FieldType.phone,
        "number": FieldType.number,
        "date": FieldType.date,
        "url": FieldType.url,
        "file": FieldType.file,
        "checkbox": FieldType.checkbox,
        "radio": FieldType.radio,
        "text": FieldType.text,
        "password": FieldType.text,
    }.get(html_type, FieldType.unknown)


def _parse_source(value: Any) -> AnswerSource | None:
    if not value:
        return None
    try:
        return AnswerSource(value)
    except ValueError:
        return None


def _to_generated_answer(field: FieldDescriptor):
    from app.models.application import GeneratedAnswer

    return GeneratedAnswer(
        question=field.label,
        answer=field.suggested_answer or "",
        source=field.answered_from or AnswerSource.llm,
    )
