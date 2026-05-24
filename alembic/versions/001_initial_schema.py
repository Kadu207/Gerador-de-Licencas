"""Schema inicial — todas as tabelas do gerenciador de licenças."""

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "operators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(120), server_default=""),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_operators_username", "operators", ["username"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_client_id", sa.Integer(), nullable=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("razao_social", sa.String(200), server_default=""),
        sa.Column("document_type", sa.String(8), server_default="cnpj"),
        sa.Column("cnpj", sa.String(20), server_default=""),
        sa.Column("cpf", sa.String(14), server_default=""),
        sa.Column("email", sa.String(120), server_default=""),
        sa.Column("email_02", sa.String(120), server_default=""),
        sa.Column("telefone", sa.String(40), server_default=""),
        sa.Column("telefone_02", sa.String(40), server_default=""),
        sa.Column("telefone_03", sa.String(40), server_default=""),
        sa.Column("clinica_id_erp", sa.Integer(), nullable=True),
        sa.Column("clinica_id_lab", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parent_client_id"], ["clients.id"]),
    )
    op.create_index("ix_clients_nome", "clients", ["nome"])
    op.create_index("ix_clients_cnpj", "clients", ["cnpj"])
    op.create_index("ix_clients_parent_client_id", "clients", ["parent_client_id"])
    op.create_index("ix_clients_clinica_id_erp", "clients", ["clinica_id_erp"])
    op.create_index("ix_clients_clinica_id_lab", "clients", ["clinica_id_lab"])

    op.create_table(
        "client_addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("logradouro", sa.String(200), server_default=""),
        sa.Column("numero", sa.String(20), server_default=""),
        sa.Column("complemento", sa.String(100), server_default=""),
        sa.Column("bairro", sa.String(100), server_default=""),
        sa.Column("cidade", sa.String(100), server_default=""),
        sa.Column("uf", sa.String(2), server_default=""),
        sa.Column("cep", sa.String(10), server_default=""),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.UniqueConstraint("client_id"),
    )

    op.create_table(
        "license_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("license_key", sa.String(25), nullable=False),
        sa.Column("produto", sa.String(32), nullable=False),
        sa.Column("periodo", sa.String(16), nullable=False),
        sa.Column("payment_plan", sa.String(16), server_default="annual"),
        sa.Column("payment_status", sa.String(32), server_default="active"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_status", sa.String(32), server_default="active"),
        sa.Column("lab_secret", sa.String(128), nullable=True),
        sa.Column("erp_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lab_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unidade_id", sa.String(64), nullable=True),
        sa.Column("installation_id", sa.String(128), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(64), nullable=True),
        sa.Column("created_by", sa.String(64), server_default=""),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.UniqueConstraint("license_key"),
    )
    op.create_index("ix_license_records_client_id", "license_records", ["client_id"])
    op.create_index("ix_license_records_license_key", "license_records", ["license_key"])
    op.create_index("ix_license_records_unidade_id", "license_records", ["unidade_id"])

    op.create_table(
        "license_alert_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("license_id", sa.Integer(), nullable=False),
        sa.Column("milestone_days", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(16), server_default="email"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["license_id"], ["license_records.id"]),
        sa.UniqueConstraint("license_id", "milestone_days", name="uq_alert_milestone"),
    )
    op.create_index("ix_license_alert_log_license_id", "license_alert_log", ["license_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), server_default=""),
        sa.Column("level", sa.String(16), server_default="info"),
        sa.Column("license_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("read", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["license_id"], ["license_records.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("license_id", sa.Integer(), nullable=True),
        sa.Column("stripe_session_id", sa.String(128), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("currency", sa.String(8), server_default="brl"),
        sa.Column("payment_method", sa.String(32), server_default=""),
        sa.Column("payment_plan", sa.String(16), server_default="annual"),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["license_id"], ["license_records.id"]),
    )
    op.create_index("ix_payments_client_id", "payments", ["client_id"])
    op.create_index("ix_payments_license_id", "payments", ["license_id"])
    op.create_index("ix_payments_stripe_session_id", "payments", ["stripe_session_id"])

    op.create_table(
        "invoices_nfse",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("numero", sa.String(32), server_default=""),
        sa.Column("protocolo", sa.String(64), server_default=""),
        sa.Column("verification_url", sa.String(512), server_default=""),
        sa.Column("xml_content", sa.Text(), server_default=""),
        sa.Column("pdf_path", sa.String(512), server_default=""),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
    )
    op.create_index("ix_invoices_nfse_client_id", "invoices_nfse", ["client_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator", sa.String(64), server_default=""),
        sa.Column("action", sa.String(64), server_default=""),
        sa.Column("detail", sa.Text(), server_default=""),
        sa.Column("ip_address", sa.String(45), server_default=""),
        sa.Column("correlation_id", sa.String(64), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("invoices_nfse")
    op.drop_table("payments")
    op.drop_table("notifications")
    op.drop_table("license_alert_log")
    op.drop_table("license_records")
    op.drop_table("client_addresses")
    op.drop_table("clients")
    op.drop_table("operators")
