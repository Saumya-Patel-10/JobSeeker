"""LM Studio provider (OpenAI-compatible HTTP at ``/v1/...``).

LM Studio exposes the OpenAI Chat Completions surface so we use plain httpx
rather than the `openai` SDK. This avoids carrying their dep just for one
endpoint and lets us tune retry behaviour with tenacity directly.
"""

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


class LMStudioProvider:
    name = "lmstudio"

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.chat_model = config.chat_model
        self.embedding_model = config.embedding_model
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.request_timeout,
            headers={"Authorization": f"Bearer {config.api_key}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> LMStudioProvider:
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
                        f"LM Studio unreachable at {self.config.base_url}: {exc}"
                    ) from exc
                if resp.status_code >= 500:
                    raise LLMUnavailableError(
                        f"LM Studio returned {resp.status_code}: {resp.text[:200]}"
                    )
                if resp.status_code >= 400:
                    raise LLMError(f"LM Studio returned {resp.status_code}: {resp.text[:500]}")
                return resp.json()
        raise LLMUnavailableError("LM Studio retries exhausted")

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature if temperature is not None else self.config.temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        data = await self._post("/chat/completions", payload)
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected LM Studio response: {data}") from exc

    async def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature if temperature is not None else self.config.temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": response_schema,
                    "strict": False,
                },
            }
        else:
            # LM Studio rejects ``json_object``; it only accepts ``json_schema`` or ``text``.
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": {"type": "object"},
                    "strict": False,
                },
            }

        data = await self._post("/chat/completions", payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected LM Studio response: {data}") from exc
        return _parse_json(content)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.embedding_model:
            raise LLMError(
                "No embedding_model configured for LM Studio. Set "
                "llm.embedding_model in preferences.yaml, or rely on ChromaDB's "
                "bundled default embeddings for the question memory."
            )
        data = await self._post(
            "/embeddings",
            {"model": self.embedding_model, "input": texts},
        )
        try:
            return [list(item["embedding"]) for item in data["data"]]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected embeddings response: {data}") from exc

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/models")
            return resp.status_code == 200
        except httpx.RequestError:
            return False


def _parse_json(content: str) -> dict[str, Any]:
    """Robust JSON parsing — tolerates code-fence wrappers small models emit."""
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
