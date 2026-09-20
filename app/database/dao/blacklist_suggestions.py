"""DAO for blacklist suggestions."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BlacklistSuggestion


async def create(
    db: AsyncSession,
    *,
    company: str,
    job_title: str,
    reason: str,
    matched_pattern: str | None = None,
) -> BlacklistSuggestion:
    row = BlacklistSuggestion(
        company=company,
        job_title=job_title,
        reason=reason,
        matched_pattern=matched_pattern,
        status="pending",
    )
    db.add(row)
    await db.flush()
    return row


async def get_by_id(db: AsyncSession, suggestion_id: int) -> BlacklistSuggestion | None:
    return await db.get(BlacklistSuggestion, suggestion_id)


async def list_pending(db: AsyncSession, *, limit: int = 100) -> list[BlacklistSuggestion]:
    stmt = (
        select(BlacklistSuggestion)
        .where(BlacklistSuggestion.status == "pending")
        .order_by(BlacklistSuggestion.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def resolve(
    db: AsyncSession,
    suggestion: BlacklistSuggestion,
    *,
    status: str,
) -> BlacklistSuggestion:
    suggestion.status = status
    suggestion.resolved_at = datetime.now(UTC)
    await db.flush()
    return suggestion
