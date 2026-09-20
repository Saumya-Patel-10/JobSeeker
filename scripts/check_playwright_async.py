"""Quick check: asyncio subprocess + Playwright on Windows."""
from __future__ import annotations

import asyncio
import sys

from app.utils.event_loop import configure_event_loop

configure_event_loop()


async def main() -> None:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "print('subprocess-ok')",
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    assert b"subprocess-ok" in stdout
    print("asyncio subprocess: ok")

    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        print("playwright firefox: ok")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
