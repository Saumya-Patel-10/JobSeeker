"""``/scoring`` routes — fetch latest score or trigger a rescore."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.dao import job_scores as scores_dao
from app.pipelines.score_pipeline import score_existing_job

router = APIRouter(prefix="/scoring", tags=["scoring"])


class ScoreView(BaseModel):
    job_id: int
    fit_score: float
    salary_fit: float
    skill_overlap: float
    seniority_alignment: float
    location_compatibility: float
    confidence: float
    composite: float
    rationale: str
    matched_skills: list[str]
    missing_skills: list[str]
    model_used: str
    created_at: str


@router.get("/{job_id}", response_model=ScoreView)
async def latest(job_id: int, db: AsyncSession = Depends(get_db)) -> ScoreView:
    row = await scores_dao.latest_for_job(db, job_id)
    if row is None:
        raise HTTPException(404, f"No score recorded for job {job_id}")
    return ScoreView(
        job_id=row.job_id,
        fit_score=row.fit_score,
        salary_fit=row.salary_fit,
        skill_overlap=row.skill_overlap,
        seniority_alignment=row.seniority_alignment,
        location_compatibility=row.location_compatibility,
        confidence=row.confidence,
        composite=row.composite,
        rationale=row.rationale,
        matched_skills=row.matched_skills or [],
        missing_skills=row.missing_skills or [],
        model_used=row.model_used,
        created_at=row.created_at.isoformat(),
    )


@router.post("/{job_id}/rescore", response_model=ScoreView)
async def rescore(job_id: int, db: AsyncSession = Depends(get_db)) -> ScoreView:
    await score_existing_job(job_id)
    row = await scores_dao.latest_for_job(db, job_id)
    if row is None:
        raise HTTPException(500, "Rescore did not produce a row")
    return ScoreView(
        job_id=row.job_id,
        fit_score=row.fit_score,
        salary_fit=row.salary_fit,
        skill_overlap=row.skill_overlap,
        seniority_alignment=row.seniority_alignment,
        location_compatibility=row.location_compatibility,
        confidence=row.confidence,
        composite=row.composite,
        rationale=row.rationale,
        matched_skills=row.matched_skills or [],
        missing_skills=row.missing_skills or [],
        model_used=row.model_used,
        created_at=row.created_at.isoformat(),
    )
