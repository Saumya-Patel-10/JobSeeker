"""ResumeVersion DAO."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ResumeVersion
from app.models.enums import ResumeKind


async def create(
    session: AsyncSession,
    *,
    job_id: int | None,
    kind: ResumeKind,
    template: str,
    docx_path: str | None,
    pdf_path: str | None,
    json_payload: dict[str, object],
    model_used: str = "",
    ats_score_notes: str | None = None,
) -> ResumeVersion:
    row = ResumeVersion(
        job_id=job_id,
        kind=kind.value,
        template=template,
        docx_path=docx_path,
        pdf_path=pdf_path,
        json_payload=json_payload,
        model_used=model_used,
        ats_score_notes=ats_score_notes,
    )
    session.add(row)
    await session.flush()
    return row


async def get_by_id(session: AsyncSession, version_id: int) -> ResumeVersion | None:
    return await session.get(ResumeVersion, version_id)


async def list_for_job(session: AsyncSession, job_id: int) -> list[ResumeVersion]:
    result = await session.execute(
        select(ResumeVersion)
        .where(ResumeVersion.job_id == job_id)
        .order_by(ResumeVersion.created_at.desc())
    )
    return list(result.scalars().all())


async def latest_for_job(session: AsyncSession, job_id: int) -> ResumeVersion | None:
    rows = await list_for_job(session, job_id)
    return rows[0] if rows else None
