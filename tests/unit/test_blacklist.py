"""Blacklist service truth table."""

from __future__ import annotations

from app.config.schema import BlacklistConfig
from app.models.enums import ATSSource
from app.models.job import Job
from app.services.blacklist import Blacklist


def _job(**overrides: object) -> Job:
    data = {
        "title": "Backend Engineer",
        "company": "Acme",
        "description_text": "Build APIs.",
        "source_url": "https://example.com/job/1",
        "url_hash": "x",
        "ats_source": ATSSource.greenhouse,
    }
    data.update(overrides)
    return Job(**data)  # type: ignore[arg-type]


def test_company_blocked() -> None:
    bl = Blacklist(BlacklistConfig(companies=["acme"]))
    blocked, reason = bl.is_blocked(_job())
    assert blocked is True
    assert reason is not None
    assert "acme" in reason.lower()


def test_keyword_blocked() -> None:
    bl = Blacklist(BlacklistConfig(keywords=["unpaid internship"]))
    blocked, _ = bl.is_blocked(_job(description_text="This is an unpaid internship."))
    assert blocked is True


def test_domain_blocked() -> None:
    bl = Blacklist(BlacklistConfig(domains=["spam.example.com"]))
    blocked, _ = bl.is_blocked(_job(source_url="https://spam.example.com/job/1"))
    assert blocked is True


def test_not_blocked() -> None:
    bl = Blacklist(BlacklistConfig())
    blocked, reason = bl.is_blocked(_job())
    assert blocked is False
    assert reason is None
