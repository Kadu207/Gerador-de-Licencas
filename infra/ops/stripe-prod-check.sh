#!/usr/bin/env bash
# Verifica Stripe em produção (sem exibir segredos).
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"
BASE="${BASE:-http://127.0.0.1:8195}"

pass() { echo "  OK: $1"; }
fail() { echo "  FALHA: $1"; exit 1; }
warn() { echo "  AVISO: $1"; }

echo "==> Checklist Stripe produção"

for var in STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET PUBLIC_BASE_URL; do
  if grep -qE "^${var}=.+" "$APP_DIR/.env" 2>/dev/null; then
    pass "$var definido no .env raiz"
  else
    fail "$var ausente no .env raiz"
  fi
done

if grep -qE '^STRIPE_SECRET_KEY=.+' "$APP_DIR/apps/web/.env" 2>/dev/null; then
  pass "STRIPE_SECRET_KEY provisionado em apps/web/.env"
else
  warn "Rode: bash infra/ops/provision-web-env.sh"
fi

echo "==> Webhook endpoint (sem assinatura -> 400)"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/stripe/webhook" -d '{}')"
[[ "$code" == "400" ]] || fail "webhook esperava 400 sem signature, obteve $code"
pass "POST /api/stripe/webhook ativo"

health="$(curl -sf "$BASE/api/health")"
echo "$health" | grep -q '"productApiConfigured":true' || warn "PRODUCT_API_KEY não configurada"
pass "health OK"

echo ""
echo "Configure no Stripe Dashboard (modo Live):"
echo "  Webhook URL: https://licencas.inovatitech.com.br/api/stripe/webhook"
echo "  Evento: checkout.session.completed"
echo "  Chave restrita (rk_live_): Checkout Sessions → Write"
echo "  PIX/boleto/cartão: Payment Method Configurations (Brasil)"
echo ""
echo "==> Checklist Stripe concluído"
