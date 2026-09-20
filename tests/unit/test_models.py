"""Pydantic model validation invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.enums import ATSSource
from app.models.job import Job
from app.models.profile import (
    EmploymentEntry,
    PersonalInfo,
    Profile,
)
from app.models.scoring import JobScore


def _make_profile() -> Profile:
    return Profile(
        personal=PersonalInfo(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="+1-555-0100",
        )
    )


def test_profile_full_name() -> None:
    profile = _make_profile()
    assert profile.personal.full_name == "Ada Lovelace"


def test_profile_rejects_unknown_top_level_key() -> None:
    with pytest.raises(ValidationError):
        Profile(  # type: ignore[call-arg]
            personal=PersonalInfo(
                first_name="A",
                last_name="B",
                email="a@b.com",
                phone="+1",
            ),
            bogus="x",
        )


def test_employment_entry_allows_current() -> None:
    e = EmploymentEntry(
        company="Acme",
        title="SWE",
        start="2024-01",
        end=None,
        current=True,
        bullets=["did things"],
    )
    assert e.current and e.end is None


def test_job_score_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        JobScore(
            job_id=1,
            fit_score=1.5,  # out of [0, 1]
            salary_fit=0.5,
            skill_overlap=0.5,
            seniority_alignment=0.5,
            location_compatibility=0.5,
            confidence=0.5,
            rationale="",
            model_used="local",
        )


def test_job_round_trip() -> None:
    job = Job(
        title="Backend Engineer",
        company="Acme",
        description_text="Build APIs.",
        source_url="https://example.com/job/1",
        url_hash="abc",
        ats_source=ATSSource.greenhouse,
    )
    payload = job.model_dump(mode="json")
    again = Job.model_validate(payload)
    assert again.title == job.title
    assert again.ats_source == ATSSource.greenhouse
