"""FastAPI dependency providers (DB session + cached config)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.loader import AppConfig, load_config
from app.database.session import session_scope


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a transactional DB session for the request lifetime."""
    async with session_scope() as session:
        yield session


def get_config() -> AppConfig:
    """Return the cached :class:`AppConfig` for read-only handlers."""
    return load_config()
