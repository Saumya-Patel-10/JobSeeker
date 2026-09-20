"""Adapter ``detect`` truth tables and registry routing."""

from __future__ import annotations

import pytest

from app.ats.generic import GenericAdapter
from app.ats.greenhouse import GreenhouseAdapter
from app.ats.lever import LeverAdapter
from app.ats.linkedin import LinkedInAdapter
from app.ats.registry import detect_adapter_class


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://boards.greenhouse.io/example/jobs/12345", GreenhouseAdapter),
        ("https://job-boards.greenhouse.io/example/jobs/12345", GreenhouseAdapter),
        ("https://jobs.lever.co/example/abc-123-def", LeverAdapter),
        ("https://www.linkedin.com/jobs/view/3829374659", LinkedInAdapter),
        ("https://linkedin.com/jobs/view/3829374659", LinkedInAdapter),
        ("https://careers.acme.com/openings/staff-backend", GenericAdapter),
    ],
)
def test_detect_routing(url: str, expected: type) -> None:
    assert detect_adapter_class(url) is expected


def test_greenhouse_parse_url() -> None:
    parsed = GreenhouseAdapter.parse_url("https://boards.greenhouse.io/example/jobs/12345")
    assert parsed == ("example", "12345")


def test_lever_parse_url() -> None:
    parsed = LeverAdapter.parse_url("https://jobs.lever.co/example/abc-123-def")
    assert parsed == ("example", "abc-123-def")


def test_linkedin_parse_url() -> None:
    parsed = LinkedInAdapter.parse_url("https://www.linkedin.com/jobs/view/12345")
    assert parsed == "12345"


def test_generic_detect_always_false() -> None:
    assert GenericAdapter.detect("https://anything.example.com/foo") is False
