#!/usr/bin/env bash
# Cria/atualiza operadores master no Postgres (VPS ou local com Docker).
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

echo "==> Schema operators.role + seed SQL"
docker exec -i licencas-db psql -U licencas -d licencas_db < "$APP_DIR/infra/ops/seed-operators.sql"
docker exec licencas-db psql -U licencas -d licencas_db -c "SELECT username, role, ativo FROM operators WHERE username IN ('supervisor','licencasadmin') ORDER BY username;"

echo "==> Operadores master aplicados"
