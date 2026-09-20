"""LLM-driven cover letter generation."""

from __future__ import annotations

from app.llm.base import ChatMessage, LLMProvider
from app.llm.prompts import PromptRegistry
from app.models.job import Job
from app.models.profile import Profile
from app.models.resume import TailoredResume


async def generate_cover_letter(
    *,
    job: Job,
    profile: Profile,
    resume: TailoredResume,
    provider: LLMProvider,
    prompts: PromptRegistry,
) -> str:
    entry = prompts.get_entry("cover_letter")
    rendered = prompts.render(
        "cover_letter",
        job=job,
        profile=profile,
        resume=resume,
    )
    text = await provider.chat(
        [
            ChatMessage(
                role="system",
                content="You write tailored cover letters in clear, honest prose.",
            ),
            ChatMessage(role="user", content=rendered),
        ],
        temperature=entry.temperature,
        max_tokens=entry.max_tokens,
    )
    return text.strip()
