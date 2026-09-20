"""Job domain model produced by ATS adapters and persisted in the DB."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ATSSource, JobStatus, RemoteType, SalaryPeriod


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Job(BaseModel):
    """A scraped job posting in normalized form."""

    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    external_id: str | None = None
    title: str
    company: str
    location: str | None = None
    remote_type: RemoteType = RemoteType.unknown

    description_text: str = ""
    description_html: str | None = None

    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    salary_period: SalaryPeriod = SalaryPeriod.year

    source_url: str
    ats_source: ATSSource = ATSSource.manual
    url_hash: str

    posted_at: datetime | None = None
    scraped_at: datetime = Field(default_factory=_utcnow)
    status: JobStatus = JobStatus.open

    raw_payload: dict[str, Any] | None = None
