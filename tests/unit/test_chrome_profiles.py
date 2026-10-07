"""Tests for Google Chrome system profile discovery."""

from __future__ import annotations

import json
from pathlib import Path

from app.automation.chrome_profiles import (
    chrome_is_running,
    discover_system_chrome_profiles,
    find_chrome_profile_by_email,
    get_chrome_profile,
)


def _write_local_state(root: Path, last_used: str = "Profile 1") -> None:
    local_state = {
        "profile": {
            "last_used": last_used,
            "info_cache": {
                "Default": {"name": "Person 1", "user_name": ""},
                "Profile 1": {"name": "Saumya", "user_name": "saumya.a.patel@gmail.com"},
            },
        }
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "Local State").write_text(json.dumps(local_state), encoding="utf-8")


def test_discover_reads_local_state(tmp_path: Path) -> None:
    _write_local_state(tmp_path)
    profiles = discover_system_chrome_profiles(root=tmp_path)
    assert [p.dir_name for p in profiles] == ["Default", "Profile 1"]
    saumya = profiles[1]
    assert saumya.display_name == "Saumya"
    assert saumya.email == "saumya.a.patel@gmail.com"
    assert saumya.is_last_used is True
    assert profiles[0].email is None


def test_get_and_find(tmp_path: Path) -> None:
    _write_local_state(tmp_path)
    assert get_chrome_profile("Profile 1", root=tmp_path) is not None
    assert get_chrome_profile("Profile 9", root=tmp_path) is None
    match = find_chrome_profile_by_email("Saumya.A.Patel@Gmail.com", root=tmp_path)
    assert match is not None and match.dir_name == "Profile 1"
    assert find_chrome_profile_by_email("nobody@example.com", root=tmp_path) is None


def test_missing_local_state(tmp_path: Path) -> None:
    assert discover_system_chrome_profiles(root=tmp_path) == []


def test_running_check(tmp_path: Path) -> None:
    assert chrome_is_running(user_data_dir=tmp_path) is False
    (tmp_path / "lockfile").write_text("x", encoding="utf-8")
    assert chrome_is_running(user_data_dir=tmp_path) is True


def test_chrome_locked_fallback(tmp_path: Path, monkeypatch) -> None:
    from app.automation.browser import BrowserSession
    from app.config.schema import BrowserConfig

    _write_local_state(tmp_path)
    (tmp_path / "lockfile").write_text("locked", encoding="utf-8")
    monkeypatch.setattr("app.automation.browser.chrome_user_data_dir", lambda: tmp_path)

    cfg = BrowserConfig(
        engine="chromium",
        profile_source="system",
        account_email="saumya.a.patel@gmail.com",
        clone_system_profile_on_lock=True,
    )
    session = BrowserSession(cfg)
    path, label = session._resolve_user_data_dir()
    assert "managed fallback" in label
    assert path.is_dir()