"""``jobassist doctor`` — environment + dependency health check."""

from __future__ import annotations

import asyncio
import sys

from rich.table import Table

from app.automation.firefox_profiles import (
    discover_managed_firefox_profiles,
    discover_system_firefox_profiles,
    get_firefox_profile,
    profile_health,
)
from app.cli._common import console, setup
from app.config.loader import load_config
from app.config.paths import DEFAULT_DB_PATH
from app.database.engine import init_db
from app.llm.factory import provider_session


def doctor() -> None:
    """Verify Python, configs, database, LLM, and Playwright."""
    setup()
    table = Table(title="Job Finding Assistant — Doctor", show_lines=False)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    asyncio.run(_run_checks(table))
    console.print(table)


async def _run_checks(table: Table) -> None:
    _check_python(table)
    config = _check_configs(table)
    await _check_database(table)
    if config is not None:
        await _check_llm(table, config)
        _check_firefox_profiles(table, config)
    await _check_playwright(table, config)


def _check_python(table: Table) -> None:
    ok = sys.version_info >= (3, 12)
    table.add_row(
        "Python >= 3.12",
        "[green]OK[/green]" if ok else "[red]FAIL[/red]",
        sys.version.split(" ", 1)[0],
    )


def _check_configs(table: Table):
    try:
        config = load_config()
    except Exception as exc:
        table.add_row("Configs", "[red]FAIL[/red]", str(exc)[:200])
        return None
    table.add_row("Configs", "[green]OK[/green]", "all YAML/JSON files validated")
    return config


async def _check_database(table: Table) -> None:
    try:
        await init_db()
    except Exception as exc:
        table.add_row("Database", "[red]FAIL[/red]", str(exc)[:200])
        return
    table.add_row("Database", "[green]OK[/green]", str(DEFAULT_DB_PATH))


async def _check_llm(table: Table, config) -> None:
    llm_cfg = config.preferences.llm
    label = f"LLM ({llm_cfg.provider})"
    try:
        async with provider_session(llm_cfg) as provider:
            ok = await provider.health()
    except Exception as exc:
        table.add_row(label, "[red]FAIL[/red]", f"{llm_cfg.base_url} — {exc}")
        return
    if ok:
        table.add_row(label, "[green]OK[/green]", f"{llm_cfg.base_url} reachable")
    else:
        table.add_row(label, "[yellow]WARN[/yellow]", f"{llm_cfg.base_url} not reachable")


def _check_firefox_profiles(table: Table, config) -> None:
    browser_cfg = config.preferences.browser
    system_profiles = discover_system_firefox_profiles()
    managed_profiles = discover_managed_firefox_profiles()
    table.add_row(
        "Firefox profiles",
        "[green]OK[/green]",
        f"system={len(system_profiles)} managed={len(managed_profiles)}",
    )
    if browser_cfg.engine != "firefox":
        return
    if browser_cfg.profile_source == "system":
        if not browser_cfg.firefox_profile:
            table.add_row(
                "Firefox profile selection",
                "[yellow]WARN[/yellow]",
                "profile_source=system but browser.firefox_profile is not set",
            )
            return
        profile = get_firefox_profile(browser_cfg.firefox_profile, source="system")
        if profile is None:
            table.add_row(
                "Firefox profile selection",
                "[red]FAIL[/red]",
                f"Profile not found: {browser_cfg.firefox_profile}",
            )
            return
        health = profile_health(profile.path)
        state = "locked" if health.locked else "ready"
        table.add_row(
            "Firefox profile selection",
            "[green]OK[/green]",
            f"{profile.name} ({state}) at {profile.path}",
        )


async def _check_playwright(table: Table, config) -> None:
    try:
        from playwright.async_api import async_playwright

        engine = config.preferences.browser.engine if config is not None else "firefox"
        install_hint = f"python -m playwright install {engine}"
        async with async_playwright() as pw:
            try:
                browser_type = getattr(pw, engine)
                browser = await browser_type.launch(headless=True)
                await browser.close()
            except Exception as exc:
                table.add_row(
                    f"Playwright {engine}",
                    "[red]FAIL[/red]",
                    f"Run `{install_hint}` ({exc})",
                )
                return
        table.add_row(f"Playwright {engine}", "[green]OK[/green]", "launchable")
    except Exception as exc:
        table.add_row("Playwright", "[red]FAIL[/red]", str(exc)[:200])
