"""Smoke tests for DOCX and PDF renderers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.models.profile import EmploymentEntry, PersonalInfo, Profile
from app.models.resume import TailoredResume
from app.resume.renderers.docx_renderer import render_docx
from app.resume.renderers.pdf_renderer import render_pdf


def _profile() -> Profile:
    return Profile(
        personal=PersonalInfo(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="+1-555-0100",
        ),
    )


def _resume() -> TailoredResume:
    return TailoredResume(
        summary="Backend engineer with bias toward ownership.",
        headline="Backend Engineer",
        skills=["Python", "Postgres"],
        employment=[
            EmploymentEntry(
                company="Acme",
                title="SWE",
                start="2024-01",
                end=None,
                current=True,
                bullets=["Shipped X", "Cut Y"],
            )
        ],
        education=[],
        generated_at=datetime.now(UTC),
    )


def test_docx_renderer_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "resume.docx"
    render_docx(_resume(), _profile(), out)
    assert out.exists()
    assert out.stat().st_size > 1000


def test_pdf_renderer_writes_file(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")
    out = tmp_path / "resume.pdf"
    render_pdf(_resume(), _profile(), out)
    assert out.exists()
    assert out.stat().st_size > 1000
