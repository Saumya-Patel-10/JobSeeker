"""Shared string enums used by Pydantic models and SQLAlchemy rows alike.

Using string enums lets us serialize cleanly to JSON/YAML and store as plain
``VARCHAR`` columns in SQLite without dialect-specific ENUM types.
"""

from __future__ import annotations

import enum


class JobStatus(enum.StrEnum):
    open = "open"
    closed = "closed"
    expired = "expired"


class RemoteType(enum.StrEnum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"


class SalaryPeriod(enum.StrEnum):
    hour = "hour"
    month = "month"
    year = "year"


class ATSSource(enum.StrEnum):
    greenhouse = "greenhouse"
    lever = "lever"
    linkedin = "linkedin"
    generic = "generic"
    manual = "manual"


class ApplicationStatus(enum.StrEnum):
    draft = "draft"
    awaiting_review = "awaiting_review"
    submitted = "submitted"
    withdrawn = "withdrawn"
    rejected = "rejected"
    interviewing = "interviewing"
    offer = "offer"
    accepted = "accepted"


class ApplicationMode(enum.StrEnum):
    dry_run = "dry_run"
    human_review = "human_review"
    auto = "auto"


class JobHuntMode(enum.StrEnum):
    manual_review = "manual_review"
    assisted_apply = "assisted_apply"
    autonomous_apply = "autonomous_apply"
    linkedin_assist = "linkedin_assist"


class ResumeKind(enum.StrEnum):
    master = "master"
    tailored = "tailored"


class FieldType(enum.StrEnum):
    text = "text"
    textarea = "textarea"
    select = "select"
    multiselect = "multiselect"
    checkbox = "checkbox"
    radio = "radio"
    file = "file"
    date = "date"
    email = "email"
    phone = "phone"
    number = "number"
    url = "url"
    unknown = "unknown"


class AnswerSource(enum.StrEnum):
    profile = "profile"
    memory = "memory"
    llm = "llm"
    user = "user"


class Seniority(enum.StrEnum):
    intern = "intern"
    entry = "entry"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    principal = "principal"
