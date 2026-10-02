"""Tests for job discovery filter matching."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config.loader import load_config
from app.models.enums import ATSSource, JobStatus, RemoteType
from app.models.job import Job
from app.services.discovery_config import JobDiscoveryConfig
from app.services.job_filters import matches_filters


def _job(
    title: str = "Systems Engineer",
    company: str = "Acme",
    description_text: str = "defense systems",
) -> Job:
    return Job(
        id=1,
        external_id=None,
        title=title,
        company=company,
        location="Remote",
        remote_type=RemoteType.remote,
        description_text=description_text,
        description_html=None,
        # Hourly pay consistent with an internship-seeking profile's salary
        # expectations (the real preferences.yaml sets min 25 / max 30 per hour;
        # an annual 100k-150k fixture would be correctly filtered out).
        salary_min=25,
        salary_max=30,
        salary_currency="USD",
        salary_period="hour",
        source_url="https://example.com/jobs/1",
        ats_source=ATSSource.generic,
        url_hash="abc",
        posted_at=None,
        scraped_at=datetime.now(UTC),
        status=JobStatus.open,
        raw_payload=None,
    )


def test_excluded_title_filters_out():
    config = load_config()
    discovery = JobDiscoveryConfig()
    job = _job(title="Senior Software Engineer")
    assert matches_filters(job, discovery, config) is False


def test_keyword_match_passes():
    config = load_config()
    discovery = JobDiscoveryConfig(
        keywords=["program"],
        locations=["Remote"],
        remote_preference="remote",
    )
    job = _job(title="Program Manager", description_text="defense program management")
    assert matches_filters(job, discovery, config) is True
