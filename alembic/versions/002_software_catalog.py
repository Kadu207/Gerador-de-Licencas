"""software catalog + contracted_products on clients"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_software_catalog"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("contracted_products", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_table(
        "software_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(32), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("status", sa.String(24), server_default="active"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("license_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_software_products_slug", "software_products", ["slug"], unique=True)

    op.create_table(
        "software_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("software_products.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("billing_period", sa.String(24), server_default="annual"),
        sa.Column("price", sa.Numeric(12, 2), server_default="0"),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_software_plans_product_id", "software_plans", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_software_plans_product_id", "software_plans")
    op.drop_table("software_plans")
    op.drop_index("ix_software_products_slug", "software_products")
    op.drop_table("software_products")
    op.drop_column("clients", "contracted_products")
