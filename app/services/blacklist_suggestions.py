"""Blacklist suggestion workflow — never auto-modify blacklist.yaml."""

from __future__ import annotations

import yaml

from app.config.loader import load_config, reload_config
from app.config.paths import user_config_path
from app.database.dao import blacklist_suggestions as bl_dao
from app.database.session import session_scope
from app.services.event_bus import get_event_bus
from app.utils.logging import get_logger

log = get_logger(__name__)

DEFAULT_EXCLUDED_TITLES = [
    "telemarketer",
    "cashier",
    "retail associate",
    "truck driver",
    "warehouse worker",
]


def get_excluded_title_patterns() -> list[str]:
    config = load_config()
    patterns = list(config.preferences.excluded_titles)
    if not patterns:
        patterns = list(DEFAULT_EXCLUDED_TITLES)
    patterns.extend(config.preferences.excluded_keywords)
    return patterns


def title_matches_excluded(title: str, patterns: list[str] | None = None) -> str | None:
    title_lower = title.lower()
    for pattern in patterns or get_excluded_title_patterns():
        if pattern.lower() in title_lower:
            return pattern
    return None


async def maybe_suggest_blacklist(company: str, job_title: str) -> int | None:
    """Create suggestion if title matches excluded pattern and company not blacklisted."""
    config = load_config()
    if any(c.lower() == company.lower() for c in config.blacklist.companies):
        return None

    matched = title_matches_excluded(job_title)
    if not matched:
        return None

    async with session_scope() as db:
        row = await bl_dao.create(
            db,
            company=company,
            job_title=job_title,
            reason=f"Title matches excluded pattern: {matched}",
            matched_pattern=matched,
        )
        suggestion_id = row.id

    get_event_bus().emit(
        "blacklist.suggestion",
        {"id": suggestion_id, "company": company, "job_title": job_title, "pattern": matched},
    )
    return suggestion_id


async def approve_suggestion(suggestion_id: int) -> bool:
    async with session_scope() as db:
        row = await bl_dao.get_by_id(db, suggestion_id)
        if row is None or row.status != "pending":
            return False
        await bl_dao.resolve(db, row, status="approved")
        company = row.company

    path = user_config_path("blacklist.yaml")
    data: dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    companies = data.get("companies") or []
    if company not in companies:
        companies.append(company)
    data["companies"] = companies
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    reload_config()
    log.info("blacklist.suggestion_approved", company=company)
    get_event_bus().emit("blacklist.applied", {"company": company})
    return True


async def reject_suggestion(suggestion_id: int) -> bool:
    async with session_scope() as db:
        row = await bl_dao.get_by_id(db, suggestion_id)
        if row is None or row.status != "pending":
            return False
        await bl_dao.resolve(db, row, status="rejected")
    return True
