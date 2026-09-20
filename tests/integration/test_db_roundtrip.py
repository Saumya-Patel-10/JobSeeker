"""Round-trip: upsert a Job through the DAO and read it back."""

from __future__ import annotations

import pytest

from app.database.dao import jobs as jobs_dao
from app.database.session import session_scope
from app.models.enums import ATSSource
from app.models.job import Job


@pytest.mark.asyncio
async def test_upsert_then_get(fresh_db: None) -> None:
    job = Job(
        title="Backend Engineer",
        company="Acme",
        description_text="Build APIs.",
        source_url="https://example.com/job/1",
        url_hash="abc123",
        ats_source=ATSSource.generic,
    )
    async with session_scope() as session:
        row = await jobs_dao.upsert(session, job)
        first_id = row.id

    async with session_scope() as session:
        again = await jobs_dao.upsert(session, job)
        assert again.id == first_id  # dedupe by url_hash
        fetched = await jobs_dao.get_by_id(session, first_id)
        assert fetched is not None
        assert fetched.title == "Backend Engineer"
        assert fetched.company.name == "Acme"
