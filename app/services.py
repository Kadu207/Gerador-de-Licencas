"""Regras de negócio: clientes, licenças, renovação, revogação e sincronização."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.licensing import (
    ALLOWED_PAYMENT_PLANS,
    ALLOWED_PERIODS,
    ALLOWED_PRODUCTS,
    PERIOD_LABELS,
    PRODUCT_LABELS,
    STATUS_ACTIVE,
    STATUS_CANCELLED,
    STATUS_REVOKED,
    compute_effective_status,
    compute_ends_at,
    format_remaining_counter,
    generate_lab_secret,
    generate_license_key,
    now_ts,
    now_utc,
    parse_ts,
    product_includes_lab,
)
from app.models import AuditLog, Client, ClientAddress, LicenseRecord
from app.sync import sync_license_to_products


def _dt_to_str(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def log_action(
    db: Session,
    operator: str,
    action: str,
    detail: str,
    *,
    ip_address: str = "",
    correlation_id: str = "",
) -> None:
    db.add(
        AuditLog(
            operator=operator,
            action=action,
            detail=detail,
            ip_address=ip_address,
            correlation_id=correlation_id,
        )
    )
    db.commit()


def license_to_dict(lic: LicenseRecord) -> dict:
    return {
        "id": lic.id,
        "client_id": lic.client_id,
        "license_key": lic.license_key,
        "produto": lic.produto,
        "produto_label": PRODUCT_LABELS.get(lic.produto, lic.produto),
        "periodo": lic.periodo,
        "periodo_label": PERIOD_LABELS.get(lic.periodo, lic.periodo),
        "payment_plan": lic.payment_plan,
        "payment_status": lic.payment_status,
        "starts_at": _dt_to_str(lic.starts_at),
        "ends_at": _dt_to_str(lic.ends_at),
        "payment_due_at": _dt_to_str(lic.payment_due_at),
        "manual_status": lic.manual_status,
        "lab_secret": lic.lab_secret,
        "erp_synced_at": _dt_to_str(lic.erp_synced_at),
        "lab_synced_at": _dt_to_str(lic.lab_synced_at),
        "unidade_id": lic.unidade_id,
        "installation_id": lic.installation_id,
        "revoked_at": _dt_to_str(lic.revoked_at),
        "created_by": lic.created_by,
        "notes": lic.notes,
        "created_at": _dt_to_str(lic.created_at),
    }


def client_to_dict(client: Client) -> dict:
    addr = client.address
    return {
        "id": client.id,
        "parent_client_id": client.parent_client_id,
        "nome": client.nome,
        "razao_social": client.razao_social,
        "document_type": client.document_type,
        "cnpj": client.cnpj,
        "cpf": client.cpf,
        "email": client.email,
        "email_02": client.email_02,
        "telefone": client.telefone,
        "telefone_02": client.telefone_02,
        "telefone_03": client.telefone_03,
        "clinica_id_erp": client.clinica_id_erp,
        "clinica_id_lab": client.clinica_id_lab,
        "status": client.status,
        "notes": client.notes,
        "address": {
            "logradouro": addr.logradouro if addr else "",
            "numero": addr.numero if addr else "",
            "complemento": addr.complemento if addr else "",
            "bairro": addr.bairro if addr else "",
            "cidade": addr.cidade if addr else "",
            "uf": addr.uf if addr else "",
            "cep": addr.cep if addr else "",
        },
        "created_at": _dt_to_str(client.created_at),
        "updated_at": _dt_to_str(client.updated_at),
    }


def effective_for_license(lic: LicenseRecord) -> dict:
    eff = compute_effective_status(
        manual_status=lic.manual_status,
        ends_at=lic.ends_at,
        payment_due_at=lic.payment_due_at,
        block_after_days=settings.block_after_days,
        cancel_after_days=settings.cancel_after_days,
    )
    eff["remainingLabel"] = format_remaining_counter(eff.get("daysRemaining", 0))
    return eff


def create_client(
    db: Session,
    *,
    operator: str,
    nome: str,
    razao_social: str = "",
    document_type: str = "cnpj",
    cnpj: str = "",
    cpf: str = "",
    email: str = "",
    email_02: str = "",
    telefone: str = "",
    telefone_02: str = "",
    telefone_03: str = "",
    clinica_id_erp: int | None = None,
    clinica_id_lab: int | None = None,
    parent_client_id: int | None = None,
    notes: str = "",
    address: dict | None = None,
) -> Client:
    client = Client(
        nome=nome.strip(),
        razao_social=razao_social.strip(),
        document_type=document_type.strip() or "cnpj",
        cnpj=cnpj.strip(),
        cpf=cpf.strip(),
        email=email.strip(),
        email_02=email_02.strip(),
        telefone=telefone.strip(),
        telefone_02=telefone_02.strip(),
        telefone_03=telefone_03.strip(),
        clinica_id_erp=clinica_id_erp,
        clinica_id_lab=clinica_id_lab or clinica_id_erp,
        parent_client_id=parent_client_id,
        notes=notes.strip(),
    )
    db.add(client)
    db.flush()

    if address:
        db.add(
            ClientAddress(
                client_id=client.id,
                logradouro=address.get("logradouro", ""),
                numero=address.get("numero", ""),
                complemento=address.get("complemento", ""),
                bairro=address.get("bairro", ""),
                cidade=address.get("cidade", ""),
                uf=address.get("uf", ""),
                cep=address.get("cep", ""),
            )
        )

    db.commit()
    db.refresh(client)
    log_action(db, operator, "client_create", f"Cliente {client.id} — {client.nome}")
    return client


def issue_license(
    db: Session,
    *,
    operator: str,
    client_id: int,
    produto: str,
    periodo: str,
    payment_plan: str = "annual",
    notes: str = "",
) -> LicenseRecord:
    if produto not in ALLOWED_PRODUCTS:
        raise ValueError("INVALID_PRODUCT")
    if periodo not in ALLOWED_PERIODS:
        raise ValueError("INVALID_PERIOD")
    if payment_plan not in ALLOWED_PAYMENT_PLANS:
        raise ValueError("INVALID_PAYMENT_PLAN")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    start = now_utc()
    ends = compute_ends_at(start, periodo)

    for _ in range(12):
        key = generate_license_key()
        if db.query(LicenseRecord).filter(LicenseRecord.license_key == key).first():
            continue
        lic = LicenseRecord(
            client_id=client.id,
            license_key=key,
            produto=produto,
            periodo=periodo,
            payment_plan=payment_plan,
            payment_status=STATUS_ACTIVE,
            starts_at=start,
            ends_at=ends,
            payment_due_at=ends,
            manual_status=STATUS_ACTIVE,
            lab_secret=generate_lab_secret() if product_includes_lab(produto) else None,
            created_by=operator,
            notes=notes.strip(),
        )
        db.add(lic)
        db.commit()
        db.refresh(lic)
        sync_and_refresh(db, lic, client, operator)
        log_action(db, operator, "license_issue", f"{key} — {produto}/{periodo} — cliente {client.nome}")
        return lic

    raise RuntimeError("LICENSE_KEY_COLLISION")


def renew_license(
    db: Session,
    *,
    operator: str,
    license_id: int,
    periodo: str,
) -> LicenseRecord:
    if periodo not in ALLOWED_PERIODS:
        raise ValueError("INVALID_PERIOD")

    lic = db.query(LicenseRecord).filter(LicenseRecord.id == license_id).first()
    if not lic:
        raise ValueError("LICENSE_NOT_FOUND")

    client = db.query(Client).filter(Client.id == lic.client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    ref = now_utc()
    current_end = lic.ends_at or ref
    if isinstance(current_end, str):
        current_end = parse_ts(current_end) or ref
    base = current_end if current_end > ref else ref
    new_end = compute_ends_at(base, periodo)

    lic.periodo = periodo
    lic.starts_at = base
    lic.ends_at = new_end
    lic.payment_due_at = new_end
    lic.manual_status = STATUS_ACTIVE
    lic.payment_status = STATUS_ACTIVE
    if product_includes_lab(lic.produto) and not lic.lab_secret:
        lic.lab_secret = generate_lab_secret()

    db.commit()
    db.refresh(lic)
    sync_and_refresh(db, lic, client, operator)
    log_action(db, operator, "license_renew", f"{lic.license_key} renovada — {periodo}")
    return lic


def revoke_license(
    db: Session,
    *,
    operator: str,
    license_id: int,
    reason: str = "",
) -> LicenseRecord:
    lic = db.query(LicenseRecord).filter(LicenseRecord.id == license_id).first()
    if not lic:
        raise ValueError("LICENSE_NOT_FOUND")

    client = db.query(Client).filter(Client.id == lic.client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    lic.manual_status = STATUS_REVOKED
    lic.payment_status = STATUS_REVOKED
    lic.revoked_at = now_utc()
    lic.revoked_by = operator
    if reason:
        lic.notes = (lic.notes or "") + f" | revoke: {reason}"

    db.commit()
    db.refresh(lic)
    sync_and_refresh(db, lic, client, operator)
    log_action(db, operator, "license_revoke", f"{lic.license_key} — {reason}")
    return lic


def cancel_client(db: Session, *, operator: str, client_id: int, reason: str = "") -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    client.status = STATUS_CANCELLED
    for lic in client.licenses:
        lic.manual_status = STATUS_CANCELLED
        lic.payment_status = STATUS_CANCELLED
        if reason:
            lic.notes = (lic.notes or "") + f" | cancel: {reason}"

    db.commit()
    for lic in client.licenses:
        sync_and_refresh(db, lic, client, operator)

    log_action(db, operator, "client_cancel", f"Cliente {client.id} — {reason}")
    db.refresh(client)
    return client


def sync_and_refresh(db: Session, lic: LicenseRecord, client: Client, operator: str) -> dict:
    effective = effective_for_license(lic)
    sync_result = sync_license_to_products(license_to_dict(lic), client_to_dict(client), effective)
    ts = now_utc()
    if sync_result.get("erp") == "ok":
        lic.erp_synced_at = ts
    if sync_result.get("lab") == "ok":
        lic.lab_synced_at = ts
    db.commit()
    return {"effective": effective, "sync": sync_result}


def refresh_all_licenses(db: Session) -> int:
    count = 0
    licenses = db.query(LicenseRecord).all()
    for lic in licenses:
        client = db.query(Client).filter(Client.id == lic.client_id).first()
        if not client or client.status == STATUS_CANCELLED:
            continue
        effective = effective_for_license(lic)
        if effective["phase"] == "cancel_eligible" and lic.manual_status != STATUS_CANCELLED:
            lic.manual_status = STATUS_ACTIVE
        sync_license_to_products(license_to_dict(lic), client_to_dict(client), effective)
        count += 1
    db.commit()
    return count
