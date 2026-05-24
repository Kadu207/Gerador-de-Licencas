#!/bin/bash
# Cria usuario app licencas e database (primeira inicializacao do volume).
set -e

APP_PW="$POSTGRES_APP_PASSWORD"
# Escapa aspas simples para SQL
APP_PW_SQL="${APP_PW//\'/\'\'}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'licencas') THEN
            EXECUTE format('CREATE ROLE licencas LOGIN PASSWORD %L', '${APP_PW_SQL}');
        ELSE
            EXECUTE format('ALTER ROLE licencas PASSWORD %L', '${APP_PW_SQL}');
        END IF;
    END
    \$\$;

    SELECT format('CREATE DATABASE %I OWNER licencas', 'licencas_db')
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'licencas_db')\\gexec

    GRANT ALL PRIVILEGES ON DATABASE licencas_db TO licencas;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "licencas_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO licencas;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO licencas;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO licencas;
EOSQL

echo "[init] licencas_db pronto."
