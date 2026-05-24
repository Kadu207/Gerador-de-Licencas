"""Sincronização de licenças com PostgreSQL do ERP e do Lab."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings
from app.licensing import (
    product_includes_erp,
    product_includes_lab,
    product_includes_vde,
    sync_status_for_product_db,
)

logger = logging.getLogger("license-sync")

_erp_engine: Engine | None = None
_lab_engine: Engine | None = None


def _normalize_pg_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def get_erp_engine() -> Engine | None:
    global _erp_engine
    if not settings.erp_database_url.strip():
        return None
    if _erp_engine is None:
        _erp_engine = create_engine(_normalize_pg_url(settings.erp_database_url), pool_pre_ping=True)
    return _erp_engine


def get_lab_engine() -> Engine | None:
    global _lab_engine
    url = settings.lab_database_url.strip() or settings.erp_database_url.strip()
    if not url:
        return None
    if _lab_engine is None:
        _lab_engine = create_engine(_normalize_pg_url(url), pool_pre_ping=True)
    return _lab_engine


def ensure_remote_tables() -> None:
    if not settings.sync_remote_enabled:
        return
    erp = get_erp_engine()
    if erp:
        with erp.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS product_licenses (
                        id SERIAL PRIMARY KEY,
                        license_key VARCHAR(25) NOT NULL UNIQUE,
                        clinica_id INTEGER,
                        produto VARCHAR(32) NOT NULL DEFAULT 'cloud',
                        periodo VARCHAR(16) NOT NULL DEFAULT 'trial',
                        cliente_nome TEXT DEFAULT '',
                        starts_at TEXT DEFAULT '',
                        ends_at TEXT DEFAULT '',
                        status VARCHAR(16) NOT NULL DEFAULT 'pending',
                        activated_at TEXT,
                        lab_secret TEXT,
                        created_at TEXT DEFAULT '',
                        created_by TEXT DEFAULT '',
                        notes TEXT DEFAULT ''
                    )
                    """
                )
            )

    lab = get_lab_engine()
    if lab:
        schema = settings.lab_schema
        try:
            with lab.begin() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {schema}.product_licenses (
                            id SERIAL PRIMARY KEY,
                            license_key VARCHAR(25) NOT NULL UNIQUE,
                            clinica_id INTEGER,
                            produto VARCHAR(32) NOT NULL DEFAULT 'lab',
                            periodo VARCHAR(16) NOT NULL DEFAULT 'trial',
                            cliente_nome TEXT DEFAULT '',
                            starts_at TEXT DEFAULT '',
                            ends_at TEXT DEFAULT '',
                            status VARCHAR(16) NOT NULL DEFAULT 'pending',
                            activated_at TEXT,
                            lab_secret TEXT,
                            created_at TEXT DEFAULT '',
                            created_by TEXT DEFAULT '',
                            notes TEXT DEFAULT ''
                        )
                        """
                    )
                )
        except Exception as exc:
            logger.warning("Lab schema/tabela nao preparados (sync Lab pode falhar): %s", exc)


def _upsert_license(conn, table: str, payload: dict[str, Any]) -> None:
    conn.execute(
        text(
            f"""
            INSERT INTO {table} (
                license_key, clinica_id, produto, periodo, cliente_nome,
                starts_at, ends_at, status, activated_at, lab_secret,
                created_at, created_by, notes
            ) VALUES (
                :license_key, :clinica_id, :produto, :periodo, :cliente_nome,
                :starts_at, :ends_at, :status, :activated_at, :lab_secret,
                :created_at, :created_by, :notes
            )
            ON CONFLICT (license_key) DO UPDATE SET
                clinica_id = EXCLUDED.clinica_id,
                produto = EXCLUDED.produto,
                periodo = EXCLUDED.periodo,
                cliente_nome = EXCLUDED.cliente_nome,
                starts_at = EXCLUDED.starts_at,
                ends_at = EXCLUDED.ends_at,
                status = EXCLUDED.status,
                activated_at = EXCLUDED.activated_at,
                lab_secret = EXCLUDED.lab_secret,
                notes = EXCLUDED.notes
            """
        ),
        payload,
    )


def sync_license_to_products(license_row: dict[str, Any], client_row: dict[str, Any], effective: dict[str, Any]) -> dict[str, str]:
    """Propaga licença para ERP (public) e Lab (schema dental_lab)."""
    if not settings.sync_remote_enabled:
        return {"erp": "skipped: sync remoto desligado", "lab": "skipped: sync remoto desligado"}
    ensure_remote_tables()
    produto = license_row["produto"]
    sync_status = sync_status_for_product_db(effective)
    clinica_erp = client_row.get("clinica_id_erp")
    clinica_lab = client_row.get("clinica_id_lab") or clinica_erp

    payload = {
        "license_key": license_row["license_key"],
        "clinica_id": clinica_erp,
        "produto": produto,
        "periodo": license_row["periodo"],
        "cliente_nome": client_row.get("nome") or "",
        "starts_at": license_row.get("starts_at") or "",
        "ends_at": license_row.get("ends_at") or "",
        "status": sync_status,
        "activated_at": license_row.get("starts_at") or "",
        "lab_secret": license_row.get("lab_secret"),
        "created_at": license_row.get("created_at") or "",
        "created_by": license_row.get("created_by") or "license-server",
        "notes": (license_row.get("notes") or "") + f" | phase={effective.get('phase')}",
    }

    results: dict[str, str] = {}

    if (product_includes_erp(produto) or product_includes_vde(produto)) and clinica_erp:
        erp = get_erp_engine()
        if erp:
            try:
                with erp.begin() as conn:
                    _upsert_license(conn, "product_licenses", payload)
                results["erp"] = "ok"
            except Exception as exc:
                logger.exception("ERP sync failed")
                results["erp"] = f"error: {exc}"
        else:
            results["erp"] = "skipped: ERP_DATABASE_URL não configurada"
    else:
        results["erp"] = "skipped"

    if product_includes_lab(produto):
        lab = get_lab_engine()
        if lab:
            lab_payload = {**payload, "clinica_id": clinica_lab, "produto": produto}
            try:
                with lab.begin() as conn:
                    _upsert_license(conn, f"{settings.lab_schema}.product_licenses", lab_payload)
                results["lab"] = "ok"
            except Exception as exc:
                logger.exception("Lab sync failed")
                results["lab"] = f"error: {exc}"
        else:
            results["lab"] = "skipped: LAB_DATABASE_URL não configurada"
    else:
        results["lab"] = "skipped"

    return results


def PRODUCT_LAB_ALIAS(produto: str) -> str:
    return "cloud_lab" if produto == "cloud_lab" else "lab"


def test_connections() -> dict[str, str]:
    out: dict[str, str] = {"local": "ok"}
    erp = get_erp_engine()
    if erp:
        try:
            with erp.connect() as conn:
                conn.execute(text("SELECT 1"))
            out["erp"] = "ok"
        except Exception as exc:
            out["erp"] = f"error: {exc}"
    else:
        out["erp"] = "not configured"

    lab = get_lab_engine()
    if lab:
        try:
            with lab.connect() as conn:
                conn.execute(text("SELECT 1"))
            out["lab"] = "ok"
        except Exception as exc:
            out["lab"] = f"error: {exc}"
    else:
        out["lab"] = "not configured"
    return out
