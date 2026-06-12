#!/usr/bin/env bash
set -euo pipefail

# Migração segura de banco com backup prévio.
# Uso:
#   bash scripts/db_migrate_safe.sh

echo "1) Backup pre-migracao"
bash scripts/db_backup.sh

echo "2) Aplicando migracoes via helper do projeto"
docker compose exec license-server python docker/ensure_migrations.py

echo "3) Verificando saude da aplicacao"
curl -fsS "http://127.0.0.1:8195/health" >/dev/null
echo "Migracao concluida com sucesso."
