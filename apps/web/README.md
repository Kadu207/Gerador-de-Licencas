# Gerenciador de Licenças — Next.js

Stack principal do projeto (App Router + Prisma + Postgres dedicado).

## Desenvolvimento

```bash
cp .env.example .env
npm install
npm run dev
```

## Testes (TDD)

```bash
npm test
```

## Build produção

```bash
npm run build
npm start
```

## Rotas principais

| Rota | Descrição |
|------|-----------|
| `/` | Landing responsiva (dvh) |
| `/login` | Painel admin |
| `/dashboard` | KPIs e alertas |
| `/clients` | Cadastro completo |
| `/finance` | Gerenciador financeiro |
| `/catalog` | Catálogo de produtos SaaS |
| `/api/v1/licenses/*` | API para Cloud, Lab, VDE |

## Docker

Build a partir da raiz do monorepo:

```bash
docker compose up -d license-db license-web --build
```
