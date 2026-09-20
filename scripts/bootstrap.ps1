# Bootstrap script for Windows PowerShell.
# Creates a virtual environment, installs dependencies, installs Playwright
# Firefox, and runs `jobassist init` to create local data directories.

$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $root

Write-Host "==> Checking Python version" -ForegroundColor Cyan
python --version

if (-not (Test-Path ".\.venv")) {
    Write-Host "==> Creating virtual environment at .venv" -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "==> Activating virtual environment" -ForegroundColor Cyan
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Upgrading pip" -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "==> Installing project with dev extras" -ForegroundColor Cyan
python -m pip install -e ".[dev]"

Write-Host "==> Installing Playwright Firefox" -ForegroundColor Cyan
python -m playwright install firefox

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "==> Installing frontend dependencies" -ForegroundColor Cyan
    npm --prefix frontend install
} else {
    Write-Host "npm not found; skipping frontend dependency install." -ForegroundColor Yellow
}

Write-Host "==> Running jobassist init" -ForegroundColor Cyan
python -m app.cli.main init

Write-Host ""
Write-Host "Bootstrap complete." -ForegroundColor Green
Write-Host "Activate the venv in new shells with:  .\.venv\Scripts\Activate.ps1"
Write-Host "Then run:  python -m app.cli.main doctor"
