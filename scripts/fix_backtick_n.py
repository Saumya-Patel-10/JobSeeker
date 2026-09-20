"""One-off repair for PowerShell-corrupted `n literals in Python sources."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    ROOT / "app/automation/browser.py",
    ROOT / "app/services/job_hunt_manager.py",
    ROOT / "app/api/main.py",
    ROOT / "app/ats/generic.py",
]


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    fixed = text.replace("`n", "\n")
    fixed = fixed.replace(')\\n            ', ')\n            ')
    # PowerShell-escaped docstrings like "\""text"\""
    fixed = re.sub(r'"\""([^"]+)"\""', r'"""\1"""', fixed)
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
        return True
    return False


def main() -> None:
    for path in FILES:
        if path.exists() and fix_file(path):
            print(f"fixed {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
