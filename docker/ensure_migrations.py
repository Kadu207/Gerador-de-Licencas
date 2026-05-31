#!/usr/bin/env python3
"""Aplica migrations Alembic; faz stamp 001 em bancos criados antes do Alembic."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.database_url import resolve_database_url


def _detect_revision(insp) -> str | None:
    """Infere revisão Alembic quando alembic_version não existe."""
    if insp.has_table("software_products"):
        return "002_software_catalog"
    if insp.has_table("operators"):
        return "001_initial"
    return None


def main() -> int:
    url = resolve_database_url()
    os.environ["LOCAL_DATABASE_URL"] = url
    engine = create_engine(url)
    insp = inspect(engine)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

    if not insp.has_table("alembic_version"):
        revision = _detect_revision(insp)
        if revision:
            print(f"[migrate] Banco existente sem alembic_version — stamp {revision}")
            command.stamp(cfg, revision)

    print(f"[migrate] upgrade head ({engine.dialect.name})")
    command.upgrade(cfg, "head")
    print("[migrate] OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[migrate] ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
