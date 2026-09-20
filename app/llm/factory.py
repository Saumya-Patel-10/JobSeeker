"""Factory + helper to obtain an :class:`LLMProvider` from config."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.config.schema import LLMConfig
from app.llm.base import LLMProvider
from app.llm.lmstudio import LMStudioProvider
from app.llm.ollama import OllamaProvider


def make_provider(config: LLMConfig) -> LLMProvider:
    """Instantiate the configured provider."""
    if config.provider == "lmstudio":
        return LMStudioProvider(config)
    if config.provider == "ollama":
        return OllamaProvider(config)
    raise ValueError(f"Unknown LLM provider: {config.provider}")


@asynccontextmanager
async def provider_session(config: LLMConfig) -> AsyncIterator[LLMProvider]:
    """Context-manager wrapper that always closes the HTTP client."""
    provider = make_provider(config)
    try:
        yield provider
    finally:
        await provider.close()
