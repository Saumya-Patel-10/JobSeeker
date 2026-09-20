"""Project-wide exception hierarchy.

All custom errors inherit from :class:`JobAssistError` so callers can do a
single broad catch when needed (e.g., in CLI commands) while still benefiting
from precise types deeper in the stack.
"""

from __future__ import annotations


class JobAssistError(Exception):
    """Base error for the application."""


class ConfigError(JobAssistError):
    """Raised when configuration files are missing or fail validation."""


class LLMError(JobAssistError):
    """Generic LLM-layer failure."""


class LLMUnavailableError(LLMError):
    """The configured LLM provider is unreachable."""


class LLMValidationError(LLMError):
    """The LLM returned output that failed JSON-schema validation."""


class AdapterError(JobAssistError):
    """Base ATS adapter error."""


class AdapterNotFoundError(AdapterError):
    """No adapter detected the given URL."""


class ScrapeError(AdapterError):
    """An adapter failed to scrape a job posting."""


class FillError(AdapterError):
    """An adapter failed to fill an application form."""


class SubmitError(AdapterError):
    """An adapter failed during submission."""


class BrowserError(JobAssistError):
    """The browser session could not be created or used."""


class DatabaseError(JobAssistError):
    """A database-layer failure."""


class HumanReviewRequired(JobAssistError):
    """Raised by pipelines when execution stops awaiting human approval.

    This is a control-flow signal, not an error condition.
    """
