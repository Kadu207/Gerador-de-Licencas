"""Envio de e-mails para alertas de licença."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("license-email")


def send_email(*, to: str, subject: str, html_body: str, text_body: str = "", cc: str = "") -> bool:
    if not settings.smtp_host or not to:
        logger.info("SMTP não configurado — email simulado para %s: %s", to, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    if cc:
        msg["Cc"] = cc

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    recipients = [to]
    if cc:
        recipients.append(cc)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, recipients, msg.as_string())
        return True
    except Exception:
        logger.exception("Falha ao enviar email para %s", to)
        return False


def alert_email_html(client_name: str, license_key: str, days: int, ends_at: str) -> str:
    return f"""
    <html><body style="font-family:sans-serif">
    <h2>Alerta de vencimento — InovatiTech</h2>
    <p>Olá, <strong>{client_name}</strong>,</p>
    <p>Sua licença <code>{license_key[:8]}…</code> vence em <strong>{days} dia(s)</strong>
    ({ends_at}).</p>
    <p>Renove pelo painel comercial ou entre em contato com o suporte.</p>
    </body></html>
    """
