"""Apply pipeline — prepare applications (fill only). Submission via submission.py only."""

from __future__ import annotations

from dataclasses import dataclass

from app.ats.registry import adapter_for
from app.config.loader import load_config
from app.database.dao import applications as apps_dao
from app.database.dao import job_scores as scores_dao
from app.database.dao import jobs as jobs_dao
from app.database.dao import resume_versions as resume_dao
from app.database.session import session_scope
from app.llm.factory import provider_session
from app.llm.prompts import PromptRegistry
from app.models.application import (
    ApplicationContext,
    ApplicationMode,
    ApplicationStatus,
    DryRunReport,
    FillReport,
)
from app.models.job import Job
from app.models.resume import TailoredResume
from app.runtime.automation_runtime import get_automation_runtime
from app.services.approval_service import get_approval_service
from app.services.event_bus import get_event_bus
from app.utils.errors import AdapterError
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ApplyResult:
    application_id: int | None
    mode: ApplicationMode
    fill: FillReport | None = None
    dry_run: DryRunReport | None = None
    approval_checkpoint_id: int | None = None


async def prepare_application(
    job_id: int,
    *,
    mode: ApplicationMode | None = None,
    allow_auto: bool = False,
    session_id: str | None = None,
) -> ApplyResult:
    """Fill application form and create approval checkpoint. Does NOT submit."""
    config = load_config()
    resolved_mode = mode or config.preferences.apply.default_mode
    runtime = get_automation_runtime()
    sid = session_id or f"apply_{job_id}"

    if not await runtime.await_ready():
        raise AdapterError("Automation stopped")

    async with session_scope() as db:
        job_row = await jobs_dao.get_by_id(db, job_id)
        if job_row is None:
            raise ValueError(f"Job id {job_id} not found")
        resume_row = await resume_dao.latest_for_job(db, job_id)
        if resume_row is None:
            raise AdapterError(
                f"No tailored resume found for job {job_id}; run generate-resume first."
            )

    job = _job_from_row(job_row)
    tailored = TailoredResume.model_validate(resume_row.json_payload)

    ctx = ApplicationContext(
        job=job,
        profile=config.profile,
        tailored_resume=tailored,
        resume_docx_path=resume_row.docx_path,
        resume_pdf_path=resume_row.pdf_path,
        cover_letter=None,
        memory_lookup=[],
        mode=resolved_mode,
    )

    async with session_scope() as db:
        app_row = await apps_dao.create(
            db,
            job_id=job_id,
            profile_snapshot=config.profile.model_dump(mode="json"),
            resume_version_id=resume_row.id,
            mode=resolved_mode,
            status=ApplicationStatus.draft,
            source=job.ats_source.value,
        )
        application_id = app_row.id
        await apps_dao.add_event(db, application_id, "apply.start", {"mode": resolved_mode.value})

    async with provider_session(config.preferences.llm) as llm:
        prompts = PromptRegistry(config.prompts)
        session = await runtime.get_browser_session(
            session_id=sid, application_id=application_id, config=config.preferences.browser
        )
        adapter = adapter_for(job.source_url, session=session, llm=llm, prompts=prompts)

        if resolved_mode == ApplicationMode.dry_run:
            report = await adapter.dry_run(ctx)
            async with session_scope() as db:
                await apps_dao.add_event(
                    db,
                    application_id,
                    "apply.dry_run",
                    {"fields_detected": len(report.fields_detected)},
                )
            return ApplyResult(
                application_id=application_id, mode=resolved_mode, dry_run=report
            )

        runtime.update_browser_context(task=f"Filling application: {job.title}")
        get_event_bus().emit(
            "browser.form_step",
            {"step": "fill_start", "job_id": job_id, "application_id": application_id},
        )
        fill = await adapter.fill_application(ctx)
        async with session_scope() as db:
            await apps_dao.add_event(
                db,
                application_id,
                "apply.filled",
                fill.model_dump(mode="json"),
            )

        confidence, rationale, risks = await _load_score_context(job_id)
        checkpoint_id = await _create_submit_checkpoint(
            application_id=application_id,
            job_id=job_id,
            job=job,
            resume_version_id=resume_row.id,
            confidence=confidence,
            rationale=rationale,
            risks=risks,
            fill=fill,
            mode=resolved_mode,
        )

        async with session_scope() as db:
            await apps_dao.update_status(db, application_id, ApplicationStatus.awaiting_review)
            await apps_dao.add_event(
                db,
                application_id,
                "apply.awaiting_review",
                {"screenshots": fill.screenshots, "checkpoint_id": checkpoint_id},
            )

        get_event_bus().emit(
            "approval.pause",
            {
                "application_id": application_id,
                "checkpoint_id": checkpoint_id,
                "job_id": job_id,
                "allow_auto": allow_auto,
            },
        )
        log.info(
            "apply.prepared",
            job_id=job_id,
            application_id=application_id,
            checkpoint_id=checkpoint_id,
        )
        return ApplyResult(
            application_id=application_id,
            mode=resolved_mode,
            fill=fill,
            approval_checkpoint_id=checkpoint_id,
        )


async def apply_to_job(
    job_id: int,
    *,
    mode: ApplicationMode | None = None,
    allow_auto: bool = False,
    session_id: str | None = None,
) -> ApplyResult:
    """CLI/API alias — prepare only; use submit_application_if_approved to submit."""
    return await prepare_application(
        job_id, mode=mode, allow_auto=allow_auto, session_id=session_id
    )


async def _load_score_context(job_id: int) -> tuple[float | None, str, list[str]]:
    async with session_scope() as db:
        score_row = await scores_dao.latest_for_job(db, job_id)
    if score_row is None:
        return None, "", []
    risks: list[str] = []
    if score_row.confidence < 0.5:
        risks.append("Low confidence score")
    if score_row.composite < 0.6:
        risks.append("Below composite threshold")
    return score_row.confidence, score_row.rationale, risks


async def _create_submit_checkpoint(
    *,
    application_id: int,
    job_id: int,
    job: Job,
    resume_version_id: int,
    confidence: float | None,
    rationale: str,
    risks: list[str],
    fill: FillReport,
    mode: ApplicationMode,
) -> int:
    if fill.fields_skipped > 0 or any("unanswered" in n.lower() for n in fill.notes):
        risks = list(risks) + ["Unanswered or skipped form fields detected"]
    return await get_approval_service().create_checkpoint(
        application_id=application_id,
        job_id=job_id,
        checkpoint_type="pre_submit",
        confidence=confidence,
        resume_version_id=resume_version_id,
        ai_summary=rationale,
        risks=risks,
        payload={
            "company": job.company,
            "role": job.title,
            "mode": mode.value,
            "screenshots": fill.screenshots,
            "assist_only": job.ats_source.value == "linkedin",
        },
    )


def _job_from_row(row) -> Job:
    return Job(
        id=row.id,
        external_id=row.external_id,
        title=row.title,
        company=row.company.name,
        location=row.location,
        remote_type=row.remote_type,
        description_text=row.description_text,
        description_html=row.description_html,
        salary_min=row.salary_min,
        salary_max=row.salary_max,
        salary_currency=row.salary_currency,
        salary_period=row.salary_period,
        source_url=row.source_url,
        ats_source=row.ats_source,
        url_hash=row.url_hash,
        posted_at=row.posted_at,
        scraped_at=row.scraped_at,
        status=row.status,
        raw_payload=row.raw_payload,
    )
