"""Windows asyncio setup for Playwright subprocess support."""

from __future__ import annotations

import sys


def configure_event_loop() -> None:
    """Use ProactorEventLoop on Windows so asyncio subprocess works (Playwright, etc.).

    Uvicorn with ``--reload`` on Windows can otherwise use a loop without subprocess
    support, causing ``NotImplementedError`` in ``create_subprocess_exec``.
    """
    if sys.platform != "win32":
        return
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
