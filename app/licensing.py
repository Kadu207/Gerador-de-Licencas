"""Regras de licenciamento — cada software possui licença independente."""
from __future__ import annotations

import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

LICENSE_KEY_LEN = 25
LICENSE_ALPHABET = string.ascii_uppercase + string.digits
LICENSE_KEY_PATTERN = re.compile(rf"^[A-Z0-9]{{{LICENSE_KEY_LEN}}}$")

PRODUCT_CLOUD = "cloud"
PRODUCT_LAB = "lab"
PRODUCT_VDE = "vde"
ALLOWED_PRODUCTS = {PRODUCT_CLOUD, PRODUCT_LAB, PRODUCT_VDE}

PERIOD_TRIAL = "trial"
PERIOD_1Y = "1y"
PERIOD_2Y = "2y"
PERIOD_3Y = "3y"
PERIOD_4Y = "4y"
PERIOD_5Y = "5y"
ALLOWED_PERIODS = {PERIOD_TRIAL, PERIOD_1Y, PERIOD_2Y, PERIOD_3Y, PERIOD_4Y, PERIOD_5Y}

PERIOD_DAYS: dict[str, int] = {
    PERIOD_TRIAL: 30,
    PERIOD_1Y: 365,
    PERIOD_2Y: 730,
    PERIOD_3Y: 1095,
    PERIOD_4Y: 1460,
    PERIOD_5Y: 1825,
}

PRODUCT_LABELS = {
    PRODUCT_CLOUD: "Produto 01",
    PRODUCT_LAB: "Produto 02",
    PRODUCT_VDE: "Produto 03",
}

PERIOD_LABELS = {
    PERIOD_TRIAL: "Teste (30 dias)",
    PERIOD_1Y: "1 ano",
    PERIOD_2Y: "2 anos",
    PERIOD_3Y: "3 anos",
    PERIOD_4Y: "4 anos",
    PERIOD_5Y: "5 anos",
}

PAYMENT_PLAN_MONTHLY = "monthly"
PAYMENT_PLAN_SEMIANNUAL = "semiannual"
PAYMENT_PLAN_ANNUAL = "annual"
ALLOWED_PAYMENT_PLANS = {PAYMENT_PLAN_MONTHLY, PAYMENT_PLAN_SEMIANNUAL, PAYMENT_PLAN_ANNUAL}
PAYMENT_PLAN_LABELS = {
    PAYMENT_PLAN_MONTHLY: "Mensal",
    PAYMENT_PLAN_SEMIANNUAL: "Semestral",
    PAYMENT_PLAN_ANNUAL: "Anual",
}

ALERT_MILESTONES = (20, 15, 7, 3, 2, 1)

STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_GRACE = "grace"
STATUS_BLOCKED = "blocked"
STATUS_CANCELLED = "cancelled"
STATUS_REVOKED = "revoked"
STATUS_EXPIRED = "expired"

