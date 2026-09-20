"""Browser profile discovery and Firefox session management routes."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.automation.firefox_profiles import (
    clone_firefox_profile,
    discover_managed_firefox_profiles,
    discover_system_firefox_profiles,
    get_firefox_profile,
    profile_health,
)
from app.config.loader import reload_config
from app.config.paths import BROWSER_PROFILES_DIR, user_config_path

router = APIRouter(prefix="/browser", tags=["browser"])


class BrowserProfileView(BaseModel):
    name: str
    path: str
    source: Literal["system", "managed"]
    is_default: bool
    exists: bool
    has_prefs: bool
    has_cookies_db: bool
    locked: bool


class BrowserHealthView(BaseModel):
    engine: str
    headless: bool
    persistent_profile: bool
    profile_source: str
    active_profile_name: str | None
    active_profile_path: str | None
    profile_exists: bool
    cookies_available: bool
    locked: bool
    detected_system_profiles: int
    detected_managed_profiles: int
    reuse_existing_session: bool
    clone_system_profile_on_lock: bool


class CloneProfileRequest(BaseModel):
    source_profile_name: str
    target_name: str | None = None
    overwrite: bool = False


class SetActiveProfileRequest(BaseModel):
    profile_source: Literal["system", "managed"]
    profile_name: str
    persistent_profile: bool = True
    reuse_existing_session: bool = True
    clone_system_profile_on_lock: bool = True


@router.get("/profiles", response_model=list[BrowserProfileView])
async def list_profiles() -> list[BrowserProfileView]:
    profiles = [*discover_system_firefox_profiles(), *discover_managed_firefox_profiles()]
    output: list[BrowserProfileView] = []
    for profile in profiles:
        health = profile_health(profile.path)
        output.append(
            BrowserProfileView(
                name=profile.name,
                path=str(profile.path),
                source=profile.source,
                is_default=profile.is_default,
                exists=health.exists,
                has_prefs=health.has_prefs,
                has_cookies_db=health.has_cookies_db,
                locked=health.locked,
            )
        )
    return output


@router.get("/health", response_model=BrowserHealthView)
async def browser_health() -> BrowserHealthView:
    cfg = reload_config()
    browser_cfg = cfg.preferences.browser
    active_name: str | None
    active_path: Path | None
    if browser_cfg.profile_source == "system":
        active_name = browser_cfg.firefox_profile
        profile = (
            get_firefox_profile(browser_cfg.firefox_profile, source="system")
            if browser_cfg.firefox_profile
            else None
        )
        active_path = profile.path if profile is not None else None
    else:
        active_name = browser_cfg.profile
        active_path = (BROWSER_PROFILES_DIR / browser_cfg.profile).resolve()

    health = profile_health(active_path) if active_path else None
    system_profiles = discover_system_firefox_profiles()
    managed_profiles = discover_managed_firefox_profiles()
    return BrowserHealthView(
        engine=browser_cfg.engine,
        headless=browser_cfg.headless,
        persistent_profile=browser_cfg.persistent_profile,
        profile_source=browser_cfg.profile_source,
        active_profile_name=active_name,
        active_profile_path=str(active_path) if active_path else None,
        profile_exists=health.exists if health else False,
        cookies_available=health.has_cookies_db if health else False,
        locked=health.locked if health else False,
        detected_system_profiles=len(system_profiles),
        detected_managed_profiles=len(managed_profiles),
        reuse_existing_session=browser_cfg.reuse_existing_session,
        clone_system_profile_on_lock=browser_cfg.clone_system_profile_on_lock,
    )


@router.post("/profiles/clone", response_model=BrowserProfileView)
async def clone_profile(payload: CloneProfileRequest) -> BrowserProfileView:
    profile = get_firefox_profile(payload.source_profile_name, source="system")
    if profile is None:
        raise HTTPException(status_code=404, detail="System Firefox profile not found")
    target_name = payload.target_name or f"{profile.name}-managed"
    try:
        cloned_path = clone_firefox_profile(profile.path, target_name, overwrite=payload.overwrite)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    health = profile_health(cloned_path)
    return BrowserProfileView(
        name=target_name,
        path=str(cloned_path),
        source="managed",
        is_default=target_name == "default",
        exists=health.exists,
        has_prefs=health.has_prefs,
        has_cookies_db=health.has_cookies_db,
        locked=health.locked,
    )


@router.put("/active", response_model=BrowserHealthView)
async def set_active_profile(payload: SetActiveProfileRequest) -> BrowserHealthView:
    if payload.profile_source == "system":
        profile = get_firefox_profile(payload.profile_name, source="system")
    else:
        profile = get_firefox_profile(payload.profile_name, source="managed")
    if profile is None:
        raise HTTPException(status_code=404, detail="Firefox profile not found")

    preferences_path = user_config_path("preferences.yaml")
    raw = yaml.safe_load(preferences_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise HTTPException(status_code=500, detail="preferences.yaml root must be an object")

    browser_cfg = raw.get("browser", {})
    if not isinstance(browser_cfg, dict):
        browser_cfg = {}
    browser_cfg["engine"] = "firefox"
    browser_cfg["persistent_profile"] = payload.persistent_profile
    browser_cfg["profile_source"] = payload.profile_source
    browser_cfg["reuse_existing_session"] = payload.reuse_existing_session
    browser_cfg["clone_system_profile_on_lock"] = payload.clone_system_profile_on_lock
    if payload.profile_source == "system":
        browser_cfg["firefox_profile"] = payload.profile_name
    else:
        browser_cfg["profile"] = payload.profile_name

    raw["browser"] = browser_cfg
    preferences_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return await browser_health()

@router.get("/sessions")
async def list_active_sessions():
    from app.automation.browser import get_browser_session_manager
    return {"sessions": list(get_browser_session_manager()._sessions.keys())}

@router.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    from app.automation.browser import get_browser_session_manager
    await get_browser_session_manager().close(session_id)
    return {"status": "ok"}
