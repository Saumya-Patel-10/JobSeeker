"""Project path resolution.

All paths derive from ``PROJECT_ROOT`` which is the parent of the ``app/``
package. The environment variable ``JOBASSIST_ROOT`` overrides this for
non-standard installs (e.g., running from a packaged wheel).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

PROJECT_ROOT: Path = Path(os.environ.get("JOBASSIST_ROOT", Path(__file__).resolve().parents[2]))

APP_DIR: Path = PROJECT_ROOT / "app"
CONFIG_DIR: Path = PROJECT_ROOT / "config"
DATA_DIR: Path = PROJECT_ROOT / "data"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
SCRIPTS_DIR: Path = PROJECT_ROOT / "scripts"

LOG_DIR: Path = DATA_DIR / "logs"
CACHE_DIR: Path = DATA_DIR / "cache"
JOBS_DIR: Path = DATA_DIR / "jobs"
APPLICATIONS_DIR: Path = DATA_DIR / "applications"
RESUMES_DIR: Path = DATA_DIR / "resumes"
RESUMES_MASTER_DIR: Path = RESUMES_DIR / "master"
RESUMES_GENERATED_DIR: Path = RESUMES_DIR / "generated"
BROWSER_PROFILES_DIR: Path = DATA_DIR / "browser_profiles"
SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"
CHROMA_DIR: Path = CACHE_DIR / "chroma"

PROMPTS_DIR: Path = APP_DIR / "prompts"
RESUME_TEMPLATES_DIR: Path = APP_DIR / "resume" / "templates"

DEFAULT_DB_PATH: Path = DATA_DIR / "jobassist.db"
DEFAULT_DB_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}"

_ALL_DATA_DIRS: tuple[Path, ...] = (
    DATA_DIR,
    LOG_DIR,
    CACHE_DIR,
    JOBS_DIR,
    APPLICATIONS_DIR,
    RESUMES_DIR,
    RESUMES_MASTER_DIR,
    RESUMES_GENERATED_DIR,
    BROWSER_PROFILES_DIR,
    SCREENSHOTS_DIR,
    CHROMA_DIR,
)


def ensure_data_dirs() -> None:
    """Create every expected data directory (idempotent)."""
    for directory in _ALL_DATA_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def user_config_path(name: str) -> Path:
    """Resolve a user-editable config file inside ``config/``.

    Personal files (``profile.yaml``, ``preferences.yaml``,
    ``resume_master.json``) are git-ignored; only ``<name>.example`` templates
    are committed. If the real file is missing, it is created from its
    template on first access so a fresh clone works out of the box.
    """
    target = CONFIG_DIR / name
    if not target.exists():
        template = CONFIG_DIR / f"{name}.example"
        if template.exists():
            shutil.copyfile(template, target)
    return target
