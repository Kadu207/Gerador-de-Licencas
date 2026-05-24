"""Integracao Gerador -> Postgres ERP -> ativacao via API."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from app.config import settings
from app.models import Client, LicenseRecord, SessionLocal, init_db
from app.services import refresh_all_licenses, sync_and_refresh


def erp_request(method: str, path: str, token: str, cid: int, body: dict | None = None) -> dict:
    base = settings.erp_api_base.rstrip("/")
    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Clinica-Id": str(cid),
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def erp_login(base: str, usuario: str, senha: str) -> tuple[str, int]:
    url = f"{base.rstrip('/')}/login"
    body = json.dumps({"usuario": usuario, "senha": senha}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("token") or data.get("access_token")
    cid = data.get("clinica_id") or data.get("cid")
    if not token or cid is None:
        raise RuntimeError(f"Login ERP sem token/cid: {data}")
    return token, int(cid)


def main() -> int:
    from app.config import settings as s

    if not s.sync_remote_enabled:
        print("ERRO: SYNC_REMOTE_ENABLED=false no .env do Gerador.", file=sys.stderr)
        return 1

    init_db()
    db = SessionLocal()
    try:
        n = refresh_all_licenses(db)
        print(f"[sync] {n} licenca(s) processada(s)")

        lic = db.query(LicenseRecord).order_by(LicenseRecord.id.desc()).first()
        if not lic:
            print("ERRO: nenhuma licenca no gerador.", file=sys.stderr)
            return 1
        client = db.query(Client).filter(Client.id == lic.client_id).first()
        if not client:
            print("ERRO: cliente da licenca nao encontrado.", file=sys.stderr)
            return 1

        result = sync_and_refresh(db, lic, client, "integration_e2e")
        print(f"[sync] ERP: {result['sync'].get('erp')} | Lab: {result['sync'].get('lab')}")

        if result["sync"].get("erp") != "ok":
            print("ERRO: sync ERP falhou. Verifique Postgres exposto na porta 5432.", file=sys.stderr)
            return 1

        key = lic.license_key
        cid = client.clinica_id_erp or 1
    finally:
        db.close()

    usuario = s.erp_admin_user
    senha = s.erp_admin_password
    base = s.erp_api_base

    print(f"[erp] login em {base} como {usuario}...")
    token, login_cid = erp_login(base, usuario, senha)
    use_cid = cid or login_cid
    print(f"[erp] clinica_id={use_cid}")

    print(f"[erp] ativando chave {key}...")
    activated = erp_request("POST", "/licencas/ativar", token, use_cid, {"license_key": key})
    print("[erp] licenca ativada:")
    print(json.dumps(activated, ensure_ascii=False, indent=2))

    status = erp_request("GET", "/licencas/status", token, use_cid)
    print("[erp] status atual:")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {detail}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"ERP indisponivel: {exc.reason}", file=sys.stderr)
        raise SystemExit(1)
