"""Application DAO and application event helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database.models import Application, ApplicationEvent
from app.models.enums import ApplicationMode, ApplicationStatus


async def create(
    session: AsyncSession,
    *,
    job_id: int,
    profile_snapshot: dict[str, Any],
    resume_version_id: int | None = None,
    mode: ApplicationMode = ApplicationMode.human_review,
    status: ApplicationStatus = ApplicationStatus.draft,
    source: str | None = None,
    cover_letter: str | None = None,
) -> Application:
    row = Application(
        job_id=job_id,
        resume_version_id=resume_version_id,
        profile_snapshot=profile_snapshot,
        mode=mode.value,
        status=status.value,
        source=source,
        cover_letter=cover_letter,
    )
    session.add(row)
    await session.flush()
    return row


async def get_by_id(session: AsyncSession, app_id: int) -> Application | None:
    stmt = (
        select(Application)
        .where(Application.id == app_id)
        .options(
            joinedload(Application.job),
            joinedload(Application.resume_version),
            selectinload(Application.events),
            selectinload(Application.answers),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_applications(
    session: AsyncSession,
    *,
    status: ApplicationStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Application]:
    stmt = (
        select(Application)
        .options(joinedload(Application.job))
        .order_by(Application.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(Application.status == status.value)
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_status(
    session: AsyncSession,
    app_id: int,
    status: ApplicationStatus,
    *,
    confirmation_text: str | None = None,
) -> Application | None:
    row = await get_by_id(session, app_id)
    if row is None:
        return None
    row.status = status.value
    if status == ApplicationStatus.submitted and row.submitted_at is None:
        row.submitted_at = datetime.now(UTC)
    if confirmation_text is not None:
        row.confirmation_text = confirmation_text
    return row


async def add_event(
    session: AsyncSession,
    app_id: int,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> ApplicationEvent:
    event = ApplicationEvent(application_id=app_id, event_type=event_type, payload=payload)
    session.add(event)
    await session.flush()
    return event
