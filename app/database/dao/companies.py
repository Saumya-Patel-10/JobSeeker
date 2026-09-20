"""Company DAO."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Company


async def upsert(session: AsyncSession, name: str, website: str | None = None) -> Company:
    """Get an existing company by name or create a new one."""
    name = name.strip()
    if not name:
        raise ValueError("Company name cannot be empty")
    result = await session.execute(select(Company).where(Company.name == name))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(name=name, website=website)
        session.add(company)
        await session.flush()
    elif website and not company.website:
        company.website = website
    return company


async def get_by_id(session: AsyncSession, company_id: int) -> Company | None:
    return await session.get(Company, company_id)


async def list_all(session: AsyncSession) -> list[Company]:
    result = await session.execute(select(Company).order_by(Company.name))
    return list(result.scalars().all())
