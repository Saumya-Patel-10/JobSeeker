"""The shipped starter configs should validate against the Pydantic schema."""

from __future__ import annotations

from app.config.loader import reload_config


def test_shipped_configs_validate() -> None:
    config = reload_config()
    assert config.profile.personal.full_name
    assert config.preferences.llm.provider in {"lmstudio", "ollama"}
    assert config.resume_master.summary
    assert True


def test_resume_master_has_employment_entries() -> None:
    config = reload_config()
    assert config.resume_master.employment, "starter resume should ship with example employment"


def test_prompts_config_registers_required_prompts() -> None:
    config = reload_config()
    for name in (
        "job_match",
        "resume_tailor",
        "cover_letter",
        "field_classify",
        "answer_question",
    ):
        assert name in config.prompts.prompts, f"missing prompt: {name}"
