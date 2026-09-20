"""Ingest a job URL: detect adapter → scrape → dedupe → persist."""

from __future__ import annotations

from app.ats.generic import GenericAdapter
from app.ats.linkedin import LinkedInAdapter
from app.ats.registry import adapter_for, detect_adapter_class
from app.automation.browser import BrowserSession
from app.config.loader import load_config
from app.database.dao import jobs as jobs_dao
from app.database.session import session_scope
from app.models.job import Job
from app.services.blacklist import Blacklist
from app.services.blacklist_suggestions import maybe_suggest_blacklist
from app.utils.errors import ScrapeError
from app.utils.logging import get_logger

log = get_logger(__name__)

_BROWSER_REQUIRED: tuple[type, ...] = (LinkedInAdapter, GenericAdapter)


async def ingest_url(url: str, *, session_id: str = "default") -> Job:
    """Fetch, normalize, dedupe, persist a single job URL."""
    config = load_config()
    blacklist = Blacklist(config.blacklist)
    adapter_cls = detect_adapter_class(url)

    if adapter_cls in _BROWSER_REQUIRED:
        from app.runtime.automation_runtime import get_automation_runtime

        runtime = get_automation_runtime()
        session = await runtime.get_browser_session(session_id=session_id)
        adapter = adapter_for(url, session=session)
        job = await adapter.scrape_job(url)
    else:
        adapter = adapter_for(url)
        job = await adapter.scrape_job(url)

    blocked, reason = blacklist.is_blocked(job)
    if blocked:
        log.info("ingest.blacklisted", url=url, reason=reason)
        raise ScrapeError(f"Job blocked by blacklist: {reason}")

    async with session_scope() as db_session:
        row = await jobs_dao.upsert(db_session, job)
        job.id = row.id

    await maybe_suggest_blacklist(job.company, job.title)

    log.info(
        "ingest.success",
        url=url,
        adapter=adapter.name,
        job_id=job.id,
        title=job.title,
        company=job.company,
    )
    return job
