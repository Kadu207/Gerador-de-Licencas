#!/usr/bin/env bash
# Deploy Gerador de Licenças na VPS (Ubuntu/Debian)
# Pré-requisitos: Docker, nginx, certbot, DNS licencas.inovatitech.com.br → IP da VPS
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gerador-licencas}"
REPO_URL="${REPO_URL:-}"

echo "==> Gerador de Licenças — deploy VPS"

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Crie $APP_DIR/.env a partir de .env.production.example"
  exit 1
fi

cd "$APP_DIR"
docker compose up -d --build

echo "==> Health local"
curl -fsS "http://127.0.0.1:8195/health" | head -c 500
echo ""

if [[ -f "$APP_DIR/infra/nginx/licencas.inovatitech.com.br.conf" ]]; then
  echo "==> Instale nginx (se ainda não):"
  echo "  sudo cp infra/nginx/licencas.inovatitech.com.br.conf /etc/nginx/sites-available/"
  echo "  sudo ln -sf /etc/nginx/sites-available/licencas.inovatitech.com.br.conf /etc/nginx/sites-enabled/"
  echo "  sudo certbot --nginx -d licencas.inovatitech.com.br"
  echo "  sudo nginx -t && sudo systemctl reload nginx"
fi

echo "==> Pronto. Admin: https://licencas.inovatitech.com.br"
echo "    API:     https://licencas.inovatitech.com.br/api/v1/licenses/status"
