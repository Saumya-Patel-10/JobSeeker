"""Runtime validator used by bootstrap and development orchestration."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass

from app.config.loader import load_config
from app.config.paths import DEFAULT_DB_PATH, ensure_data_dirs
from app.database.engine import init_db
from app.llm.factory import provider_session


@dataclass(slots=True)
class RuntimeReport:
    python_ok: bool
    python_version: str
    config_ok: bool
    config_error: str | None
    db_ok: bool
    db_path: str
    db_exists: bool
    llm_reachable: bool
    llm_provider: str | None
    llm_base_url: str | None
    llm_error: str | None

    @property
    def healthy(self) -> bool:
        return self.python_ok and self.config_ok and self.db_ok


async def run_runtime_validation() -> RuntimeReport:
    ensure_data_dirs()
    python_ok = sys.version_info >= (3, 12)
    python_version = sys.version.split(" ", 1)[0]
    try:
        config = load_config()
        config_ok = True
        config_error = None
    except Exception as exc:
        config = None
        config_ok = False
        config_error = str(exc)

    try:
        await init_db()
        db_ok = True
    except Exception:
        db_ok = False

    llm_reachable = False
    llm_provider: str | None = None
    llm_base_url: str | None = None
    llm_error: str | None = None
    if config is not None:
        llm_cfg = config.preferences.llm
        llm_provider = llm_cfg.provider
        llm_base_url = llm_cfg.base_url
        try:
            async with provider_session(llm_cfg) as provider:
                llm_reachable = await provider.health()
        except Exception as exc:
            llm_error = str(exc)
    return RuntimeReport(
        python_ok=python_ok,
        python_version=python_version,
        config_ok=config_ok,
        config_error=config_error,
        db_ok=db_ok,
        db_path=str(DEFAULT_DB_PATH),
        db_exists=DEFAULT_DB_PATH.exists(),
        llm_reachable=llm_reachable,
        llm_provider=llm_provider,
        llm_base_url=llm_base_url,
        llm_error=llm_error,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local runtime readiness.")
    parser.add_argument("--json", action="store_true", help="Emit report as JSON.")
    args = parser.parse_args()

    report = asyncio.run(run_runtime_validation())
    if args.json:
        sys.stdout.write(f"{json.dumps(asdict(report), indent=2)}\n")
        return

    lines = ["Runtime validation"]
    lines.append(f"- python: {'ok' if report.python_ok else 'fail'} ({report.python_version})")
    lines.append(f"- config: {'ok' if report.config_ok else 'fail'}")
    if report.config_error:
        lines.append(f"  error: {report.config_error}")
    lines.append(f"- database: {'ok' if report.db_ok else 'fail'} ({report.db_path})")
    lines.append(f"- llm reachable: {'yes' if report.llm_reachable else 'no'}")
    if report.llm_provider:
        lines.append(f"  provider: {report.llm_provider} ({report.llm_base_url})")
    if report.llm_error:
        lines.append(f"  llm error: {report.llm_error}")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
