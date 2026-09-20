$ErrorActionPreference = "Stop"

$root = (Resolve-Path $PSScriptRoot).Path
Set-Location $root

$script = if ($args.Count -gt 0) { $args[0] } else { "dev" }

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    Write-Host "==> Running: pnpm $script" -ForegroundColor Cyan
    pnpm $script
} elseif (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "==> Running: npm run $script" -ForegroundColor Cyan
    npm run $script
} else {
    Write-Host "Node package manager not found. Install pnpm or npm." -ForegroundColor Red
    exit 1
}
