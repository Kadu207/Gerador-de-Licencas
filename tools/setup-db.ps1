$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env criado - preencha as senhas Postgres."
    exit 1
}

Write-Host "Recriando Postgres (volume limpo)..."
docker compose down -v 2>$null
docker compose up -d license-db

Write-Host "Aguardando Postgres..."
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    $h = docker inspect --format='{{.State.Health.Status}}' licencas-db 2>$null
    if ($h -eq "healthy") { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) { throw "Postgres timeout" }

Write-Host "Alembic upgrade head..."
& .\.venv\Scripts\alembic.exe upgrade head

Write-Host "Verificando..."
& .\.venv\Scripts\python.exe .\tools\verify_db.py

Write-Host "OK. Suba o app com: docker compose up -d --build"
