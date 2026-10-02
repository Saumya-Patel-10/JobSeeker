"""Browser profile management CLI commands (Firefox and Chrome)."""

from __future__ import annotations

import asyncio
from typing import Literal

import typer
import yaml
from rich.table import Table

from app.automation.browser import BrowserSession
from app.automation.chrome_profiles import (
    ChromeProfile,
    chrome_is_running,
    chrome_user_data_dir,
    discover_system_chrome_profiles,
    find_chrome_profile_by_email,
    get_chrome_profile,
)
from app.automation.firefox_profiles import (
    clone_firefox_profile,
    discover_managed_firefox_profiles,
    discover_system_firefox_profiles,
    get_firefox_profile,
    profile_health,
)
from app.cli._common import console, setup
from app.config.paths import user_config_path


def _list_chrome_profiles(root=None) -> list[ChromeProfile]:
    profiles = discover_system_chrome_profiles(root)
    table = Table(title="Google Chrome Profiles (system)")
    table.add_column("Dir", style="bold")
    table.add_column("Display name")
    table.add_column("Signed-in account")
    table.add_column("Last used")
    for p in profiles:
        table.add_row(
            p.dir_name,
            p.display_name,
            p.email or "[dim]not signed in[/dim]",
            "yes" if p.is_last_used else "",
        )
    if not profiles:
        console.print("[yellow]No Chrome profiles discovered.[/yellow]")
    else:
        console.print(table)
    return profiles


def browser_chrome_list() -> None:
    """List discovered Google Chrome profiles on this machine."""
    setup()
    _list_chrome_profiles()


