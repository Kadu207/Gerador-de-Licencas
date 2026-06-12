# Premissas do Gerenciador de Licenças InovatiTech

Documento vivo de decisões arquiteturais e de negócio. **Fonte de verdade do projeto** — consultar antes de implementar.

## Produtos suportados

| Slug | Nome |
|------|------|
| `cloud` | Excellence Dental Cloud |
| `lab` | Dental Lab |
| `vde` | VDE Incorporadora |

> **Licenças independentes:** cada software exige sua própria chave. Não há pacote compartilhado.

## Banco de dados (Postgres dedicado)

| Item | Valor |
|------|-------|
| Container | `licencas-db` |
| Imagem | `postgres:16-alpine` |
| Porta host | `127.0.0.1:5436` (5433 ocupada pelo Dental Lab local) |
| Database | `licencas_db` |
| Superusuário (VPS opcional) | `postgres` — senha em `POSTGRES_SUPER_PASSWORD` |
| Usuário app | `licencas` (owner de `licencas_db`) — senha em `POSTGRES_APP_PASSWORD` |
| URL app | `LOCAL_DATABASE_URL` no `.env` — senha com `$` usa `%24` na URL |
| Migrações | Alembic (`alembic upgrade head`) |
| Setup | `.\tools\setup-db.ps1` recria volume e aplica schema |

### Tabelas

`operators`, `clients`, `client_addresses`, `license_records`, `license_alert_log`, `notifications`, `payments`, `invoices_nfse`, `audit_logs`

> Senhas **nunca** commitadas — apenas em `.env` (gitignore).

## Períodos de licença

| Código | Dias |
|--------|------|
| trial | 30 |
| 1y | 365 |
| 2y | 730 |
| 3y | 1095 |
| 4y | 1460 |
| 5y | 1825 |

## Duas linhas do tempo (bloqueio)

1. **Validade técnica (`ends_at`)** — bloqueio nos softwares no dia seguinte ao vencimento.
2. **Pagamento comercial (`payment_due_at` + 30 dias)** — fase `grace`/`blocked`.

## Stack Next.js (v2 — painel + API)

| Item | Valor |
|------|-------|
| App | `apps/web` — Next.js 16 App Router |
| ORM | Prisma (mesmo Postgres `licencas_db`) |
| UI | Tailwind v4 + `dvh`/`svh` responsivo |
| Testes | Vitest (domínio) — `cd apps/web && npm test` |
| Governança | Spec Kit + SDD + TDD — ver `docs/TDD-SDD-WORKFLOW.md` |
| FastAPI legado | `app/` — referência até desativação completa |

## Gerenciador financeiro

- Catálogo `software_products` + planos comerciais (`software_plans`).
- Stripe Checkout (sem `payment_method_types` fixo — PIX/boleto/cartão via Dashboard Brasil).
- Página `/finance` — receita, pendentes, histórico.
- Webhook: `POST /api/stripe/webhook`.

## API como fonte da verdade

- `SYNC_REMOTE_ENABLED=false` por padrão.
- Base: `https://licencas.inovatitech.com.br/api/v1/licenses/*`

## GitHub

- Remoto: `git@github.com:kadu207/Gerador-de-Licencas.git`
- Push exige chave SSH cadastrada em https://github.com/settings/keys
- Alternativa HTTPS: `git remote set-url origin https://github.com/kadu207/Gerador-de-Licencas.git`

## Segurança

- `.env` nunca commitado
- `PRODUCT_API_KEY` com `hmac.compare_digest`
