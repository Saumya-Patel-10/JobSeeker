"""Job model — Pydantic domain model + SQLAlchemy ORM table.

``Job``       — Pydantic model used by pipelines, adapters, and the API layer.
``JobORM``    — SQLAlchemy ORM row (aliased to avoid name collision with Pydantic Job).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ATSSource, ApplicationStatus, RemoteType, JobStatus  # noqa: F401


# ── Pydantic domain model (used everywhere in pipelines + API) ───────────────

class Job(BaseModel):
    """Normalized job posting — produced by every ATS adapter's scrape_job()."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    title: str
    company: str
    location: str | None = None
    remote: RemoteType = RemoteType.unknown
    description: str = ""
    requirements: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    salary_period: str = "year"
    ats_source: ATSSource = ATSSource.generic
    source_url: str
    external_id: str | None = None
    keywords: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.open
    posted_at: datetime | None = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── SQLAlchemy ORM model ─────────────────────────────────────────────────────

try:
    import enum as _enum
    from datetime import datetime as _dt

    from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.db.base_class import Base as _Base  # type: ignore[import]

    class JobSource(_enum.Enum):
        LINKEDIN   = "linkedin"
        INDEED     = "indeed"
        GREENHOUSE = "greenhouse"
        OTHER      = "other"

    class JobORM(_Base):  # type: ignore[valid-type]
        """SQLAlchemy ORM table — use Job (Pydantic) in application logic."""

        __tablename__ = "jobs"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
        title: Mapped[str] = mapped_column(String(512), nullable=False)
        company: Mapped[str] = mapped_column(String(512), nullable=False)
        location: Mapped[str | None] = mapped_column(String(512), nullable=True)
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
        salary_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
        job_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
        ats_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
        source: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
        source_url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
        external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
        keywords_json: Mapped[str | None] = mapped_column(Text, nullable=True)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        posted_at: Mapped[_dt | None] = mapped_column(DateTime(timezone=True), nullable=True)
        discovered_at: Mapped[_dt] = mapped_column(DateTime(timezone=True), server_default=func.now())

        applications: Mapped[list] = relationship("Application", back_populates="job")  # type: ignore[type-arg]

except Exception:
    JobORM = None  # type: ignore[assignment, misc]
