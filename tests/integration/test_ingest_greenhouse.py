"""Integration test: ingest a Greenhouse URL with HTTP mocked via respx."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.ats.greenhouse import GreenhouseAdapter

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "greenhouse_job.json"


@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_returns_normalized_job() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    respx.get("https://boards-api.greenhouse.io/v1/boards/example/jobs/12345").mock(
        return_value=Response(200, json=data)
    )

    adapter = GreenhouseAdapter()
    job = await adapter.scrape_job("https://boards.greenhouse.io/example/jobs/12345")
    assert job.title == "Senior Backend Engineer"
    assert job.company == "Example Inc."
    assert job.location == "Remote — US"
    assert "Python services" in job.description_text
    assert job.ats_source.value == "greenhouse"
