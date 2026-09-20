"""LLM-driven resume tailoring."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.llm.base import ChatMessage, LLMProvider
from app.llm.prompts import PromptRegistry
from app.models.job import Job
from app.models.resume import ResumeMaster, TailoredResume
from app.utils.errors import LLMValidationError
from app.utils.logging import get_logger

log = get_logger(__name__)


def pick_template(job: Job, _master: ResumeMaster) -> str:
    """Heuristic template picker — overridable by callers."""
    title = job.title.lower()
    desc = (job.description_text or "").lower()
    ml_terms = (
        "ml engineer",
        "machine learning",
        "data scientist",
        "ai engineer",
        "applied scientist",
    )
    backend_terms = ("backend", "platform", "infrastructure", "distributed", "site reliability")
    if any(t in title or t in desc[:1500] for t in ml_terms):
        return "ml"
    if any(t in title or t in desc[:1500] for t in backend_terms):
        return "backend"
    return "generic"


async def tailor_resume(
    *,
    job: Job,
    master: ResumeMaster,
    provider: LLMProvider,
    prompts: PromptRegistry,
    template: str | None = None,
) -> TailoredResume:
    """Ask the LLM to rewrite the master resume for the given job."""
    template = template or pick_template(job, master)
    entry = prompts.get_entry("resume_tailor")
    rendered = prompts.render(
        "resume_tailor",
        resume_json=master.model_dump_json(indent=2),
        job=job,
    )
    messages = [
        ChatMessage(
            role="system",
            content="You are an expert technical resume writer who never lies.",
        ),
        ChatMessage(role="user", content=rendered),
    ]
    raw = await provider.chat_json(
        messages,
        temperature=entry.temperature,
        max_tokens=entry.max_tokens,
    )

    _fill_defaults(raw, master, job, template, provider.chat_model)
    try:
        return TailoredResume.model_validate(raw)
    except ValidationError as exc:
        log.warning("tailor.validation_failed", error=str(exc))
        raise LLMValidationError(f"Tailored resume failed validation: {exc}") from exc


def _fill_defaults(
    raw: dict[str, Any],
    master: ResumeMaster,
    job: Job,
    template: str,
    model_name: str,
) -> None:
    raw.setdefault("skills", master.skills)
    raw.setdefault("employment", [e.model_dump(mode="json") for e in master.employment])
    raw.setdefault("education", [e.model_dump(mode="json") for e in master.education])
    raw.setdefault("projects", [p.model_dump(mode="json") for p in master.projects])
    raw.setdefault("keywords_targeted", [])
    raw["template"] = template
    raw["job_id"] = job.id
    raw["model_used"] = model_name
