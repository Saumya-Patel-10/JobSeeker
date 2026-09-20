"""Lightweight browser source health — no Playwright launch on panel refresh."""

from __future__ import annotations

from pathlib import Path

from app.automation.firefox_profiles import get_firefox_profile, profile_health
from app.config.loader import load_config
from app.sources.base import SourceHealth


def profile_based_browser_health(*, source_label: str) -> SourceHealth:
    """Check Firefox profile readiness without starting Playwright."""
    cfg = load_config().preferences.browser
    if not cfg.persistent_profile:
        return SourceHealth(
            status="unknown",
            message=f"{source_label}: enable persistent_profile for session reuse",
            authenticated=False,
        )

    active_path: Path | None = None
    if cfg.profile_source == "system" and cfg.firefox_profile:
        profile = get_firefox_profile(cfg.firefox_profile, source="system")
        active_path = profile.path if profile is not None else None
    elif cfg.profile:
        from app.config.paths import BROWSER_PROFILES_DIR

        safe = "".join(
            ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in cfg.profile
        )
        active_path = (BROWSER_PROFILES_DIR / safe).resolve()

    if active_path is None:
        return SourceHealth(
            status="error",
            message=f"{source_label}: no Firefox profile configured in preferences.yaml",
            authenticated=False,
        )

    health = profile_health(active_path)
    if not health.exists:
        return SourceHealth(
            status="error",
            message=f"{source_label}: profile path missing ({active_path})",
            authenticated=False,
        )
    if health.locked:
        return SourceHealth(
            status="unknown",
            message=f"{source_label}: profile locked — close Firefox or use clone-on-lock",
            authenticated=False,
        )
    if health.has_cookies_db:
        return SourceHealth(
            status="healthy",
            message=f"{source_label}: profile ready (login verified on first discover run)",
            authenticated=True,
        )
    return SourceHealth(
        status="unauthenticated",
        message=f"{source_label}: log in via Firefox once, then reuse this profile",
        authenticated=False,
    )
