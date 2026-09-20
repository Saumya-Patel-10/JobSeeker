"""Resume template descriptor loader.

Each JSON file in ``app/resume/templates/`` describes how a tailored resume
is rendered: section ordering, bullet caps, optional flags. The DOCX and
PDF renderers honour these values.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

from app.config.paths import RESUME_TEMPLATES_DIR

TemplateName = Literal["backend", "ml", "generic"]


class TemplateConfig(TypedDict):
    name: str
    section_order: list[str]
    max_bullets_per_role: int
    include_tech_line: bool
    include_publications: bool


_DEFAULTS: dict[str, TemplateConfig] = {
    "generic": {
        "name": "Generic",
        "section_order": ["summary", "skills", "experience", "education", "projects"],
        "max_bullets_per_role": 6,
        "include_tech_line": True,
        "include_publications": False,
    },
    "backend": {
        "name": "Backend Engineer",
        "section_order": ["summary", "skills", "experience", "projects", "education"],
        "max_bullets_per_role": 5,
        "include_tech_line": True,
        "include_publications": False,
    },
    "ml": {
        "name": "ML / AI Engineer",
        "section_order": ["summary", "skills", "projects", "experience", "education"],
        "max_bullets_per_role": 5,
        "include_tech_line": True,
        "include_publications": True,
    },
}


@lru_cache(maxsize=8)
def load_template(name: str, *, directory: Path | None = None) -> TemplateConfig:
    """Return the JSON config for a template, falling back to bundled defaults."""
    directory = directory or RESUME_TEMPLATES_DIR
    path = directory / f"{name}.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return TemplateConfig(**data)  # type: ignore[typeddict-item]
    if name in _DEFAULTS:
        return _DEFAULTS[name]
    return _DEFAULTS["generic"]
