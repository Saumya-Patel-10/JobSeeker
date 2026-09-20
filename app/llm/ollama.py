"""Ollama provider (native ``/api/chat`` + ``/api/embeddings``)."""

from __future__ import annotations

import json
from types import TracebackType
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.schema import LLMConfig
from app.llm.base import ChatMessage
from app.utils.errors import LLMError, LLMUnavailableError, LLMValidationError
from app.utils.logging import get_logger

log = get_logger(__name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.chat_model = config.chat_model
        # Ollama lets you embed with chat models, so fall back if not set.
        self.embedding_model = config.embedding_model or config.chat_model
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.request_timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OllamaProvider:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(min=1, max=10),
            retry=retry_if_exception_type((LLMUnavailableError, httpx.HTTPStatusError)),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                try:
                    resp = await self._client.post(path, json=payload)
                except httpx.RequestError as exc:
                    raise LLMUnavailableError(
                        f"Ollama unreachable at {self.config.base_url}: {exc}"
                    ) from exc
                if resp.status_code >= 500:
                    raise LLMUnavailableError(
                        f"Ollama returned {resp.status_code}: {resp.text[:200]}"
                    )
                if resp.status_code >= 400:
                    raise LLMError(f"Ollama returned {resp.status_code}: {resp.text[:500]}")
                return resp.json()
        raise LLMUnavailableError("Ollama retries exhausted")

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> str:
        options: dict[str, Any] = {
            "temperature": temperature if temperature is not None else self.config.temperature,
        }
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if stop:
            options["stop"] = stop

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": options,
        }
        data = await self._post("/api/chat", payload)
        message = data.get("message") or {}
        return str(message.get("content", ""))

    async def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        options: dict[str, Any] = {
            "temperature": temperature if temperature is not None else self.config.temperature,
        }
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": options,
            # Ollama 0.5+ accepts a JSON schema or the literal "json".
            "format": response_schema if response_schema is not None else "json",
        }
        data = await self._post("/api/chat", payload)
        content = (data.get("message") or {}).get("content", "")
        return _parse_json(content)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            data = await self._post(
                "/api/embeddings",
                {"model": self.embedding_model, "prompt": text},
            )
            embeddings.append(list(data.get("embedding", [])))
        return embeddings

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except httpx.RequestError:
            return False


def _parse_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        fence_end = text.rfind("```")
        if fence_end > 3:
            inner = text[3:fence_end]
            if inner.lower().startswith("json"):
                inner = inner[4:]
            text = inner.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMValidationError(f"Model returned non-JSON content: {content[:300]}") from exc
    if not isinstance(result, dict):
        raise LLMValidationError(f"Expected JSON object, got {type(result).__name__}")
    return result
