#!/usr/bin/env bash
# Teste ponta-a-ponta na VPS: emite licença + pagamento pendente + simula webhook Stripe.
#
# Uso:
#   cd /opt/gerador-licencas
#   bash infra/ops/e2e-payment-flow.sh
#   bash infra/ops/e2e-payment-flow.sh --product lab
#   bash infra/ops/e2e-payment-flow.sh --keep
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

ENV_FILE="${ENV_FILE:-$APP_DIR/apps/web/.env}"
BASE="${BASE:-http://127.0.0.1:8195}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERRO: $ENV_FILE não encontrado. Rode: bash infra/ops/provision-web-env.sh"
  exit 1
fi

exec python3 "$APP_DIR/infra/ops/e2e-payment-flow.py" \
  --env-file "$ENV_FILE" \
  --base "$BASE" \
  "$@"
