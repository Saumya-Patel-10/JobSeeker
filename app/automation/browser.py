"""Playwright wrapper that prefers Firefox persistent contexts."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.automation.chrome_profiles import (
    ChromeProfile,
    chrome_is_running,
    chrome_user_data_dir,
    discover_system_chrome_profiles,
    find_chrome_profile_by_email,
    get_chrome_profile,
)
from app.automation.firefox_profiles import (
    clone_firefox_profile,
    get_firefox_profile,
    profile_health,
)
from app.config.paths import BROWSER_PROFILES_DIR, SCREENSHOTS_DIR
from app.config.schema import BrowserConfig
from app.services.event_bus import get_event_bus
from app.utils.errors import BrowserError
from app.utils.logging import get_logger

log = get_logger(__name__)


class BrowserSession:
    """Persistent-context Playwright session wrapper."""

    def __init__(self, config: BrowserConfig) -> None:
        self.config = config
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._chrome_profile_directory: str | None = None

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise BrowserError("Browser session not started")
        return self._context

    @classmethod
    @asynccontextmanager
    async def launch(cls, config: BrowserConfig) -> AsyncIterator[BrowserSession]:
        """Async context manager. Always tears the browser down on exit."""
        session = cls(config)
        await session.start()
        try:
            yield session
        finally:
            await session.stop()

    async def start(self) -> None:
        BROWSER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self._pw = await async_playwright().start()
            browser_type = self._browser_type()
            channel = self._resolve_channel()
            args = self._launch_args()
            if self.config.persistent_profile:
                user_data_dir, profile_label = self._resolve_user_data_dir()
                self._context = await browser_type.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    channel=channel,
                    args=args,
                    headless=self.config.headless,
                    slow_mo=self.config.slowmo_ms,
                    locale=self.config.locale,
                    user_agent=self.config.user_agent,
                    viewport={
                        "width": self.config.viewport_width,
                        "height": self.config.viewport_height,
                    },
                    accept_downloads=True,
                )
            else:
                profile_label = "ephemeral"
                self._browser = await browser_type.launch(
                    channel=channel,
                    args=args,
                    headless=self.config.headless,
                    slow_mo=self.config.slowmo_ms,
                )
                self._context = await self._browser.new_context(
                    locale=self.config.locale,
                    user_agent=self.config.user_agent,
                    viewport={
                        "width": self.config.viewport_width,
                        "height": self.config.viewport_height,
                    },
                    accept_downloads=True,
                )
            self._context.set_default_timeout(self.config.timeout_ms)
            log.info(
                "browser.started",
                engine=self.config.engine,
                profile=profile_label,
                persistent=self.config.persistent_profile,
                headless=self.config.headless,
            )
        except Exception as exc:
            await self.stop()
            raise BrowserError(f"Failed to launch browser: {exc}") from exc

    async def stop(self) -> None:
        if self._context is not None:
            try:
                await self._context.close()
            except Exception as exc:
                log.warning("browser.close_failed", error=str(exc))
        self._context = None
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as exc:
                log.warning("browser.close_failed", error=str(exc))
        self._browser = None
        if self._pw is not None:
            try:
                await self._pw.stop()
            except Exception as exc:
                log.warning("playwright.stop_failed", error=str(exc))
        self._pw = None

    async def new_page(self) -> Page:
        page = await self.context.new_page()

        async def _on_nav(frame) -> None:
            if frame != page.main_frame:
                return
            try:
                title = await page.title()
            except Exception:
                title = ""
            payload = {"url": page.url, "title": title, "main": True}
            get_event_bus().emit("browser.navigate", payload)
            try:
                from app.runtime.automation_runtime import get_automation_runtime

                get_automation_runtime().update_browser_context(url=page.url, title=title)
                get_automation_runtime().log_action("navigate", detail=page.url)
            except Exception:
                pass

        page.on("framenavigated", lambda frame: asyncio.create_task(_on_nav(frame)))
        return page

    async def screenshot(self, page: Page, name: str) -> Path:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:80]
        path = SCREENSHOTS_DIR / f"{safe}.png"
        try:
            await page.screenshot(path=str(path), full_page=True)
            payload = {"name": name, "url": page.url, "path": str(path)}
            get_event_bus().emit("browser.screenshot", payload)
            try:
                from app.runtime.automation_runtime import get_automation_runtime

                get_automation_runtime().update_browser_context(screenshot_path=str(path))
            except Exception:
                pass
        except Exception as exc:
            log.warning("screenshot.failed", name=name, error=str(exc))
        return path

    async def dom_snapshot(self, page: Page, name: str) -> Path:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:80]
        path = SCREENSHOTS_DIR / f"{safe}.html"
        content = await page.content()
        path.write_text(content, encoding="utf-8")
        return path

    def set_task(self, task: str) -> None:
        get_event_bus().emit("browser.task", {"task": task})
        try:
            from app.runtime.automation_runtime import get_automation_runtime

            get_automation_runtime().update_browser_context(task=task)
        except Exception:
            pass

    def set_form_step(self, step: str) -> None:
        get_event_bus().emit("browser.form_step", {"step": step})
        try:
            from app.runtime.automation_runtime import get_automation_runtime

            get_automation_runtime().update_browser_context(form_step=step)
        except Exception:
            pass

    def emit_blocker(self, message: str) -> None:
        get_event_bus().emit("browser.blocker", {"message": message})
        try:
            from app.runtime.automation_runtime import get_automation_runtime

            get_automation_runtime().update_browser_context(error=message)
        except Exception:
            pass

    def log_action(self, action: str, *, detail: str | None = None) -> None:
        try:
            from app.runtime.automation_runtime import get_automation_runtime

            get_automation_runtime().log_action(action, detail=detail)
        except Exception:
            get_event_bus().emit("browser.action", {"action": action, "detail": detail})

    def _resolve_channel(self) -> str | None:
        """Resolve the Playwright channel (e.g. installed Chrome/Edge).

        Only applies to Chromium-family engines; Firefox/WebKit ignore it.
        A configured channel that is not installed surfaces as a launch
        failure via the normal BrowserError path in ``start()``.
        """
        if self._pw is None:
            raise BrowserError("Playwright engine not initialized")
        channel = self.config.channel
        if not channel or self.config.engine != "chromium":
            return None
        return channel

    def _browser_type(self):
        if self._pw is None:
            raise BrowserError("Playwright engine not initialized")
        if self.config.engine == "firefox":
            return self._pw.firefox
        if self.config.engine == "webkit":
            return self._pw.webkit
        return self._pw.chromium

    def _resolve_user_data_dir(self) -> tuple[Path, str]:
        if self.config.engine == "chromium" and self.config.profile_source == "system":
            return self._resolve_chrome_system_profile()
        if self.config.engine == "firefox" and self.config.profile_source == "system":
            profile_name = self.config.firefox_profile
            if not profile_name:
                raise BrowserError(
                    "browser.firefox_profile must be set when profile_source is 'system'"
                )
            profile = get_firefox_profile(profile_name, source="system")
            if profile is None:
                raise BrowserError(f"System Firefox profile not found: {profile_name}")
            health = profile_health(profile.path)
            if (
                health.locked
                and self.config.clone_system_profile_on_lock
                and self.config.reuse_existing_session
            ):
                clone_name = f"{_safe_name(profile.name)}-clone"
                cloned = clone_firefox_profile(profile.path, clone_name, overwrite=True)
                return cloned, f"{clone_name} (cloned)"
            return profile.path, profile.name

        profile_name = self.config.profile or "default"
        managed_profile = (BROWSER_PROFILES_DIR / _safe_name(profile_name)).resolve()
        managed_profile.mkdir(parents=True, exist_ok=True)
        return managed_profile, profile_name

    def _resolve_chrome_system_profile(self) -> tuple[Path, str]:
        """Resolve the user's real Chrome profile for system-profile mode.

        Selection order:
        1. ``browser.chrome_profile`` (a Chrome profile directory name such as
           "Default" or "Profile 1")
        2. the profile signed in with ``browser.account_email``
        3. Chrome's last-used profile
        """
        base = chrome_user_data_dir()
        if not base.is_dir():
            raise BrowserError(f"Chrome User Data directory not found: {base}")

        profile: ChromeProfile | None = None
        if self.config.chrome_profile:
            profile = get_chrome_profile(self.config.chrome_profile, root=base)
            if profile is None:
                raise BrowserError(f"Chrome profile not found: {self.config.chrome_profile}")
        if profile is None and self.config.account_email:
            profile = find_chrome_profile_by_email(self.config.account_email, root=base)
        if profile is None:
            profiles = discover_system_chrome_profiles(root=base)
            profile = next((p for p in profiles if p.is_last_used), None) or (
                profiles[0] if profiles else None
            )
        if profile is None:
            profile = ChromeProfile(dir_name="Default", display_name="Default", email=None)

        if chrome_is_running(base):
            raise BrowserError(
                "Google Chrome appears to be running with this profile. "
                "Close all Chrome windows and try again, or set "
                "browser.profile_source: managed in preferences.yaml."
            )

        self._chrome_profile_directory = profile.dir_name
        log.info(
            "chrome.system_profile_selected",
            dir_name=profile.dir_name,
            display_name=profile.display_name,
            email=profile.email,
        )
        return base, f"{profile.display_name} ({profile.dir_name})"

    def _launch_args(self) -> list[str]:
        """Extra Chromium launch args, e.g. to select a real Chrome profile."""
        if self._chrome_profile_directory:
            return [f"--profile-directory={self._chrome_profile_directory}"]
        return []


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)


class BrowserSessionManager:
    """Manages long-lived browser sessions."""
    def __init__(self) -> None:
        self._sessions: dict[str, BrowserSession] = {}

    async def get_or_create(self, session_id: str, config: BrowserConfig) -> BrowserSession:
        if session_id in self._sessions:
            return self._sessions[session_id]
        session = BrowserSession(config)
        await session.start()
        self._sessions[session_id] = session
        return session

    async def close(self, session_id: str) -> None:
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            await session.stop()

    async def close_all(self) -> None:
        for session_id in list(self._sessions.keys()):
            await self.close(session_id)

    def active_sessions(self) -> list[tuple[str, BrowserSession]]:
        return list(self._sessions.items())

_global_session_manager: BrowserSessionManager | None = None

def get_browser_session_manager() -> BrowserSessionManager:
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = BrowserSessionManager()
    return _global_session_manager



