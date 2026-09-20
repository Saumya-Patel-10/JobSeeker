#!/usr/bin/env bash
set -euo pipefail
echo "==> Starting FastAPI server on http://127.0.0.1:8000"
python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
