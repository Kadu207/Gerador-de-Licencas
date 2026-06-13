#!/usr/bin/env bash
# Deploy Gerador de Licencas na VPS (Next.js + Postgres)
# Pre-requisitos: Docker, nginx, DNS licencas.inovatitech.com.br
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gerador-licencas}"

echo "==> Gerador de Licencas — deploy VPS (Next.js)"

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Crie $APP_DIR/.env a partir de .env.production.example"
  exit 1
fi

cd "$APP_DIR"

if [[ -d .git ]]; then
  echo "==> git pull"
  git pull --ff-only origin main || git pull --ff-only
fi

bash "$APP_DIR/infra/ops/provision-web-env.sh"

# Porta 8195 no host (nginx Excellence usa host.docker.internal:8195)
export LICENSE_WEB_PORT="${LICENSE_WEB_PORT:-8195}"
export LICENSE_WEB_BIND="${LICENSE_WEB_BIND:-0.0.0.0}"

echo "==> Parando FastAPI legado (license-server) se estiver ativo"
docker compose stop license-server 2>/dev/null || true

set -a
# shellcheck disable=SC1091
source <(grep -v '^\s*#' .env | grep -v '^\s*$' | sed 's/\r$//')
set +a

echo "==> Build e subida (license-db + license-web na porta ${LICENSE_WEB_PORT})"
docker compose up -d license-db license-web --build

echo "==> Schema Postgres (SQL idempotente)"
docker exec -i licencas-db psql -U licencas -d licencas_db < "$APP_DIR/infra/ops/schema-sync.sql"

echo "==> Health local"
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${LICENSE_WEB_PORT}/api/health" >/dev/null 2>&1; then
    curl -s "http://127.0.0.1:${LICENSE_WEB_PORT}/api/health"
    echo ""
    break
  fi
  sleep 2
  if [[ "$i" -eq 30 ]]; then
    echo "ERRO: Next.js nao respondeu em :${LICENSE_WEB_PORT}"
    docker compose logs --tail=80 license-web
    exit 1
  fi
done

if [[ -f "$APP_DIR/infra/nginx/licencas.inovatitech.com.br.conf" ]]; then
  echo "==> Nginx (se necessario):"
  echo "  sudo cp infra/nginx/licencas.inovatitech.com.br.conf /etc/nginx/sites-available/"
  echo "  sudo ln -sf /etc/nginx/sites-available/licencas.inovatitech.com.br.conf /etc/nginx/sites-enabled/"
  echo "  sudo nginx -t && sudo systemctl reload nginx"
fi

echo "==> Pronto"
echo "    Admin: https://licencas.inovatitech.com.br/login"
echo "    API:   https://licencas.inovatitech.com.br/api/v1/licenses/status"
echo "    Health: https://licencas.inovatitech.com.br/api/health"
