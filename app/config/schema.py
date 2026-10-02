"""Pydantic models describing the shape of every YAML config file.

These are pure "config" types. Domain types (Job, Profile, etc.) live in
``app/models/``. ``loader.load_config`` returns an ``AppConfig`` that bundles
every config plus the loaded ``Profile`` and ``ResumeMaster``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ApplicationMode, Seniority


class LLMConfig(BaseModel):
    """Local LLM provider configuration."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["lmstudio", "ollama"] = "lmstudio"
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "lm-studio"  # LM Studio ignores; placeholder keeps OpenAI client happy.
    chat_model: str = "local-model"
    embedding_model: str | None = None
    request_timeout: float = 120.0
    max_retries: int = 3
    temperature: float = 0.2

    @field_validator("base_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class BrowserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: Literal["firefox", "chromium", "webkit"] = "firefox"
    # Optional Playwright browser channel, e.g. "chrome" or "msedge".
    # Only used when engine is "chromium"; launches the locally installed
    # branded browser instead of Playwright's bundled Chromium build.
    channel: str | None = None
    persistent_profile: bool = True
    profile_source: Literal["managed", "system"] = "managed"
    firefox_profile: str | None = None
    # Chrome profile directory name (e.g. "Default", "Profile 1") used when
    # profile_source is "system" and the engine is "chromium". If null, the
    # profile signed in with account_email is chosen automatically.
    chrome_profile: str | None = None
    # Google account used to auto-select the Chrome profile when
    # chrome_profile is null (matches the profile signed in with this email).
    account_email: str | None = None
    headless: bool = False
    slowmo_ms: int = 50
    profile: str = "default"
    reuse_existing_session: bool = True
    clone_system_profile_on_lock: bool = True
    locale: str = "en-US"
    user_agent: str | None = None
    timeout_ms: int = 30000
    viewport_width: int = 1366
    viewport_height: int = 900


class ApplyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_mode: ApplicationMode = ApplicationMode.human_review
    allow_auto_submit: bool = False
    daily_limit: int = 20
    require_min_score: float = Field(default=0.6, ge=0.0, le=1.0)
    confirm_before_submit: bool = True


class AutomationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_concurrent_sessions: int = Field(default=1, ge=1, le=5)
    cooldown_seconds: int = Field(default=90, ge=0, le=3600)
    default_interval_minutes: int = Field(default=30, ge=1, le=720)


class ScoringWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_overlap: float = 0.35
    seniority_alignment: float = 0.20
    salary_fit: float = 0.15
    location_compatibility: float = 0.15
    fit_score: float = 0.15


class ScoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class SalaryExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int | None = None
    max: int | None = None
    currency: str = "USD"
    period: Literal["year", "hour"] = "year"


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    apply: ApplyConfig = Field(default_factory=ApplyConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)

    seniority: Seniority | None = None
    locations: list[str] = Field(default_factory=list)
    role_keywords: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    excluded_titles: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    salary_expectations: SalaryExpectations = Field(default_factory=SalaryExpectations)
    remote_preference: Literal["remote", "hybrid", "onsite", "no_preference"] = "no_preference"


JobSourceType = Literal[
    # ── Legacy / single-board ───────────────────────────────────────────────
    "greenhouse_board",
    "lever_board",
    "url_list",
    "rss",
    "career_site",
    # ── Browser-based adapters ──────────────────────────────────────────────
    "linkedin_search",
    "raytheon_careers",
    "indeed_search",
    "glassdoor_search",
    "l3harris_careers",
    "ti_careers",
    # ── Multi-company API adapters (Jobright-style) ─────────────────────────
    "greenhouse_multi",
    "lever_multi",
    "ashby",
    "ashby_multi",
    "workday",
    "smartrecruiters",
]


class JobSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: JobSourceType
    # config values can be: strings, lists of strings, ints, bools,
    # dicts (e.g. Workday company objects), or lists of dicts.
    config: dict[str, str | list | int | bool | dict] = Field(default_factory=dict)
    enabled: bool = True


class JobSources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: list[JobSource] = Field(default_factory=list)


class PromptEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template: str
    description: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: Literal["text", "json"] = "text"


class PromptsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompts: dict[str, PromptEntry] = Field(default_factory=dict)


class BlacklistConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    companies: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
