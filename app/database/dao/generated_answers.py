"""Generated answer DAO (paired with the ChromaDB question-memory service)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import GeneratedAnswerRow
from app.models.enums import AnswerSource
from app.utils.hashing import stable_hash


def question_hash(question: str) -> str:
    return stable_hash(question.strip().lower())


async def upsert_by_question(
    session: AsyncSession,
    *,
    question: str,
    generated_text: str,
    source: AnswerSource,
    category: str | None = None,
    application_id: int | None = None,
) -> GeneratedAnswerRow:
    q_hash = question_hash(question)
    stmt = select(GeneratedAnswerRow).where(GeneratedAnswerRow.question_hash == q_hash)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.generated_text = generated_text
        existing.category = category or existing.category
        existing.source = source.value
        return existing
    row = GeneratedAnswerRow(
        question_text=question,
        question_hash=q_hash,
        generated_text=generated_text,
        category=category,
        source=source.value,
        application_id=application_id,
    )
    session.add(row)
    await session.flush()
    return row


async def approve(
    session: AsyncSession, answer_id: int, approved_text: str
) -> GeneratedAnswerRow | None:
    row = await session.get(GeneratedAnswerRow, answer_id)
    if row is None:
        return None
    row.approved_text = approved_text
    row.approved = True
    return row


async def find_by_question(session: AsyncSession, question: str) -> GeneratedAnswerRow | None:
    q_hash = question_hash(question)
    result = await session.execute(
        select(GeneratedAnswerRow).where(GeneratedAnswerRow.question_hash == q_hash)
    )
    return result.scalar_one_or_none()


async def list_approved(session: AsyncSession) -> list[GeneratedAnswerRow]:
    result = await session.execute(
        select(GeneratedAnswerRow)
        .where(GeneratedAnswerRow.approved.is_(True))
        .order_by(GeneratedAnswerRow.updated_at.desc())
    )
    return list(result.scalars().all())
