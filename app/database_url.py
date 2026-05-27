"""Resolve a URL do banco — Postgres via POSTGRES_* quando LOCAL_DATABASE_URL não está definida."""
from __future__ import annotations

import os
from urllib.parse import quote_plus


def _build_postgres_url() -> str | None:
    password = os.environ.get("POSTGRES_APP_PASSWORD", "").strip()
    if not password:
        return None
    user = os.environ.get("POSTGRES_USER", "licencas")
    host = os.environ.get("POSTGRES_HOST", "license-db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "licencas_db")
    return f"postgresql+psycopg://{user}:{quote_plus(password)}@{host}:{port}/{db}"


def resolve_database_url(configured: str = "") -> str:
    """Prioridade: LOCAL_DATABASE_URL (Postgres) → configured (Postgres) → POSTGRES_* → sqlite."""
    env_url = os.environ.get("LOCAL_DATABASE_URL", "").strip()
    cfg = (configured or "").strip()

    if env_url.startswith("postgresql"):
        return env_url
    if cfg.startswith("postgresql"):
        return cfg

    built = _build_postgres_url()
    if built:
        return built

    if env_url:
        return env_url
    if cfg:
        return cfg
    return "sqlite:///./data/gerador_licencas.db"
