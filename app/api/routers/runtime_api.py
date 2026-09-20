"""Automation runtime control and telemetry API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config.paths import SCREENSHOTS_DIR
from app.runtime.automation_runtime import RuntimeSnapshot, get_automation_runtime
from app.runtime.discovery_scheduler import DiscoverySchedulerStatus, get_discovery_scheduler
from app.services.approval_service import get_approval_service

router = APIRouter(prefix="/automation/runtime", tags=["automation-runtime"])


@router.get("", response_model=RuntimeSnapshot)
async def get_runtime_snapshot() -> RuntimeSnapshot:
    pending = await get_approval_service().pending_count()
    return get_automation_runtime().snapshot(pending_approval_count=pending)


@router.post("/pause")
async def pause_ai() -> RuntimeSnapshot:
    return await get_automation_runtime().pause_ai()


@router.post("/resume")
async def resume_ai() -> RuntimeSnapshot:
    return await get_automation_runtime().resume_ai()


@router.post("/stop")
async def stop_ai() -> RuntimeSnapshot:
    return await get_automation_runtime().stop_ai()


@router.post("/pause-all")
async def pause_all() -> RuntimeSnapshot:
    await get_discovery_scheduler().pause()
    return await get_automation_runtime().pause_all_automation()


@router.post("/resume-all")
async def resume_all() -> RuntimeSnapshot:
    await get_discovery_scheduler().resume()
    return await get_automation_runtime().resume_all_automation()


@router.post("/manual-control")
async def manual_control(session_id: str | None = None) -> RuntimeSnapshot:
    return await get_automation_runtime().enter_manual_control(session_id)


@router.post("/return-to-ai")
async def return_to_ai() -> RuntimeSnapshot:
    return await get_automation_runtime().return_control_to_ai()


@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str) -> dict[str, bool]:
    return {"ok": get_automation_runtime().approve_action(action_id)}


@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str) -> dict[str, bool]:
    return {"ok": get_automation_runtime().reject_action(action_id)}


@router.get("/discovery/status", response_model=DiscoverySchedulerStatus)
async def discovery_status() -> DiscoverySchedulerStatus:
    return get_discovery_scheduler().status()


@router.get("/screenshots/{filename}")
async def get_screenshot(filename: str) -> FileResponse:
    safe = Path(filename).name
    path = SCREENSHOTS_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(path, media_type="image/png")
