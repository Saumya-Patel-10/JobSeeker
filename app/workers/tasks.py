"""
Celery tasks — the main orchestration pipeline.

Flow:
  1. process_application (AI Worker, ai_queue)
     a. Load application + user + job + resume from DB
     b. Score match → skip if < threshold
     c. Tailor resume (GPT-4o)         [all plans]
     d. Generate cover letter (GPT-4o) [BASIC + PRO]
     e. ATS optimise + interview prep  [PRO only]
     f. Trigger run_bot_application    (Bot Worker, bot_queue)

  2. run_bot_application (Bot Worker, bot_queue)
     a. Playwright opens job source URL
     b. Fills & submits application form
     c. Updates Application status → SUBMITTED

  3. run_job_discovery (AI Worker, ai_queue)
     a. Calls scrapers for LinkedIn, Indeed, Greenhouse
     b. Scores each job against all users' master resumes
     c. Notifies matching users
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

try:
    from celery import shared_task
except ImportError:
    def shared_task(*args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **k: None
            func.apply_async = lambda *a, **k: None
            return func
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.resume import Resume
from app.models.job import Job
from app.models.user import User, PlanType
from app.services.ai_service import (
    score_match,
    tailor_resume,
    generate_cover_letter,
    ats_optimize_resume,
    generate_interview_questions,
)
from app.services.storage import upload_file_to_s3, generate_presigned_url
from app.services.notification import send_job_match_notification
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.indeed import IndeedScraper
from app.scrapers.greenhouse import GreenhouseScraper

logger = logging.getLogger(__name__)

MIN_MATCH_SCORE = 0.45   # Skip if below 45% match


def run_async(coro):
    """Run async coroutine in the Celery worker's event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — process_application  (AI Worker)
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="app.workers.tasks.process_application", max_retries=3)
def process_application(self, application_id: int, user_id: int):
    """AI Worker 1 — tailors resume and dispatches to Bot Worker."""
    try:
        run_async(_process_application_async(self, application_id, user_id))
    except Exception as exc:
        logger.error(f"process_application error: {exc}")
        run_async(_set_app_status(application_id, ApplicationStatus.FAILED, str(exc)))
        raise self.retry(exc=exc, countdown=60)


