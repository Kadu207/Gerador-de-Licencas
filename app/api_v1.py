"""API REST pública para produtos validarem licenças remotamente."""
from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.licensing import (
    PERIOD_LABELS,
    PRODUCT_LABELS,
    STATUS_CANCELLED,
    STATUS_REVOKED,
    is_valid_license_key_format,
    normalize_api_product,
    normalize_license_key,
    product_matches_license,
)
from app.models import Client, LicenseRecord, get_db
from app.services import effective_for_license, revoke_license

router = APIRouter(prefix="/api/v1/licenses", tags=["licenses-api"])


def require_product_api_key(x_license_api_key: str | None = Header(default=None)) -> None:
    expected = (settings.product_api_key or "").strip()
    if not expected:
        raise HTTPException(503, "Servidor de licenças sem PRODUCT_API_KEY configurada")
    provided = (x_license_api_key or "").strip()
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(401, "Chave de API inválida")


class LicenseScope(BaseModel):
    clinica_id: int = Field(..., ge=1)
    unidade_id: str | None = Field(default=None, max_length=64)
    product: str = Field(default="lab", max_length=32)


class ValidateRequest(LicenseScope):
    license_key: str = Field(..., min_length=25, max_length=30)


class ActivateRequest(ValidateRequest):
    installation_id: str | None = Field(default=None, max_length=128)


class RevokeRequest(BaseModel):
    license_key: str = Field(..., min_length=25, max_length=30)
    reason: str = Field(default="", max_length=500)


def _status_payload(lic: LicenseRecord, client: Client | None, effective: dict) -> dict:
    valid = effective.get("validForSoftware", False) and lic.manual_status not in {
        STATUS_REVOKED,
        STATUS_CANCELLED,
    }
    return {
        "valid": valid,
        "hasLicense": valid,
        "status": effective.get("status"),
        "phase": effective.get("phase"),
        "produto": lic.produto,
        "produtoLabel": PRODUCT_LABELS.get(lic.produto, lic.produto),
        "periodo": lic.periodo,
        "periodoLabel": PERIOD_LABELS.get(lic.periodo, lic.periodo),
        "paymentPlan": lic.payment_plan,
        "startsAt": lic.starts_at.isoformat() if lic.starts_at else None,
        "endsAt": lic.ends_at.isoformat() if lic.ends_at else None,
        "paymentDueAt": lic.payment_due_at.isoformat() if lic.payment_due_at else None,
        "daysRemaining": effective.get("daysRemaining", 0),
        "daysOverdue": effective.get("daysOverdue", 0),
        "licenseExpired": effective.get("licenseExpired", False),
        "paymentPhase": effective.get("paymentPhase"),
        "licenseKeyMasked": f"****{lic.license_key[-4:]}" if len(lic.license_key) >= 4 else "****",
        "clinicaId": client.clinica_id_lab if client else None,
        "clinicaIdErp": client.clinica_id_erp if client else None,
        "unidadeId": lic.unidade_id,
        "clienteNome": client.nome if client else "",
        "message": effective.get("message", ""),
        "alertLevel": effective.get("alertLevel", "none"),
        "remainingLabel": effective.get("remainingLabel", ""),
        "source": "license-server",
    }


def _find_license(db: Session, key: str) -> tuple[LicenseRecord | None, Client | None]:
    lic = db.query(LicenseRecord).filter(LicenseRecord.license_key == key).first()
    if not lic:
        return None, None
    client = db.query(Client).filter(Client.id == lic.client_id).first()
    return lic, client


def _bound_to_other_scope(
    lic: LicenseRecord,
    client: Client | None,
    clinica_id: int,
    unidade_id: str | None,
    api_product: str,
) -> bool:
    normalized = normalize_api_product(api_product)
    if normalized in {"cloud", "erp"}:
        bound = client.clinica_id_erp if client and client.clinica_id_erp else None
    elif normalized == "vde":
        bound = client.clinica_id_erp if client and client.clinica_id_erp else None
    else:
        bound = client.clinica_id_lab if client and client.clinica_id_lab else None

    if bound and bound != clinica_id:
        return True
    if lic.unidade_id:
        expected = unidade_id or ""
        return lic.unidade_id != expected
    return False


def _validate_product_match(lic: LicenseRecord, api_product: str) -> None:
    if not product_matches_license(api_product, lic.produto):
        normalized = normalize_api_product(api_product)
        raise HTTPException(422, f"LICENSE_PRODUCT_MISMATCH:{normalized}")


@router.post("/validate", dependencies=[Depends(require_product_api_key)])
def validate_license(body: ValidateRequest, db: Session = Depends(get_db)):
    key = normalize_license_key(body.license_key)
    if not is_valid_license_key_format(key):
        raise HTTPException(422, "INVALID_LICENSE_KEY")

    lic, client = _find_license(db, key)
    if not lic:
        raise HTTPException(404, "LICENSE_NOT_FOUND")
    _validate_product_match(lic, body.product)
    if _bound_to_other_scope(lic, client, body.clinica_id, body.unidade_id, body.product):
        raise HTTPException(409, "LICENSE_SCOPE_MISMATCH")

    effective = effective_for_license(lic)
    return _status_payload(lic, client, effective)


