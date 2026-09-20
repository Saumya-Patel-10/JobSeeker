"""Automation monitor endpoints for browser execution visibility."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config.paths import SCREENSHOTS_DIR
from app.database.models import Application, ApplicationEvent, Job

router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationEventView(BaseModel):
    id: int
    application_id: int
    job_id: int | None
    job_title: str | None
    event_type: str
    payload: dict[str, Any] | None
    created_at: str


class ScreenshotView(BaseModel):
    name: str
    path: str
    modified_at: str
    size_bytes: int


class AutomationSessionView(BaseModel):
    application_id: int
    job_id: int
    job_title: str | None
    status: str
    mode: str
    updated_at: str
    latest_event: str | None


class AutomationOverview(BaseModel):
    active_sessions: int
    pending_review: int
    recent_sessions: list[AutomationSessionView]
    recent_events: list[AutomationEventView]
    recent_screenshots: list[ScreenshotView]


@router.get("/overview", response_model=AutomationOverview)
async def get_overview(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> AutomationOverview:
    recent_sessions = await _recent_sessions(db, limit=limit)
    recent_events = await _recent_events(db, limit=limit)
    recent_screenshots = _recent_screenshots(limit=limit)

    active_sessions = sum(
        1 for session in recent_sessions if session.status in {"draft", "awaiting_review"}
    )
    pending_review = sum(1 for session in recent_sessions if session.status == "awaiting_review")
    return AutomationOverview(
        active_sessions=active_sessions,
        pending_review=pending_review,
        recent_sessions=recent_sessions,
        recent_events=recent_events,
        recent_screenshots=recent_screenshots,
    )


@router.get("/sessions", response_model=list[AutomationSessionView])
async def list_sessions(limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[AutomationSessionView]:
    return await _recent_sessions(db, limit=limit)


@router.get("/events", response_model=list[AutomationEventView])
async def list_events(
    application_id: int | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[AutomationEventView]:
    return await _recent_events(db, application_id=application_id, limit=limit)


@router.get("/screenshots", response_model=list[ScreenshotView])
async def list_screenshots(limit: int = 100) -> list[ScreenshotView]:
    return _recent_screenshots(limit=limit)


async def _recent_sessions(db: AsyncSession, *, limit: int) -> list[AutomationSessionView]:
    window_start = datetime.now(UTC) - timedelta(days=30)
    rows = await db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.updated_at >= window_start)
        .order_by(desc(Application.updated_at))
        .limit(limit)
    )
    sessions: list[AutomationSessionView] = []
    for app, job in rows.all():
        latest_event = await db.execute(
            select(ApplicationEvent.event_type)
            .where(ApplicationEvent.application_id == app.id)
            .order_by(desc(ApplicationEvent.created_at))
            .limit(1)
        )
        sessions.append(
            AutomationSessionView(
                application_id=app.id,
                job_id=app.job_id,
                job_title=job.title if job else None,
                status=app.status,
                mode=app.mode,
                updated_at=app.updated_at.isoformat(),
                latest_event=latest_event.scalar_one_or_none(),
            )
        )
    return sessions


async def _recent_events(
    db: AsyncSession,
    *,
    application_id: int | None = None,
    limit: int,
) -> list[AutomationEventView]:
    stmt = (
        select(ApplicationEvent, Application.job_id, Job.title)
        .join(Application, Application.id == ApplicationEvent.application_id)
        .join(Job, Job.id == Application.job_id)
        .order_by(desc(ApplicationEvent.created_at))
        .limit(limit)
    )
    if application_id is not None:
        stmt = stmt.where(ApplicationEvent.application_id == application_id)
    rows = await db.execute(stmt)
    return [
        AutomationEventView(
            id=event.id,
            application_id=event.application_id,
            job_id=job_id,
            job_title=job_title,
            event_type=event.event_type,
            payload=event.payload,
            created_at=event.created_at.isoformat(),
        )
        for event, job_id, job_title in rows.all()
    ]


def _recent_screenshots(*, limit: int) -> list[ScreenshotView]:
    if not SCREENSHOTS_DIR.exists():
        return []
    files = [entry for entry in SCREENSHOTS_DIR.iterdir() if entry.is_file()]
    files.sort(key=lambda file: file.stat().st_mtime, reverse=True)
    output: list[ScreenshotView] = []
    for file in files[:limit]:
        stat = file.stat()
        output.append(
            ScreenshotView(
                name=file.name,
                path=str(file),
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                size_bytes=stat.st_size,
            )
        )
    return output
