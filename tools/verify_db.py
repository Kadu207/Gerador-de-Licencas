"""Verifica conexão Postgres e lista tabelas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, inspect, text

from app.config import settings

e = create_engine(settings.local_database_url)
with e.connect() as c:
    tables = inspect(e).get_table_names()
    print("Tabelas:", ", ".join(sorted(tables)))
    c.execute(text("SELECT 1"))
print("Conexão OK:", settings.local_database_url.split("@")[-1])
