ALTER TABLE operators ADD COLUMN IF NOT EXISTS role varchar(32) DEFAULT 'operator' NOT NULL;

INSERT INTO operators (username, password_hash, nome, role, ativo)
VALUES (
  'supervisor',
  '$2b$12$xakFeARCNtq9CgmnR5bpK.5rTCr8I2.JIhVkt5rEvo.dgswytbig6',
  'Supervisor Master',
  'master',
  true
)
ON CONFLICT (username) DO UPDATE SET
  password_hash = EXCLUDED.password_hash,
  nome = EXCLUDED.nome,
  role = EXCLUDED.role,
  ativo = true;

INSERT INTO operators (username, password_hash, nome, role, ativo)
VALUES (
  'licencasadmin',
  '$2b$12$eJTt47YaeTkNMWihkdmVIO1piVXwFTxnl4Ak138SvSjlbtogFZs2i',
  'Admin Master Licencas',
  'master',
  true
)
ON CONFLICT (username) DO UPDATE SET
  password_hash = EXCLUDED.password_hash,
  nome = EXCLUDED.nome,
  role = EXCLUDED.role,
  ativo = true;
