"""Firefox profile management CLI commands."""

from __future__ import annotations

from typing import Literal

import typer
import yaml
from rich.table import Table

from app.automation.firefox_profiles import (
    clone_firefox_profile,
    discover_managed_firefox_profiles,
    discover_system_firefox_profiles,
    get_firefox_profile,
    profile_health,
)
from app.cli._common import console, setup
from app.config.paths import user_config_path


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
