"""Shared CLI helpers."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable
from typing import TypeVar

from rich.console import Console

from app.utils.logging import configure_logging

T = TypeVar("T")


def _ensure_utf8_streams() -> None:
    """Force UTF-8 on stdout/stderr so Rich's box glyphs don't trip up the
    legacy Windows codepage when output is piped or captured."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            current = (getattr(stream, "encoding", "") or "").lower()
            if current != "utf-8":
                reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_ensure_utf8_streams()

console = Console()


def setup() -> None:
    """Configure logging exactly once for the CLI."""
    _ensure_utf8_streams()
    configure_logging()


def run_async[T](coro: Awaitable[T]) -> T:
    """Run an awaitable from a sync Typer command."""
    return asyncio.run(coro)
