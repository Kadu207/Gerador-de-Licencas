#!/bin/sh
set -e

if echo "$LOCAL_DATABASE_URL" | grep -q postgresql; then
  echo "[entrypoint] Aguardando Postgres..."
  until python -c "
import os, sys
from sqlalchemy import create_engine, text
url = os.environ.get('LOCAL_DATABASE_URL', '')
try:
    e = create_engine(url)
    with e.connect() as c:
        c.execute(text('SELECT 1'))
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 2
  done
  echo "[entrypoint] Postgres disponível."
  alembic upgrade head 2>/dev/null || python -c "from app.models import init_db; init_db()"
else
  python -c "from app.models import init_db; init_db()"
fi

exec uvicorn app.main:app \
  --host "${LICENSE_SERVER_HOST:-0.0.0.0}" \
  --port "${LICENSE_SERVER_PORT:-8195}" \
  --proxy-headers
