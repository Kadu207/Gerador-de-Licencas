Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "1) Backup pre-migracao"
& ".\\scripts\\db_backup.ps1"

Write-Host "2) Preparando URL interna do Postgres para migracao no container"
$postgresPasswordLine = Get-Content ".\\.env" | Where-Object { $_ -match "^POSTGRES_APP_PASSWORD=" } | Select-Object -First 1
if ([string]::IsNullOrWhiteSpace($postgresPasswordLine)) {
  throw "POSTGRES_APP_PASSWORD nao encontrado no .env."
}
$postgresPassword = $postgresPasswordLine.Split("=", 2)[1]
$encodedPassword = [System.Uri]::EscapeDataString($postgresPassword)
$containerDbUrl = "postgresql+psycopg://licencas:$encodedPassword@license-db:5432/licencas_db"

Write-Host "2) Aplicando migracoes via helper do projeto"
docker compose exec -e "LOCAL_DATABASE_URL=$containerDbUrl" license-server python docker/ensure_migrations.py
if ($LASTEXITCODE -ne 0) {
  throw "Falha ao aplicar migracoes no Gerador de Licencas."
}

Write-Host "3) Verificando saude da aplicacao"
Invoke-WebRequest -Uri "http://127.0.0.1:8195/health" -UseBasicParsing | Out-Null

Write-Host "Migracao concluida com sucesso."
