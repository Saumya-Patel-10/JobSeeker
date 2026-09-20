"""Application and form-filling domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnswerSource, ApplicationMode, ApplicationStatus, FieldType
from app.models.job import Job
from app.models.profile import Profile
from app.models.resume import TailoredResume


class GeneratedAnswer(BaseModel):
    """A question/answer pair from profile, memory, or the LLM."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    category: str | None = None
    source: AnswerSource = AnswerSource.llm
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FieldDescriptor(BaseModel):
    """One detected form field on an application page."""

    model_config = ConfigDict(extra="forbid")

    label: str
    selector: str
    field_type: FieldType = FieldType.unknown
    required: bool = False
    options: list[str] = Field(default_factory=list)
    suggested_answer: str | None = None
    answered_from: AnswerSource | None = None


class FillReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: int | None = None
    fields_filled: int = 0
    fields_skipped: int = 0
    fields_failed: int = 0
    screenshots: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SubmitReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: int | None = None
    submitted: bool = False
    confirmation_text: str | None = None
    error: str | None = None
    screenshot: str | None = None
    submitted_at: datetime | None = None


class DryRunReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: int
    adapter: str
    fields_detected: list[FieldDescriptor] = Field(default_factory=list)
    answers_prepared: list[GeneratedAnswer] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)


class ApplicationContext(BaseModel):
    """Everything an adapter needs to fill + submit an application."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    job: Job
    profile: Profile
    tailored_resume: TailoredResume
    resume_docx_path: str | None = None
    resume_pdf_path: str | None = None
    cover_letter: str | None = None
    memory_lookup: list[GeneratedAnswer] = Field(default_factory=list)
    mode: ApplicationMode = ApplicationMode.human_review


class ApplicationRecord(BaseModel):
    """A summary view of an Application row for the API and CLI."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    job_id: int
    status: ApplicationStatus
    mode: ApplicationMode
    submitted_at: datetime | None = None
    notes: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    created_at: datetime
    updated_at: datetime
