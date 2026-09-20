"""Session context manager utilities."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import get_session_factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield an :class:`AsyncSession` that auto-commits on success."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def read_only_session() -> AsyncIterator[AsyncSession]:
    """Session that never commits (for SELECT-only flows)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()
