"""``/resumes`` routes — list and download generated resumes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database.dao import resume_versions as resume_dao

router = APIRouter(prefix="/resumes", tags=["resumes"])


class ResumeSummary(BaseModel):
    id: int
    job_id: int | None
    kind: str
    template: str
    docx_path: str | None
    pdf_path: str | None
    created_at: str


@router.get("/job/{job_id}", response_model=list[ResumeSummary])
async def list_for_job(job_id: int, db: AsyncSession = Depends(get_db)) -> list[ResumeSummary]:
    rows = await resume_dao.list_for_job(db, job_id)
    return [_to_summary(r) for r in rows]


@router.get("/{resume_id}", response_model=ResumeSummary)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)) -> ResumeSummary:
    row = await resume_dao.get_by_id(db, resume_id)
    if row is None:
        raise HTTPException(404, f"Resume version {resume_id} not found")
    return _to_summary(row)


@router.get("/{resume_id}/download/{ext}")
async def download(resume_id: int, ext: str, db: AsyncSession = Depends(get_db)) -> FileResponse:
    row = await resume_dao.get_by_id(db, resume_id)
    if row is None:
        raise HTTPException(404, f"Resume version {resume_id} not found")
    path_str = row.docx_path if ext == "docx" else row.pdf_path if ext == "pdf" else None
    if not path_str:
        raise HTTPException(404, f"No {ext} file recorded for resume {resume_id}")
    path = Path(path_str)
    if not path.exists():
        raise HTTPException(410, f"File no longer exists on disk: {path}")
    return FileResponse(
        path,
        filename=path.name,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if ext == "docx"
            else "application/pdf"
        ),
    )


def _to_summary(row) -> ResumeSummary:
    return ResumeSummary(
        id=row.id,
        job_id=row.job_id,
        kind=row.kind,
        template=row.template,
        docx_path=row.docx_path,
        pdf_path=row.pdf_path,
        created_at=row.created_at.isoformat(),
    )
