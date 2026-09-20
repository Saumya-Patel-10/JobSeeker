"""Job DAO: upsert by url_hash + listing helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database.dao import companies as company_dao
from app.database.models import Job as JobRow
from app.models.job import Job


async def get_by_url_hash(session: AsyncSession, url_hash: str) -> JobRow | None:
    result = await session.execute(select(JobRow).where(JobRow.url_hash == url_hash))
    return result.scalar_one_or_none()


async def upsert(session: AsyncSession, job: Job) -> JobRow:
    """Insert a new job or refresh the mutable fields of an existing one."""
    existing = await get_by_url_hash(session, job.url_hash)
    if existing is not None:
        existing.title = job.title
        existing.description_text = job.description_text
        existing.description_html = job.description_html
        existing.location = job.location
        existing.salary_min = job.salary_min
        existing.salary_max = job.salary_max
        existing.status = job.status.value
        existing.raw_payload = job.raw_payload
        return existing

    company = await company_dao.upsert(session, job.company)
    row = JobRow(
        external_id=job.external_id,
        title=job.title,
        company_id=company.id,
        location=job.location,
        remote_type=job.remote_type.value,
        description_text=job.description_text,
        description_html=job.description_html,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period.value,
        source_url=job.source_url,
        ats_source=job.ats_source.value,
        url_hash=job.url_hash,
        posted_at=job.posted_at,
        scraped_at=job.scraped_at,
        status=job.status.value,
        raw_payload=job.raw_payload,
    )
    session.add(row)
    await session.flush()
    return row


async def get_by_id(session: AsyncSession, job_id: int) -> JobRow | None:
    stmt = (
        select(JobRow)
        .where(JobRow.id == job_id)
        .options(joinedload(JobRow.company), selectinload(JobRow.scores))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_jobs(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> list[JobRow]:
    stmt = select(JobRow).options(joinedload(JobRow.company)).order_by(JobRow.created_at.desc())
    if status is not None:
        stmt = stmt.where(JobRow.status == status)
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_jobs(session: AsyncSession) -> int:
    from sqlalchemy import func

    result = await session.execute(select(func.count()).select_from(JobRow))
    return int(result.scalar_one())
