"""LinkedIn job discovery — assist-only, supervised browser search."""

from __future__ import annotations

import urllib.parse

from app.runtime.automation_runtime import get_automation_runtime
from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.sources.browser_health import profile_based_browser_health
from app.utils.logging import get_logger

log = get_logger(__name__)

LINKEDIN_JOBS_SEARCH = "https://www.linkedin.com/jobs/search/"


class LinkedInSourceAdapter(JobSourceAdapter):
    name = "linkedin"

    async def health(self) -> SourceHealth:
        return profile_based_browser_health(source_label="LinkedIn (assist-only)")

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        runtime = get_automation_runtime()
        if not await runtime.await_ready():
            return []

        keywords = ctx.keywords or self._config_keywords()
        if not keywords:
            log.info("linkedin.discover_skipped", reason="no_keywords")
            return []

        session = await runtime.get_browser_session(session_id="linkedin-discovery")
        runtime.update_browser_context(task="LinkedIn job search (assist-only)")
        get_event_bus().emit("browser.task", {"task": "LinkedIn discovery search"})

        urls: list[str] = []
        for keyword in keywords[:3]:
            if not await runtime.await_ready():
                break
            query = urllib.parse.urlencode(
                {
                    "keywords": keyword,
                    "location": ctx.locations[0] if ctx.locations else "",
                }
            )
            search_url = f"{LINKEDIN_JOBS_SEARCH}?{query}"
            page = await session.new_page()
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                runtime.update_browser_context(url=page.url, title=await page.title())
                await session.screenshot(page, f"linkedin_search_{keyword[:20]}")
                job_links = await page.eval_on_selector_all(
                    'a[href*="/jobs/view/"]',
                    "els => els.map(e => e.href).filter((v,i,a) => a.indexOf(v) === i)",
                )
                for link in job_links:
                    if isinstance(link, str) and "/jobs/view/" in link:
                        clean = link.split("?")[0]
                        if clean not in urls:
                            urls.append(clean)
                    if len(urls) >= ctx.limit:
                        break
            except Exception as exc:
                log.warning("linkedin.discover_failed", keyword=keyword, error=str(exc))
                runtime.update_browser_context(error=str(exc))
            finally:
                await page.close()

        get_event_bus().emit(
            "discovery.source_complete",
            {"source": self.source.name, "urls": len(urls)},
        )
        return urls[: ctx.limit]

    def _config_keywords(self) -> list[str]:
        raw = self.source.config.get("keywords", [])
        if isinstance(raw, list):
            return [str(k) for k in raw]
        return []
