$ErrorActionPreference = "Stop"
Write-Host "==> Installing Playwright Firefox" -ForegroundColor Cyan
python -m playwright install firefox
