"""Typer entry point.

Run with::

    python -m app.cli.main --help

Each command lives in its own module under ``app/cli/commands/`` so the
entry-point stays a tiny wiring file.
"""

from __future__ import annotations

import typer

from app.cli.commands import (
    analyze as analyze_cmd,
)
from app.cli.commands import (
    apply as apply_cmd,
)
from app.cli.commands import (
    browser_profiles as browser_profiles_cmd,
)
from app.cli.commands import (
    doctor as doctor_cmd,
)
from app.cli.commands import (
    dryrun as dryrun_cmd,
)
from app.cli.commands import (
    export as export_cmd,
)
from app.cli.commands import (
    generate_resume as resume_cmd,
)
from app.cli.commands import (
    ingest as ingest_cmd,
)
from app.cli.commands import (
    init as init_cmd,
)
from app.cli.commands import (
    listing as listing_cmd,
)
from app.cli.commands import (
    review as review_cmd,
)
from app.cli.commands import (
    runtime_check as runtime_check_cmd,
)
from app.cli.commands import (
    search as search_cmd,
)

app = typer.Typer(
    name="jobassist",
    help="Local AI-powered job application agent.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("init")(init_cmd.init)
app.command("doctor")(doctor_cmd.doctor)
app.command("search")(search_cmd.search)
app.command("ingest-url")(ingest_cmd.ingest_url)
app.command("analyze")(analyze_cmd.analyze)
app.command("generate-resume")(resume_cmd.generate_resume)
app.command("apply")(apply_cmd.apply)
app.command("dry-run")(dryrun_cmd.dry_run)
app.command("review")(review_cmd.review)
app.command("list-applications")(listing_cmd.list_applications)
app.command("export")(export_cmd.export)
app.command("runtime-check")(runtime_check_cmd.runtime_check)
app.command("browser-profiles")(browser_profiles_cmd.browser_profiles)
app.command("browser-clone")(browser_profiles_cmd.browser_clone)
app.command("browser-activate")(browser_profiles_cmd.browser_activate)
app.command("browser-chrome-profiles")(browser_profiles_cmd.browser_chrome_list)
app.command("browser-chrome-activate")(browser_profiles_cmd.browser_chrome_activate)
app.command("browser-login")(browser_profiles_cmd.browser_login)
app.command("browser-check-login")(browser_profiles_cmd.browser_check_login)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
