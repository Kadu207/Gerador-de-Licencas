# Integração Stripe — Gerenciador de Licenças (Next.js v2)

## Configuração na VPS (`/opt/gerador-licencas/.env`)

```env
STRIPE_SECRET_KEY=rk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
PUBLIC_BASE_URL=https://licencas.inovatitech.com.br
```

Após editar o `.env` raiz:

```bash
bash infra/ops/provision-web-env.sh
docker compose up -d license-web --build
bash infra/ops/stripe-prod-check.sh
```

### Tipo de chave no Dashboard Stripe

Escolha: **Alimentando uma integração que você criou**

Prefira **Restricted key** (`rk_live_`) com permissão **Checkout Sessions → Write**.

## Métodos de pagamento

Configure PIX, boleto e cartão no **Stripe Dashboard Brasil** via Payment Method Configurations.  
**Não** fixe `payment_method_types` no código.

## Preços

Edite em **Financeiro** no painel (master) ou na tabela `software_plans`.

| Sistema | Mensal | Semestral | Anual |
|---------|--------|-----------|-------|
| **Dental Lab** | R$ 299 | R$ 1.599 | R$ 2.999 |
| **Excellence Dental Cloud** | R$ 497 | R$ 2.486 | R$ 4.970 |

## Webhook (produção)

| Item | Valor |
|------|-------|
| URL | `POST https://licencas.inovatitech.com.br/api/stripe/webhook` |
| Evento | `checkout.session.completed` |

Ao confirmar pagamento o sistema:

1. Marca `payments.status = completed`
2. Renova a licença vinculada (`ends_at` + `payment_due_at` conforme plano mensal/semestral/anual)

## Fluxo operacional

1. Operador master gera licença no cliente
2. Clica **Link pagamento** (Stripe Checkout)
3. Cliente paga
4. Webhook confirma → licença estendida automaticamente

Pagamentos offline: **Financeiro → Marcar pago** (master).

## Teste local

```bash
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

## Go-live checklist

- [ ] `STRIPE_SECRET_KEY` e `STRIPE_WEBHOOK_SECRET` no `.env` da VPS
- [ ] Webhook Live apontando para `/api/stripe/webhook`
- [ ] PIX/boleto habilitados no Dashboard Brasil
- [ ] `bash infra/ops/stripe-prod-check.sh` sem falhas
- [ ] Teste real com valor baixo em produção
