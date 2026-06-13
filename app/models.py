from __future__ import annotations

import os

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class Operator(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nome = Column(String(120), default="")
    role = Column(String(32), default="operator")
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    parent_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    nome = Column(String(200), nullable=False, index=True)
    razao_social = Column(String(200), default="")
    document_type = Column(String(8), default="cnpj")
    cnpj = Column(String(20), default="", index=True)
    cpf = Column(String(14), default="")
    email = Column(String(120), default="")
    email_02 = Column(String(120), default="")
    telefone = Column(String(40), default="")
    telefone_02 = Column(String(40), default="")
    telefone_03 = Column(String(40), default="")
    clinica_id_erp = Column(Integer, nullable=True, index=True)
    clinica_id_lab = Column(Integer, nullable=True, index=True)
    contracted_products = Column(Text, default="[]")
    status = Column(String(32), default="active")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    parent = relationship("Client", remote_side=[id], backref="branches")
    address = relationship("ClientAddress", back_populates="client", uselist=False, cascade="all, delete-orphan")
    licenses = relationship("LicenseRecord", back_populates="client", cascade="all, delete-orphan")


class ClientAddress(Base):
    __tablename__ = "client_addresses"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), unique=True, nullable=False)
    logradouro = Column(String(200), default="")
    numero = Column(String(20), default="")
    complemento = Column(String(100), default="")
    bairro = Column(String(100), default="")
    cidade = Column(String(100), default="")
    uf = Column(String(2), default="")
    cep = Column(String(10), default="")

    client = relationship("Client", back_populates="address")


class LicenseRecord(Base):
    __tablename__ = "license_records"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    license_key = Column(String(25), unique=True, nullable=False, index=True)
    produto = Column(String(32), nullable=False)
    periodo = Column(String(16), nullable=False)
    payment_plan = Column(String(16), default="annual")
    payment_status = Column(String(32), default="active")
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    payment_due_at = Column(DateTime(timezone=True), nullable=True)
    manual_status = Column(String(32), default="active")
    lab_secret = Column(String(128), nullable=True)
    erp_synced_at = Column(DateTime(timezone=True), nullable=True)
    lab_synced_at = Column(DateTime(timezone=True), nullable=True)
    unidade_id = Column(String(64), nullable=True, index=True)
    installation_id = Column(String(128), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(64), nullable=True)
    created_by = Column(String(64), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="licenses")
    alert_logs = relationship("LicenseAlertLog", back_populates="license", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="license", cascade="all, delete-orphan")


class SoftwareProduct(Base):
    __tablename__ = "software_products"
    id = Column(Integer, primary_key=True)
    slug = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(160), nullable=False)
    description = Column(Text, default="")
    status = Column(String(24), default="active")
    sort_order = Column(Integer, default=0)
    license_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    plans = relationship(
        "SoftwarePlan",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="SoftwarePlan.sort_order",
    )


class SoftwarePlan(Base):
    __tablename__ = "software_plans"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("software_products.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    billing_period = Column(String(24), default="annual")
    price = Column(Numeric(12, 2), default=0)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("SoftwareProduct", back_populates="plans")


class LicenseAlertLog(Base):
    __tablename__ = "license_alert_log"
    __table_args__ = (UniqueConstraint("license_id", "milestone_days", name="uq_alert_milestone"),)
    id = Column(Integer, primary_key=True)
    license_id = Column(Integer, ForeignKey("license_records.id"), nullable=False, index=True)
    milestone_days = Column(Integer, nullable=False)
    channel = Column(String(16), default="email")
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    license = relationship("LicenseRecord", back_populates="alert_logs")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, default="")
    level = Column(String(16), default="info")
    license_id = Column(Integer, ForeignKey("license_records.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    license_id = Column(Integer, ForeignKey("license_records.id"), nullable=True, index=True)
    stripe_session_id = Column(String(128), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(128), nullable=True)
    amount = Column(Numeric(12, 2), default=0)
    currency = Column(String(8), default="brl")
    payment_method = Column(String(32), default="")
    payment_plan = Column(String(16), default="annual")
    status = Column(String(32), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    license = relationship("LicenseRecord", back_populates="payments")


class InvoiceNfse(Base):
    __tablename__ = "invoices_nfse"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    numero = Column(String(32), default="")
    protocolo = Column(String(64), default="")
    verification_url = Column(String(512), default="")
    xml_content = Column(Text, default="")
    pdf_path = Column(String(512), default="")
    status = Column(String(32), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    operator = Column(String(64), default="")
    action = Column(String(64), default="")
    detail = Column(Text, default="")
    ip_address = Column(String(45), default="")
    correlation_id = Column(String(64), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def _engine_kwargs() -> dict:
    url = settings.local_database_url
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


engine = create_engine(settings.local_database_url, **_engine_kwargs())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    if settings.local_database_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
        Base.metadata.create_all(bind=engine)
    # Postgres: schema via Alembic (alembic upgrade head)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
