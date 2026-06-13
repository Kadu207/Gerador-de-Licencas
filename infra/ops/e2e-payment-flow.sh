#!/usr/bin/env bash
# Teste ponta-a-ponta na VPS: emite licença + pagamento pendente + simula webhook Stripe.
#
# Uso:
#   cd /opt/gerador-licencas
#   bash infra/ops/e2e-payment-flow.sh
#   bash infra/ops/e2e-payment-flow.sh --product lab
#   bash infra/ops/e2e-payment-flow.sh --keep   # não remove dados de teste
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

BASE="${BASE:-http://127.0.0.1:8195}"
ENV_FILE="${ENV_FILE:-$APP_DIR/apps/web/.env}"
PRODUCT="${PRODUCT:-cloud}"
PAYMENT_PLAN="${PAYMENT_PLAN:-annual}"
KEEP_DATA=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --product) PRODUCT="$2"; shift 2 ;;
    --plan) PAYMENT_PLAN="$2"; shift 2 ;;
    --keep) KEEP_DATA=1; shift ;;
    -h|--help)
      echo "Uso: bash infra/ops/e2e-payment-flow.sh [--product cloud|lab] [--plan annual|monthly|semiannual] [--keep]"
      exit 0
      ;;
    *) echo "Opção desconhecida: $1"; exit 1 ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERRO: $ENV_FILE não encontrado. Rode: bash infra/ops/provision-web-env.sh"
  exit 1
fi

WEBHOOK_SECRET="$(grep -E '^STRIPE_WEBHOOK_SECRET=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r')"
API_KEY="$(grep -E '^PRODUCT_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r')"

if [[ -z "$WEBHOOK_SECRET" || "$WEBHOOK_SECRET" == *"troque"* ]]; then
  echo "ERRO: STRIPE_WEBHOOK_SECRET não configurado em $ENV_FILE"
  exit 1
fi

echo "==> E2E pagamento + webhook ($PRODUCT / $PAYMENT_PLAN)"

python3 <<'PY' "$ENV_FILE" "$BASE" "$PRODUCT" "$PAYMENT_PLAN" "$WEBHOOK_SECRET" "$API_KEY" "$KEEP_DATA"
import json
import hmac
import hashlib
import os
import random
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

env_file, base, product, payment_plan, webhook_secret, api_key, keep_data = sys.argv[1:8]
keep_data = keep_data == "1"
stamp = int(time.time())
client_name = f"E2E PAGAMENTO {stamp}"
license_key = "".join(random.choices(string.ascii_uppercase + string.digits, k=25))

def psql(sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", "licencas-db",
        "psql", "-U", "licencas", "-d", "licencas_db",
        "-v", "ON_ERROR_STOP=1", "-t", "-A", "-c", sql,
    ]
    return subprocess.check_output(cmd, text=True).strip()

