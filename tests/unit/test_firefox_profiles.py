from __future__ import annotations

from pathlib import Path

from app.automation import firefox_profiles


def test_discover_system_firefox_profiles(tmp_path: Path) -> None:
    root = tmp_path / "firefox"
    root.mkdir(parents=True)
    (root / "Profiles" / "abc.default-release").mkdir(parents=True)
    (root / "Profiles" / "xyz.dev").mkdir(parents=True)
    (root / "profiles.ini").write_text(
        "\n".join(
            [
                "[Profile0]",
                "Name=default-release",
                "IsRelative=1",
                "Path=Profiles/abc.default-release",
                "Default=1",
                "",
                "[Profile1]",
                "Name=dev",
                "IsRelative=1",
                "Path=Profiles/xyz.dev",
            ]
        ),
        encoding="utf-8",
    )

    profiles = firefox_profiles.discover_system_firefox_profiles(root=root)
    assert len(profiles) == 2
    assert profiles[0].name == "default-release"
    assert profiles[0].is_default is True
    assert profiles[0].path.exists()


def test_clone_profile_ignores_locks(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source-profile"
    source.mkdir()
    (source / "prefs.js").write_text("user_pref('a',1);", encoding="utf-8")
    (source / "cookies.sqlite").write_text("fake-db", encoding="utf-8")
    (source / "parent.lock").write_text("locked", encoding="utf-8")

    managed = tmp_path / "managed"
    monkeypatch.setattr(firefox_profiles, "BROWSER_PROFILES_DIR", managed)

    cloned = firefox_profiles.clone_firefox_profile(source, "my-profile", overwrite=False)
    assert cloned.exists()
    assert (cloned / "prefs.js").exists()
    assert not (cloned / "parent.lock").exists()

    health = firefox_profiles.profile_health(cloned)
    assert health.exists is True
    assert health.has_prefs is True
    assert health.has_cookies_db is True
