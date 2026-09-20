"""``/applications`` routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.dao import applications as apps_dao
from app.models.enums import ApplicationStatus

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationSummary(BaseModel):
    id: int
    job_id: int
    job_title: str | None
    status: str
    mode: str
    submitted_at: str | None
    created_at: str


class ApplicationDetail(ApplicationSummary):
    source: str | None
    notes: str | None
    recruiter_name: str | None
    recruiter_email: str | None
    cover_letter: str | None
    confirmation_text: str | None
    events: list[dict[str, str | int | dict[str, str] | None]]
    generated_answers: list[dict[str, str | int | bool | None]]


class StatusUpdate(BaseModel):
    status: ApplicationStatus
    notes: str | None = None
    confirmation_text: str | None = None


@router.get("", response_model=list[ApplicationSummary])
async def list_applications(
    status: ApplicationStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationSummary]:
    rows = await apps_dao.list_applications(db, status=status, limit=limit, offset=offset)
    return [
        ApplicationSummary(
            id=r.id,
            job_id=r.job_id,
            job_title=r.job.title if r.job else None,
            status=r.status,
            mode=r.mode,
            submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: int, db: AsyncSession = Depends(get_db)
) -> ApplicationDetail:
    row = await apps_dao.get_by_id(db, application_id)
    if row is None:
        raise HTTPException(404, f"Application {application_id} not found")
    return ApplicationDetail(
        id=row.id,
        job_id=row.job_id,
        job_title=row.job.title if row.job else None,
        status=row.status,
        mode=row.mode,
        submitted_at=row.submitted_at.isoformat() if row.submitted_at else None,
        created_at=row.created_at.isoformat(),
        source=row.source,
        notes=row.notes,
        recruiter_name=row.recruiter_name,
        recruiter_email=row.recruiter_email,
        cover_letter=row.cover_letter,
        confirmation_text=row.confirmation_text,
        events=[
            {
                "id": event.id,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
                "payload": event.payload,
            }
            for event in row.events
        ],
        generated_answers=[
            {
                "id": answer.id,
                "question_text": answer.question_text,
                "generated_text": answer.generated_text,
                "approved_text": answer.approved_text,
                "category": answer.category,
                "approved": answer.approved,
                "source": answer.source,
                "created_at": answer.created_at.isoformat(),
            }
            for answer in row.answers
        ],
    )


@router.patch("/{application_id}", response_model=ApplicationDetail)
async def update_status(
    application_id: int,
    payload: StatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationDetail:
    if payload.status == ApplicationStatus.submitted:
        raise HTTPException(
            status_code=403,
            detail="Cannot set submitted via PATCH. Approve a checkpoint and use submit_application_if_approved.",
        )
    row = await apps_dao.update_status(
        db, application_id, payload.status, confirmation_text=payload.confirmation_text
    )
    if row is None:
        raise HTTPException(404, f"Application {application_id} not found")
    if payload.notes is not None:
        row.notes = payload.notes
    await apps_dao.add_event(
        db,
        application_id,
        f"api.status_update.{payload.status.value}",
        payload.model_dump(mode="json"),
    )
    return ApplicationDetail(
        id=row.id,
        job_id=row.job_id,
        job_title=row.job.title if row.job else None,
        status=row.status,
        mode=row.mode,
        submitted_at=row.submitted_at.isoformat() if row.submitted_at else None,
        created_at=row.created_at.isoformat(),
        source=row.source,
        notes=row.notes,
        recruiter_name=row.recruiter_name,
        recruiter_email=row.recruiter_email,
        cover_letter=row.cover_letter,
        confirmation_text=row.confirmation_text,
        events=[
            {
                "id": event.id,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
                "payload": event.payload,
            }
            for event in row.events
        ],
        generated_answers=[
            {
                "id": answer.id,
                "question_text": answer.question_text,
                "generated_text": answer.generated_text,
                "approved_text": answer.approved_text,
                "category": answer.category,
                "approved": answer.approved,
                "source": answer.source,
                "created_at": answer.created_at.isoformat(),
            }
            for answer in row.answers
        ],
    )
