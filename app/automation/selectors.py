"""Common form-field selectors shared across ATS adapters.

These are pragmatic patterns observed across Greenhouse / Lever / Workday-ish
pages. They are deliberately loose so adapters can ``or``-chain them with
their own specifics.
"""

from __future__ import annotations

FIRST_NAME = ", ".join(
    [
        'input[autocomplete="given-name"]',
        "input#first_name",
        'input[name*="first" i]',
        'input[name="firstName"]',
    ]
)

LAST_NAME = ", ".join(
    [
        'input[autocomplete="family-name"]',
        "input#last_name",
        'input[name*="last" i]',
        'input[name="lastName"]',
    ]
)

EMAIL = ", ".join(
    [
        'input[type="email"]',
        'input[autocomplete="email"]',
        'input[name="email"]',
    ]
)

PHONE = ", ".join(
    [
        'input[type="tel"]',
        'input[autocomplete="tel"]',
        'input[name*="phone" i]',
    ]
)

RESUME_UPLOAD = ", ".join(
    [
        'input[type="file"][name*="resume" i]',
        'input[type="file"][accept*="pdf"]',
        'input[type="file"]',
    ]
)

COVER_LETTER = ", ".join(
    [
        'textarea[name="cover_letter"]',
        "textarea#cover_letter",
        'textarea[name*="cover" i]',
    ]
)

LINKEDIN = ", ".join(
    [
        'input[name*="linkedin" i]',
        'input[name="urls[LinkedIn]"]',
    ]
)

GITHUB = ", ".join(
    [
        'input[name*="github" i]',
        'input[name="urls[GitHub]"]',
    ]
)

SUBMIT = ", ".join(
    [
        'button[type="submit"]',
        'input[type="submit"]',
        "#submit_app",
        "#btn-submit",
        'button:has-text("Submit application")',
        'button:has-text("Submit")',
    ]
)
