"""
Jobs routes
- List discovered jobs (with optional match score)
- Trigger manual job discovery
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.common import JobOut
from app.core.dependencies import get_current_user
from app.workers.tasks import run_job_discovery

router = APIRouter()


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    source: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated discovered job listings."""
    query = select(Job).where(Job.is_active == True).order_by(desc(Job.discovered_at))
    if source:
        query = query.where(Job.source == source)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/discover", status_code=202)
async def trigger_discovery(current_user: User = Depends(get_current_user)):
    """Manually trigger the job-discovery Celery task (admin / testing)."""
    task = run_job_discovery.delay()
    return {"message": "Job discovery started", "task_id": task.id}
