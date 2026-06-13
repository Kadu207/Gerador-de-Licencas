# Push (opcional) + redeploy Gerador de Licencas na VPS producao.
# Uso:
#   powershell -ExecutionPolicy Bypass -File infra/ops/deploy-vps.ps1
#   powershell -ExecutionPolicy Bypass -File infra/ops/deploy-vps.ps1 -SkipPush
#   powershell -ExecutionPolicy Bypass -File infra/ops/deploy-vps.ps1 -SkipCommit
#
# Pre-requisito SSH: chave em gestaoti@128.140.77.31 (BatchMode)

param(
  [switch]$SkipPush,
  [switch]$SkipCommit,
  [switch]$AutoCommit,
  [string]$Branch = "main",
  [string]$VpsHost = "128.140.77.31",
  [string]$SshUser = "gestaoti",
  [string]$SshKey = "$env:USERPROFILE\.ssh\agenda-deploy",
  [string]$RemoteDir = "/opt/gerador-licencas"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SshTarget = "$SshUser@$VpsHost"

function Log([string]$msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

function Invoke-Git {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  $prev = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & git @Args 2>&1 | ForEach-Object {
    if ($_ -is [System.Management.Automation.ErrorRecord]) {
      $text = $_.ToString()
      if ($text -match '^(fatal|error):') { throw $text }
      Write-Host $text
    } else {
      Write-Host $_
    }
  }
  if ($LASTEXITCODE -ne 0) { throw "git $($Args -join ' ') falhou (exit $LASTEXITCODE)" }
  $ErrorActionPreference = $prev
}

Set-Location $RepoRoot

if (-not $SkipCommit) {
  $dirty = Invoke-Git status --porcelain
  if ($dirty) {
    if (-not $AutoCommit) {
      Write-Host "Ha alteracoes locais nao commitadas. Use -SkipCommit para deploy sem commit ou -AutoCommit para commitar automaticamente." -ForegroundColor Yellow
      Invoke-Git status --short
      exit 1
    }
    Log "Commit automatico para deploy..."
    Invoke-Git add apps/ infra/ops/ tools/sync-web-env.ps1 tools/sync_web_env.py run-web.ps1 docker-compose.yml
    Invoke-Git commit -m "Deploy: atualiza app e scripts de publicacao VPS."
  }
}

if (-not $SkipPush) {
  Log "git push origin $Branch"
  Invoke-Git push -u origin $Branch
}

Log "SSH deploy em ${SshTarget}:${RemoteDir}"
$remoteCmd = "set -euo pipefail; cd '$RemoteDir'; if [[ -d .git ]]; then git fetch origin; git checkout '$Branch' 2>/dev/null || git checkout -b '$Branch' origin/'$Branch'; git pull --ff-only origin '$Branch' || git pull --ff-only; fi; bash infra/ops/deploy-vps.sh"

ssh -i $SshKey -o BatchMode=yes -o ConnectTimeout=20 -o IdentitiesOnly=yes $SshTarget $remoteCmd

Log "Verificando producao"
try {
  $health = Invoke-RestMethod -Uri "https://licencas.inovatitech.com.br/api/health" -TimeoutSec 20
  $health | ConvertTo-Json -Compress
} catch {
  Write-Warning "Health publico falhou: $($_.Exception.Message)"
}

Log "Deploy concluido: https://licencas.inovatitech.com.br/login"
