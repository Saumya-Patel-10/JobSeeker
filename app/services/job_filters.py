"""Job filtering for discovery and hunt workflows."""

from __future__ import annotations

from app.models.job import Job
from app.services.blacklist_suggestions import get_excluded_title_patterns
from app.services.discovery_config import JobDiscoveryConfig


def matches_filters(job: Job, discovery: JobDiscoveryConfig, config) -> bool:
    keywords = discovery.keywords or config.preferences.role_keywords
    companies = discovery.companies or config.preferences.target_companies
    locations = discovery.locations or config.preferences.locations
    remote_preference = discovery.remote_preference or config.preferences.remote_preference

    if companies:
        if job.company.strip().lower() not in {c.strip().lower() for c in companies if c.strip()}:
            return False

    if keywords:
        haystack = f"{job.title}\n{job.description_text}".lower()
        if not any(str(keyword).lower() in haystack for keyword in keywords):
            return False

    if locations:
        location = (job.location or "").lower()
        if not any(str(loc).lower() in location for loc in locations):
            return False

    if remote_preference and remote_preference != "no_preference":
        if job.remote_type.value != remote_preference:
            return False

    excluded = list(config.preferences.excluded_keywords) + get_excluded_title_patterns()
    if excluded:
        haystack = f"{job.title}\n{job.description_text}".lower()
        if any(str(ex).lower() in haystack for ex in excluded if ex):
            return False

    salary_cfg = config.preferences.salary_expectations
    if salary_cfg.min is not None and job.salary_max is not None:
        if job.salary_max < salary_cfg.min:
            return False
    if salary_cfg.max is not None and job.salary_min is not None:
        if job.salary_min > salary_cfg.max:
            return False

    return True
