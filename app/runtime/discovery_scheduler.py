"""Background discovery polling — not frontend timers."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.config.loader import load_config
from app.runtime.automation_runtime import get_automation_runtime
from app.services.event_bus import get_event_bus
from app.services.discovery_config import JobDiscoveryConfig
from app.utils.logging import get_logger

log = get_logger(__name__)

DiscoverySchedulerState = Literal["idle", "running", "paused", "stopped"]


class SourceRuntimeStatus(BaseModel):
    name: str
    enabled: bool
    last_poll_at: str | None = None
    jobs_discovered: int = 0
    ingestion_failures: int = 0
    auth_status: str = "unknown"
    rate_limit_until: str | None = None
    health_status: str = "unknown"
    last_error: str | None = None


class DiscoverySchedulerStatus(BaseModel):
    status: DiscoverySchedulerState = "idle"
    interval_minutes: int = 30
    last_run_at: str | None = None
    sources: list[SourceRuntimeStatus] = Field(default_factory=list)
    total_urls_found: int = 0
    total_ingested: int = 0


class DiscoveryScheduler:
    def __init__(self) -> None:
        self._status: DiscoverySchedulerState = "idle"
        self._task: asyncio.Task[None] | None = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._interval_minutes = 30
        self._last_run_at: datetime | None = None
        self._source_status: dict[str, SourceRuntimeStatus] = {}
        self._discovery = JobDiscoveryConfig()
        self._total_urls = 0
        self._total_ingested = 0

    def status(self) -> DiscoverySchedulerStatus:
        return DiscoverySchedulerStatus(
            status=self._status,
            interval_minutes=self._interval_minutes,
            last_run_at=self._last_run_at.isoformat() if self._last_run_at else None,
            sources=list(self._source_status.values()),
            total_urls_found=self._total_urls,
            total_ingested=self._total_ingested,
        )

    def _emit(self) -> None:
        get_event_bus().emit("discovery.status", self.status().model_dump(mode="json"))

    async def start(
        self,
        *,
        interval_minutes: int | None = None,
        discovery: JobDiscoveryConfig | None = None,
    ) -> DiscoverySchedulerStatus:
        if self._task and not self._task.done():
            if self._status == "paused":
                return await self.resume()
            return self.status()

        config = load_config()
        self._interval_minutes = (
            interval_minutes or config.preferences.automation.default_interval_minutes
        )
        if discovery:
            self._discovery = discovery
        self._stop_requested = False
        self._status = "running"
        self._pause_event.set()
        self._task = asyncio.create_task(self._loop())
        log.info("discovery.started", interval_minutes=self._interval_minutes)
        self._emit()
        return self.status()

    async def pause(self) -> DiscoverySchedulerStatus:
        self._status = "paused"
        self._pause_event.clear()
        log.info("discovery.paused")
        self._emit()
        return self.status()

    async def resume(self) -> DiscoverySchedulerStatus:
        if self._status != "paused":
            return self.status()
        self._status = "running"
        self._pause_event.set()
        log.info("discovery.resumed")
        self._emit()
        return self.status()

    async def stop(self) -> DiscoverySchedulerStatus:
        self._stop_requested = True
        self._status = "stopped"
        self._pause_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        log.info("discovery.stopped")
        self._emit()
        return self.status()

    async def run_once(self, discovery: JobDiscoveryConfig | None = None) -> dict[str, Any]:
        if discovery:
            self._discovery = discovery
        return await self._execute_poll()

    async def _loop(self) -> None:
        try:
            while not self._stop_requested:
                await self._pause_event.wait()
                if self._stop_requested:
                    break
                runtime = get_automation_runtime()
                if not await runtime.await_ready():
                    break
                await self._execute_poll()
                if self._stop_requested:
                    break
                await asyncio.sleep(self._interval_minutes * 60)
        except asyncio.CancelledError:
            pass
        finally:
            if self._status == "running":
                self._status = "idle"
                self._emit()

    async def _execute_poll(self) -> dict[str, Any]:
        from app.services.source_orchestrator import get_source_orchestrator

        self._last_run_at = datetime.now(UTC)
        orchestrator = get_source_orchestrator()
        result = await orchestrator.poll_all(self._discovery)
        self._total_urls += result.get("urls_found", 0)
        self._total_ingested += result.get("ingested", 0)

        for name, src_status in result.get("sources", {}).items():
            self._source_status[name] = SourceRuntimeStatus(**src_status)

        get_event_bus().emit("discovery.poll_complete", result)
        self._emit()
        return result


_scheduler: DiscoveryScheduler | None = None


def get_discovery_scheduler() -> DiscoveryScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = DiscoveryScheduler()
    return _scheduler
