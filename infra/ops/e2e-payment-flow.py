#!/usr/bin/env python3
"""Teste E2E na VPS: licença + pagamento pendente + webhook Stripe simulado."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import random
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request


def psql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "licencas-db",
        "psql",
        "-U",
        "licencas",
        "-d",
        "licencas_db",
        "-v",
        "ON_ERROR_STOP=1",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    return subprocess.check_output(cmd, text=True).strip()


def read_env_value(path: str, key: str) -> str:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip("\r")
    return ""


def http_post(url: str, body: bytes, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> int:
    parser = argparse.ArgumentParser(description="E2E pagamento + webhook Stripe")
    parser.add_argument("--env-file", default="apps/web/.env")
    parser.add_argument("--base", default="http://127.0.0.1:8195")
    parser.add_argument("--product", default="cloud", choices=["cloud", "lab", "vde"])
    parser.add_argument("--plan", default="annual", choices=["monthly", "semiannual", "annual"])
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    webhook_secret = read_env_value(args.env_file, "STRIPE_WEBHOOK_SECRET")
    api_key = read_env_value(args.env_file, "PRODUCT_API_KEY")

    if not webhook_secret or "troque" in webhook_secret.lower():
        print("ERRO: STRIPE_WEBHOOK_SECRET não configurado")
        return 1

    stamp = int(time.time())
    client_name = f"E2E PAGAMENTO {stamp}"
    license_key = "".join(random.choices(string.ascii_uppercase + string.digits, k=25))

    print(f"==> E2E ({args.product} / {args.plan})")
    print(f"1. Cliente: {client_name}")

    client_id = psql(
        f"""
        INSERT INTO clients (nome, document_type, status, email, created_at, updated_at)
        VALUES ('{client_name}', 'cnpj', 'active', 'e2e{stamp}@inovatitech.test', NOW(), NOW())
        RETURNING id;
        """
    )
    print(f"   client_id={client_id}")

    clinica_col = "clinica_id_erp" if args.product in ("cloud", "vde", "erp") else "clinica_id_lab"
    clinica_val = 900000 + (stamp % 100000)
    psql(f"UPDATE clients SET {clinica_col} = {clinica_val} WHERE id = {client_id};")
    print(f"   {clinica_col}={clinica_val}")

    print("2. Licença (validade 5 dias)")
    license_id = psql(
        f"""
        INSERT INTO license_records (
          client_id, license_key, produto, periodo, payment_plan, payment_status,
          starts_at, ends_at, payment_due_at, manual_status, created_by, created_at
        ) VALUES (
          {client_id}, '{license_key}', '{args.product}', '1y', '{args.plan}', 'pending',
          NOW(), NOW() + interval '5 days', NOW() + interval '5 days', 'active', 'e2e_script', NOW()
        )
        RETURNING id;
        """
    )
    ends_before = psql(f"SELECT ends_at FROM license_records WHERE id = {license_id};")
    print(f"   license_id={license_id} key={license_key}")
    print(f"   ends_at antes={ends_before}")

    prices = {
        ("cloud", "monthly"): "497.00",
        ("cloud", "semiannual"): "2486.00",
        ("cloud", "annual"): "4970.00",
        ("lab", "monthly"): "299.00",
        ("lab", "semiannual"): "1599.00",
        ("lab", "annual"): "2999.00",
        ("vde", "annual"): "0.00",
    }
    amount = prices.get((args.product, args.plan), "100.00")

    print("3. Pagamento pendente")
    payment_id = psql(
        f"""
        INSERT INTO payments (
          client_id, license_id, amount, currency, payment_plan, status, created_at
        ) VALUES (
          {client_id}, {license_id}, {amount}, 'brl', '{args.plan}', 'pending', NOW()
        )
        RETURNING id;
        """
    )
    print(f"   payment_id={payment_id} R$ {amount}")

    print("4. Webhook simulado")
    event = {
        "id": f"evt_e2e_{stamp}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_e2e_{stamp}",
                "object": "checkout.session",
                "payment_intent": f"pi_e2e_{stamp}",
                "payment_method_types": ["card"],
                "metadata": {
                    "payment_id": str(payment_id),
                    "client_id": str(client_id),
                    "license_id": str(license_id),
                    "operator": "e2e_script",
                    "product_slug": args.product,
                    "payment_plan": args.plan,
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
        f"{args.base}/api/stripe/webhook",
        payload.encode(),
        {
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
            "Content-Length": str(len(payload)),
        },
    )
    print(f"   HTTP {status}: {body}")
    if status != 200:
        return 1

    payment_status = psql(f"SELECT status FROM payments WHERE id = {payment_id};")
    ends_after = psql(f"SELECT ends_at FROM license_records WHERE id = {license_id};")
    lic_payment = psql(f"SELECT payment_status FROM license_records WHERE id = {license_id};")

    print("5. Verificação")
    print(f"   payment.status={payment_status}")
    print(f"   license.payment_status={lic_payment}")
    print(f"   ends_at depois={ends_after}")

    if payment_status != "completed":
        print("ERRO: pagamento não confirmado")
        return 1
    if ends_after <= ends_before:
        print("ERRO: ends_at não estendido")
        return 1

    if api_key and "troque" not in api_key.lower():
        print("6. API validate")
        validate_body = json.dumps(
            {"license_key": license_key, "clinica_id": clinica_val, "product": args.product}
        ).encode()
        req = urllib.request.Request(
            f"{args.base}/api/v1/licenses/validate",
            data=validate_body,
            headers={"Content-Type": "application/json", "X-License-Api-Key": api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        print(f"   valid={data.get('valid')} daysRemaining={data.get('daysRemaining')}")
        if not data.get("valid"):
            print("ERRO: validate retornou valid=false")
            return 1
    else:
        print("6. API validate — pulado")

    if not args.keep:
        print("7. Limpeza")
        psql(f"DELETE FROM payments WHERE client_id = {client_id};")
        psql(f"DELETE FROM license_records WHERE id = {license_id};")
        psql(f"DELETE FROM clients WHERE id = {client_id};")
    else:
        print(f"7. Dados mantidos — /clients/{client_id}")

    print("\n✓ E2E OK: licença + webhook + renovação confirmados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
