#!/usr/bin/env bash
set -euo pipefail

# Backup seguro do banco do Gerador de Licencas (local ou VPS).
# Uso:
#   bash scripts/db_backup.sh
#   DB_CONTAINER=licencas-db DB_USER=licencas DB_NAME=licencas_db bash scripts/db_backup.sh

DB_CONTAINER="${DB_CONTAINER:-licencas-db}"
DB_USER="${DB_USER:-licencas}"
DB_NAME="${DB_NAME:-licencas_db}"
OUTPUT_DIR="${OUTPUT_DIR:-./data/backups}"

mkdir -p "$OUTPUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUTPUT_DIR/licencas-db-$STAMP.sql.gz"

echo "Gerando backup em: $OUT_FILE"
docker exec -i "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT_FILE"
echo "Backup concluido."
