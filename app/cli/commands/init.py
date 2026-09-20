"""``jobassist init`` — create data dirs + initialize the database."""

from __future__ import annotations

import typer

from app.cli._common import console, run_async, setup
from app.config.paths import (
    CONFIG_DIR,
    DEFAULT_DB_PATH,
    ensure_data_dirs,
)
from app.database.engine import init_db


def init(
    _force: bool = typer.Option(
        False, "--force", help="Currently unused — placeholder for future overwrite logic."
    ),
) -> None:
    """Initialize local data directories + SQLite database."""
    setup()
    ensure_data_dirs()
    console.print(f"[green]OK[/green] data directories under {CONFIG_DIR.parent / 'data'}")
    run_async(init_db())
    console.print(f"[green]OK[/green] database at {DEFAULT_DB_PATH}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Edit [cyan]config/profile.yaml[/cyan] with your details")
    console.print("  2. Edit [cyan]config/resume_master.json[/cyan] with your experience")
    console.print("  3. Start LM Studio (or Ollama) and load a model")
    console.print("  4. Run [cyan]python -m app.cli.main doctor[/cyan]")
