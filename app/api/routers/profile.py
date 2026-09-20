"""``/profile`` routes."""

from __future__ import annotations

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from app.api.deps import get_config
from app.config.loader import AppConfig, reload_config
from app.config.paths import user_config_path
from app.models.profile import Profile
from app.utils.errors import ConfigError

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Profile)
async def get_profile(config: AppConfig = Depends(get_config)) -> Profile:
    return config.profile


@router.put("", response_model=Profile)
async def update_profile(payload: Profile) -> Profile:
    path = user_config_path("profile.yaml")
    path.write_text(yaml.safe_dump(payload.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
    try:
        cfg = reload_config()
    except (ConfigError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=f"Updated profile failed validation: {exc}") from exc
    return cfg.profile
