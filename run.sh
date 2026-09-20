#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

SCRIPT_NAME="${1:-dev}"

if command -v pnpm >/dev/null 2>&1; then
  echo "==> Running: pnpm ${SCRIPT_NAME}"
  pnpm "${SCRIPT_NAME}"
elif command -v npm >/dev/null 2>&1; then
  echo "==> Running: npm run ${SCRIPT_NAME}"
  npm run "${SCRIPT_NAME}"
else
  echo "Node package manager not found. Install pnpm or npm."
  exit 1
fi