def browser_chrome_activate(
    profile_dir: str = typer.Argument(
        "",
        help="Chrome profile directory (e.g. 'Default', 'Profile 1'). Omit to auto-select "
        "the profile signed in with your profile email.",
    ),
) -> None:
    """Use your own Chrome profile for automation (sets preferences.yaml)."""
    setup()
    preferences_path = user_config_path("preferences.yaml")
    payload = yaml.safe_load(preferences_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise typer.Exit(code=1)
    browser_cfg = payload.get("browser", {})
    if not isinstance(browser_cfg, dict):
        browser_cfg = {}

    browser_cfg["engine"] = "chromium"
    browser_cfg["channel"] = "chrome"
    browser_cfg["profile_source"] = "system"

    chosen = profile_dir
    if not chosen:
        # Auto-select the Chrome profile signed in with the user's email.
        from app.config.loader import load_config

        email = (load_config().profile.personal.email or "").strip().lower()
        match = find_chrome_profile_by_email(email) if email else None
        if match is None:
            console.print(
                "[yellow]No Chrome profile found for the profile email; "
                "falling back to Chrome's last-used profile.[/yellow]"
            )
        chosen = match.dir_name if match else ""

    if chosen:
        browser_cfg["chrome_profile"] = chosen
        label = chosen
    else:
        browser_cfg["chrome_profile"] = None
        label = "Chrome's last-used profile"

    payload["browser"] = browser_cfg
    preferences_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    console.print(
        f"[green]OK[/green] Automation will use your own Chrome profile ({label}) via "
        "profile_source: system. Close all Chrome windows before running automation."
    )


def browser_login() -> None:
    """Open Chrome with the configured profile and prompt you to sign in.

    Use this once after switching to your own Chrome profile: the browser
    opens, you sign in with your Google account (and LinkedIn if you like),
    and the session persists for future automation runs.
    """
    setup()
    from app.config.loader import load_config

    config = load_config()
    console.print(
        "[bold]Opening Chrome with your configured profile...[/bold] "
        "Sign in to Google (and LinkedIn) if prompted, then press Enter here when done."
    )

    async def _run() -> None:
        async with BrowserSession.launch(config.preferences.browser) as session:
            page = await session.new_page()
            try:
                await page.goto("https://accounts.google.com", wait_until="domcontentloaded")
            except Exception as exc:
                console.print(f"[yellow]Could not open accounts.google.com: {exc}[/yellow]")
            await asyncio.get_event_loop().run_in_executor(
                None, input, "Press Enter when you have finished signing in... "
            )
            console.print("[green]OK[/green] Login session saved to the browser profile.")

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Login session failed: {exc}[/red]")
        raise typer.Exit(code=1)


def browser_check_login() -> None:
    """Check whether the configured Chrome profile is still signed in to Google."""
    setup()
    from app.config.loader import load_config

    config = load_config()

    async def _run() -> None:
        async with BrowserSession.launch(config.preferences.browser) as session:
            page = await session.new_page()
            await page.goto("https://accounts.google.com", wait_until="domcontentloaded")
            content = await page.content()
            # When signed out, accounts.google.com shows a "Sign in" control.
            signed_out = "sign in" in content.lower()
            if signed_out:
                console.print(
                    "[yellow]Not signed in.[/yellow] Run "
                    "[bold]jobassist browser-login[/bold] to sign in with your Google account."
                )
            else:
                console.print(
                    "[green]OK[/green] The configured Chrome profile appears signed in to Google."
                )

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Login check failed: {exc}[/red]")
        raise typer.Exit(code=1)


def browser_profiles(
    source: Literal["all", "system", "managed"] = typer.Option("all"),
) -> None:
    """List discovered Firefox profiles."""
    setup()
    profiles = []
    if source in {"all", "system"}:
        profiles.extend(discover_system_firefox_profiles())
    if source in {"all", "managed"}:
        profiles.extend(discover_managed_firefox_profiles())
    table = Table(title="Firefox Profiles")
    table.add_column("Name", style="bold")
    table.add_column("Source")
    table.add_column("Default")
    table.add_column("Cookies")
    table.add_column("Locked")
    table.add_column("Path")
    for profile in profiles:
        health = profile_health(profile.path)
        table.add_row(
            profile.name,
            profile.source,
            "yes" if profile.is_default else "",
            "yes" if health.has_cookies_db else "no",
            "yes" if health.locked else "no",
            str(profile.path),
        )
    if not profiles:
        console.print("[yellow]No Firefox profiles discovered.[/yellow]")
        return
    console.print(table)


def browser_clone(
    source_profile_name: str,
    target_name: str = typer.Option("", help="Managed profile name."),
    overwrite: bool = typer.Option(False, help="Overwrite existing target profile."),
) -> None:
    """Clone an existing system Firefox profile into managed automation profiles."""
    setup()
    source_profile = get_firefox_profile(source_profile_name, source="system")
    if source_profile is None:
        raise typer.BadParameter(f"System Firefox profile not found: {source_profile_name}")
    resolved_target = target_name or f"{source_profile.name}-managed"
    cloned = clone_firefox_profile(source_profile.path, resolved_target, overwrite=overwrite)
    console.print(f"[green]OK[/green] cloned profile to {cloned}")


def browser_activate(
    profile_name: str,
    source: Literal["system", "managed"] = typer.Option("managed"),
    persistent: bool = typer.Option(True),
    reuse_existing_session: bool = typer.Option(True),
    clone_system_profile_on_lock: bool = typer.Option(True),
) -> None:
    """Set active Firefox profile in ``config/preferences.yaml``."""
    setup()
    profile = get_firefox_profile(profile_name, source=source)
    if profile is None:
        raise typer.BadParameter(f"{source} Firefox profile not found: {profile_name}")

    preferences_path = user_config_path("preferences.yaml")
    payload = yaml.safe_load(preferences_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise typer.Exit(code=1)
    browser_cfg = payload.get("browser", {})
    if not isinstance(browser_cfg, dict):
        browser_cfg = {}
    browser_cfg["engine"] = "firefox"
    browser_cfg["persistent_profile"] = persistent
    browser_cfg["profile_source"] = source
    browser_cfg["reuse_existing_session"] = reuse_existing_session
    browser_cfg["clone_system_profile_on_lock"] = clone_system_profile_on_lock
    if source == "system":
        browser_cfg["firefox_profile"] = profile_name
    else:
        browser_cfg["profile"] = profile_name
    payload["browser"] = browser_cfg
    preferences_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    console.print(
        f"[green]OK[/green] Active browser profile set to '{profile_name}' ({source}) in preferences.yaml"
    )
