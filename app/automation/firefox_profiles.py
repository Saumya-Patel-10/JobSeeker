"""Firefox profile discovery, validation, and cloning utilities."""

from __future__ import annotations

import configparser
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.config.paths import BROWSER_PROFILES_DIR

ProfileSource = Literal["system", "managed"]

_LOCK_FILES = ("parent.lock", ".parentlock", "lock")
_COPY_IGNORE_NAMES = {"parent.lock", ".parentlock", "lock", "startupCache"}


@dataclass(slots=True)
class FirefoxProfile:
    name: str
    path: Path
    source: ProfileSource
    is_default: bool
    profile_id: str | None = None


@dataclass(slots=True)
class FirefoxProfileHealth:
    exists: bool
    has_prefs: bool
    has_cookies_db: bool
    locked: bool


def firefox_root_dir() -> Path:
    """Return platform-specific Firefox configuration root."""
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Mozilla" / "Firefox"
        return Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Firefox"
    return Path.home() / ".mozilla" / "firefox"


def discover_system_firefox_profiles(root: Path | None = None) -> list[FirefoxProfile]:
    """Discover installed Firefox user profiles from ``profiles.ini``."""
    base = root or firefox_root_dir()
    ini_path = base / "profiles.ini"
    if not ini_path.exists():
        return []

    parser = configparser.ConfigParser()
    parser.read(ini_path, encoding="utf-8")

    profiles: list[FirefoxProfile] = []
    for section in parser.sections():
        if not section.lower().startswith("profile"):
            continue
        cfg = parser[section]
        name = cfg.get("Name", section)
        raw_path = cfg.get("Path", "")
        if not raw_path:
            continue
        is_relative = cfg.get("IsRelative", "1") == "1"
        resolved = (base / raw_path).resolve() if is_relative else Path(raw_path).expanduser().resolve()
        profiles.append(
            FirefoxProfile(
                name=name,
                path=resolved,
                source="system",
                is_default=cfg.get("Default", "0") == "1",
                profile_id=section,
            )
        )
    profiles.sort(key=lambda p: (not p.is_default, p.name.lower()))
    return profiles


def discover_managed_firefox_profiles() -> list[FirefoxProfile]:
    """Discover managed automation profiles under ``data/browser_profiles``."""
    BROWSER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profiles: list[FirefoxProfile] = []
    for path in BROWSER_PROFILES_DIR.iterdir():
        if not path.is_dir():
            continue
        profiles.append(
            FirefoxProfile(
                name=path.name,
                path=path.resolve(),
                source="managed",
                is_default=path.name == "default",
                profile_id=f"managed:{path.name}",
            )
        )
    profiles.sort(key=lambda p: (not p.is_default, p.name.lower()))
    return profiles


def discover_all_firefox_profiles() -> list[FirefoxProfile]:
    """Return system + managed Firefox profiles."""
    return [*discover_system_firefox_profiles(), *discover_managed_firefox_profiles()]


def get_firefox_profile(
    name: str,
    *,
    source: Literal["system", "managed", "auto"] = "auto",
) -> FirefoxProfile | None:
    """Find a profile by name and source."""
    if source in {"system", "auto"}:
        for profile in discover_system_firefox_profiles():
            if profile.name == name:
                return profile
    if source in {"managed", "auto"}:
        for profile in discover_managed_firefox_profiles():
            if profile.name == name:
                return profile
    return None


def profile_health(profile_dir: Path) -> FirefoxProfileHealth:
    """Run basic local profile health checks."""
    exists = profile_dir.exists() and profile_dir.is_dir()
    has_prefs = (profile_dir / "prefs.js").exists() if exists else False
    has_cookies_db = (profile_dir / "cookies.sqlite").exists() if exists else False
    locked = is_profile_locked(profile_dir) if exists else False
    return FirefoxProfileHealth(
        exists=exists,
        has_prefs=has_prefs,
        has_cookies_db=has_cookies_db,
        locked=locked,
    )


def is_profile_locked(profile_dir: Path) -> bool:
    """Return whether a profile appears to be locked by a running Firefox instance."""
    return any((profile_dir / lock_name).exists() for lock_name in _LOCK_FILES)


def clone_firefox_profile(
    source_profile_dir: Path,
    target_name: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Clone a Firefox profile into managed automation profiles."""
    if not source_profile_dir.exists():
        raise FileNotFoundError(f"Profile does not exist: {source_profile_dir}")
    BROWSER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    target_path = (BROWSER_PROFILES_DIR / target_name).resolve()
    if target_path.exists():
        if not overwrite:
            raise FileExistsError(f"Managed profile already exists: {target_path.name}")
        shutil.rmtree(target_path, ignore_errors=True)

    def _ignore(_base: str, names: list[str]) -> set[str]:
        return {name for name in names if name in _COPY_IGNORE_NAMES}

    shutil.copytree(source_profile_dir, target_path, ignore=_ignore)
    return target_path
