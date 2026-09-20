"""Timestamped screenshot helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from playwright.async_api import Page

from app.config.paths import SCREENSHOTS_DIR


def _safe(label: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:80]


async def capture(page: Page, label: str) -> Path:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = SCREENSHOTS_DIR / f"{ts}_{_safe(label)}.png"
    await page.screenshot(path=str(path), full_page=True)
    return path


async def capture_dom(page: Page, label: str) -> Path:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = SCREENSHOTS_DIR / f"{ts}_{_safe(label)}.html"
    content = await page.content()
    path.write_text(content, encoding="utf-8")
    return path