API_PRODUCT_ALIASES = {
    "cloud": PRODUCT_CLOUD,
    "erp": PRODUCT_CLOUD,
    "lab": PRODUCT_LAB,
    "vde": PRODUCT_VDE,
    "vde_incorporadora": PRODUCT_VDE,
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_ts() -> str:
    return now_utc().strftime("%Y-%m-%d %H:%M:%S")


def parse_ts(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    raw = str(value).strip().replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:19] if " " in fmt else raw[:10], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def generate_license_key() -> str:
    return "".join(secrets.choice(LICENSE_ALPHABET) for _ in range(LICENSE_KEY_LEN))


def generate_lab_secret() -> str:
    return secrets.token_hex(32)


def normalize_license_key(key: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", key or "").upper()[:LICENSE_KEY_LEN]


def is_valid_license_key_format(key: str) -> bool:
    normalized = normalize_license_key(key)
    return bool(LICENSE_KEY_PATTERN.match(normalized))


def compute_ends_at(start: datetime, periodo: str) -> datetime:
    days = PERIOD_DAYS.get(periodo, PERIOD_DAYS[PERIOD_TRIAL])
    return start + timedelta(days=days)


def normalize_api_product(product: str) -> str:
    return API_PRODUCT_ALIASES.get((product or "").strip().lower(), (product or "").strip().lower())


def product_includes_erp(produto: str) -> bool:
    return produto == PRODUCT_CLOUD


def product_includes_lab(produto: str) -> bool:
    return produto == PRODUCT_LAB


def product_includes_vde(produto: str) -> bool:
    return produto == PRODUCT_VDE


def product_matches_license(api_product: str, license_produto: str) -> bool:
    """Licença exclusiva por software — sem compartilhamento entre produtos."""
    normalized = normalize_api_product(api_product)
    legacy = license_produto.strip().lower()
    if legacy == "cloud_lab":
        return False
    return normalized == legacy


def days_until(target: datetime | None, ref: datetime) -> int:
    if not target:
        return 0
    return max(0, (target.date() - ref.date()).days)


def compute_license_validity(
    *,
    manual_status: str,
    ends_at: str | datetime | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    ref = now or now_utc()
    if manual_status in {STATUS_CANCELLED, STATUS_REVOKED}:
        return {
            "licenseStatus": manual_status,
            "licenseExpired": True,
            "daysRemaining": 0,
            "validForSoftware": False,
        }

    due = parse_ts(ends_at)
    if not due:
        return {
            "licenseStatus": STATUS_PENDING,
            "licenseExpired": False,
            "daysRemaining": 0,
            "validForSoftware": False,
        }

    remaining = days_until(due, ref)
    expired = ref > due
    return {
        "licenseStatus": STATUS_EXPIRED if expired else STATUS_ACTIVE,
        "licenseExpired": expired,
        "daysRemaining": 0 if expired else remaining,
        "validForSoftware": not expired,
    }


def compute_payment_phase(
    *,
    manual_status: str,
    payment_due_at: str | datetime | None,
    block_after_days: int,
    cancel_after_days: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    ref = now or now_utc()
    if manual_status in {STATUS_CANCELLED, STATUS_REVOKED}:
        return {
            "paymentPhase": manual_status,
            "paymentStatus": manual_status,
            "daysOverdue": 0,
            "block_at": None,
            "cancel_eligible_at": None,
            "message": "Cliente cancelado ou licença revogada.",
        }

    due = parse_ts(payment_due_at)
    if not due:
        return {
            "paymentPhase": STATUS_PENDING,
            "paymentStatus": STATUS_PENDING,
            "daysOverdue": 0,
            "block_at": None,
            "cancel_eligible_at": None,
            "message": "Aguardando definição de pagamento.",
        }

    block_at = due + timedelta(days=block_after_days)
    cancel_at = due + timedelta(days=cancel_after_days)
    days_overdue = max(0, (ref - due).days)

    if ref <= due:
        return {
            "paymentPhase": STATUS_ACTIVE,
            "paymentStatus": STATUS_ACTIVE,
            "daysOverdue": 0,
            "block_at": block_at.isoformat(),
            "cancel_eligible_at": cancel_at.isoformat(),
            "message": "Pagamento em dia.",
        }

    if ref <= block_at:
        grace_left = block_after_days - days_overdue
        return {
            "paymentPhase": STATUS_GRACE,
            "paymentStatus": STATUS_GRACE,
            "daysOverdue": days_overdue,
            "block_at": block_at.isoformat(),
            "cancel_eligible_at": cancel_at.isoformat(),
            "message": (
                f"Pagamento vencido há {days_overdue} dia(s). "
                f"Carência comercial: {grace_left} dia(s) restante(s)."
            ),
        }

    if ref <= cancel_at:
        return {
            "paymentPhase": STATUS_BLOCKED,
            "paymentStatus": STATUS_BLOCKED,
            "daysOverdue": days_overdue,
            "block_at": block_at.isoformat(),
            "cancel_eligible_at": cancel_at.isoformat(),
            "message": (
                f"Bloqueio comercial por inadimplência ({days_overdue} dias após vencimento do pagamento)."
            ),
        }

    return {
        "paymentPhase": "cancel_eligible",
        "paymentStatus": STATUS_BLOCKED,
        "daysOverdue": days_overdue,
        "block_at": block_at.isoformat(),
        "cancel_eligible_at": cancel_at.isoformat(),
        "message": (
            f"Elegível para cancelamento comercial ({days_overdue} dias). "
            f"Limite: {cancel_after_days} dias após vencimento do pagamento."
        ),
    }


def compute_alert_level(
    *,
    license_expired: bool,
    days_remaining: int,
    payment_phase: str,
) -> str:
    if license_expired:
        return "expired"
    if payment_phase in {STATUS_BLOCKED, "cancel_eligible"}:
        return "critical"
    if payment_phase == STATUS_GRACE:
        return "warning"
    if days_remaining in ALERT_MILESTONES:
        return "warning"
    if days_remaining <= 3:
        return "critical"
    return "none"


def compute_effective_status(
    *,
    manual_status: str,
    ends_at: str | datetime | None,
    payment_due_at: str | datetime | None = None,
    block_after_days: int = 30,
    cancel_after_days: int = 45,
    now: datetime | None = None,
) -> dict[str, Any]:
    ref = now or now_utc()
    validity = compute_license_validity(manual_status=manual_status, ends_at=ends_at, now=ref)
    payment = compute_payment_phase(
        manual_status=manual_status,
        payment_due_at=payment_due_at or ends_at,
        block_after_days=block_after_days,
        cancel_after_days=cancel_after_days,
        now=ref,
    )

    valid_for_software = validity["validForSoftware"] and manual_status not in {
        STATUS_REVOKED,
        STATUS_CANCELLED,
    }
    if payment["paymentPhase"] in {STATUS_BLOCKED, "cancel_eligible"}:
        valid_for_software = False

    alert_level = compute_alert_level(
        license_expired=validity["licenseExpired"],
        days_remaining=validity["daysRemaining"],
        payment_phase=payment["paymentPhase"],
    )

    status = payment["paymentPhase"]
    if validity["licenseExpired"]:
        status = STATUS_EXPIRED

    return {
        **validity,
        **payment,
        "status": status,
        "phase": status,
        "daysRemaining": validity["daysRemaining"],
        "daysOverdue": payment["daysOverdue"],
        "validForSoftware": valid_for_software,
        "alertLevel": alert_level,
        "licenseExpired": validity["licenseExpired"],
        "paymentPhase": payment["paymentPhase"],
    }


def sync_status_for_product_db(effective: dict[str, Any]) -> str:
    phase = effective.get("phase") or effective.get("status")
    if phase in {STATUS_CANCELLED, STATUS_REVOKED}:
        return STATUS_REVOKED
    if effective.get("licenseExpired"):
        return STATUS_BLOCKED
    if phase in {STATUS_BLOCKED, "cancel_eligible"}:
        return STATUS_BLOCKED
    if phase == STATUS_GRACE:
        return STATUS_ACTIVE
    if phase == STATUS_ACTIVE and effective.get("validForSoftware"):
        return STATUS_ACTIVE
    return STATUS_PENDING


def format_remaining_counter(days: int) -> str:
    if days <= 0:
        return "Vencido"
    years, rem = divmod(days, 365)
    months, d = divmod(rem, 30)
    parts = []
    if years:
        parts.append(f"{years} ano{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} mês{'es' if months > 1 else ''}")
    if d or not parts:
        parts.append(f"{d} dia{'s' if d != 1 else ''}")
    return ", ".join(parts)
