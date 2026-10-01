"""``GET /status`` — coarse health check + automation status."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_config
from app.automation.firefox_profiles import (
    discover_managed_firefox_profiles,
    discover_system_firefox_profiles,
    get_firefox_profile,
    profile_health,
)
from app.config.loader import AppConfig
from app.config.paths import BROWSER_PROFILES_DIR, DEFAULT_DB_PATH
from app.llm.factory import provider_session

router = APIRouter(prefix="/status", tags=["status"])


class StatusResponse(BaseModel):
    healthy: bool
    llm_provider: str
    llm_reachable: bool
    llm_base_url: str
    db_path: str
    db_exists: bool
    apply_default_mode: str
    allow_auto_submit: bool
    browser_engine: str
    browser_headless: bool
    browser_persistent_profile: bool
    browser_profile_source: str
    browser_profile_name: str | None
    browser_profile_path: str | None
    browser_profile_exists: bool
    browser_profile_locked: bool
    browser_profile_has_cookies: bool
    firefox_profiles_detected: int
    managed_browser_profiles_detected: int


@router.get("", response_model=StatusResponse)
async def get_status(config: AppConfig = Depends(get_config)) -> StatusResponse:
    llm_cfg = config.preferences.llm
    browser_cfg = config.preferences.browser
    try:
        async with provider_session(llm_cfg) as provider:
            reachable = await provider.health()
    except Exception:
        reachable = False

    if browser_cfg.profile_source == "system":
        browser_name = browser_cfg.firefox_profile
        profile = (
            get_firefox_profile(browser_cfg.firefox_profile, source="system")
            if browser_cfg.firefox_profile
            else None
        )
        profile_path = profile.path if profile else None
    else:
        browser_name = browser_cfg.profile
        profile_path = (BROWSER_PROFILES_DIR / browser_cfg.profile).resolve()
    health = profile_health(profile_path) if profile_path is not None else None
    system_profiles = discover_system_firefox_profiles()
    managed_profiles = discover_managed_firefox_profiles()

    # A managed browser profile is created on first launch, so a missing profile
    # directory must not mark the whole backend as unhealthy. Browser state is
    # reported separately through the ``browser_*`` fields.
    is_healthy = DEFAULT_DB_PATH.exists()
    return StatusResponse(
        healthy=is_healthy,
        llm_provider=llm_cfg.provider,
        llm_reachable=reachable,
        llm_base_url=llm_cfg.base_url,
        db_path=str(DEFAULT_DB_PATH),
        db_exists=DEFAULT_DB_PATH.exists(),
        apply_default_mode=config.preferences.apply.default_mode.value,
        allow_auto_submit=config.preferences.apply.allow_auto_submit,
        browser_engine=browser_cfg.engine,
        browser_headless=browser_cfg.headless,
        browser_persistent_profile=browser_cfg.persistent_profile,
        browser_profile_source=browser_cfg.profile_source,
        browser_profile_name=browser_name,
        browser_profile_path=str(profile_path) if profile_path is not None else None,
        browser_profile_exists=health.exists if health else False,
        browser_profile_locked=health.locked if health else False,
        browser_profile_has_cookies=health.has_cookies_db if health else False,
        firefox_profiles_detected=len(system_profiles),
        managed_browser_profiles_detected=len(managed_profiles),
    )
