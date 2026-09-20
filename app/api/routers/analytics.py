"""Analytics endpoints consumed by the frontend operations console."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.models import Application, Job, JobScoreRow

router = APIRouter(prefix="/analytics", tags=["analytics"])


class FunnelItem(BaseModel):
    stage: str
    count: int


class SourceEffectiveness(BaseModel):
    source: str
    jobs: int
    applications: int
    submitted: int
    submission_rate: float


class ScoreBucket(BaseModel):
    label: str
    min: float
    max: float
    count: int


class TimelinePoint(BaseModel):
    day: str
    jobs: int
    applications: int
    submitted: int


class AnalyticsSummary(BaseModel):
    jobs_ingested_today: int
    applications_pending_review: int
    total_jobs: int
    total_applications: int
    funnel: list[FunnelItem]
    score_distribution: list[ScoreBucket]
    source_effectiveness: list[SourceEffectiveness]
    timeline_14d: list[TimelinePoint]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(db: AsyncSession = Depends(get_db)) -> AnalyticsSummary:
    now = datetime.now(UTC)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    jobs_ingested_today = await _count_by_time(db, Job, Job.created_at, start_today)
    applications_pending_review = await _count_where(
        db, select(func.count()).select_from(Application).where(Application.status == "awaiting_review")
    )
    total_jobs = await _count_where(db, select(func.count()).select_from(Job))
    total_applications = await _count_where(db, select(func.count()).select_from(Application))

    funnel = await _build_funnel(db)
    score_distribution = await _score_distribution(db)
    source_effectiveness = await _source_effectiveness(db)
    timeline = await _timeline_last_days(db, 14)

    return AnalyticsSummary(
        jobs_ingested_today=jobs_ingested_today,
        applications_pending_review=applications_pending_review,
        total_jobs=total_jobs,
        total_applications=total_applications,
        funnel=funnel,
        score_distribution=score_distribution,
        source_effectiveness=source_effectiveness,
        timeline_14d=timeline,
    )


async def _count_by_time(
    db: AsyncSession, model: type, column, start_time: datetime
) -> int:
    stmt = select(func.count()).select_from(model).where(column >= start_time)
    return await _count_where(db, stmt)


async def _count_where(db: AsyncSession, stmt) -> int:
    result = await db.execute(stmt)
    return int(result.scalar_one() or 0)


async def _build_funnel(db: AsyncSession) -> list[FunnelItem]:
    stages = [
        "draft",
        "awaiting_review",
        "submitted",
        "interviewing",
        "offer",
        "accepted",
        "rejected",
        "withdrawn",
    ]
    out: list[FunnelItem] = []
    for stage in stages:
        count = await _count_where(
            db,
            select(func.count()).select_from(Application).where(Application.status == stage),
        )
        out.append(FunnelItem(stage=stage, count=count))
    return out


async def _score_distribution(db: AsyncSession) -> list[ScoreBucket]:
    rows = await db.execute(select(JobScoreRow.composite))
    scores = [float(v) for v in rows.scalars().all() if v is not None]

    buckets = [
        ("0.0-0.2", 0.0, 0.2),
        ("0.2-0.4", 0.2, 0.4),
        ("0.4-0.6", 0.4, 0.6),
        ("0.6-0.8", 0.6, 0.8),
        ("0.8-1.0", 0.8, 1.0),
    ]
    output: list[ScoreBucket] = []
    for label, minimum, maximum in buckets:
        if maximum < 1.0:
            count = sum(1 for score in scores if minimum <= score < maximum)
        else:
            count = sum(1 for score in scores if minimum <= score <= maximum)
        output.append(ScoreBucket(label=label, min=minimum, max=maximum, count=count))
    return output


async def _source_effectiveness(db: AsyncSession) -> list[SourceEffectiveness]:
    job_rows = await db.execute(
        select(Job.ats_source, func.count()).group_by(Job.ats_source).order_by(func.count().desc())
    )
    jobs_by_source = {str(source): int(count) for source, count in job_rows.all()}

    app_rows = await db.execute(
        select(Job.ats_source, func.count())
        .join(Application, Application.job_id == Job.id)
        .group_by(Job.ats_source)
    )
    applications_by_source = {str(source): int(count) for source, count in app_rows.all()}

    submitted_rows = await db.execute(
        select(Job.ats_source, func.count())
        .join(Application, Application.job_id == Job.id)
        .where(Application.status.in_(["submitted", "interviewing", "offer", "accepted"]))
        .group_by(Job.ats_source)
    )
    submitted_by_source = {str(source): int(count) for source, count in submitted_rows.all()}

    sources = sorted(jobs_by_source.keys())
    output: list[SourceEffectiveness] = []
    for source in sources:
        jobs = jobs_by_source.get(source, 0)
        applications = applications_by_source.get(source, 0)
        submitted = submitted_by_source.get(source, 0)
        submission_rate = (submitted / applications) if applications else 0.0
        output.append(
            SourceEffectiveness(
                source=source,
                jobs=jobs,
                applications=applications,
                submitted=submitted,
                submission_rate=round(submission_rate, 4),
            )
        )
    return output


async def _timeline_last_days(db: AsyncSession, days: int) -> list[TimelinePoint]:
    now = datetime.now(UTC)
    output: list[TimelinePoint] = []
    for offset in range(days - 1, -1, -1):
        start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        jobs = await _count_where(
            db,
            select(func.count()).select_from(Job).where(Job.created_at >= start, Job.created_at < end),
        )
        applications = await _count_where(
            db,
            select(func.count())
            .select_from(Application)
            .where(Application.created_at >= start, Application.created_at < end),
        )
        submitted = await _count_where(
            db,
            select(func.count())
            .select_from(Application)
            .where(
                Application.submitted_at.is_not(None),
                Application.submitted_at >= start,
                Application.submitted_at < end,
            ),
        )
        output.append(
            TimelinePoint(
                day=start.date().isoformat(),
                jobs=jobs,
                applications=applications,
                submitted=submitted,
            )
        )
    return output
