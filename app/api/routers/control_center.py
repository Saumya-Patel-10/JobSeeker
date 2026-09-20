"""Control Center endpoints for UI-driven orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config.loader import reload_config
from app.config.paths import LOG_DIR, user_config_path
from app.database.models import ApplicationEvent, Company, Job, ResumeVersion
from app.services.discovery_config import JobDiscoveryConfig
from app.services.job_application_orchestrator import (
    OrchestratorRunRequest,
    OrchestratorStatus,
    get_job_application_orchestrator,
)
router = APIRouter(prefix="/control-center", tags=["control-center"])


class IngestRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)


class IngestResult(BaseModel):
    url: str
    status: Literal["ingested", "filtered", "error"]
    job_id: int | None = None
    title: str | None = None
    company: str | None = None
    ats_source: str | None = None
    error: str | None = None


class BatchIngestResponse(BaseModel):
    total: int
    ingested: int
    failed: int
    results: list[IngestResult]


class SearchRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=250)
    discovery: JobDiscoveryConfig = Field(default_factory=JobDiscoveryConfig)
    save_defaults: bool = False


class SourceSummary(BaseModel):
    source: str
    urls: int
    ingested: int
    failed: int


class SearchResponse(BaseModel):
    sources: list[SourceSummary]
    results: list[IngestResult]


class JobHuntStartRequest(OrchestratorRunRequest):
    save_defaults: bool = False


class ActivityEntry(BaseModel):
    timestamp: str
    category: str
    title: str
    detail: str | None = None
    job_id: int | None = None
    application_id: int | None = None
    payload: dict[str, Any] | None = None


@router.post("/ingest", response_model=BatchIngestResponse)
async def ingest_urls(payload: IngestRequest) -> BatchIngestResponse:
    orch = get_job_application_orchestrator()
    raw = await orch.ingest_urls(payload.urls, JobDiscoveryConfig())
    results: list[IngestResult] = []
    ingested = 0
    failed = 0
    for row in raw:
        if row.get("status") == "ingested":
            ingested += 1
        elif row.get("status") == "error":
            failed += 1
        results.append(
            IngestResult(
                url=row["url"],
                status=row.get("status", "error"),
                job_id=row.get("job_id"),
                title=row.get("title"),
                company=row.get("company"),
                error=row.get("error"),
            )
        )
    return BatchIngestResponse(total=len(results), ingested=ingested, failed=failed, results=results)


@router.post("/search", response_model=SearchResponse)
async def search_sources(payload: SearchRequest) -> SearchResponse:
    if payload.save_defaults:
        _persist_discovery_defaults(payload.discovery)

    poll = await get_job_application_orchestrator().discover(
        payload.discovery, ingest=True
    )
    summaries: list[SourceSummary] = []
    for name, meta in poll.get("sources", {}).items():
        summaries.append(
            SourceSummary(
                source=name,
                urls=meta.get("jobs_discovered", 0),
                ingested=meta.get("ingested", 0),
                failed=meta.get("ingestion_failures", 0),
            )
        )
    return SearchResponse(sources=summaries, results=[])


@router.get("/job-hunt/status", response_model=OrchestratorStatus)
async def job_hunt_status() -> OrchestratorStatus:
    return get_job_application_orchestrator().status()


@router.post("/job-hunt/start", response_model=OrchestratorStatus)
async def job_hunt_start(payload: JobHuntStartRequest) -> OrchestratorStatus:
    if payload.save_defaults:
        _persist_discovery_defaults(payload.discovery)
    try:
        return await get_job_application_orchestrator().start(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/job-hunt/pause", response_model=OrchestratorStatus)
async def job_hunt_pause() -> OrchestratorStatus:
    return await get_job_application_orchestrator().pause()


@router.post("/job-hunt/resume", response_model=OrchestratorStatus)
async def job_hunt_resume() -> OrchestratorStatus:
    return await get_job_application_orchestrator().resume()


@router.post("/job-hunt/stop", response_model=OrchestratorStatus)
async def job_hunt_stop() -> OrchestratorStatus:
    return await get_job_application_orchestrator().stop()


@router.get("/activity", response_model=list[ActivityEntry])
async def activity_feed(
    limit: int = 120,
    db: AsyncSession = Depends(get_db),
) -> list[ActivityEntry]:
    entries: list[ActivityEntry] = []

    job_rows = await db.execute(
        select(Job, Company)
        .join(Company, Company.id == Job.company_id)
        .order_by(desc(Job.created_at))
        .limit(limit)
    )
    for job, company in job_rows.all():
        entries.append(
            ActivityEntry(
                timestamp=job.created_at.isoformat(),
                category="jobs",
                title="Job discovered",
                detail=f"{job.title} @ {company.name}",
                job_id=job.id,
                payload={"source_url": job.source_url, "ats_source": job.ats_source},
            )
        )

    resume_rows = await db.execute(
        select(ResumeVersion, Job, Company)
        .join(Job, Job.id == ResumeVersion.job_id)
        .join(Company, Company.id == Job.company_id)
        .order_by(desc(ResumeVersion.created_at))
        .limit(limit)
    )
    for resume, job, company in resume_rows.all():
        entries.append(
            ActivityEntry(
                timestamp=resume.created_at.isoformat(),
                category="resumes",
                title="Resume generated",
                detail=f"{job.title} @ {company.name}",
                job_id=job.id,
                payload={"docx_path": resume.docx_path, "pdf_path": resume.pdf_path},
            )
        )

    event_rows = await db.execute(
        select(ApplicationEvent)
        .order_by(desc(ApplicationEvent.created_at))
        .limit(limit)
    )
    for event in event_rows.scalars().all():
        entries.append(
            ActivityEntry(
                timestamp=event.created_at.isoformat(),
                category="automation",
                title=event.event_type,
                detail="application automation event",
                application_id=event.application_id,
                payload=event.payload,
            )
        )

    entries.extend(_log_activity_entries(limit=limit))

    entries.sort(key=lambda entry: entry.timestamp, reverse=True)
    return entries[:limit]


def _persist_discovery_defaults(discovery: JobDiscoveryConfig) -> None:
    preferences_path = user_config_path("preferences.yaml")
    prefs_raw = yaml.safe_load(preferences_path.read_text(encoding="utf-8")) or {}
    if not isinstance(prefs_raw, dict):
        raise HTTPException(status_code=500, detail="preferences.yaml root must be an object")

    prefs_raw["role_keywords"] = discovery.keywords
    prefs_raw["locations"] = discovery.locations
    prefs_raw["target_companies"] = discovery.companies
    prefs_raw["remote_preference"] = discovery.remote_preference

    preferences_path.write_text(yaml.safe_dump(prefs_raw, sort_keys=False), encoding="utf-8")

    if discovery.urls:
        job_sources_path = user_config_path("job_sources.yaml")
        sources_raw = yaml.safe_load(job_sources_path.read_text(encoding="utf-8")) or {}
        if not isinstance(sources_raw, dict):
            raise HTTPException(status_code=500, detail="job_sources.yaml root must be an object")
        sources = sources_raw.get("sources", [])
        if not isinstance(sources, list):
            sources = []
        updated = False
        for source in sources:
            if not isinstance(source, dict):
                continue
            if source.get("type") == "url_list" or source.get("name") == "manual-urls":
                config = source.get("config") or {}
                if not isinstance(config, dict):
                    config = {}
                config["urls"] = discovery.urls
                source["config"] = config
                source.setdefault("enabled", True)
                source.setdefault("name", "manual-urls")
                source.setdefault("type", "url_list")
                updated = True
                break
        if not updated:
            sources.append(
                {
                    "name": "manual-urls",
                    "type": "url_list",
                    "enabled": True,
                    "config": {"urls": discovery.urls},
                }
            )
        sources_raw["sources"] = sources
        job_sources_path.write_text(yaml.safe_dump(sources_raw, sort_keys=False), encoding="utf-8")

    reload_config()


def _log_activity_entries(*, limit: int) -> list[ActivityEntry]:
    lines = _tail_json_lines(LOG_DIR / "app.log", max_lines=max(limit * 4, 400))
    entries: list[ActivityEntry] = []
    for obj in reversed(lines):
        event = str(obj.get("event", ""))
        if not _is_control_center_event(event):
            continue
        payload = {
            key: value
            for key, value in obj.items()
            if key not in {"timestamp", "level", "logger", "event", "app"}
        }
        entries.append(
            ActivityEntry(
                timestamp=str(obj.get("timestamp", datetime.now(UTC).isoformat())),
                category="runtime",
                title=event,
                detail=str(obj.get("message") or ""),
                payload=payload,
            )
        )
        if len(entries) >= limit:
            break
    return entries


def _is_control_center_event(event: str) -> bool:
    event = event.lower()
    return any(
        token in event
        for token in [
            "job_hunt",
            "orchestrator.",
            "ingest.",
            "score.",
            "tailor.",
            "apply.",
        ]
    )


def _tail_json_lines(path: Path, *, max_lines: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    objs: list[dict[str, Any]] = []
    for line in lines[-max_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            objs.append(obj)
    return objs

@router.post("/discovery/start")
async def discovery_start(
    payload: SearchRequest,
    interval_minutes: int | None = None,
):
    from app.runtime.discovery_scheduler import get_discovery_scheduler

    if payload.save_defaults:
        _persist_discovery_defaults(payload.discovery)
    return await get_discovery_scheduler().start(
        interval_minutes=interval_minutes,
        discovery=payload.discovery,
    )


@router.post("/discovery/pause")
async def discovery_pause():
    from app.runtime.discovery_scheduler import get_discovery_scheduler

    return await get_discovery_scheduler().pause()


@router.post("/discovery/resume")
async def discovery_resume():
    from app.runtime.discovery_scheduler import get_discovery_scheduler

    return await get_discovery_scheduler().resume()


@router.post("/discovery/stop")
async def discovery_stop():
    from app.runtime.discovery_scheduler import get_discovery_scheduler

    return await get_discovery_scheduler().stop()


@router.post("/automation/pause-all")
async def pause_all_automation():
    from app.runtime.automation_runtime import get_automation_runtime
    from app.runtime.discovery_scheduler import get_discovery_scheduler

    await get_discovery_scheduler().pause()
    return await get_automation_runtime().pause_all_automation()


@router.get("/approvals/pending")
async def list_pending_approvals_compat(db: AsyncSession = Depends(get_db)):
    from app.api.routers.approvals import list_pending

    return await list_pending(db=db)


@router.post("/approvals/{approval_id}/approve")
async def approve_checkpoint_compat(approval_id: str):
    from app.services.approval_service import get_approval_service

    try:
        cid = int(approval_id.replace("submit_", ""))
    except ValueError:
        cid = int(approval_id) if approval_id.isdigit() else None
    if cid is None:
        from app.services.approval_manager import get_approval_manager

        get_approval_manager().approve(approval_id)
        return {"status": "ok"}
    await get_approval_service().approve(cid)
    return {"status": "ok"}


@router.post("/approvals/{approval_id}/reject")
async def reject_checkpoint_compat(approval_id: str):
    from app.services.approval_service import get_approval_service

    try:
        cid = int(approval_id.replace("submit_", ""))
    except ValueError:
        cid = int(approval_id) if approval_id.isdigit() else None
    if cid is None:
        from app.services.approval_manager import get_approval_manager

        get_approval_manager().reject(approval_id)
        return {"status": "ok"}
    await get_approval_service().reject(cid)
    return {"status": "ok"}
