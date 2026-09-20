"""Load + validate the master resume from ``config/resume_master.json``."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.config.paths import user_config_path
from app.models.resume import ResumeMaster
from app.utils.errors import ConfigError


def load_master(path: Path | None = None) -> ResumeMaster:
    target = path or user_config_path("resume_master.json")
    if not target.exists():
        raise ConfigError(f"Master resume not found at {target}")
    with target.open("r", encoding="utf-8") as f:
        data = json.load(f)
    try:
        return ResumeMaster.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"Master resume validation failed:\n{exc}") from exc
