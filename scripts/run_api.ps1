$ErrorActionPreference = "Stop"
Write-Host "==> Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Cyan
python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
