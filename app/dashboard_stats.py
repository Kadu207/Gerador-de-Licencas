"""Agregação de estatísticas para o dashboard administrativo."""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.catalog import product_labels_dict
from app.licensing import PAYMENT_PLAN_LABELS
from app.models import Client, LicenseRecord, Notification, Payment, SoftwareProduct
from app.services import effective_for_license


def _money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_dashboard_stats(db: Session) -> dict:
    labels = product_labels_dict(db)
    catalog_products = (
        db.query(SoftwareProduct)
        .filter(SoftwareProduct.license_enabled.is_(True))
        .order_by(SoftwareProduct.sort_order)
        .all()
    )
    product_keys = [p.slug for p in catalog_products] or list(labels.keys())
    clients = db.query(Client).all()
    licenses = db.query(LicenseRecord).all()
    payments = db.query(Payment).all()
    notifications = (
        db.query(Notification)
        .filter(Notification.read.is_(False))
        .order_by(Notification.id.desc())
        .limit(15)
        .all()
    )

    status_counts: Counter[str] = Counter()
    product_counts: Counter[str] = Counter()
    delinquency_by_product: Counter[str] = Counter()
    delinquent_rows: list[dict] = []

    active = grace = blocked = expired = revoked = valid = 0

    for lic in licenses:
        eff = effective_for_license(lic)
        phase = eff.get("phase") or eff.get("status") or "unknown"
        status_counts[phase] += 1
        product_counts[lic.produto] += 1

        if lic.manual_status == "revoked":
            revoked += 1
        elif eff.get("licenseExpired"):
            expired += 1
        elif phase == "grace":
            grace += 1
        elif phase in {"blocked", "cancel_eligible"}:
            blocked += 1
        elif eff.get("validForSoftware"):
            active += 1
            valid += 1

        if phase in {"grace", "blocked", "cancel_eligible"}:
            delinquency_by_product[lic.produto] += 1
            client = db.query(Client).filter(Client.id == lic.client_id).first()
            delinquent_rows.append(
                {
                    "client_name": client.nome if client else "—",
                    "client_id": lic.client_id,
                    "product": lic.produto,
                    "product_label": labels.get(lic.produto, lic.produto),
                    "phase": phase,
                    "days_overdue": eff.get("daysOverdue", 0),
                    "license_key": lic.license_key,
                }
            )

    delinquent_rows.sort(key=lambda r: r["days_overdue"], reverse=True)

    completed = [p for p in payments if p.status == "completed"]
    pending = [p for p in payments if p.status == "pending"]
    failed = [p for p in payments if p.status not in {"completed", "pending"}]

    total_revenue = sum(_money(p.amount) for p in completed)
    revenue_by_plan: Counter[str] = Counter()
    payments_by_month: dict[str, float] = defaultdict(float)
    payment_method_counts: Counter[str] = Counter()

    for p in completed:
        plan = p.payment_plan or "annual"
        revenue_by_plan[plan] += _money(p.amount)
        if p.completed_at:
            key = p.completed_at.strftime("%Y-%m")
            payments_by_month[key] += _money(p.amount)
        if p.payment_method:
            payment_method_counts[p.payment_method] += 1

    month_labels = sorted(payments_by_month.keys())[-12:]
    month_values = [round(payments_by_month[m], 2) for m in month_labels]

    recent_payments = sorted(
        payments,
        key=lambda p: p.created_at or p.completed_at,
        reverse=True,
    )[:15]

    recent_license_rows = []
    for lic in sorted(licenses, key=lambda x: x.id, reverse=True)[:20]:
        client = db.query(Client).filter(Client.id == lic.client_id).first()
        eff = effective_for_license(lic)
        recent_license_rows.append(
            {
                "license": lic,
                "client": client,
                "effective": eff,
            }
        )

    product_labels = [labels.get(k, k) for k in product_keys]
    product_values = [product_counts.get(k, 0) for k in product_keys]

    delinq_labels = [labels.get(k, k) for k in product_keys]
    delinq_values = [delinquency_by_product.get(k, 0) for k in product_keys]

    status_order = ["active", "grace", "blocked", "cancel_eligible", "expired", "revoked", "cancelled", "pending"]
    status_labels = []
    status_values = []
    status_colors = {
        "active": "#107c10",
        "grace": "#ca5010",
        "blocked": "#a4262c",
        "cancel_eligible": "#8a8886",
        "expired": "#605e5c",
        "revoked": "#323130",
        "cancelled": "#c8c6c4",
        "pending": "#0078d4",
    }
    chart_status_colors = []
    for key in status_order:
        count = status_counts.get(key, 0)
        if count:
            status_labels.append(key.replace("_", " ").title())
            status_values.append(count)
            chart_status_colors.append(status_colors.get(key, "#0078d4"))

    plan_labels = [PAYMENT_PLAN_LABELS.get(k, k) for k in PAYMENT_PLAN_LABELS]
    plan_values = [round(revenue_by_plan.get(k, 0), 2) for k in PAYMENT_PLAN_LABELS]

    branches = sum(1 for c in clients if c.parent_client_id)
    matrices = sum(1 for c in clients if not c.parent_client_id)

    return {
        "kpis": {
            "clients_total": len(clients),
            "clients_matrices": matrices,
            "clients_branches": branches,
            "licenses_total": len(licenses),
            "licenses_active": active,
            "licenses_valid": valid,
            "licenses_grace": grace,
            "licenses_blocked": blocked,
            "licenses_expired": expired,
            "licenses_revoked": revoked,
            "payments_completed": len(completed),
            "payments_pending": len(pending),
            "payments_failed": len(failed),
            "revenue_total": round(total_revenue, 2),
            "delinquency_total": grace + blocked,
            "notifications_unread": len(notifications),
        },
        "charts": {
            "licenses_by_product": {
                "labels": product_labels,
                "values": product_values,
            },
            "status_distribution": {
                "labels": status_labels,
                "values": status_values,
                "colors": chart_status_colors,
            },
            "revenue_by_month": {
                "labels": month_labels or ["Sem dados"],
                "values": month_values or [0],
            },
            "delinquency_by_product": {
                "labels": delinq_labels,
                "values": delinq_values,
            },
            "revenue_by_plan": {
                "labels": plan_labels,
                "values": plan_values,
            },
        },
        "delinquent_rows": delinquent_rows[:20],
        "recent_payments": recent_payments,
        "recent_licenses": recent_license_rows,
        "notifications": notifications,
        "block_days": settings.block_after_days,
        "cancel_days": settings.cancel_after_days,
    }
