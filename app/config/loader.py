"""Load + validate every config file into a single ``AppConfig`` object.

Files expected under ``config/``:

- ``profile.yaml``         → :class:`app.models.profile.Profile`
- ``preferences.yaml``     → :class:`app.config.schema.Preferences`
- ``job_sources.yaml``     → :class:`app.config.schema.JobSources`
- ``prompts.yaml``         → :class:`app.config.schema.PromptsConfig`
- ``blacklist.yaml``       → :class:`app.config.schema.BlacklistConfig`
- ``resume_master.json``   → :class:`app.models.resume.ResumeMaster`

``.env`` is loaded first so YAML values can reference env-injected secrets if
needed in the future. Result is cached via ``functools.lru_cache``; call
:func:`reload_config` after editing a YAML file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from app.config.paths import PROJECT_ROOT, user_config_path
from app.config.schema import (
    BlacklistConfig,
    JobSources,
    Preferences,
    PromptsConfig,
)
from app.models.profile import Profile
from app.models.resume import ResumeMaster
from app.utils.errors import ConfigError

T = TypeVar("T", bound=BaseModel)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(
            f"Missing config file: {path}\nRun `python -m app.cli.main init` "
            f"to copy starter templates from the repo."
        )
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file {path} must be a YAML mapping at the top level")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Config file {path} must be a JSON object at the top level")
    return data


def _validate[T: BaseModel](model: type[T], data: dict[str, Any], source: Path) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"Validation failed for {source}:\n{exc}") from exc


class AppConfig(BaseModel):
    """Bundled config + profile + resume — the only object pipelines need."""

    profile: Profile
    preferences: Preferences
    job_sources: JobSources
    prompts: PromptsConfig
    blacklist: BlacklistConfig
    resume_master: ResumeMaster


def load_dotenv_file() -> None:
    """Load ``.env`` from the project root if present (non-overriding)."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    """Load, validate, and cache every configuration file."""
    load_dotenv_file()

    profile_path = user_config_path("profile.yaml")
    preferences_path = user_config_path("preferences.yaml")
    sources_path = user_config_path("job_sources.yaml")
    prompts_path = user_config_path("prompts.yaml")
    blacklist_path = user_config_path("blacklist.yaml")
    resume_path = user_config_path("resume_master.json")

    return AppConfig(
        profile=_validate(Profile, _load_yaml(profile_path), profile_path),
        preferences=_validate(Preferences, _load_yaml(preferences_path), preferences_path),
        job_sources=_validate(JobSources, _load_yaml(sources_path), sources_path),
        prompts=_validate(PromptsConfig, _load_yaml(prompts_path), prompts_path),
        blacklist=_validate(BlacklistConfig, _load_yaml(blacklist_path), blacklist_path),
        resume_master=_validate(ResumeMaster, _load_json(resume_path), resume_path),
    )


def reload_config() -> AppConfig:
    """Bust the LRU cache and reload from disk."""
    load_config.cache_clear()
    return load_config()
