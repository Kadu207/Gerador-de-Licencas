# Sincroniza apps/web/.env a partir do .env raiz (DATABASE_URL, secrets)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not (Test-Path ".env")) {
    Write-Warning ".env raiz ausente - pulando sync."
    exit 0
}

$py = Join-Path $PSScriptRoot "sync_web_env.py"
& .\.venv\Scripts\python.exe $py
