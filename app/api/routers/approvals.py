"""Approval checkpoint API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.database.dao import approvals as approvals_dao
from app.database.models import ApprovalCheckpoint, Job
from app.database.session import session_scope
from app.runtime.automation_runtime import get_automation_runtime
from app.services.approval_service import get_approval_service
from app.services.submission import SubmissionNotAllowedError, submit_application_if_approved

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalQueueItem(BaseModel):
    id: int
    application_id: int
    job_id: int
    company: str
    role: str
    checkpoint_type: str
    status: str
    confidence: float | None
    resume_version_id: int | None
    ai_summary: str | None
    risks: list[str]
    generated_answers: dict[str, Any] | None
    payload: dict[str, Any] | None
    created_at: str


@router.get("/pending", response_model=list[ApprovalQueueItem])
async def list_pending(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalQueueItem]:
    rows = await approvals_dao.list_pending(db, limit=limit)
    return [await _to_queue_item(db, row) for row in rows]


@router.get("/{checkpoint_id}", response_model=ApprovalQueueItem)
async def get_checkpoint(
    checkpoint_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApprovalQueueItem:
    row = await approvals_dao.get_by_id(db, checkpoint_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return await _to_queue_item(db, row)


@router.post("/{checkpoint_id}/approve")
async def approve_checkpoint(
    checkpoint_id: int, submit: bool = Query(default=False)
) -> dict[str, Any]:
    ok = await get_approval_service().approve(checkpoint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    result: dict[str, Any] = {"approved": True, "checkpoint_id": checkpoint_id}
    if submit:
        async with session_scope() as db:
            row = await approvals_dao.get_by_id(db, checkpoint_id)
        if row:
            try:
                report = await submit_application_if_approved(
                    row.application_id, checkpoint_id=checkpoint_id
                )
                result["submitted"] = report.submitted
            except (SubmissionNotAllowedError, Exception) as exc:
                result["submit_error"] = str(exc)
    return result


@router.post("/{checkpoint_id}/reject")
async def reject_checkpoint(checkpoint_id: int) -> dict[str, Any]:
    ok = await get_approval_service().reject(checkpoint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"rejected": True, "checkpoint_id": checkpoint_id}


@router.post("/{checkpoint_id}/request-edit")
async def request_edit(checkpoint_id: int) -> dict[str, Any]:
    ok = await get_approval_service().request_edit(checkpoint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    await get_automation_runtime().pause_ai()
    return {"edit_requested": True, "checkpoint_id": checkpoint_id}


@router.post("/{checkpoint_id}/open-browser")
async def open_in_browser(checkpoint_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = await approvals_dao.get_by_id(db, checkpoint_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    session_id = f"apply_{row.application_id}"
    await get_automation_runtime().get_browser_session(
        session_id=session_id, application_id=row.application_id
    )
    return {"session_id": session_id, "application_id": row.application_id}


async def _to_queue_item(db: AsyncSession, row: ApprovalCheckpoint) -> ApprovalQueueItem:
    stmt = (
        select(Job)
        .where(Job.id == row.job_id)
        .options(selectinload(Job.company))
    )
    job_result = await db.execute(stmt)
    job = job_result.scalar_one_or_none()
    company = job.company.name if job and job.company else "Unknown"
    role = job.title if job else "Unknown"
    return ApprovalQueueItem(
        id=row.id,
        application_id=row.application_id,
        job_id=row.job_id,
        company=company,
        role=role,
        checkpoint_type=row.checkpoint_type,
        status=row.status,
        confidence=row.confidence,
        resume_version_id=row.resume_version_id,
        ai_summary=row.ai_summary,
        risks=list(row.risks or []),
        generated_answers=row.generated_answers,
        payload=row.payload,
        created_at=row.created_at.isoformat(),
    )

