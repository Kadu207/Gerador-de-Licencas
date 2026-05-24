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

## Instalação rápida

```powershell
cd "Gerador de Licenças"
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\run.ps1
```

Acesse http://127.0.0.1:8195 — landing pública; painel em `/app/login`.

## Docker + Postgres

```bash
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:8195/health
```

## Produção

- URL: https://licencas.inovatitech.com.br
- Ver `docs/PREMISSAS.md`, `infra/nginx/`, `infra/ops/deploy-vps.sh`
- Cloudflare: SSL Full (strict)

## Testes

```bash
pytest tests/ -v
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
