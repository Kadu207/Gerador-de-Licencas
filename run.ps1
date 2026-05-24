# Inicia o Gerador de Licencas (servidor local)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Arquivo .env criado a partir de .env.example - ajuste as URLs dos bancos."
}

if (-not (Test-Path ".venv")) {
  python -m venv .venv
  & .\.venv\Scripts\pip install -r requirements.txt
}

& .\.venv\Scripts\python -m app.main
