"""Supervised Job Application Orchestrator — single pipeline for all entry points."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.config.loader import load_config
from app.database.dao import job_scores as scores_dao
from app.database.dao import resume_versions as resume_dao
from app.database.models import Application
from app.database.session import session_scope
from app.models.enums import ApplicationMode, JobHuntMode
from app.models.job import Job
from app.pipelines.apply_pipeline import ApplyResult, prepare_application
from app.pipelines.ingest_pipeline import ingest_url
from app.pipelines.score_pipeline import score_existing_job
from app.pipelines.tailor_pipeline import tailor_existing_job
from app.runtime.automation_runtime import get_automation_runtime
from app.services.blacklist_suggestions import maybe_suggest_blacklist
from app.services.discovery_config import JobDiscoveryConfig
from app.services.event_bus import get_event_bus
from app.services.job_filters import matches_filters
from app.services.source_orchestrator import get_source_orchestrator
from app.services.submission import SubmissionNotAllowedError, submit_application_if_approved
from app.utils.logging import get_logger

log = get_logger(__name__)

OrchestratorRunState = Literal["idle", "running", "paused", "stopped", "error"]


class PipelineStage(str, Enum):
    idle = "idle"
    discovering = "discovering"
    ingesting = "ingesting"
    filtering = "filtering"
    scoring = "scoring"
    tailoring = "tailoring"
    preparing = "preparing"
    awaiting_approval = "awaiting_approval"
    submitting = "submitting"
    cooldown = "cooldown"
    sleeping = "sleeping"


class OrchestratorRunRequest(BaseModel):
    """Same contract as legacy JobHuntRunRequest."""

    mode: JobHuntMode = JobHuntMode.manual_review
    run_once: bool = True
    interval_minutes: int | None = Field(default=None, ge=1, le=720)
    discovery: JobDiscoveryConfig = Field(default_factory=JobDiscoveryConfig)


class OrchestratorStats(BaseModel):
    jobs_seen: int = 0
    jobs_ingested: int = 0
    jobs_filtered: int = 0
    jobs_analyzed: int = 0
    resumes_generated: int = 0
    applications_prepared: int = 0
    applications_attempted: int = 0  # legacy alias, kept equal to applications_prepared
    applications_submitted: int = 0
    applications_skipped: int = 0
    errors: int = 0


class QueueItem(BaseModel):
    url: str | None = None
    job_id: int | None = None
    title: str | None = None
    company: str | None = None
    stage: PipelineStage = PipelineStage.idle


class OrchestratorStatus(BaseModel):
    status: OrchestratorRunState = "idle"
    stage: PipelineStage = PipelineStage.idle
    mode: JobHuntMode | None = None
    run_once: bool = True
    interval_minutes: int | None = None
    started_at: datetime | None = None
    last_tick_at: datetime | None = None
    stopped_at: datetime | None = None
    last_event: str | None = None
    last_error: str | None = None
    current_task: str | None = None
    current_job_id: int | None = None
    current_job_title: str | None = None
    current_company: str | None = None
    queue: list[QueueItem] = Field(default_factory=list)
    stats: OrchestratorStats = Field(default_factory=OrchestratorStats)


@dataclass
class _RunContext:
    request: OrchestratorRunRequest


class JobApplicationOrchestrator:
    """Unified supervised loop: discover → filter → score → tailor → prepare → approve → submit."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()
        self._status = OrchestratorStatus()

    def status(self) -> OrchestratorStatus:
        return self._status

    def _emit(self, event: str, extra: dict[str, Any] | None = None) -> None:
        payload = self._status.model_dump(mode="json")
        if extra:
            payload.update(extra)
        get_event_bus().emit(event, payload)
        # Legacy UI listens for job_hunt.* events
        if event.startswith("orchestrator."):
            legacy = event.replace("orchestrator.", "job_hunt.", 1)
            get_event_bus().emit(legacy, payload)

    def _set_stage(self, stage: PipelineStage, *, task_label: str | None = None) -> None:
        self._status.stage = stage
        self._status.current_task = stage.value
        if task_label is not None:
            self._status.last_event = task_label
        self._emit(f"orchestrator.{stage.value}")

    async def start(self, request: OrchestratorRunRequest) -> OrchestratorStatus:
        async with self._lock:
            if self._task and not self._task.done():
                raise RuntimeError("Orchestrator is already running")
            self._stop_event = asyncio.Event()
            self._pause_event = asyncio.Event()
            self._pause_event.set()
            get_automation_runtime().reset_for_new_run()
            self._status = OrchestratorStatus(
                status="running",
                stage=PipelineStage.discovering,
                mode=request.mode,
                run_once=request.run_once,
                interval_minutes=request.interval_minutes,
                started_at=datetime.now(UTC),
                last_event="orchestrator.start",
            )
            self._task = asyncio.create_task(self._run_loop(_RunContext(request=request)))
            log.info("orchestrator.start", mode=request.mode.value)
            self._emit("orchestrator.start")
            return self._status

    async def pause(self) -> OrchestratorStatus:
        if self._status.status != "running":
            return self._status
        self._pause_event.clear()
        self._status.status = "paused"
        self._set_stage(PipelineStage.idle, task_label="orchestrator.paused")
        return self._status

    async def resume(self) -> OrchestratorStatus:
        if self._status.status != "paused":
            return self._status
        self._pause_event.set()
        self._status.status = "running"
        self._set_stage(self._status.stage, task_label="orchestrator.resumed")
        return self._status

    async def stop(self) -> OrchestratorStatus:
        self._stop_event.set()
        self._pause_event.set()
        self._status.status = "stopped"
        self._status.stopped_at = datetime.now(UTC)
        self._status.stage = PipelineStage.idle
        self._set_stage(PipelineStage.idle, task_label="orchestrator.stopped")
        self._status.current_job_id = None
        return self._status

    async def discover(
        self, discovery: JobDiscoveryConfig, *, ingest: bool = True
    ) -> dict[str, Any]:
        """Unified discovery — used by search CLI and Control Center search."""
        self._set_stage(PipelineStage.discovering, task_label="orchestrator.discover")
        orchestrator = get_source_orchestrator()
        if ingest:
            return await orchestrator.poll_all(discovery)
        return await orchestrator.discover_urls(discovery)

    async def ingest_urls(self, urls: list[str], discovery: JobDiscoveryConfig) -> list[dict[str, Any]]:
        """Ingest manual URLs through filter pipeline (no apply)."""
        config = load_config()
        results: list[dict[str, Any]] = []
        for url in urls:
            url = url.strip()
            if not url:
                continue
            try:
                self._set_stage(PipelineStage.ingesting)
                job = await ingest_url(url)
                await maybe_suggest_blacklist(job.company, job.title)
                matched = matches_filters(job, discovery, config)
                results.append(
                    {
                        "url": url,
                        "status": "ingested" if matched else "filtered",
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                    }
                )
            except Exception as exc:
                results.append({"url": url, "status": "error", "error": str(exc)})
        return results

    async def _run_loop(self, ctx: _RunContext) -> None:
        try:
            while not self._stop_event.is_set():
                self._status.last_tick_at = datetime.now(UTC)
                await self._run_once(ctx)
                if ctx.request.run_once:
                    break
                interval = ctx.request.interval_minutes
                if interval is None:
                    interval = load_config().preferences.automation.default_interval_minutes
                if interval <= 0:
                    break
                self._set_stage(PipelineStage.sleeping)
                if not await self._sleep_with_stop(interval * 60):
                    break
        except Exception as exc:
            self._status.status = "error"
            self._status.last_error = str(exc)
            self._emit("orchestrator.error", {"error": str(exc)})
            log.exception("orchestrator.error")
        finally:
            if self._status.status not in {"error", "stopped"}:
                self._status.status = "stopped"
                self._status.stopped_at = datetime.now(UTC)
                self._status.stage = PipelineStage.idle
                self._emit("orchestrator.finished")
            self._status.current_job_id = None

    async def _run_once(self, ctx: _RunContext) -> None:
        if not await self._await_ready():
            return

        discovery = ctx.request.discovery
        config = load_config()

        # 1. Discover
        self._set_stage(PipelineStage.discovering)
        urls: list[str] = list(discovery.urls)
        if discovery.run_search:
            by_source = await get_source_orchestrator().discover_urls(discovery)
            for batch in by_source.values():
                urls.extend(batch)
        # Also include any open jobs in the database that haven't been scored yet
        try:
            async with session_scope() as db:
                from app.database.dao import jobs as jobs_dao
                existing_jobs = await jobs_dao.list_jobs(db, limit=50)
                for r in existing_jobs:
                    if r.source_url and r.source_url not in urls:
                        if not await _has_score(r.id):
                            urls.append(r.source_url)
        except Exception as exc:
            log.warning("orchestrator.unscored_db_load_failed", error=str(exc))

        urls = _dedupe(urls)
        self._status.stats.jobs_seen += len(urls)
        self._status.queue = [
            QueueItem(url=u, stage=PipelineStage.ingesting) for u in urls[:50]
        ]
        self._emit("orchestrator.discovered", {"url_count": len(urls)})

        for url in urls:
            if not await self._await_ready():
                return

            self._status.current_job_id = None
            self._status.current_job_title = None
            self._status.current_company = None
            self._set_stage(PipelineStage.ingesting)

            try:
                job = await ingest_url(url)
                await maybe_suggest_blacklist(job.company, job.title)
                self._status.stats.jobs_ingested += 1
            except Exception as exc:
                self._status.stats.errors += 1
                log.warning("orchestrator.ingest_failed", url=url, error=str(exc))
                continue

            self._set_stage(PipelineStage.filtering)
            if not matches_filters(job, discovery, config):
                self._status.stats.jobs_filtered += 1
                continue

            try:
                await self._process_job(job, ctx)
            except Exception as exc:
                self._status.stats.errors += 1
                log.warning("orchestrator.job_failed", job_id=job.id, error=str(exc))
                self._emit("orchestrator.job_error", {"job_id": job.id, "error": str(exc)})

    async def _process_job(self, job: Job, ctx: _RunContext) -> None:
        if job.id is None:
            self._status.stats.errors += 1
            return
        if not await self._await_ready():
            return

        self._status.current_job_id = job.id
        self._status.current_job_title = job.title
        self._status.current_company = job.company

        config = load_config()
        mode = ctx.request.mode

        # 3. Score
        self._set_stage(PipelineStage.scoring)
        if not await _has_score(job.id):
            await score_existing_job(job.id)
            self._status.stats.jobs_analyzed += 1

        if await _score_below_threshold(job.id, config.preferences.apply.require_min_score):
            self._status.stats.jobs_filtered += 1
            return

        if mode == JobHuntMode.assisted_apply:
            if not await _has_resume(job.id):
                self._set_stage(PipelineStage.tailoring)
                await tailor_existing_job(job.id, write_cover_letter=True)
                self._status.stats.resumes_generated += 1
            self._emit("orchestrator.assisted_complete")
            return

        if not await _has_resume(job.id):
            self._set_stage(PipelineStage.tailoring)
            await tailor_existing_job(job.id, write_cover_letter=True)
            self._status.stats.resumes_generated += 1

        if await _has_application(job.id):
            self._status.stats.applications_skipped += 1
            return

        if not await _within_daily_limit(config.preferences.apply.daily_limit):
            self._status.stats.applications_skipped += 1
            return

        # 5. Prepare (fill) — stops at approval
        apply_mode, allow_auto = _resolve_apply_mode(mode, job.ats_source.value)
        self._set_stage(PipelineStage.preparing)
        result = await prepare_application(
            job.id, mode=apply_mode, allow_auto=allow_auto
        )
        self._status.stats.applications_prepared += 1
        self._status.stats.applications_attempted = self._status.stats.applications_prepared
        self._set_stage(PipelineStage.awaiting_approval)

        get_event_bus().emit(
            "approval.pause",
            {
                "application_id": result.application_id,
                "checkpoint_id": result.approval_checkpoint_id,
                "job_id": job.id,
            },
        )

        # 7. Submit only if auto + approved (blocking wait during run)
        if (
            mode == JobHuntMode.autonomous_apply
            and allow_auto
            and result.approval_checkpoint_id
            and job.ats_source.value != "linkedin"
        ):
            from app.services.approval_service import get_approval_service

            approved = await get_approval_service().wait_for_checkpoint(
                result.approval_checkpoint_id
            )
            if approved:
                self._set_stage(PipelineStage.submitting)
                try:
                    await submit_application_if_approved(
                        result.application_id,
                        checkpoint_id=result.approval_checkpoint_id,
                    )
                    self._status.stats.applications_submitted += 1
                except SubmissionNotAllowedError as exc:
                    log.info("orchestrator.submit_skipped", reason=str(exc))

        cooldown = config.preferences.automation.cooldown_seconds
        if cooldown > 0:
            self._set_stage(PipelineStage.cooldown)
            await self._sleep_with_stop(cooldown)

    async def _await_ready(self) -> bool:
        if self._stop_event.is_set():
            return False
        await self._pause_event.wait()
        return not self._stop_event.is_set()

    async def _sleep_with_stop(self, seconds: int) -> bool:
        if seconds <= 0:
            return True
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
            return False
        except TimeoutError:
            return True


