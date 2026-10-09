"""Score a job against the user's profile using the LLM + deterministic mix."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import ValidationError

from app.config.loader import load_config
from app.config.schema import ScoringWeights
from app.database.dao import job_scores as job_scores_dao
from app.database.dao import jobs as jobs_dao
from app.database.session import session_scope
from app.llm.base import ChatMessage
from app.llm.factory import provider_session
from app.llm.prompts import PromptRegistry
from app.models.job import Job
from app.models.scoring import JobScore
from app.utils.errors import LLMValidationError
from app.utils.logging import get_logger

log = get_logger(__name__)


async def score_job(job: Job) -> JobScore:
    """Compute and persist a :class:`JobScore` for ``job``."""
    config = load_config()
    prompts = PromptRegistry(config.prompts)
    weights = config.preferences.scoring.weights

    score: JobScore | None = None
    try:
        rendered = prompts.render(
            "job_match",
            job=job,
            profile=config.profile,
            preferences=config.preferences,
        )
        entry = prompts.get_entry("job_match")

        async with provider_session(config.preferences.llm) as provider:
            raw = await provider.chat_json(
                [
                    ChatMessage(
                        role="system",
                        content="You are a brutally honest technical recruiter.",
                    ),
                    ChatMessage(role="user", content=rendered),
                ],
                temperature=entry.temperature,
                max_tokens=entry.max_tokens,
            )
            model_used = provider.chat_model

        raw["job_id"] = job.id or 0
        raw["model_used"] = model_used
        raw.setdefault("matched_skills", [])
        raw.setdefault("missing_skills", [])
        raw.setdefault("rationale", "")
        score = JobScore.model_validate(raw)
    except Exception as exc:
        log.warning("score.llm_unavailable_fallback", job_id=job.id, error=str(exc))
        from app.resume.master import load_master
        master = load_master()
        score = _heuristic_score(job, config, master)

    composite = _composite(score, weights)

    async with session_scope() as db:
        await job_scores_dao.create(db, score, composite=composite)

    log.info(
        "score.success",
        job_id=job.id,
        composite=composite,
        fit=score.fit_score,
        skills=score.skill_overlap,
    )
    return score


async def score_existing_job(job_id: int) -> JobScore:
    """Convenience wrapper: load a persisted job by id then score it."""
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
    return await score_job(job)


def _composite(score: JobScore, weights: ScoringWeights) -> float:
    """Deterministic blend of the five sub-scores using config weights."""
    values: Iterable[tuple[float, float]] = (
        (score.skill_overlap, weights.skill_overlap),
        (score.seniority_alignment, weights.seniority_alignment),
        (score.salary_fit, weights.salary_fit),
        (score.location_compatibility, weights.location_compatibility),
        (score.fit_score, weights.fit_score),
    )
    total_weight = sum(w for _, w in values) or 1.0
    return round(sum(s * w for s, w in values) / total_weight, 4)


def _heuristic_score(job: Job, config, master) -> JobScore:
    """Heuristic scoring fallback when LLM is unavailable."""
    text = f"{job.title} {job.description_text}".lower()
    skills = getattr(master, "skills", []) or []
    matched = [s for s in skills if s.lower() in text]
    missing = [s for s in skills[:12] if s not in matched][:5]

    if matched:
        skill_overlap = min(1.0, max(0.5, len(matched) / 6.0))
    elif any(kw in text for kw in ("software", "developer", "engineer", "code", "programming", "intern")):
        skill_overlap = 0.65
    else:
        skill_overlap = 0.50

    title_lower = job.title.lower()
    if any(k in title_lower for k in ("intern", "internship", "co-op", "student")):
        seniority = 0.95
    elif any(k in title_lower for k in ("junior", "entry", "associate", "new grad", "early career")):
        seniority = 0.90
    elif any(k in title_lower for k in ("senior", "lead", "staff", "principal", "director", "manager", "head")):
        seniority = 0.45
    else:
        seniority = 0.75

    loc_str = (job.location or "").lower()
    if getattr(job.remote_type, "value", "") == "remote" or "remote" in loc_str:
        loc_fit = 0.95
    elif any(c in loc_str for c in ("austin", "dallas", "richardson", "tx", "texas")):
        loc_fit = 1.0
    else:
        loc_fit = 0.85

    salary_fit = 0.85
    fit_score = round((skill_overlap + seniority + loc_fit) / 3.0, 2)

    return JobScore(
        job_id=job.id or 0,
        fit_score=fit_score,
        salary_fit=salary_fit,
        skill_overlap=round(skill_overlap, 2),
        seniority_alignment=round(seniority, 2),
        location_compatibility=round(loc_fit, 2),
        confidence=0.85,
        rationale=f"Heuristic match based on {len(matched)} matched skills: {', '.join(matched[:4]) or 'general software engineering profile'}",
        matched_skills=matched,
        missing_skills=missing,
        model_used="heuristic",
    )

