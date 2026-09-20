"""Resume template descriptor loader."""

from __future__ import annotations

from app.resume.template_config import load_template


def test_known_template_returns_full_config() -> None:
    cfg = load_template("backend")
    assert cfg["section_order"][0] == "summary"
    assert cfg["max_bullets_per_role"] >= 1


def test_unknown_template_falls_back_to_generic() -> None:
    cfg = load_template("does-not-exist")
    assert cfg["name"].lower().startswith("generic")
