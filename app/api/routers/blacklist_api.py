"""Blacklist suggestion review API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.dao import blacklist_suggestions as bl_dao
from app.services.blacklist_suggestions import approve_suggestion, reject_suggestion

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


class BlacklistSuggestionView(BaseModel):
    id: int
    company: str
    job_title: str
    reason: str
    status: str
    matched_pattern: str | None
    created_at: str


@router.get("/suggestions", response_model=list[BlacklistSuggestionView])
async def list_suggestions(
    status: str = "pending",
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[BlacklistSuggestionView]:
    if status == "pending":
        rows = await bl_dao.list_pending(db, limit=limit)
    else:
        rows = await bl_dao.list_pending(db, limit=limit)
    return [
        BlacklistSuggestionView(
            id=r.id,
            company=r.company,
            job_title=r.job_title,
            reason=r.reason,
            status=r.status,
            matched_pattern=r.matched_pattern,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/suggestions/{suggestion_id}/approve")
async def approve(suggestion_id: int) -> dict[str, bool]:
    ok = await approve_suggestion(suggestion_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"approved": True}


@router.post("/suggestions/{suggestion_id}/reject")
async def reject(suggestion_id: int) -> dict[str, bool]:
    ok = await reject_suggestion(suggestion_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"rejected": True}
