"""Tenacity-based retry decorator for async functions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

P = ParamSpec("P")
T = TypeVar("T")


def with_retry(
    attempts: int = 3,
    on_exceptions: tuple[type[BaseException], ...] = (Exception,),
    *,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry an async function on the given exception types."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(min=wait_min, max=wait_max),
                retry=retry_if_exception_type(on_exceptions),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)
            raise RuntimeError("with_retry: retries exhausted without raising")

        return wrapper

    return decorator


__all__ = ["with_retry"]
