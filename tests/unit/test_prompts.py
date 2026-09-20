"""Jinja2 prompt registry rendering."""

from __future__ import annotations

import pytest

from app.config.schema import PromptEntry, PromptsConfig
from app.llm.prompts import PromptRegistry
from app.models.enums import ATSSource
from app.models.job import Job
from app.models.profile import PersonalInfo, Profile


def _profile() -> Profile:
    return Profile(
        personal=PersonalInfo(
            first_name="A",
            last_name="B",
            email="a@b.com",
            phone="+1",
        ),
        skills=["python"],
    )


def _job() -> Job:
    return Job(
        title="Backend Engineer",
        company="Acme",
        description_text="Build APIs.",
        source_url="https://example.com/job/1",
        url_hash="x",
        ats_source=ATSSource.greenhouse,
    )


def test_renders_job_match_prompt() -> None:
    config = PromptsConfig(
        prompts={
            "job_match": PromptEntry(template="job_match.j2", response_format="json"),
        }
    )
    registry = PromptRegistry(config)
    from app.config.schema import Preferences

    text = registry.render(
        "job_match",
        job=_job(),
        profile=_profile(),
        preferences=Preferences(),
    )
    assert "Backend Engineer" in text
    assert "fit_score" in text


def test_missing_prompt_raises_key_error() -> None:
    registry = PromptRegistry(PromptsConfig())
    with pytest.raises(KeyError):
        registry.render("does_not_exist")
