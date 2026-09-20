"""Async SQLAlchemy engine + session factory + ``init_db``.

A single engine is memoized at module level; tests that need a fresh DB can
call :func:`dispose` between cases. ``init_db`` is idempotent.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.paths import DEFAULT_DB_URL, ensure_data_dirs
from app.database.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(url: str | None = None) -> AsyncEngine:
    """Return the lazily-constructed async engine."""
    global _engine
    if _engine is None:
        ensure_data_dirs()
        _engine = create_async_engine(url or DEFAULT_DB_URL, future=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _session_factory


async def init_db(url: str | None = None) -> None:
    """Create every table declared on ``Base.metadata`` if missing."""
    engine = get_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose() -> None:
    """Tear down the engine + session factory (mostly for tests)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def reset_for_tests(url: str = "sqlite+aiosqlite:///:memory:") -> None:
    """Replace the global engine with a fresh one bound to ``url`` and create tables."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = create_async_engine(url, future=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
