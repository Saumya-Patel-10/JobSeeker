#!/usr/bin/env bash
# Bootstrap script for macOS/Linux.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Checking Python version"
python3 --version

if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment at .venv"
    python3 -m venv .venv
fi

echo "==> Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing project with dev extras"
python -m pip install -e ".[dev]"

echo "==> Installing Playwright Firefox"
python -m playwright install firefox

if command -v npm >/dev/null 2>&1; then
    echo "==> Installing frontend dependencies"
    npm --prefix frontend install
else
    echo "npm not found; skipping frontend dependency install."
fi

echo "==> Running jobassist init"
python -m app.cli.main init

echo
echo "Bootstrap complete."
echo "Activate the venv in new shells with: source .venv/bin/activate"
echo "Then run: python -m app.cli.main doctor"
