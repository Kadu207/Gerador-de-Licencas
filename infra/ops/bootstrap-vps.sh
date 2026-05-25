#!/usr/bin/env bash
# Bootstrap VPS — Gerador de Licenças
#   git clone https://github.com/Kadu207/Gerador-de-Licencas.git /opt/gerador-licencas
#   cd /opt/gerador-licencas
#   cp .env.production.example .env && nano .env
#   bash infra/ops/bootstrap-vps.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP_DIR"

echo "==> Diretório: $APP_DIR"

if [[ ! -f docker-compose.yml ]]; then
  echo "ERRO: clone o repositório em /opt/gerador-licencas primeiro."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Instalando Docker..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi

if ! command -v nginx >/dev/null 2>&1; then
  echo "==> Instalando nginx + certbot..."
  sudo apt-get update
  sudo apt-get install -y nginx certbot python3-certbot-nginx curl git
fi

if [[ ! -f .env ]]; then
  cp .env.production.example .env
  echo "==> .env criado. Edite POSTGRES_APP_PASSWORD, SECRET_KEY, ADMIN_PASSWORD, PRODUCT_API_KEY:"
  echo "    nano .env"
  exit 0
fi

if ! grep -qE '^POSTGRES_APP_PASSWORD=.+' .env || grep -q 'TROQUE-SENHA-POSTGRES' .env; then
  echo "ERRO: defina POSTGRES_APP_PASSWORD no .env (senha forte, mesma em LOCAL_DATABASE_URL)"
  exit 1
fi

# Exporta para docker compose ler POSTGRES_APP_PASSWORD
set -a
# shellcheck disable=SC1091
source <(grep -v '^\s*#' .env | grep -v '^\s*$' | sed 's/\r$//')
set +a

echo "==> Subindo containers..."
docker compose up -d --build

echo "==> Aguardando health (até 60s)..."
ok=0
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:8195/health" >/dev/null 2>&1; then
    curl -s "http://127.0.0.1:8195/health"
    echo ""
    ok=1
    break
  fi
  sleep 2
done
if [[ "$ok" -ne 1 ]]; then
  echo "ERRO: app não respondeu. Logs:"
  docker compose logs --tail=50
  exit 1
fi

NGINX_CONF="infra/nginx/licencas.inovatitech.com.br.conf"
if [[ -f "$NGINX_CONF" ]]; then
  echo "==> Nginx (HTTP inicial — certbot adiciona HTTPS depois)..."
  sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
  sudo cp "$NGINX_CONF" /etc/nginx/sites-available/licencas.inovatitech.com.br.conf
  sudo ln -sf /etc/nginx/sites-available/licencas.inovatitech.com.br.conf /etc/nginx/sites-enabled/
  sudo rm -f /etc/nginx/sites-enabled/default
  sudo nginx -t
  sudo systemctl enable nginx
  sudo systemctl reload nginx

  echo "==> Certificado SSL..."
  sudo certbot --nginx -d licencas.inovatitech.com.br --non-interactive --agree-tos \
    -m admin@inovatitech.com.br --redirect || {
    echo "certbot falhou — tente: sudo certbot --nginx -d licencas.inovatitech.com.br"
  }
fi

echo ""
echo "==> OK"
echo "    http://127.0.0.1:8195/health"
echo "    https://licencas.inovatitech.com.br/login"
