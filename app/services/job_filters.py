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
        if not _location_matches(job, locations):
            return False

    if remote_preference and remote_preference != "no_preference":
        if not _remote_matches(job, remote_preference):
            return False

    excluded = list(config.preferences.excluded_keywords) + get_excluded_title_patterns()
    if excluded:
        haystack = f"{job.title}\n{job.description_text}".lower()
        if any(str(ex).lower() in haystack for ex in excluded if ex):
            return False

    salary_cfg = config.preferences.salary_expectations
    if (salary_cfg.min is not None or salary_cfg.max is not None) and (
        job.salary_min is not None or job.salary_max is not None
    ):
        # Normalize the job's salary into the configured expectation period
        # (e.g. an annual $80k posting must not be compared against a $30/hr
        # expectation as a raw number). 2080 hours ≈ 1 full-time year.
        factor = 1.0
        job_period = str(getattr(job.salary_period, "value", job.salary_period))
        if job_period != salary_cfg.period:
            if job_period == "hour" and salary_cfg.period == "year":
                factor = 2080.0
            elif job_period == "year" and salary_cfg.period == "hour":
                factor = 1.0 / 2080.0
            else:
                factor = 1.0

        if salary_cfg.min is not None and job.salary_max is not None:
            if job.salary_max * factor < salary_cfg.min:
                return False
        if salary_cfg.max is not None and job.salary_min is not None:
            if job.salary_min * factor > salary_cfg.max:
                return False

    return True


def _location_matches(job: Job, locations: list[str]) -> bool:
    if not locations:
        return True

    normalized_locs = [str(l).strip().lower() for l in locations if str(l).strip()]
    if not normalized_locs:
        return True

    # If user specifies wildcard / "Anywhere", they accept jobs everywhere!
    if any(l in ("anywhere", "any", "all", "*", "worldwide", "everywhere") for l in normalized_locs):
        return True

    job_loc = (job.location or "").strip().lower()
    is_job_remote = (
        getattr(job.remote_type, "value", str(job.remote_type)).lower() == "remote"
        or "remote" in job_loc
        or "telecommute" in job_loc
        or "work from home" in job_loc
        or "wfh" in job_loc
    )

    for req in normalized_locs:
        if "remote" in req:
            if is_job_remote:
                return True
            if not job_loc or job_loc == "unknown":
                return True

        if not job_loc or job_loc == "unknown":
            continue

        if req in job_loc or job_loc in req:
            return True

        parts = [p.strip() for p in req.replace("-", " ").split(",") if p.strip()]
        for part in parts:
            if len(part) >= 3 and part in job_loc:
                return True

    return False


def _remote_matches(job: Job, remote_preference: str) -> bool:
    if not remote_preference or remote_preference == "no_preference":
        return True

    job_remote = getattr(job.remote_type, "value", str(job.remote_type)).lower()
    job_loc = (job.location or "").lower()
    title_lower = (job.title or "").lower()

    inferred_remote = (
        job_remote == "remote"
        or "remote" in job_loc
        or "remote" in title_lower
        or "work from home" in job_loc
    )
    inferred_hybrid = (
        job_remote == "hybrid"
        or "hybrid" in job_loc
        or "hybrid" in title_lower
    )
    inferred_onsite = (
        job_remote == "onsite"
        or "onsite" in job_loc
        or "on-site" in job_loc
    )

    if remote_preference == "remote":
        return inferred_remote
    if remote_preference == "hybrid":
        return inferred_hybrid or inferred_remote
    if remote_preference == "onsite":
        return inferred_onsite or (not inferred_remote and not inferred_hybrid)

    return True

