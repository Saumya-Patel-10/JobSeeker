"""Resume tailoring pipeline.

Loads the master resume, asks the LLM to tailor it, renders DOCX + PDF, and
records a :class:`ResumeVersion` row.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from app.config.loader import load_config
from app.config.paths import RESUMES_GENERATED_DIR
from app.database.dao import jobs as jobs_dao
from app.database.dao import resume_versions as resume_dao
from app.database.session import session_scope
from app.llm.factory import provider_session
from app.llm.prompts import PromptRegistry
from app.models.enums import ResumeKind
from app.models.job import Job
from app.models.resume import TailoredResume
from app.resume.cover_letter import generate_cover_letter
from app.resume.master import load_master
from app.resume.renderers.docx_renderer import render_docx
from app.resume.renderers.pdf_renderer import render_pdf
from app.resume.tailor import tailor_resume
from app.utils.logging import get_logger

log = get_logger(__name__)


class TailorResult(NamedTuple):
    resume: TailoredResume
    docx_path: Path
    pdf_path: Path
    cover_letter: str | None
    resume_version_id: int


async def tailor_for_job(
    job: Job,
    *,
    write_cover_letter: bool = True,
) -> TailorResult:
    """Run the full tailor pipeline for a single job."""
    config = load_config()
    master = load_master()
    prompts = PromptRegistry(config.prompts)

    async with provider_session(config.preferences.llm) as provider:
        resume = await tailor_resume(
            job=job,
            master=master,
            provider=provider,
            prompts=prompts,
        )
        cover = None
        if write_cover_letter:
            cover = await generate_cover_letter(
                job=job,
                profile=config.profile,
                resume=resume,
                provider=provider,
                prompts=prompts,
            )

    job_dir = RESUMES_GENERATED_DIR / f"job_{job.id or 'unknown'}"
    job_dir.mkdir(parents=True, exist_ok=True)
    docx_path = render_docx(resume, config.profile, job_dir / "resume.docx")
    pdf_path = render_pdf(resume, config.profile, job_dir / "resume.pdf")
    if cover:
        (job_dir / "cover_letter.txt").write_text(cover, encoding="utf-8")

    async with session_scope() as db:
        row = await resume_dao.create(
            db,
            job_id=job.id,
            kind=ResumeKind.tailored,
            template=resume.template,
            docx_path=str(docx_path),
            pdf_path=str(pdf_path),
            json_payload=resume.model_dump(mode="json"),
            model_used=resume.model_used,
            ats_score_notes=resume.ats_score_notes,
        )
        version_id = row.id

    log.info(
        "tailor.success",
        job_id=job.id,
        docx=str(docx_path),
        pdf=str(pdf_path),
        template=resume.template,
    )
    return TailorResult(
        resume=resume,
        docx_path=docx_path,
        pdf_path=pdf_path,
        cover_letter=cover,
        resume_version_id=version_id,
    )


async def tailor_existing_job(
    job_id: int,
    *,
    write_cover_letter: bool = True,
) -> TailorResult:
    """Convenience wrapper to tailor by persisted job id."""
    async with session_scope() as db:
        row = await jobs_dao.get_by_id(db, job_id)
    if row is None:
        raise ValueError(f"Job id {job_id} not found")
    job = Job(
        id=row.id,
        external_id=row.external_id,
        title=row.title,
        company=row.company.name,
        location=row.location,
        remote_type=row.remote_type,  # type: ignore[arg-type]
        description_text=row.description_text,
        description_html=row.description_html,
        salary_min=row.salary_min,
        salary_max=row.salary_max,
        salary_currency=row.salary_currency,
        salary_period=row.salary_period,  # type: ignore[arg-type]
        source_url=row.source_url,
        ats_source=row.ats_source,  # type: ignore[arg-type]
        url_hash=row.url_hash,
        posted_at=row.posted_at,
        scraped_at=row.scraped_at,
        status=row.status,  # type: ignore[arg-type]
        raw_payload=row.raw_payload,
    )
    return await tailor_for_job(job, write_cover_letter=write_cover_letter)
