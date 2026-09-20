"""Central automation runtime: pause/stop, manual control, browser sessions."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.automation.browser import BrowserSession, get_browser_session_manager
from app.config.loader import load_config
from app.config.schema import BrowserConfig
from app.services.event_bus import get_event_bus
from app.utils.logging import get_logger

log = get_logger(__name__)

AutomationState = Literal["idle", "running", "paused", "stopped", "manual_control"]


class QueuedAction(BaseModel):
    id: str
    action: str
    detail: str | None = None
    created_at: str


class BrowserActionLog(BaseModel):
    action: str
    detail: str | None = None
    url: str | None = None
    timestamp: str


class RuntimeSnapshot(BaseModel):
    state: AutomationState = "idle"
    pause_all: bool = False
    current_url: str | None = None
    current_title: str | None = None
    current_task: str | None = None
    current_form_step: str | None = None
    session_id: str | None = None
    application_id: int | None = None
    last_screenshot: str | None = None
    last_error: str | None = None
    ai_summary: str | None = None
    queued_actions: list[QueuedAction] = Field(default_factory=list)
    recent_actions: list[BrowserActionLog] = Field(default_factory=list)
    pending_approval_count: int = 0


class AutomationRuntime:
    """In-process controller for supervised browser automation."""

    def __init__(self) -> None:
        self._state: AutomationState = "idle"
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._pause_all = False
        self._stop_requested = False
        self._session_id: str | None = None
        self._application_id: int | None = None
        self._current_url: str | None = None
        self._current_title: str | None = None
        self._current_task: str | None = None
        self._current_form_step: str | None = None
        self._last_screenshot: str | None = None
        self._last_error: str | None = None
        self._ai_summary: str | None = None
        self._queued: list[QueuedAction] = []
        self._action_log: deque[BrowserActionLog] = deque(maxlen=100)
        self._action_counter = 0
        self._pending_actions: dict[str, asyncio.Event] = {}
        self._action_results: dict[str, bool] = {}

    @property
    def state(self) -> AutomationState:
        return self._state

    def snapshot(self, *, pending_approval_count: int = 0) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            state=self._state,
            pause_all=self._pause_all,
            current_url=self._current_url,
            current_title=self._current_title,
            current_task=self._current_task,
            current_form_step=self._current_form_step,
            session_id=self._session_id,
            application_id=self._application_id,
            last_screenshot=self._last_screenshot,
            last_error=self._last_error,
            ai_summary=self._ai_summary,
            queued_actions=list(self._queued),
            recent_actions=list(self._action_log),
            pending_approval_count=pending_approval_count,
        )

    def _emit_state(self) -> None:
        get_event_bus().emit("automation.state", self.snapshot().model_dump(mode="json"))

    async def await_ready(self) -> bool:
        """Wait until automation may proceed. Returns False if stopped."""
        if self._stop_requested:
            return False
        if self._pause_all or self._state == "paused":
            await self._pause_event.wait()
        return not self._stop_requested

    async def get_browser_session(
        self,
        session_id: str | None = None,
        *,
        application_id: int | None = None,
        config: BrowserConfig | None = None,
    ) -> BrowserSession:
        if self._state == "manual_control":
            raise RuntimeError("Cannot acquire browser while in manual control from another caller")
        cfg = config or load_config().preferences.browser
        sid = session_id or self._session_id or "default"
        self._session_id = sid
        if application_id is not None:
            self._application_id = application_id
        manager = get_browser_session_manager()
        session = await manager.get_or_create(sid, cfg)
        if self._state == "idle":
            self._state = "running"
            self._emit_state()
        return session

    def update_browser_context(
        self,
        *,
        url: str | None = None,
        title: str | None = None,
        task: str | None = None,
        form_step: str | None = None,
        screenshot_path: str | None = None,
        ai_summary: str | None = None,
        error: str | None = None,
    ) -> None:
        if url is not None:
            self._current_url = url
        if title is not None:
            self._current_title = title
        if task is not None:
            self._current_task = task
        if form_step is not None:
            self._current_form_step = form_step
        if screenshot_path is not None:
            self._last_screenshot = screenshot_path
        if ai_summary is not None:
            self._ai_summary = ai_summary
        if error is not None:
            self._last_error = error

    def log_action(self, action: str, *, detail: str | None = None, url: str | None = None) -> None:
        entry = BrowserActionLog(
            action=action,
            detail=detail,
            url=url or self._current_url,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._action_log.append(entry)
        get_event_bus().emit("browser.action", entry.model_dump(mode="json"))

    def queue_action(self, action: str, detail: str | None = None) -> str:
        self._action_counter += 1
        action_id = f"action_{self._action_counter}"
        queued = QueuedAction(
            id=action_id,
            action=action,
            detail=detail,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._queued.append(queued)
        get_event_bus().emit(
            "automation.action_queued",
            {"id": action_id, "action": action, "detail": detail},
        )
        return action_id

    async def pause_ai(self) -> RuntimeSnapshot:
        self._state = "paused"
        self._pause_event.clear()
        log.info("automation.paused")
        self._emit_state()
        return self.snapshot()

    async def resume_ai(self) -> RuntimeSnapshot:
        if self._state == "manual_control":
            raise RuntimeError("Resume AI after returning from manual control")
        self._state = "running"
        self._pause_event.set()
        log.info("automation.resumed")
        self._emit_state()
        return self.snapshot()

    async def stop_ai(self) -> RuntimeSnapshot:
        self._stop_requested = True
        self._state = "stopped"
        self._pause_event.set()
        await get_browser_session_manager().close_all()
        self._session_id = None
        log.info("automation.stopped")
        self._emit_state()
        return self.snapshot()

    async def pause_all_automation(self) -> RuntimeSnapshot:
        self._pause_all = True
        self._pause_event.clear()
        self._emit_state()
        return self.snapshot()

    async def resume_all_automation(self) -> RuntimeSnapshot:
        self._pause_all = False
        if self._state not in ("stopped", "manual_control"):
            self._pause_event.set()
        self._emit_state()
        return self.snapshot()

    async def enter_manual_control(self, session_id: str | None = None) -> RuntimeSnapshot:
        await self.pause_ai()
        self._state = "manual_control"
        if session_id:
            self._session_id = session_id
        log.info("automation.manual_control", session_id=self._session_id)
        self._emit_state()
        return self.snapshot()

    async def return_control_to_ai(self) -> RuntimeSnapshot:
        if self._state != "manual_control":
            return self.snapshot()
        self._stop_requested = False
        self._state = "running"
        self._pause_event.set()
        log.info("automation.ai_resumed")
        self._emit_state()
        return self.snapshot()

    def approve_action(self, action_id: str) -> bool:
        if action_id in self._pending_actions:
            self._action_results[action_id] = True
            self._pending_actions[action_id].set()
            return True
        self._queued = [q for q in self._queued if q.id != action_id]
        get_event_bus().emit("automation.action_approved", {"id": action_id})
        return True

    def reject_action(self, action_id: str) -> bool:
        if action_id in self._pending_actions:
            self._action_results[action_id] = False
            self._pending_actions[action_id].set()
            return True
        self._queued = [q for q in self._queued if q.id != action_id]
        get_event_bus().emit("automation.action_rejected", {"id": action_id})
        return True

    def reset_for_new_run(self) -> None:
        self._stop_requested = False
        self._pause_all = False
        self._state = "idle"
        self._pause_event.set()
        self._queued.clear()
        self._last_error = None

    async def shutdown(self) -> None:
        await self.stop_ai()


_runtime: AutomationRuntime | None = None


def get_automation_runtime() -> AutomationRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AutomationRuntime()
    return _runtime
