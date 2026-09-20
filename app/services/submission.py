"""Single gateway for application submission — no bypasses."""

from __future__ import annotations

from app.ats.registry import adapter_for
from app.config.loader import load_config
from app.database.dao import applications as apps_dao
from app.database.dao import approvals as approvals_dao
from app.database.dao import jobs as jobs_dao
from app.database.dao import resume_versions as resume_dao
from app.database.session import session_scope
from app.llm.factory import provider_session
from app.llm.prompts import PromptRegistry
from app.models.application import ApplicationContext, ApplicationMode, ApplicationStatus, SubmitReport
from app.models.job import Job
from app.models.resume import TailoredResume
from app.runtime.automation_runtime import get_automation_runtime
from app.services.event_bus import get_event_bus
from app.utils.errors import AdapterError, SubmitError
from app.utils.logging import get_logger

log = get_logger(__name__)


class SubmissionNotAllowedError(AdapterError):
    """Raised when submission preconditions are not met."""


async def submit_application_if_approved(
    application_id: int,
    *,
    checkpoint_id: int | None = None,
) -> SubmitReport:
    """Submit only when a pre_submit checkpoint is approved. This is the ONLY submit path."""
    async with session_scope() as db:
        app_row = await apps_dao.get_by_id(db, application_id)
        if app_row is None:
            raise SubmissionNotAllowedError(f"Application {application_id} not found")

        checkpoint = None
        if checkpoint_id is not None:
            checkpoint = await approvals_dao.get_by_id(db, checkpoint_id)
        else:
            from sqlalchemy import select
            from app.database.models import ApprovalCheckpoint

            stmt = (
                select(ApprovalCheckpoint)
                .where(
                    ApprovalCheckpoint.application_id == application_id,
                    ApprovalCheckpoint.checkpoint_type == "pre_submit",
                    ApprovalCheckpoint.status == "approved",
                )
                .order_by(ApprovalCheckpoint.resolved_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            checkpoint = result.scalar_one_or_none()

        if checkpoint is None:
            raise SubmissionNotAllowedError(
                "No approved pre_submit checkpoint for this application"
            )
        if checkpoint.status != "approved":
            raise SubmissionNotAllowedError(
                f"Checkpoint {checkpoint.id} is not approved (status={checkpoint.status})"
            )
        if checkpoint.application_id != application_id:
            raise SubmissionNotAllowedError("Checkpoint does not match application")

        job_row = await jobs_dao.get_by_id(db, app_row.job_id)
        resume_row = await resume_dao.latest_for_job(db, app_row.job_id)

    if job_row is None or resume_row is None:
        raise SubmissionNotAllowedError("Missing job or resume for submission")

    job = _job_from_row(job_row)
    if job.ats_source.value == "linkedin":
        raise SubmissionNotAllowedError(
            "LinkedIn is assist-only — complete submission manually in Firefox"
        )

    config = load_config()
    if not config.preferences.apply.allow_auto_submit:
        raise SubmissionNotAllowedError("allow_auto_submit is disabled in preferences")

    payload = checkpoint.payload or {}
    if payload.get("assist_only"):
        raise SubmissionNotAllowedError("Application is marked assist-only")

    tailored = TailoredResume.model_validate(resume_row.json_payload)
    ctx = ApplicationContext(
        job=job,
        profile=config.profile,
        tailored_resume=tailored,
        resume_docx_path=resume_row.docx_path,
        resume_pdf_path=resume_row.pdf_path,
        cover_letter=app_row.cover_letter,
        memory_lookup=[],
        mode=ApplicationMode(app_row.mode),
    )

    runtime = get_automation_runtime()
    if not await runtime.await_ready():
        raise SubmissionNotAllowedError("Automation runtime is stopped")

    get_event_bus().emit(
        "orchestrator.submitting",
        {"application_id": application_id, "checkpoint_id": checkpoint.id},
    )

    async with provider_session(config.preferences.llm) as llm:
        prompts = PromptRegistry(config.prompts)
        session = await runtime.get_browser_session(
            session_id=f"apply_{application_id}",
            application_id=application_id,
            config=config.preferences.browser,
        )
        adapter = adapter_for(job.source_url, session=session, llm=llm, prompts=prompts)
        try:
            submit_report = await adapter.submit(ctx)
        except SubmitError as exc:
            async with session_scope() as db:
                await apps_dao.add_event(
                    db, application_id, "apply.submit_failed", {"error": str(exc)}
                )
            raise

    async with session_scope() as db:
        status = (
            ApplicationStatus.submitted
            if submit_report.submitted
            else ApplicationStatus.draft
        )
        await apps_dao.update_status(
            db,
            application_id,
            status,
            confirmation_text=submit_report.confirmation_text,
        )
        await apps_dao.add_event(
            db,
            application_id,
            "apply.submitted" if submit_report.submitted else "apply.submit_failed",
            submit_report.model_dump(mode="json"),
        )

    get_event_bus().emit(
        "orchestrator.submitted",
        {
            "application_id": application_id,
            "submitted": submit_report.submitted,
        },
    )
    log.info(
        "submission.complete",
        application_id=application_id,
        submitted=submit_report.submitted,
    )
    return submit_report


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