def http_post(url: str, body: bytes, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print(f"1. Cliente de teste: {client_name}")
client_id = psql(
    f"""
    INSERT INTO clients (nome, document_type, status, email, created_at, updated_at)
    VALUES ('{client_name}', 'cnpj', 'active', 'e2e{stamp}@inovatitech.test', NOW(), NOW())
    RETURNING id;
    """
)
print(f"   client_id={client_id}")

clinica_col = "clinica_id_erp" if product in ("cloud", "vde", "erp") else "clinica_id_lab"
clinica_val = 900000 + (stamp % 100000)
psql(f"UPDATE clients SET {clinica_col} = {clinica_val} WHERE id = {client_id};")
print(f"   {clinica_col}={clinica_val}")

print("2. Licença emitida (validade curta: 5 dias)")
license_id = psql(
    f"""
    INSERT INTO license_records (
      client_id, license_key, produto, periodo, payment_plan, payment_status,
      starts_at, ends_at, payment_due_at, manual_status, created_by, created_at
    ) VALUES (
      {client_id}, '{license_key}', '{product}', '1y', '{payment_plan}', 'pending',
      NOW(), NOW() + interval '5 days', NOW() + interval '5 days', 'active', 'e2e_script', NOW()
    )
    RETURNING id;
    """
)
ends_before = psql(f"SELECT ends_at FROM license_records WHERE id = {license_id};")
print(f"   license_id={license_id} key={license_key}")
print(f"   ends_at antes={ends_before}")

amount = "497.00" if product == "cloud" else "299.00"
if payment_plan == "monthly":
    amount = "497.00" if product == "cloud" else "299.00"
elif payment_plan == "semiannual":
    amount = "2486.00" if product == "cloud" else "1599.00"
else:
    amount = "4970.00" if product == "cloud" else "2999.00"

print("3. Pagamento pendente (simula Checkout Stripe)")
payment_id = psql(
    f"""
    INSERT INTO payments (
      client_id, license_id, amount, currency, payment_plan, status, created_at
    ) VALUES (
      {client_id}, {license_id}, {amount}, 'brl', '{payment_plan}', 'pending', NOW()
    )
    RETURNING id;
    """
)
print(f"   payment_id={payment_id} amount=R$ {amount}")

print("4. Simula webhook checkout.session.completed")
session_id = f"cs_e2e_{stamp}"
event = {
    "id": f"evt_e2e_{stamp}",
    "object": "event",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": session_id,
            "object": "checkout.session",
            "payment_intent": f"pi_e2e_{stamp}",
            "payment_method_types": ["card"],
            "metadata": {
                "payment_id": str(payment_id),
                "client_id": str(client_id),
                "license_id": str(license_id),
                "operator": "e2e_script",
                "product_slug": product,
                "payment_plan": payment_plan,
            },
        }
    },
}
payload = json.dumps(event, separators=(",", ":"))
ts = int(time.time())
signed = f"{ts}.{payload}"
sig = hmac.new(webhook_secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
signature = f"t={ts},v1={sig}"

status, body = http_post(
    f"{base}/api/stripe/webhook",
    payload.encode(),
    {
        "Content-Type": "application/json",
        "Stripe-Signature": signature,
        "Content-Length": str(len(payload)),
    },
)
print(f"   webhook HTTP {status}: {body}")
if status != 200:
    raise SystemExit("Webhook falhou")

payment_status = psql(f"SELECT status FROM payments WHERE id = {payment_id};")
ends_after = psql(f"SELECT ends_at FROM license_records WHERE id = {license_id};")
lic_payment = psql(f"SELECT payment_status FROM license_records WHERE id = {license_id};")

print("5. Verificação pós-webhook")
print(f"   payment.status={payment_status}")
print(f"   license.payment_status={lic_payment}")
print(f"   ends_at depois={ends_after}")

if payment_status != "completed":
    raise SystemExit("Pagamento não ficou completed")
if ends_after <= ends_before:
    raise SystemExit("ends_at não foi estendido")

if api_key and "troque" not in api_key:
    print("6. API validate (produto integrado)")
    validate_body = json.dumps({
        "license_key": license_key,
        "clinica_id": clinica_val,
        "product": product,
    }).encode()
    req = urllib.request.Request(
        f"{base}/api/v1/licenses/validate",
        data=validate_body,
        headers={
            "Content-Type": "application/json",
            "X-License-Api-Key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    print(f"   valid={data.get('valid')} daysRemaining={data.get('daysRemaining')}")
    if not data.get("valid"):
        raise SystemExit("API validate retornou valid=false")
else:
    print("6. API validate — pulado (PRODUCT_API_KEY não configurada)")

if not keep_data:
    print("7. Limpeza dos dados de teste")
    psql(f"DELETE FROM payments WHERE client_id = {client_id};")
    psql(f"DELETE FROM license_records WHERE id = {license_id};")
    psql(f"DELETE FROM clients WHERE id = {client_id};")
    print("   removido")
else:
    print("7. Dados mantidos (--keep)")
    print(f"   Painel: {base.replace('127.0.0.1:8195', 'https://licencas.inovatitech.com.br')}/clients/{client_id}")

print("")
print("✓ E2E concluído: licença emitida, webhook aceito, pagamento confirmado, validade estendida.")
PY