async def _process_application_async(task, application_id: int, user_id: int):
    async with AsyncSessionLocal() as db:
        # Load application
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        # Load related objects
        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one()

        resume_result = await db.execute(select(Resume).where(Resume.id == app.resume_id))
        resume = resume_result.scalar_one()

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()

        # ── Step 1: Score match ───────────────────────────────────────────────
        app.status = ApplicationStatus.TAILORING
        await db.commit()

        match_score = await score_match(resume.parsed_text or "", job.description or "")
        app.match_score = match_score

        if match_score < MIN_MATCH_SCORE:
            app.status = ApplicationStatus.SKIPPED
            await db.commit()
            logger.info(f"App {application_id} skipped. Score: {match_score:.2f}")
            return

        # ── Step 2: Tailor resume ─────────────────────────────────────────────
        tailored_docx_bytes = await tailor_resume(
            resume_text=resume.parsed_text or "",
            job_description=job.description or "",
            job_title=job.title,
            company=job.company,
        )
        tailored_key = f"tailored/{user_id}/{application_id}/tailored_resume.docx"
        await upload_file_to_s3(
            tailored_docx_bytes, tailored_key,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        app.tailored_resume_s3_key = tailored_key

        # ── Step 3: Cover letter (BASIC + PRO) ───────────────────────────────
        if user.plan_type in (PlanType.BASIC, PlanType.PRO):
            cover_letter_bytes = await generate_cover_letter(
                resume_text=resume.parsed_text or "",
                job_description=job.description or "",
                job_title=job.title,
                company=job.company,
                style_snapshot=resume.style_snapshot,
            )
            cl_key = f"cover_letters/{user_id}/{application_id}/cover_letter.docx"
            await upload_file_to_s3(cover_letter_bytes, cl_key,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            app.cover_letter_s3_key = cl_key

        # ── Step 4: ATS optimize + interview prep (PRO) ───────────────────────
        if user.plan_type == PlanType.PRO:
            ats_bytes = await ats_optimize_resume(tailored_docx_bytes, job.description or "")
            ats_key = f"ats/{user_id}/{application_id}/ats_resume.docx"
            await upload_file_to_s3(ats_bytes, ats_key,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            app.tailored_resume_s3_key = ats_key   # use the ATS version
            app.ats_optimized = True

            interview_qs = await generate_interview_questions(
                job_description=job.description or "",
                resume_text=resume.parsed_text or "",
            )
            app.interview_questions_json = json.dumps(interview_qs)

        await db.commit()

    # ── Step 5: Dispatch Bot Worker ───────────────────────────────────────────
    run_bot_application.apply_async(
        args=[application_id],
        queue="bot_queue",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — run_bot_application  (Bot Worker)
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="app.workers.tasks.run_bot_application", max_retries=2)
def run_bot_application(self, application_id: int):
    """Bot Worker 2 — Playwright automation for form submission."""
    try:
        run_async(_run_bot_async(self, application_id))
    except Exception as exc:
        logger.error(f"run_bot_application error: {exc}")
        run_async(_set_app_status(application_id, ApplicationStatus.FAILED, str(exc)))
        raise self.retry(exc=exc, countdown=120)


async def _run_bot_async(task, application_id: int):
    from app.services.bot_service import JobApplicationBot

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one()

        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one()

        resume_url = await generate_presigned_url(app.tailored_resume_s3_key)
        cover_letter_url = (
            await generate_presigned_url(app.cover_letter_s3_key)
            if app.cover_letter_s3_key else None
        )

        app.status = ApplicationStatus.APPLYING
        await db.commit()

    # Run Playwright bot
    bot = JobApplicationBot()
    success, error = await bot.apply(
        job_url=job.source_url,
        job_source=job.source,
        resume_url=resume_url,
        cover_letter_url=cover_letter_url,
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one()
        if success:
            app.status = ApplicationStatus.SUBMITTED
            app.applied_at = datetime.now(timezone.utc)
        else:
            app.status = ApplicationStatus.FAILED
            app.error_message = error
        await db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — run_job_discovery  (Scheduled, AI Worker)
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.run_job_discovery")
def run_job_discovery():
    """Scheduled task — scrape job boards and match against user resumes."""
    run_async(_job_discovery_async())


async def _job_discovery_async():
    scrapers = [
        LinkedInScraper(),
        IndeedScraper(),
        GreenhouseScraper(),
    ]

    async with AsyncSessionLocal() as db:
        all_jobs: list[dict] = []
        for scraper in scrapers:
            try:
                jobs = await scraper.fetch_jobs()
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Scraper {scraper.__class__.__name__} failed: {e}")

        # Persist new jobs
        new_jobs = []
        for job_data in all_jobs:
            existing = await db.execute(
                select(Job).where(Job.source_url == job_data["source_url"])
            )
            if not existing.scalar_one_or_none():
                job = Job(**job_data)
                db.add(job)
                new_jobs.append(job)

        await db.commit()

        # Match new jobs against all active users' master resumes
        users_result = await db.execute(select(User).where(User.is_active == True))
        users = users_result.scalars().all()

        for user in users:
            master_result = await db.execute(
                select(Resume).where(
                    Resume.user_id == user.id,
                    Resume.is_master == True,
                    Resume.is_active == True,
                )
            )
            master = master_result.scalar_one_or_none()
            if not master or not master.parsed_text:
                continue

            for job in new_jobs:
                if not job.description:
                    continue
                score = await score_match(master.parsed_text, job.description)
                if score >= 0.6:
                    await send_job_match_notification(user, job, score)


# ─── Utility ─────────────────────────────────────────────────────────────────

async def _set_app_status(application_id: int, status: ApplicationStatus, error: str = None):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if app:
            app.status = status
            if error:
                app.error_message = error
            await db.commit()
