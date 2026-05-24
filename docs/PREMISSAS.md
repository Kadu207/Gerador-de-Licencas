# Premissas do Gerenciador de Licenças InovatiTech

Documento vivo de decisões arquiteturais e de negócio.

## Produtos suportados

| Slug | Nome |
|------|------|
| `cloud` | Excellence Dental Cloud |
| `lab` | Dental Lab |
| `vde` | VDE Incorporadora |

> **Licenças independentes:** cada software exige sua própria chave. Não há pacote compartilhado Cloud+Lab.

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
2. **Pagamento comercial (`payment_due_at` + 30 dias)** — fase `grace`/`blocked` com alertas de cobrança.

## API como fonte da verdade

- `SYNC_REMOTE_ENABLED=false` por padrão em produção.
- Produtos consultam `https://licencas.inovatitech.com.br/api/v1/licenses/*`.
- Sync push para ERP/Lab é legado opcional.

## Alertas

Marcos: 20, 15, 7, 3, 2, 1 dias antes de `ends_at` — e-mail + notificação in-app.

## Pagamentos

- Stripe Checkout (cartão, PIX, boleto via Dashboard Brasil).
- Planos: mensal, semestral, anual.
- Webhook `checkout.session.completed` estende `payment_due_at`.

## NFS-e

Integração direta com API da prefeitura (adapter stub até credenciais).

## Deploy

- VPS: `/opt/gerador-licencas`
- Postgres dedicado no Docker (`license-db`)
- Cloudflare: SSL Full (strict), proxy laranja
- GitHub: `kadu207/Gerenciador-de-Licenas`

## Segurança

- `.env` nunca commitado
- `PRODUCT_API_KEY` comparada com `hmac.compare_digest`
- JWT HttpOnly + secure + sameSite=lax
