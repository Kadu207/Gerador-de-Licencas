# Sobe Excellence + integra licenca demo no ERP
$ErrorActionPreference = "Stop"
$ExcellenceRoot = "C:\Users\Carlos\OneDrive\Área de Trabalho\Projetos DEV\Excellence_Dental"
$GeradorRoot = $PSScriptRoot | Split-Path -Parent

function Wait-Docker {
  for ($i = 0; $i -lt 60; $i++) {
    try {
      docker info *> $null
      return $true
    } catch {
      Start-Sleep -Seconds 2
    }
  }
  return $false
}

Write-Host "=== 1/4 Docker ==="
if (-not (Wait-Docker)) {
  Write-Host "Iniciando Docker Desktop..."
  Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
  if (-not (Wait-Docker)) { throw "Docker nao respondeu. Abra o Docker Desktop manualmente." }
}

Set-Location $ExcellenceRoot
Write-Host "=== 2/4 Excellence Dental (docker compose) ==="
docker compose -f docker-compose.prod.yml up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose falhou" }

Write-Host "Aguardando backend..."
for ($i = 0; $i -lt 90; $i++) {
  try {
    $code = (curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1/api/health)
    if ($code -eq "200") { break }
  } catch {}
  Start-Sleep -Seconds 2
}

Write-Host "=== 3/4 Reiniciando Gerador de Licencas ==="
Get-NetTCPConnection -LocalPort 8195 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
Set-Location $GeradorRoot
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "app.main" -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host "=== 4/4 Sync + ativacao no ERP ==="
& .\.venv\Scripts\python.exe -m tools.integration_e2e
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Concluido. Acesse http://127.0.0.1 (ERP) e http://127.0.0.1:8195 (Gerador)."
