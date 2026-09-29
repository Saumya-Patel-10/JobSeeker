"""
Applications routes
- POST /  → queue a new application (checks credits → sends to Celery)
- GET /   → list user's applications
- GET /{id} → application detail
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.common import ApplicationCreate, ApplicationOut
from app.core.dependencies import get_current_user
from app.workers.tasks import process_application

router = APIRouter()


@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_202_ACCEPTED)
async def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Queue an automated job application.
    Checks the user's daily credit before enqueuing.
    """
    # ── Credit check (middleware logic) ───────────────────────────────────────
    if current_user.daily_apps_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily limit reached for {current_user.plan_type.value} plan. "
                "Upgrade your plan or wait until tomorrow."
            ),
        )

    # Validate job exists
    job_result = await db.execute(select(Job).where(Job.id == payload.job_id, Job.is_active == True))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate resume belongs to user
    resume_result = await db.execute(
        select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == current_user.id)
    )
    if not resume_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Resume not found")

    # Prevent duplicate applications
    dup = await db.execute(
        select(Application).where(
            Application.user_id == current_user.id,
            Application.job_id == payload.job_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already applied to this job")

    # ── Create application record ──────────────────────────────────────────────
    app_record = Application(
        user_id=current_user.id,
        job_id=payload.job_id,
        resume_id=payload.resume_id,
        status=ApplicationStatus.QUEUED,
    )
    db.add(app_record)

    # Deduct one credit
    current_user.daily_apps_remaining -= 1

    await db.commit()
    await db.refresh(app_record)

    # ── Dispatch to Celery ────────────────────────────────────────────────────
    task = process_application.apply_async(
        args=[app_record.id, current_user.id],
        queue="ai_queue",
    )
    app_record.celery_task_id = task.id
    await db.commit()
    await db.refresh(app_record)

    return app_record


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(desc(Application.created_at))
    )
    return result.scalars().all()


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app
