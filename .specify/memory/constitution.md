# Constitution — Gerenciador de Licenças

## Princípios

1. **API como fonte da verdade** — produtos consultam o servidor central.
2. **Postgres dedicado** — banco `licencas_db` independente dos projetos ERP/Lab.
3. **Licenças independentes** — Cloud, Lab e VDE: uma chave por software, sem compartilhamento.
4. **Segurança first** — secrets só em `.env`; senhas Postgres em `POSTGRES_SUPER_PASSWORD` e `POSTGRES_APP_PASSWORD`.
5. **Schema via Alembic** — não alterar produção só com `create_all`.

## Postgres (memória operacional)

- Docker service: `license-db`, porta **5436** no host
- DB: `licencas_db`, user app: `licencas`
- Setup: `tools/setup-db.ps1`
- Documentação completa: `docs/PREMISSAS.md`

## Escopo

Este repo contém **apenas** o Gerenciador de Licenças InovatiTech.
