"""Job source health and configuration API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.source_orchestrator import get_source_orchestrator

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceHealthView(BaseModel):
    name: str
    type: str
    enabled: bool
    health_status: str
    message: str
    authenticated: bool | None = None
    rate_limit_until: str | None = None


@router.get("", response_model=list[SourceHealthView])
async def list_source_health() -> list[SourceHealthView]:
    rows = await get_source_orchestrator().health_all()
    return [SourceHealthView(**row) for row in rows]
