"""JobScore DAO."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import JobScoreRow
from app.models.scoring import JobScore


async def create(session: AsyncSession, score: JobScore, *, composite: float) -> JobScoreRow:
    row = JobScoreRow(
        job_id=score.job_id,
        fit_score=score.fit_score,
        salary_fit=score.salary_fit,
        skill_overlap=score.skill_overlap,
        seniority_alignment=score.seniority_alignment,
        location_compatibility=score.location_compatibility,
        confidence=score.confidence,
        composite=composite,
        rationale=score.rationale,
        matched_skills=list(score.matched_skills),
        missing_skills=list(score.missing_skills),
        model_used=score.model_used,
    )
    session.add(row)
    await session.flush()
    return row


async def latest_for_job(session: AsyncSession, job_id: int) -> JobScoreRow | None:
    result = await session.execute(
        select(JobScoreRow)
        .where(JobScoreRow.job_id == job_id)
        .order_by(JobScoreRow.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