def _dedupe(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        u = url.strip()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _resolve_apply_mode(mode: JobHuntMode, ats_source: str) -> tuple[ApplicationMode, bool]:
    if ats_source == "linkedin":
        return ApplicationMode.human_review, False
    if mode == JobHuntMode.autonomous_apply:
        return ApplicationMode.auto, True
    return ApplicationMode.human_review, False


async def _has_resume(job_id: int) -> bool:
    async with session_scope() as db:
        return (await resume_dao.latest_for_job(db, job_id)) is not None


async def _has_score(job_id: int) -> bool:
    async with session_scope() as db:
        return (await scores_dao.latest_for_job(db, job_id)) is not None


async def _has_application(job_id: int) -> bool:
    async with session_scope() as db:
        result = await db.execute(
            select(func.count()).select_from(Application).where(Application.job_id == job_id)
        )
        return int(result.scalar_one() or 0) > 0


async def _score_below_threshold(job_id: int, threshold: float) -> bool:
    async with session_scope() as db:
        row = await scores_dao.latest_for_job(db, job_id)
    if row is None:
        return False
    return row.composite < threshold


async def _within_daily_limit(limit: int) -> bool:
    if limit <= 0:
        return True
    start_today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    async with session_scope() as db:
        result = await db.execute(
            select(func.count()).select_from(Application).where(Application.created_at >= start_today)
        )
        return int(result.scalar_one() or 0) < limit


_orchestrator: JobApplicationOrchestrator | None = None


def get_job_application_orchestrator() -> JobApplicationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = JobApplicationOrchestrator()
    return _orchestrator
