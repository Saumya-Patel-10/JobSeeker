"""Small async helpers used across pipelines and the CLI."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def gather_limited[T](coros: Iterable[Awaitable[T]], limit: int = 5) -> list[T]:
    """Run coroutines concurrently capped at ``limit`` in-flight."""
    semaphore = asyncio.Semaphore(limit)

    async def _wrapped(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_wrapped(c) for c in coros))


def run_sync[T](coro: Awaitable[T]) -> T:
    """Execute ``coro`` from synchronous code (e.g., a Typer command).

    Raises ``RuntimeError`` if called from inside a running loop, where the
    correct pattern is to ``await`` directly.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("run_sync called from within a running event loop")
