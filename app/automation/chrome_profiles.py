"""Google Chrome profile discovery for the ``chromium`` engine.

When ``browser.profile_source`` is ``system`` and the engine is ``chromium``,
the app launches the user's installed Chrome with one of their real Chrome
profiles (the ones visible in Chrome's profile switcher). Chrome stores its
profile metadata in a ``Local State`` JSON file inside the ``User Data``
directory; each entry records the profile's display name and the Google
account it is signed in with (``user_name``).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class ChromeProfile:
    """One profile shown in Chrome's profile switcher."""

    dir_name: str  # e.g. "Default", "Profile 1"
    display_name: str  # e.g. "Saumya" or "Person 1"
    email: str | None  # signed-in Google account, if any
    is_last_used: bool = False


def chrome_user_data_dir() -> Path:
    """Return the platform-specific Chrome 'User Data' root directory."""
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "Google" / "Chrome" / "User Data"
        return Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    return Path.home() / ".config" / "google-chrome"


def discover_system_chrome_profiles(root: Path | None = None) -> list[ChromeProfile]:
    """List the Chrome profiles registered on this machine.

    Chrome records every profile in the ``Local State`` JSON file inside the
    ``User Data`` directory, including the display name and the Google
    account (``user_name``) each profile is signed in with.
    """
    base = root or chrome_user_data_dir()
    local_state = base / "Local State"
    if not local_state.is_file():
        log.info("chrome.no_local_state", path=str(local_state))
        return []
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("chrome.local_state_unreadable", path=str(local_state), error=str(exc))
        return []

    info_cache = (data.get("profile") or {}).get("info_cache") or {}
    last_used = (data.get("profile") or {}).get("last_used") or ""

    profiles: list[ChromeProfile] = []
    for dir_name, info in info_cache.items():
        if not isinstance(info, dict):
            continue
        email = info.get("user_name")
        profiles.append(
            ChromeProfile(
                dir_name=str(dir_name),
                display_name=str(info.get("name") or dir_name),
                email=str(email) if email else None,
                is_last_used=str(dir_name) == last_used,
            )
        )
    return profiles


def get_chrome_profile(dir_name: str, root: Path | None = None) -> ChromeProfile | None:
    """Return one discovered Chrome profile by its directory name."""
    for profile in discover_system_chrome_profiles(root):
        if profile.dir_name == dir_name:
            return profile
    return None


def find_chrome_profile_by_email(
    email: str, root: Path | None = None
) -> ChromeProfile | None:
    """Return the Chrome profile signed in with the given Google account."""
    if not email:
        return None
    target = email.strip().lower()
    for profile in discover_system_chrome_profiles(root):
        if profile.email and profile.email.lower() == target:
            return profile
    return None


def chrome_is_running(user_data_dir: Path | None = None) -> bool:
    """Best-effort check whether Chrome currently holds the User Data dir.

    Chromium creates a ``lockfile`` inside the User Data directory while it
    is running. A second Chrome instance cannot attach to the same User Data
    directory, so a lock means automation cannot attach either.
    """
    base = user_data_dir or chrome_user_data_dir()
    return (base / "lockfile").exists()