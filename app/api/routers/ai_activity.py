"""AI activity endpoints backed by structlog JSON logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.paths import LOG_DIR

router = APIRouter(prefix="/ai", tags=["ai"])


class AIActivityEntry(BaseModel):
    timestamp: str
    level: str
    logger: str
    event: str
    payload: dict[str, Any]


class AIActivitySummary(BaseModel):
    total_entries: int
    validation_failures: int
    avg_latency_ms: float | None


@router.get("/activity", response_model=list[AIActivityEntry])
async def get_activity(limit: int = 200) -> list[AIActivityEntry]:
    lines = _tail_json_lines(LOG_DIR / "app.log", max_lines=max(limit * 4, 800))
    entries: list[AIActivityEntry] = []
    for obj in reversed(lines):
        if not _is_ai_related(obj):
            continue
        event = str(obj.get("event", "unknown"))
        payload = {
            key: value
            for key, value in obj.items()
            if key not in {"timestamp", "level", "logger", "event", "app"}
        }
        entries.append(
            AIActivityEntry(
                timestamp=str(obj.get("timestamp", "")),
                level=str(obj.get("level", "info")),
                logger=str(obj.get("logger", "")),
                event=event,
                payload=payload,
            )
        )
        if len(entries) >= limit:
            break
    return entries


@router.get("/summary", response_model=AIActivitySummary)
async def get_summary(limit: int = 500) -> AIActivitySummary:
    entries = await get_activity(limit=limit)
    validation_failures = sum(
        1 for entry in entries if "validation" in entry.event.lower() or "validation" in entry.logger.lower()
    )
    latencies: list[float] = []
    for entry in entries:
        latency = entry.payload.get("latency_ms") or entry.payload.get("duration_ms")
        if isinstance(latency, (int, float)):
            latencies.append(float(latency))
    avg_latency = (sum(latencies) / len(latencies)) if latencies else None
    return AIActivitySummary(
        total_entries=len(entries),
        validation_failures=validation_failures,
        avg_latency_ms=round(avg_latency, 2) if avg_latency is not None else None,
    )


def _is_ai_related(obj: dict[str, Any]) -> bool:
    signal = " ".join(
        [
            str(obj.get("logger", "")),
            str(obj.get("event", "")),
            str(obj.get("message", "")),
        ]
    ).lower()
    return any(token in signal for token in ["llm", "prompt", "score", "tailor", "resume", "ai."])


def _tail_json_lines(path: Path, *, max_lines: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    objs: list[dict[str, Any]] = []
    for line in lines[-max_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            objs.append(obj)
    return objs
