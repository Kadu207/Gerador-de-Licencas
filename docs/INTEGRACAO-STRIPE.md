# Integração Stripe — Gerenciador de Licenças

## Configuração

```env
STRIPE_SECRET_KEY=rk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
PUBLIC_BASE_URL=https://licencas.inovatitech.com.br
```

## Métodos de pagamento

Configure PIX, boleto e cartão no **Stripe Dashboard Brasil** via Payment Method Configurations.
**Não** fixe `payment_method_types` no código.

## Planos

| Plano | Código | Valor referência |
|-------|--------|------------------|
| Mensal | monthly | R$ 299 |
| Semestral | semiannual | R$ 1.599 |
| Anual | annual | R$ 2.999 |

## Webhook

Endpoint: `POST /webhooks/stripe`

Eventos: `checkout.session.completed`

## Fluxo

1. Operador clica "Link Stripe" no painel
2. Cliente paga via Checkout
3. Webhook confirma → `payment_status=active`, estende `payment_due_at`

## Teste local

```bash
stripe listen --forward-to localhost:8195/webhooks/stripe
```
