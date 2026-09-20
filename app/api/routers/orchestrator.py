"""Unified orchestrator API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.discovery_config import JobDiscoveryConfig
from app.services.job_application_orchestrator import (
    OrchestratorRunRequest,
    OrchestratorStatus,
    get_job_application_orchestrator,
)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/status", response_model=OrchestratorStatus)
async def orchestrator_status() -> OrchestratorStatus:
    return get_job_application_orchestrator().status()


@router.post("/start", response_model=OrchestratorStatus)
async def orchestrator_start(payload: OrchestratorRunRequest) -> OrchestratorStatus:
    try:
        return await get_job_application_orchestrator().start(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/pause", response_model=OrchestratorStatus)
async def orchestrator_pause() -> OrchestratorStatus:
    return await get_job_application_orchestrator().pause()


@router.post("/resume", response_model=OrchestratorStatus)
async def orchestrator_resume() -> OrchestratorStatus:
    return await get_job_application_orchestrator().resume()


@router.post("/stop", response_model=OrchestratorStatus)
async def orchestrator_stop() -> OrchestratorStatus:
    return await get_job_application_orchestrator().stop()
