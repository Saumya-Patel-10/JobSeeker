"""Internal event bus for real-time state broadcasting."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from app.utils.logging import get_logger

log = get_logger(__name__)

EventCallback = Callable[[str, dict[str, Any]], None]
AsyncEventCallback = Callable[[str, dict[str, Any]], asyncio.Future[None] | None]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[AsyncEventCallback] = []
        self._background_tasks: set[asyncio.Task[None]] = set()

    def subscribe(self, callback: AsyncEventCallback) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: AsyncEventCallback) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """Emits an event to all subscribers without waiting for them to finish."""
        for sub in self._subscribers:
            try:
                res = sub(event_type, payload)
                if asyncio.iscoroutine(res):
                    task = asyncio.create_task(res)
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
            except Exception as exc:
                log.error("event_bus.emit_failed", event_type=event_type, error=str(exc))

_global_bus: EventBus | None = None

def get_event_bus() -> EventBus:
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus
