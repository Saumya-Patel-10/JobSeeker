"""Tests for BrowserSessionManager session reuse and lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.automation.browser import BrowserSession, BrowserSessionManager
from app.config.schema import BrowserConfig


@pytest.fixture
def mock_session() -> BrowserSession:
    session = MagicMock(spec=BrowserSession)
    session.is_alive = True
    session.start = AsyncMock()
    session.stop = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_session_manager_reuses_active_session_for_different_session_ids(mock_session: BrowserSession) -> None:
    manager = BrowserSessionManager()
    cfg = BrowserConfig(engine="chromium", persistent_profile=True, reuse_existing_session=True)

    # First session registered
    manager._sessions["linkedin-discovery"] = mock_session

    # Ingest asks for "default"
    reused = await manager.get_or_create("default", cfg)

    assert reused is mock_session
    assert manager._sessions["default"] is mock_session
    assert manager._sessions["linkedin-discovery"] is mock_session
    mock_session.start.assert_not_called()


@pytest.mark.asyncio
async def test_session_manager_cleans_dead_sessions() -> None:
    manager = BrowserSessionManager()
    cfg = BrowserConfig(engine="chromium", persistent_profile=True, reuse_existing_session=True)

    dead_session = MagicMock(spec=BrowserSession)
    dead_session.is_alive = False
    manager._sessions["old-dead"] = dead_session

    alive_session = MagicMock(spec=BrowserSession)
    alive_session.is_alive = True
    alive_session.start = AsyncMock()

    # get_or_create will purge old-dead and start a new session
    # mock BrowserSession constructor to return alive_session
    import app.automation.browser as browser_mod

    orig_cls = browser_mod.BrowserSession
    try:
        browser_mod.BrowserSession = MagicMock(return_value=alive_session)  # type: ignore[misc]
        created = await manager.get_or_create("new-session", cfg)
        assert created is alive_session
        assert "old-dead" not in manager._sessions
        assert manager._sessions["new-session"] is alive_session
    finally:
        browser_mod.BrowserSession = orig_cls  # type: ignore[misc]


@pytest.mark.asyncio
async def test_session_manager_close_aliases() -> None:
    manager = BrowserSessionManager()
    session = MagicMock(spec=BrowserSession)
    session.is_alive = True
    session.stop = AsyncMock()

    manager._sessions["alias1"] = session
    manager._sessions["alias2"] = session

    # Closing alias1 should not stop the session because alias2 still references it
    await manager.close("alias1")
    assert "alias1" not in manager._sessions
    assert "alias2" in manager._sessions
    session.stop.assert_not_called()

    # Closing alias2 should now stop the session
    await manager.close("alias2")
    assert "alias2" not in manager._sessions
    session.stop.assert_called_once()
