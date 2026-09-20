"""DAO for approval checkpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApprovalCheckpoint


async def create(
    db: AsyncSession,
    *,
    application_id: int,
    job_id: int,
    checkpoint_type: str,
    confidence: float | None = None,
    resume_version_id: int | None = None,
    ai_summary: str | None = None,
    risks: list[str] | None = None,
    generated_answers: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> ApprovalCheckpoint:
    row = ApprovalCheckpoint(
        application_id=application_id,
        job_id=job_id,
        checkpoint_type=checkpoint_type,
        status="pending",
        confidence=confidence,
        resume_version_id=resume_version_id,
        ai_summary=ai_summary,
        risks=risks or [],
        generated_answers=generated_answers,
        payload=payload,
    )
    db.add(row)
    await db.flush()
    return row


async def get_by_id(db: AsyncSession, checkpoint_id: int) -> ApprovalCheckpoint | None:
    return await db.get(ApprovalCheckpoint, checkpoint_id)


async def list_pending(db: AsyncSession, *, limit: int = 100) -> list[ApprovalCheckpoint]:
    stmt = (
        select(ApprovalCheckpoint)
        .where(ApprovalCheckpoint.status == "pending")
        .order_by(ApprovalCheckpoint.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_pending(db: AsyncSession) -> int:
    from sqlalchemy import func

    stmt = select(func.count()).select_from(ApprovalCheckpoint).where(
        ApprovalCheckpoint.status == "pending"
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def resolve(
    db: AsyncSession,
    checkpoint: ApprovalCheckpoint,
    *,
    status: str,
    resolved_by: str = "user",
) -> ApprovalCheckpoint:
    checkpoint.status = status
    checkpoint.resolved_at = datetime.now(UTC)
    checkpoint.resolved_by = resolved_by
    await db.flush()
    return checkpoint
