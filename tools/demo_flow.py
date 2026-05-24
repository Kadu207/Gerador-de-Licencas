"""Fluxo demo: cadastrar cliente, gerar licenca e (opcional) ativar no ERP."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from app.auth import hash_password
from app.config import settings
from app.models import Operator, SessionLocal, init_db
from app.services import create_client, issue_license


def ensure_admin(db) -> None:
    if db.query(Operator).first():
        return
    db.add(
        Operator(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            nome="Administrador",
            created_at="bootstrap",
        )
    )
    db.commit()


def activate_in_erp(license_key: str, erp_base: str, token: str, clinica_id: int) -> dict:
    url = f"{erp_base.rstrip('/')}/licencas/ativar"
    body = json.dumps({"license_key": license_key}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Clinica-Id": str(clinica_id),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo do fluxo de licenciamento")
    parser.add_argument("--nome", default="Clinica Demo Excellence")
    parser.add_argument("--cnpj", default="52998224725")
    parser.add_argument("--produto", default="cloud", choices=["cloud", "cloud_lab", "lab"])
    parser.add_argument("--periodo", default="trial", choices=["trial", "1y", "2y", "4y", "5y"])
    parser.add_argument("--clinica-id-erp", type=int, default=1)
    parser.add_argument("--erp-base", default="http://127.0.0.1:8000")
    parser.add_argument("--erp-token", default="")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        ensure_admin(db)
        client = create_client(
            db,
            operator=settings.admin_username,
            nome=args.nome,
            cnpj=args.cnpj,
            clinica_id_erp=args.clinica_id_erp,
            notes="Cliente criado pelo demo_flow.py",
        )
        lic = issue_license(
            db,
            operator=settings.admin_username,
            client_id=client.id,
            produto=args.produto,
            periodo=args.periodo,
            notes="Licenca demo",
        )
        summary = {
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cnpj": client.cnpj,
            "clinica_id_erp": client.clinica_id_erp,
            "license_key": lic.license_key,
            "produto": lic.produto,
            "periodo": lic.periodo,
        }
    finally:
        db.close()

    print("=== Fluxo local concluido ===")
    print(f"Cliente ID: {summary['client_id']} | {summary['client_nome']} | CNPJ {summary['client_cnpj']}")
    print(f"Clinica ERP ID: {summary['clinica_id_erp']}")
    print(f"Produto: {summary['produto']} | Periodo: {summary['periodo']}")
    print(f"Chave: {summary['license_key']}")
    print(f"Banco local: {settings.local_database_url}")
    print(f"Sync remoto: {'ligado' if settings.sync_remote_enabled else 'desligado'}")

    if args.erp_token:
        try:
            result = activate_in_erp(summary["license_key"], args.erp_base, args.erp_token, args.clinica_id_erp)
            print("=== Ativacao no ERP ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"ERP retornou HTTP {exc.code}: {detail}", file=sys.stderr)
            return 1
        except urllib.error.URLError as exc:
            print(f"ERP indisponivel ({exc.reason}). Suba o Docker e repita com --erp-token.", file=sys.stderr)
            return 1
    else:
        print()
        print("Proximo passo (ERP):")
        print("1. Suba o Excellence Dental (Docker)")
        print("2. Em Empresa > Licenca, cole a chave acima")
        print("   ou execute:")
        print(
            f'   python tools/demo_flow.py --erp-token "SEU_JWT" --clinica-id-erp {args.clinica_id_erp}'
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
