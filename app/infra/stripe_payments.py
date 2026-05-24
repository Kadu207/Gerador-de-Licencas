"""Integração Stripe Checkout — cartão, PIX e boleto via Dashboard Brasil."""
from __future__ import annotations

import logging
from decimal import Decimal

from app.config import settings
from app.licensing import PAYMENT_PLAN_ANNUAL, PAYMENT_PLAN_MONTHLY, PAYMENT_PLAN_SEMIANNUAL

logger = logging.getLogger("license-stripe")

PLAN_AMOUNTS: dict[str, Decimal] = {
    PAYMENT_PLAN_MONTHLY: Decimal("299.00"),
    PAYMENT_PLAN_SEMIANNUAL: Decimal("1599.00"),
    PAYMENT_PLAN_ANNUAL: Decimal("2999.00"),
}


def stripe_enabled() -> bool:
    return bool((settings.stripe_secret_key or "").strip())


def _get_stripe():
    if not stripe_enabled():
        raise RuntimeError("STRIPE_NOT_CONFIGURED")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def create_checkout_session(
    *,
    client_id: int,
    license_id: int,
    payment_plan: str,
    customer_email: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    stripe = _get_stripe()
    amount = PLAN_AMOUNTS.get(payment_plan, PLAN_AMOUNTS[PAYMENT_PLAN_ANNUAL])
    amount_cents = int(amount * 100)

    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=customer_email or None,
        line_items=[
            {
                "price_data": {
                    "currency": settings.stripe_currency,
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Licença InovatiTech — plano {payment_plan}",
                    },
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "client_id": str(client_id),
            "license_id": str(license_id),
            "payment_plan": payment_plan,
        },
    )
    return {"session_id": session.id, "url": session.url}


def construct_webhook_event(payload: bytes, sig_header: str):
    stripe = _get_stripe()
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
