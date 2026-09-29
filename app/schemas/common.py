from pydantic import BaseModel
from typing import Optional


class ResumeOut(BaseModel):
    id: int
    file_name: str
    s3_key: str
    is_master: bool
    is_active: bool
    parsed_text: Optional[str] = None

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    source: str
    source_url: str
    match_score: Optional[float] = None   # populated after matching

    model_config = {"from_attributes": True}


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    resume_id: int
    status: str
    match_score: Optional[float]
    celery_task_id: Optional[str]
    tailored_resume_s3_key: Optional[str]
    cover_letter_s3_key: Optional[str]
    interview_questions_json: Optional[str]
    ats_optimized: bool
    applied_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: int


class SubscriptionOut(BaseModel):
    id: int
    stripe_subscription_id: str
    status: str
    current_period_end: Optional[str]
    cancel_at_period_end: bool

    model_config = {"from_attributes": True}


class CheckoutSessionCreate(BaseModel):
    plan: str   # "basic" | "pro"
