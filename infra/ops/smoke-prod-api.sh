#!/usr/bin/env bash
# Checklist da API de licenças em produção (rodar na VPS).
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

BASE="${BASE:-http://127.0.0.1:8195}"
ENV_FILE="${ENV_FILE:-$APP_DIR/apps/web/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERRO: $ENV_FILE não encontrado"
  exit 1
fi

API_KEY="$(grep -E '^PRODUCT_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r')"
if [[ -z "$API_KEY" || "$API_KEY" == *"troque"* ]]; then
  echo "ERRO: PRODUCT_API_KEY não configurada em $ENV_FILE"
  exit 1
fi

pass() { echo "  OK: $1"; }
fail() { echo "  FALHA: $1"; exit 1; }

echo "==> Checklist API ($BASE)"

echo "1. Health"
health="$(curl -sf "$BASE/api/health")"
echo "$health" | grep -q '"ok":true' || fail "health não retornou ok"
pass "health"

echo "2. Validate sem chave -> 401"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/licenses/validate" \
  -H "Content-Type: application/json" \
  -d '{"license_key":"AAAAAAAAAAAAAAAAAAAAAAAAA","product":"cloud","clinica_id":1}')"
[[ "$code" == "401" ]] || fail "validate sem chave esperava 401, obteve $code"
pass "validate 401 sem API key"

echo "3. Validate chave inválida -> 422"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/licenses/validate" \
  -H "Content-Type: application/json" -H "X-License-Api-Key: $API_KEY" \
  -d '{"license_key":"CURTA","product":"cloud","clinica_id":1}')"
[[ "$code" == "422" ]] || fail "validate chave curta esperava 422, obteve $code"
pass "validate 422 chave inválida"

echo "4. Validate licença inexistente -> 404"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/licenses/validate" \
  -H "Content-Type: application/json" -H "X-License-Api-Key: $API_KEY" \
  -d '{"license_key":"ZZZZZZZZZZZZZZZZZZZZZZZZZ","product":"cloud","clinica_id":1}')"
[[ "$code" == "404" ]] || fail "validate inexistente esperava 404, obteve $code"
pass "validate 404 não encontrada"

echo "5. Status por clinica_id"
code="$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/licenses/status?clinica_id=999999" \
  -H "X-License-Api-Key: $API_KEY")"
[[ "$code" == "200" ]] || fail "status clinica_id esperava 200, obteve $code"
pass "status clinica_id"

echo "6. Heartbeat chave inválida -> 422"
code="$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/licenses/heartbeat?license_key=CURTA" \
  -H "X-License-Api-Key: $API_KEY")"
[[ "$code" == "422" ]] || fail "heartbeat chave curta esperava 422, obteve $code"
pass "heartbeat 422"

echo "7. Activate licença inexistente -> 404"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/licenses/activate" \
  -H "Content-Type: application/json" -H "X-License-Api-Key: $API_KEY" \
  -d '{"license_key":"ZZZZZZZZZZZZZZZZZZZZZZZZZ","product":"lab","clinica_id":1}')"
[[ "$code" == "404" ]] || fail "activate inexistente esperava 404, obteve $code"
pass "activate 404"

echo "==> Checklist API concluído com sucesso"
