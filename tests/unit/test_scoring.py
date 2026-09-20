"""Score composite math."""

from __future__ import annotations

from app.config.schema import ScoringWeights
from app.models.scoring import JobScore
from app.pipelines.score_pipeline import _composite


def test_perfect_match_composite_is_one() -> None:
    score = JobScore(
        job_id=1,
        fit_score=1.0,
        salary_fit=1.0,
        skill_overlap=1.0,
        seniority_alignment=1.0,
        location_compatibility=1.0,
        confidence=1.0,
        rationale="",
        model_used="t",
    )
    assert _composite(score, ScoringWeights()) == 1.0


def test_zero_match_composite_is_zero() -> None:
    score = JobScore(
        job_id=1,
        fit_score=0.0,
        salary_fit=0.0,
        skill_overlap=0.0,
        seniority_alignment=0.0,
        location_compatibility=0.0,
        confidence=0.0,
        rationale="",
        model_used="t",
    )
    assert _composite(score, ScoringWeights()) == 0.0


def test_composite_within_unit_interval() -> None:
    score = JobScore(
        job_id=1,
        fit_score=0.5,
        salary_fit=0.7,
        skill_overlap=0.8,
        seniority_alignment=0.6,
        location_compatibility=0.9,
        confidence=0.7,
        rationale="",
        model_used="t",
    )
    composite = _composite(score, ScoringWeights())
    assert 0.0 <= composite <= 1.0
