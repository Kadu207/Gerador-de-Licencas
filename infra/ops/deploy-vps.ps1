# Push (opcional) + redeploy Gerador de Licencas na VPS producao.
# Uso:
#   powershell -ExecutionPolicy Bypass -File infra/ops/deploy-vps.ps1
#   powershell -ExecutionPolicy Bypass -File infra/ops/deploy-vps.ps1 -SkipPush
#
# Pre-requisito SSH: chave em gestaoti@128.140.77.31 (BatchMode)

param(
  [switch]$SkipPush,
  [switch]$SkipCommit,
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

Set-Location $RepoRoot

if (-not $SkipCommit) {
  $dirty = git status --porcelain
  if ($dirty) {
    Log "Ha alteracoes nao commitadas. Commitando automaticamente para deploy..."
    git add apps/ infra/ops/ tools/ run-web.ps1 docker-compose.yml README.md docs/PREMISSAS.md specs/001-gerenciador-licencas/tasks.md .github/workflows/web-ci.yml .env.example requirements.txt scripts/ 2>$null
    git add -u
    git commit -m @"
Deploy Next.js v2: login server action, sync env e scripts VPS.

Inclui apps/web completo, deploy-vps atualizado para porta 3000 e correcoes de autenticacao no painel admin.
"@
  }
}

if (-not $SkipPush) {
  Log "git push origin $Branch"
  git push -u origin $Branch
}

Log "SSH deploy em ${SshTarget}:${RemoteDir}"
$remoteCmd = @"
set -euo pipefail
cd '$RemoteDir'
if [[ -d .git ]]; then
  git fetch origin
  git checkout '$Branch' 2>/dev/null || git checkout -b '$Branch' origin/'$Branch'
  git pull --ff-only origin '$Branch' || git pull --ff-only
fi
bash infra/ops/deploy-vps.sh
"@

ssh -i $SshKey -o BatchMode=yes -o ConnectTimeout=20 -o IdentitiesOnly=yes $SshTarget $remoteCmd

Log "Verificando producao"
try {
  $health = Invoke-RestMethod -Uri "https://licencas.inovatitech.com.br/api/health" -TimeoutSec 20
  $health | ConvertTo-Json -Compress
} catch {
  Write-Warning "Health publico falhou: $($_.Exception.Message)"
}

Log "Deploy concluido: https://licencas.inovatitech.com.br/login"
