"""LLM provider abstractions.

Every provider implements the :class:`LLMProvider` Protocol. Pipelines code
against this Protocol so swapping LM Studio for Ollama (or a future cloud
provider) is a config change, not a code change.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """One message in an OpenAI-style chat completion."""

    role: str
    content: str


@runtime_checkable
class LLMProvider(Protocol):
    """The contract every local LLM backend must satisfy."""

    name: str
    chat_model: str
    embedding_model: str | None

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> str:
        """Return a plain-text completion."""

    async def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Return a parsed JSON object. Raise ``LLMValidationError`` on bad output."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    async def health(self) -> bool:
        """Return True iff the backend is reachable."""

    async def close(self) -> None:
        """Release any underlying HTTP client resources."""
