"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio


@pytest_asyncio.fixture
async def fresh_db() -> AsyncIterator[None]:
    """Bind the global engine to an in-memory SQLite for the duration of a test."""
    from app.database.engine import dispose, reset_for_tests

    await reset_for_tests()
    try:
        yield
    finally:
        await dispose()