@router.post("/activate", dependencies=[Depends(require_product_api_key)])
def activate_license(body: ActivateRequest, db: Session = Depends(get_db)):
    from app.licensing import STATUS_ACTIVE, now_utc
    from app.services import sync_and_refresh

    key = normalize_license_key(body.license_key)
    if not is_valid_license_key_format(key):
        raise HTTPException(422, "INVALID_LICENSE_KEY")

    lic, client = _find_license(db, key)
    if not lic:
        raise HTTPException(404, "LICENSE_NOT_FOUND")
    _validate_product_match(lic, body.product)
    if lic.manual_status in {STATUS_REVOKED, STATUS_CANCELLED}:
        raise HTTPException(422, "LICENSE_REVOKED")
    if _bound_to_other_scope(lic, client, body.clinica_id, body.unidade_id, body.product):
        raise HTTPException(409, "LICENSE_ALREADY_USED")

    normalized = normalize_api_product(body.product)
    if client:
        if normalized in {"cloud", "erp", "vde"} and not client.clinica_id_erp:
            client.clinica_id_erp = body.clinica_id
        if normalized == "lab" and not client.clinica_id_lab:
            client.clinica_id_lab = body.clinica_id

    scope_uid = (body.unidade_id or "").strip() or None
    if scope_uid and not lic.unidade_id:
        lic.unidade_id = scope_uid

    if body.installation_id:
        lic.installation_id = body.installation_id.strip()
    lic.manual_status = STATUS_ACTIVE
    db.commit()
    db.refresh(lic)

    if client:
        sync_and_refresh(db, lic, client, "api_v1_activate")

    effective = effective_for_license(lic)
    return {"msg": "OK", "licenca": _status_payload(lic, client, effective)}


@router.get("/status", dependencies=[Depends(require_product_api_key)])
def license_status(
    clinica_id: int = Query(..., ge=1),
    unidade_id: str | None = Query(default=None),
    product: str = Query(default="lab"),
    license_key: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if license_key:
        key = normalize_license_key(license_key)
        lic, client = _find_license(db, key)
        if not lic:
            raise HTTPException(404, "LICENSE_NOT_FOUND")
        effective = effective_for_license(lic)
        return _status_payload(lic, client, effective)

    normalized = normalize_api_product(product)
    if normalized in {"cloud", "erp", "vde"}:
        q = (
            db.query(LicenseRecord)
            .join(Client, Client.id == LicenseRecord.client_id)
            .filter(Client.clinica_id_erp == clinica_id)
        )
    else:
        q = (
            db.query(LicenseRecord)
            .join(Client, Client.id == LicenseRecord.client_id)
            .filter(Client.clinica_id_lab == clinica_id)
        )

    if unidade_id:
        q = q.filter(LicenseRecord.unidade_id == unidade_id)
    else:
        q = q.filter((LicenseRecord.unidade_id.is_(None)) | (LicenseRecord.unidade_id == ""))

    lic = q.order_by(LicenseRecord.id.desc()).first()
    if not lic:
        return {
            "valid": False,
            "hasLicense": False,
            "status": "none",
            "clinicaId": clinica_id,
            "unidadeId": unidade_id,
            "source": "license-server",
            "message": "Nenhuma licença vinculada a esta unidade.",
        }

    client = db.query(Client).filter(Client.id == lic.client_id).first()
    effective = effective_for_license(lic)
    return _status_payload(lic, client, effective)


@router.get("/heartbeat", dependencies=[Depends(require_product_api_key)])
def license_heartbeat(
    license_key: str = Query(..., min_length=25),
    product: str = Query(default="lab"),
    db: Session = Depends(get_db),
):
    """Poll leve para bloqueio pós-vencimento."""
    key = normalize_license_key(license_key)
    lic, client = _find_license(db, key)
    if not lic:
        return {"valid": False, "blocked": True, "reason": "LICENSE_NOT_FOUND"}
    effective = effective_for_license(lic)
    valid = effective.get("validForSoftware", False)
    return {
        "valid": valid,
        "blocked": not valid,
        "licenseExpired": effective.get("licenseExpired", False),
        "paymentPhase": effective.get("paymentPhase"),
        "daysRemaining": effective.get("daysRemaining", 0),
        "alertLevel": effective.get("alertLevel", "none"),
    }


@router.post("/revoke", dependencies=[Depends(require_product_api_key)])
def revoke_license_api(body: RevokeRequest, db: Session = Depends(get_db)):
    key = normalize_license_key(body.license_key)
    if not is_valid_license_key_format(key):
        raise HTTPException(422, "INVALID_LICENSE_KEY")

    lic, _ = _find_license(db, key)
    if not lic:
        raise HTTPException(404, "LICENSE_NOT_FOUND")

    try:
        lic = revoke_license(db, operator="api", license_id=lic.id, reason=body.reason or "API revoke")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    client = db.query(Client).filter(Client.id == lic.client_id).first()
    effective = effective_for_license(lic)
    return {"msg": "REVOKED", "licenca": _status_payload(lic, client, effective)}
