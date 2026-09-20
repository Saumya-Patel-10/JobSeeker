"""Raytheon careers site discovery via supervised browser."""

from __future__ import annotations

import httpx

from app.runtime.automation_runtime import get_automation_runtime
from app.services.event_bus import get_event_bus
from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.sources.browser_health import profile_based_browser_health
from app.utils.logging import get_logger

log = get_logger(__name__)

RAYTHEON_SEARCH = "https://careers.rtx.com/global/en/search-results"


class RaytheonCareersSourceAdapter(JobSourceAdapter):
    name = "raytheon"

    async def health(self) -> SourceHealth:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                response = await client.get(RAYTHEON_SEARCH)
            if response.status_code >= 400:
                return SourceHealth(
                    status="error",
                    message=f"Raytheon careers HTTP {response.status_code}",
                )
        except Exception as exc:
            return SourceHealth(status="error", message=str(exc))
        profile = profile_based_browser_health(source_label="Raytheon")
        if profile.status == "error":
            return profile
        return SourceHealth(
            status="healthy",
            message="Raytheon careers reachable; browser profile ready for discover",
            authenticated=profile.authenticated,
        )

    async def discover(self, ctx: DiscoveryContext) -> list[str]:
        runtime = get_automation_runtime()
        if not await runtime.await_ready():
            return []

        session = await runtime.get_browser_session(session_id="raytheon-discovery")
        runtime.update_browser_context(task="Raytheon careers search")
        get_event_bus().emit("browser.task", {"task": "Raytheon discovery"})

        keywords = ctx.keywords or self._config_keywords()
        urls: list[str] = []
        page = await session.new_page()
        try:
            query = keywords[0] if keywords else ""
            search_url = RAYTHEON_SEARCH
            if query:
                from urllib.parse import urlencode

                search_url = f"{RAYTHEON_SEARCH}?{urlencode({'q': query})}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            runtime.update_browser_context(url=page.url, title=await page.title())
            await session.screenshot(page, "raytheon_search")

            job_links = await page.eval_on_selector_all(
                'a[href*="/job/"], a[href*="/jobs/"]',
                "els => els.map(e => e.href).filter((v,i,a) => a.indexOf(v) === i)",
            )
            for link in job_links:
                if isinstance(link, str) and ("rtx.com" in link or "raytheon" in link.lower()):
                    clean = link.split("?")[0]
                    if clean not in urls:
                        urls.append(clean)
                if len(urls) >= ctx.limit:
                    break
        except Exception as exc:
            log.warning("raytheon.discover_failed", error=str(exc))
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
