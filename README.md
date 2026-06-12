# Gerenciador de Licenças — InovatiTech

Servidor central de licenciamento para **Excellence Dental Cloud**, **Dental Lab** e **VDE Incorporadora**.

## Funcionalidades

- API REST `/api/v1/licenses/*` (validate, activate, status, heartbeat, revoke)
- Painel admin com cadastro completo (CPF/CNPJ, ViaCEP, matriz/filial)
- Chaves alfanuméricas de 25 caracteres
- Períodos: teste (30d), 1y, 2y, **3y**, 4y, 5y
- Alertas automáticos (20, 15, 7, 3, 2, 1 dias)
- Stripe Checkout (cartão, PIX, boleto)
- Postgres dedicado em produção
- Landing pública responsiva

## Instalação rápida (Next.js — recomendado)

```powershell
cd "Gerador de Licenças\apps\web"
Copy-Item .env.example .env
# Edite DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD, PRODUCT_API_KEY
npm install
npm run dev
```

- Landing: http://127.0.0.1:3000
- Painel: http://127.0.0.1:3000/login
- API: http://127.0.0.1:3000/api/v1/licenses/*
- Testes TDD: `npm test`

## Docker + Postgres

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env
docker compose up -d license-db license-web --build
curl http://127.0.0.1:3000/api/health
```

FastAPI legado (opcional): `docker compose --profile legacy up -d license-server`

## Instalação FastAPI legado

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\run.ps1
```

## Produção

- URL: https://licencas.inovatitech.com.br
- Ver `docs/PREMISSAS.md`, `infra/nginx/`, `infra/ops/deploy-vps.sh`
- Cloudflare: SSL Full (strict)

## Testes

```bash
pytest tests/ -v
```

## Banco: backup e migracao segura

```bash
bash scripts/db_backup.sh
bash scripts/db_migrate_safe.sh
```

No PowerShell:

```powershell
.\scripts\db_backup.ps1
.\scripts\db_migrate_safe.ps1
```

## GitHub

Repositório alvo: `kadu207/Gerenciador-de-Licencas`

```bash
git remote add origin git@github.com:kadu207/Gerenciador-de-Licencas.git
git branch -M main
git push -u origin main
```

## Documentação

- `docs/API-PRODUTOS.md` — contrato da API
- `docs/INTEGRACAO-STRIPE.md` — pagamentos
- `docs/INTEGRACAO-NFSE-PREFEITURA.md` — NFS-e (aguardando credenciais)
- `docs/integracao-*.md` — guias por software

## Segurança

- Troque `SECRET_KEY`, `ADMIN_PASSWORD`, `PRODUCT_API_KEY` no `.env`
- `.env` está no `.gitignore` — nunca commitar secrets
- Use Restricted API Key (`rk_`) no Stripe
