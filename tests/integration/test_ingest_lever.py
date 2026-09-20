"""Integration test: ingest a Lever URL with HTTP mocked via respx."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from app.ats.lever import LeverAdapter

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lever_job.json"


@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_returns_normalized_job() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    respx.get("https://api.lever.co/v0/postings/example/abc-123-def?mode=json").mock(
        return_value=Response(200, json=data)
    )

    adapter = LeverAdapter()
    job = await adapter.scrape_job("https://jobs.lever.co/example/abc-123-def")
    assert job.title == "Backend Engineer"
    assert job.company.lower().startswith("example")
    assert job.location == "Remote"
    assert "build the platform" in job.description_text.lower()
    assert job.ats_source.value == "lever"
