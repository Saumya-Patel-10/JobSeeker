"""``/settings`` routes for editable config files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from app.config.loader import load_config, reload_config
from app.config.paths import user_config_path
from app.config.schema import BlacklistConfig, JobSources, Preferences
from app.models.profile import Profile
from app.models.resume import ResumeMaster

router = APIRouter(prefix="/settings", tags=["settings"])

SectionName = Literal[
    "profile",
    "preferences",
    "job_sources",
    "blacklist",
    "resume_master",
]


class SettingsBundle(BaseModel):
    profile: Profile
    preferences: Preferences
    job_sources: JobSources
    blacklist: BlacklistConfig
    resume_master: ResumeMaster


class SettingsUpdateRequest(BaseModel):
    data: dict[str, Any]


def _section_target(
    section: SectionName,
) -> tuple[type[BaseModel], Path, Literal["yaml", "json"]]:
    mapping: dict[SectionName, tuple[type[BaseModel], Path, Literal["yaml", "json"]]] = {
        "profile": (Profile, user_config_path("profile.yaml"), "yaml"),
        "preferences": (Preferences, user_config_path("preferences.yaml"), "yaml"),
        "job_sources": (JobSources, user_config_path("job_sources.yaml"), "yaml"),
        "blacklist": (BlacklistConfig, user_config_path("blacklist.yaml"), "yaml"),
        "resume_master": (ResumeMaster, user_config_path("resume_master.json"), "json"),
    }
    return mapping[section]


@router.get("", response_model=SettingsBundle)
async def get_settings() -> SettingsBundle:
    cfg = load_config()
    return SettingsBundle(
        profile=cfg.profile,
        preferences=cfg.preferences,
        job_sources=cfg.job_sources,
        blacklist=cfg.blacklist,
        resume_master=cfg.resume_master,
    )


@router.put("/{section}", response_model=SettingsBundle)
async def update_settings(section: SectionName, payload: SettingsUpdateRequest) -> SettingsBundle:
    model_cls, path, format_name = _section_target(section)
    try:
        validated = model_cls.model_validate(payload.data)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    serialized = validated.model_dump(mode="json")
    if format_name == "yaml":
        path.write_text(yaml.safe_dump(serialized, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    try:
        cfg = reload_config()
    except Exception as exc:  # pragma: no cover - defensive guard.
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {exc}") from exc

    return SettingsBundle(
        profile=cfg.profile,
        preferences=cfg.preferences,
        job_sources=cfg.job_sources,
        blacklist=cfg.blacklist,
        resume_master=cfg.resume_master,
    )
