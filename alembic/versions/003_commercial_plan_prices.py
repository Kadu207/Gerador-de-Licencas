"""Preços comerciais Cloud e Dental Lab — catálogo + Stripe."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "003_commercial_plan_prices"
down_revision = "002_software_catalog"
branch_labels = None
depends_on = None

COMMERCIAL_PLANS: dict[str, list[tuple]] = {
    "cloud": [
        ("monthly", "Plano Mensal", 497.00, "Por clínica / mês", 10),
        ("semiannual", "Plano Semestral", 2486.00, "Economia de 1 mês", 15),
        ("annual", "Plano Anual", 4970.00, "Economia de 2 meses", 20),
    ],
    "lab": [
        ("monthly", "Plano Mensal", 299.00, "Por laboratório / mês", 10),
        ("semiannual", "Plano Semestral", 1599.00, "Economia de 2 meses", 15),
        ("annual", "Plano Anual", 2999.00, "Economia de 2 meses", 20),
    ],
}


def _upsert_plans(connection, slug: str, plans: list[tuple]) -> None:
    row = connection.execute(
        sa.text("SELECT id FROM software_products WHERE slug = :slug"),
        {"slug": slug},
    ).fetchone()
    if not row:
        return
    product_id = row[0]
    for billing, name, price, description, sort_order in plans:
        existing = connection.execute(
            sa.text(
                "SELECT id FROM software_plans "
                "WHERE product_id = :pid AND billing_period = :billing"
            ),
            {"pid": product_id, "billing": billing},
        ).fetchone()
        if existing:
            connection.execute(
                sa.text(
                    "UPDATE software_plans SET name = :name, price = :price, "
                    "description = :description, sort_order = :sort_order, active = true "
                    "WHERE id = :id"
                ),
                {
                    "id": existing[0],
                    "name": name,
                    "price": price,
                    "description": description,
                    "sort_order": sort_order,
                },
            )
        else:
            connection.execute(
                sa.text(
                    "INSERT INTO software_plans "
                    "(product_id, name, billing_period, price, description, sort_order, active) "
                    "VALUES (:pid, :name, :billing, :price, :description, :sort_order, true)"
                ),
                {
                    "pid": product_id,
                    "name": name,
                    "billing": billing,
                    "price": price,
                    "description": description,
                    "sort_order": sort_order,
                },
            )


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("software_products") or not insp.has_table("software_plans"):
        return
    for slug, plans in COMMERCIAL_PLANS.items():
        _upsert_plans(bind, slug, plans)


def downgrade() -> None:
    pass
