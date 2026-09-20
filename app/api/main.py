"""FastAPI app entry point."""

from __future__ import annotations

from app.utils.event_loop import configure_event_loop

configure_event_loop()

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    ai_activity,
    analytics,
    applications,
    approvals,
    automation,
    blacklist_api,
    browser,
    control_center,
    orchestrator,
    jobs,
    profile,
    resumes,
    runtime_api,
    scoring,
    settings,
    sources,
    status,
    ws,
)
from app.api.routers.ws import event_bus_to_ws, manager as ws_manager
from app.database.engine import init_db
from app.runtime.automation_runtime import get_automation_runtime
from app.runtime.discovery_scheduler import get_discovery_scheduler
from app.services.event_bus import get_event_bus
from app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)

_ws_ping_task: asyncio.Task[None] | None = None
_live_screenshot_task: asyncio.Task[None] | None = None


async def _live_screenshot_loop() -> None:
    """Periodic screenshots for Live Browser when a session is active."""
    from app.automation.browser import get_browser_session_manager
    from app.runtime.automation_runtime import get_automation_runtime

    while True:
        await asyncio.sleep(8)
        runtime = get_automation_runtime()
        if runtime.state == "stopped":
            continue
        for _sid, session in get_browser_session_manager().active_sessions():
            try:
                pages = session.context.pages
                if not pages:
                    continue
                page = pages[-1]
                await session.screenshot(page, "live_telemetry")
            except Exception:
                pass


async def _ws_ping_loop() -> None:
    while True:
        await asyncio.sleep(30)
        await ws_manager.broadcast(json.dumps({"type": "ping", "payload": {}}))


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    global _ws_ping_task, _live_screenshot_task
    configure_logging()
    await init_db()
    bus = get_event_bus()
    bus.subscribe(event_bus_to_ws)
    _ws_ping_task = asyncio.create_task(_ws_ping_loop())
    _live_screenshot_task = asyncio.create_task(_live_screenshot_loop())
    log.info("api.startup")
    try:
        yield
    finally:
        for task in (_ws_ping_task, _live_screenshot_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        _ws_ping_task = None
        _live_screenshot_task = None
        bus.unsubscribe(event_bus_to_ws)
        await get_discovery_scheduler().stop()
        await get_automation_runtime().shutdown()
        log.info("api.shutdown")


app = FastAPI(
    title="Job Finding Assistant",
    description="Supervised AI job application agent — inspection and control API.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(resumes.router)
app.include_router(profile.router)
app.include_router(scoring.router)
app.include_router(settings.router)
app.include_router(automation.router)
app.include_router(runtime_api.router)
app.include_router(ai_activity.router)
app.include_router(analytics.router)
app.include_router(browser.router)
app.include_router(control_center.router)
app.include_router(orchestrator.router)
app.include_router(approvals.router)
app.include_router(sources.router)
app.include_router(blacklist_api.router)
app.include_router(ws.router)
