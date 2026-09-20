"""Backward-compatible facade — delegates to JobApplicationOrchestrator."""

from __future__ import annotations

from typing import Literal

from app.services.discovery_config import JobDiscoveryConfig, RemotePreference
from app.services.job_application_orchestrator import (
    OrchestratorRunRequest,
    OrchestratorStats,
    OrchestratorStatus,
    get_job_application_orchestrator,
)

JobHuntRunRequest = OrchestratorRunRequest
JobHuntStats = OrchestratorStats
JobHuntStatus = OrchestratorStatus
JobHuntStatusName = Literal["idle", "running", "paused", "stopped", "error"]


class JobHuntManager:
    """Deprecated name — use JobApplicationOrchestrator."""

    def __init__(self) -> None:
        self._inner = get_job_application_orchestrator()

    def status(self) -> JobHuntStatus:
        return self._inner.status()

    async def start(self, request: JobHuntRunRequest) -> JobHuntStatus:
        return await self._inner.start(request)

    async def pause(self) -> JobHuntStatus:
        return await self._inner.pause()

    async def resume(self) -> JobHuntStatus:
        return await self._inner.resume()

    async def stop(self) -> JobHuntStatus:
        return await self._inner.stop()


def get_job_hunt_manager() -> JobHuntManager:
    return JobHuntManager()
