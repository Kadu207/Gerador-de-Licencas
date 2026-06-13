-- Sincronização idempotente do schema (sem dados de seed).
ALTER TABLE operators ADD COLUMN IF NOT EXISTS role varchar(32) DEFAULT 'operator' NOT NULL;
