"""Resume parser using the main app's LLM provider.

Uses the same LLM factory as the rest of the app so config stays in one place
(config/preferences.yaml). Falls back to httpx for a direct API call if the
app's llm module is not on the path.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

# Try to use the main app's config; fall back to direct env vars if run standalone.
try:
    from app.config.loader import load_config

    def _get_llm_url() -> str:
        cfg = load_config()
        return cfg.preferences.llm.base_url

    def _get_model() -> str:
        cfg = load_config()
        return cfg.preferences.llm.chat_model

except ImportError:
    import os

    def _get_llm_url() -> str:  # type: ignore[misc]
        return os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")

    def _get_model() -> str:  # type: ignore[misc]
        return os.environ.get("LM_STUDIO_MODEL_NAME", "local-model")


def call_llm(prompt: str) -> str:
    """Call the configured LLM API and return the response text."""
    base_url = _get_llm_url().rstrip("/")
    model = _get_model()

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional resume parser. Extract information from "
                    "the provided text and output it in strictly valid JSON format."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    with httpx.Client(timeout=120) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
        )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]


def parse_resume_text(resume_text: str) -> dict[str, Any]:
    """Parse raw resume text into a structured dict using the local LLM.

    Returns a dict with keys: name, contact_info, summary, experience,
    education, skills.
    """
    prompt = f"""
Extract the following information from the resume text below.
Return ONLY a JSON object with these keys:
- name
- contact_info (phone, email, linkedin)
- summary
- experience (list of objects with: company, role, start_date, end_date, responsibilities)
- education (list of objects with: institution, degree, graduation_date)
- skills (list of strings)

Resume Text:
{resume_text}
"""
    raw_json = call_llm(prompt)
    return json.loads(raw_json)
