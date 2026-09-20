"""Job scoring domain model produced by the scoring pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


Score = Annotated[float, Field(ge=0.0, le=1.0)]


class JobScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: int
    fit_score: Score
    salary_fit: Score
    skill_overlap: Score
    seniority_alignment: Score
    location_compatibility: Score
    confidence: Score
    rationale: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    model_used: str
    scored_at: datetime = Field(default_factory=_utcnow)

    @property
    def composite(self) -> float:
        """Default composite score (callers can override using ScoringConfig.weights)."""
        return round(
            0.35 * self.skill_overlap
            + 0.20 * self.seniority_alignment
            + 0.15 * self.salary_fit
            + 0.15 * self.location_compatibility
            + 0.15 * self.fit_score,
            4,
        )
