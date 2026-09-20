"""User profile domain model.

This is what gets validated from ``config/profile.yaml`` and what every
pipeline consumes for personal information, work authorization, and
standardized application answers.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AddressInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "United States"


class PersonalInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    email: str
    phone: str
    address: AddressInfo | None = None
    pronouns: str | None = None
    date_of_birth: date | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Links(BaseModel):
    model_config = ConfigDict(extra="allow")

    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    portfolio: HttpUrl | None = None
    website: HttpUrl | None = None
    twitter: HttpUrl | None = None


class WorkAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorized_to_work_in: list[str] = Field(default_factory=lambda: ["United States"])
    requires_sponsorship: bool = False
    visa_status: str | None = None


class SalaryExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str = "USD"
    minimum: int | None = None
    target: int | None = None
    maximum: int | None = None
    period: Literal["hour", "month", "year"] = "year"


class RelocationPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    willing_to_relocate: bool = False
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: Literal["remote", "hybrid", "onsite", "no_preference"] = "no_preference"


class DemographicAnswers(BaseModel):
    """EEOC voluntary self-identification answers."""

    model_config = ConfigDict(extra="forbid")

    gender: str | None = None
    race_ethnicity: list[str] = Field(default_factory=list)
    veteran_status: str | None = None
    disability_status: str | None = None
    decline_to_self_identify: bool = False


class StandardAnswer(BaseModel):
    """A pre-canned answer to a common application question."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    category: str | None = None


class EducationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: str
    degree: str
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    gpa: float | None = None
    honors: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    issuer: str | None = None
    issued: str | None = None
    expires: str | None = None
    credential_id: str | None = None
    url: HttpUrl | None = None


class EmploymentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    title: str
    location: str | None = None
    start: str  # ``YYYY-MM``
    end: str | None = None  # ``YYYY-MM`` or ``None`` if current
    current: bool = False
    bullets: list[str] = Field(default_factory=list)
    tech: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personal: PersonalInfo
    links: Links = Field(default_factory=Links)
    work_authorization: WorkAuthorization = Field(default_factory=WorkAuthorization)
    salary: SalaryExpectations = Field(default_factory=SalaryExpectations)
    relocation: RelocationPreferences = Field(default_factory=RelocationPreferences)
    demographic: DemographicAnswers = Field(default_factory=DemographicAnswers)
    standard_answers: list[StandardAnswer] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    employment: list[EmploymentEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
