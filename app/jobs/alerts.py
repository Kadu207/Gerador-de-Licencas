"""Job diário de alertas de vencimento (20, 15, 7, 3, 2, 1 dias)."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.infra.email import alert_email_html, send_email
from app.licensing import ALERT_MILESTONES, STATUS_ACTIVE, now_utc, parse_ts
from app.models import Client, LicenseAlertLog, LicenseRecord, Notification
from app.services import effective_for_license, license_to_dict

logger = logging.getLogger("license-alerts")


def run_license_alerts(db: Session) -> int:
    """Processa alertas e retorna quantidade enviada."""
    sent = 0
    ref = now_utc()
    licenses = (
        db.query(LicenseRecord)
        .filter(LicenseRecord.manual_status == STATUS_ACTIVE)
        .all()
    )

    for lic in licenses:
        effective = effective_for_license(lic)
        days = effective.get("daysRemaining", 0)
        if days not in ALERT_MILESTONES:
            continue

        existing = (
            db.query(LicenseAlertLog)
            .filter(
                LicenseAlertLog.license_id == lic.id,
                LicenseAlertLog.milestone_days == days,
            )
            .first()
        )
        if existing:
            continue

        client = db.query(Client).filter(Client.id == lic.client_id).first()
        if not client:
            continue

        ends_str = lic.ends_at.isoformat() if lic.ends_at else ""
        title = f"Licença vence em {days} dia(s) — {client.nome}"
        message = f"Chave {lic.license_key[:8]}… vence em {days} dia(s) ({ends_str})"

        db.add(
            Notification(
                title=title,
                message=message,
                level="warning" if days > 3 else "critical",
                license_id=lic.id,
                client_id=client.id,
            )
        )

        email_to = client.email or client.email_02
        if email_to:
            html = alert_email_html(client.nome, lic.license_key, days, ends_str)
            cc = client.email_02 if client.email and client.email_02 else ""
            if send_email(to=email_to, subject=title, html_body=html, cc=cc):
                db.add(
                    LicenseAlertLog(
                        license_id=lic.id,
                        milestone_days=days,
                        channel="email",
                    )
                )
                sent += 1
        else:
            db.add(
                LicenseAlertLog(
                    license_id=lic.id,
                    milestone_days=days,
                    channel="in_app",
                )
            )
            sent += 1

    db.commit()
    logger.info("Alertas processados: %d", sent)
    return sent
