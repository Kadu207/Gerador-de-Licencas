#!/bin/sh
set -e

# Monta URL do Postgres com senha URL-encoded (evita travar quando .env aponta 127.0.0.1)
if [ -n "${POSTGRES_APP_PASSWORD:-}" ]; then
  export LOCAL_DATABASE_URL="$(python -c "
import os
from urllib.parse import quote_plus
user = os.environ.get('POSTGRES_USER', 'licencas')
pwd = os.environ['POSTGRES_APP_PASSWORD']
host = os.environ.get('POSTGRES_HOST', 'license-db')
port = os.environ.get('POSTGRES_PORT', '5432')
db = os.environ.get('POSTGRES_DB', 'licencas_db')
print(f'postgresql+psycopg://{user}:{quote_plus(pwd)}@{host}:{port}/{db}')
")"
fi

if echo "$LOCAL_DATABASE_URL" | grep -q postgresql; then
  echo "[entrypoint] Aguardando Postgres ($POSTGRES_HOST)..."
  n=0
  until python -c "
import os, sys
from sqlalchemy import create_engine, text
url = os.environ.get('LOCAL_DATABASE_URL', '')
try:
    e = create_engine(url)
    with e.connect() as c:
        c.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as ex:
    print(ex, file=sys.stderr)
    sys.exit(1)
"; do
    n=$((n + 1))
    if [ "$n" -ge 30 ]; then
      echo "[entrypoint] ERRO: Postgres indisponível após 60s. Verifique POSTGRES_APP_PASSWORD."
      exit 1
    fi
    sleep 2
  done
  echo "[entrypoint] Postgres disponível."
  alembic upgrade head 2>/dev/null || python -c "from app.models import init_db; init_db()"
else
  python -c "from app.models import init_db; init_db()"
fi

PROXY_ARGS=""
case "$(echo "${TRUST_PROXY:-false}" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes) PROXY_ARGS="--proxy-headers --forwarded-allow-ips=*" ;;
esac

# shellcheck disable=SC2086
exec uvicorn app.main:app \
  --host "${LICENSE_SERVER_HOST:-0.0.0.0}" \
  --port "${LICENSE_SERVER_PORT:-8195}" \
  $PROXY_ARGS
