# Inicia Next.js Gerenciador de Licencas (apps/web)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "apps\web")

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Criado apps/web/.env - edite DATABASE_URL e senhas antes de producao."
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sync = Join-Path $repoRoot "tools\sync-web-env.ps1"
if (Test-Path $sync) { & $sync }
Set-Location (Join-Path $repoRoot "apps\web")

# Shell pode ter DATABASE_URL antigo (ex. senha local) - forcar apps/web/.env
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^DATABASE_URL=(.+)$') {
        $env:DATABASE_URL = $matches[1]
    }
}

npm run dev
