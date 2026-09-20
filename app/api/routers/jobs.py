"""``/jobs`` routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.dao import jobs as jobs_dao
from app.database.models import Application, ApplicationEvent, JobScoreRow, ResumeVersion

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSummary(BaseModel):
    id: int
    title: str
    company: str
    location: str | None
    ats_source: str
    status: str
    source_url: str
    created_at: str
    latest_score: float | None
    resume_versions: int
    applications_count: int


class JobDetail(JobSummary):
    description_text: str
    salary_min: int | None
    salary_max: int | None
    salary_currency: str


class JobWorkspace(BaseModel):
    job: JobDetail
    latest_score: dict[str, float | str | list[str] | None] | None
    resume_versions: list[dict[str, str | int | None]]
    applications: list[dict[str, str | int | None]]
    recent_events: list[dict[str, str | int | None]]
    extracted_keywords: list[str]


@router.get("", response_model=list[JobSummary])
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[JobSummary]:
    rows = await jobs_dao.list_jobs(db, limit=limit, offset=offset, status=status)
    payload: list[JobSummary] = []
    for row in rows:
        score_row = await db.execute(
            select(JobScoreRow.composite)
            .where(JobScoreRow.job_id == row.id)
            .order_by(desc(JobScoreRow.created_at))
            .limit(1)
        )
        resumes_row = await db.execute(
            select(func.count()).select_from(ResumeVersion).where(ResumeVersion.job_id == row.id)
        )
        apps_row = await db.execute(
            select(func.count()).select_from(Application).where(Application.job_id == row.id)
        )
        payload.append(
            JobSummary(
                id=row.id,
                title=row.title,
                company=row.company.name,
                location=row.location,
                ats_source=row.ats_source,
                status=row.status,
                source_url=row.source_url,
                created_at=row.created_at.isoformat(),
                latest_score=score_row.scalar_one_or_none(),
                resume_versions=int(resumes_row.scalar_one() or 0),
                applications_count=int(apps_row.scalar_one() or 0),
            )
        )
    return payload


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)) -> JobDetail:
    row = await jobs_dao.get_by_id(db, job_id)
    if row is None:
        raise HTTPException(404, f"Job {job_id} not found")
    return JobDetail(
        id=row.id,
        title=row.title,
        company=row.company.name,
        location=row.location,
        ats_source=row.ats_source,
        status=row.status,
        source_url=row.source_url,
        created_at=row.created_at.isoformat(),
        latest_score=None,
        resume_versions=0,
        applications_count=0,
        description_text=row.description_text,
        salary_min=row.salary_min,
        salary_max=row.salary_max,
        salary_currency=row.salary_currency,
    )


@router.get("/{job_id}/workspace", response_model=JobWorkspace)
async def get_job_workspace(job_id: int, db: AsyncSession = Depends(get_db)) -> JobWorkspace:
    row = await jobs_dao.get_by_id(db, job_id)
    if row is None:
        raise HTTPException(404, f"Job {job_id} not found")

    score_row = await db.execute(
        select(JobScoreRow)
        .where(JobScoreRow.job_id == job_id)
        .order_by(desc(JobScoreRow.created_at))
        .limit(1)
    )
    score = score_row.scalar_one_or_none()

    resume_rows = await db.execute(
        select(ResumeVersion)
        .where(ResumeVersion.job_id == job_id)
        .order_by(desc(ResumeVersion.created_at))
        .limit(10)
    )
    app_rows = await db.execute(
        select(Application)
        .where(Application.job_id == job_id)
        .order_by(desc(Application.created_at))
        .limit(20)
    )
    event_rows = await db.execute(
        select(ApplicationEvent)
        .join(Application, Application.id == ApplicationEvent.application_id)
        .where(Application.job_id == job_id)
        .order_by(desc(ApplicationEvent.created_at))
        .limit(50)
    )

    description = row.description_text or ""
    keywords = _extract_keywords(description, top_k=24)
    return JobWorkspace(
        job=JobDetail(
            id=row.id,
            title=row.title,
            company=row.company.name,
            location=row.location,
            ats_source=row.ats_source,
            status=row.status,
            source_url=row.source_url,
            created_at=row.created_at.isoformat(),
            latest_score=None,
            resume_versions=0,
            applications_count=0,
            description_text=row.description_text,
            salary_min=row.salary_min,
            salary_max=row.salary_max,
            salary_currency=row.salary_currency,
        ),
        latest_score=(
            {
                "fit_score": score.fit_score,
                "salary_fit": score.salary_fit,
                "skill_overlap": score.skill_overlap,
                "seniority_alignment": score.seniority_alignment,
                "location_compatibility": score.location_compatibility,
                "confidence": score.confidence,
                "composite": score.composite,
                "rationale": score.rationale,
                "matched_skills": score.matched_skills,
                "missing_skills": score.missing_skills,
                "model_used": score.model_used,
                "created_at": score.created_at.isoformat(),
            }
            if score is not None
            else None
        ),
        resume_versions=[
            {
                "id": resume.id,
                "template": resume.template,
                "kind": resume.kind,
                "docx_path": resume.docx_path,
                "pdf_path": resume.pdf_path,
                "created_at": resume.created_at.isoformat(),
            }
            for resume in resume_rows.scalars().all()
        ],
        applications=[
            {
                "id": application.id,
                "status": application.status,
                "mode": application.mode,
                "source": application.source,
                "cover_letter": application.cover_letter,
                "submitted_at": (
                    application.submitted_at.isoformat() if application.submitted_at else None
                ),
                "created_at": application.created_at.isoformat(),
            }
            for application in app_rows.scalars().all()
        ],
        recent_events=[
            {
                "id": event.id,
                "application_id": event.application_id,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
            }
            for event in event_rows.scalars().all()
        ],
        extracted_keywords=keywords,
    )


def _extract_keywords(text: str, *, top_k: int) -> list[str]:
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "you",
        "your",
        "our",
        "that",
        "this",
        "will",
        "have",
        "are",
        "from",
        "into",
        "about",
        "able",
        "team",
        "work",
        "role",
        "job",
    }
    tokens: dict[str, int] = {}
    for raw in text.lower().split():
        token = "".join(ch for ch in raw if ch.isalnum() or ch in {"#", "+", "."})
        if len(token) < 3 or token in stopwords:
            continue
        tokens[token] = tokens.get(token, 0) + 1
    sorted_tokens = sorted(tokens.items(), key=lambda item: item[1], reverse=True)
    return [token for token, _ in sorted_tokens[:top_k]]
