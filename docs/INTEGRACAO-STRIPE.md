# Integração Stripe — Gerenciador de Licenças

## Configuração

```env
STRIPE_SECRET_KEY=rk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
PUBLIC_BASE_URL=https://licencas.inovatitech.com.br
STRIPE_CURRENCY=brl
```

### Passo 3 — tipo de chave no Dashboard Stripe

Escolha: **Alimentando uma integração que você criou**

O Gerador de Licenças é código próprio (FastAPI) que chama a API Stripe via `STRIPE_SECRET_KEY`.  
Não use “aplicativo de terceiros” nem “agente de IA” para esta chave de produção.

Prefira **Restricted key** (`rk_test_` / `rk_live_`) com permissão **Checkout Sessions → Write**.

## Métodos de pagamento

Configure PIX, boleto e cartão no **Stripe Dashboard Brasil** via Payment Method Configurations.  
**Não** fixe `payment_method_types` no código.

## Preços por sistema (Portfólio de sistemas)

Os valores são editados em **Admin → Portfólio de sistemas → Planos e custos**.  
O Checkout Stripe e a landing pública leem os mesmos preços do catálogo.

| Sistema | Mensal | Semestral | Anual |
|---------|--------|-----------|-------|
| **Dental Lab** | R$ 299,00 | R$ 1.599,00 | R$ 2.999,00 |
| **Excellence Dental Cloud** | R$ 497,00 | R$ 2.486,00 | R$ 4.970,00 |

Periodicidade no catálogo: `monthly`, `semiannual`, `annual` (vinculadas aos planos de pagamento da licença).

## Webhook

Endpoint: `POST https://licencas.inovatitech.com.br/webhooks/stripe`

Evento: `checkout.session.completed`

## Fluxo

1. Operador clica **Link Stripe** no detalhe do cliente (valor conforme sistema + plano)
2. Cliente paga via Checkout
3. Webhook confirma → pagamento `completed`, `payment_status=active`

## Teste local

```bash
stripe listen --forward-to localhost:8195/webhooks/stripe
```

## Deploy — aplicar preços no banco

```bash
docker compose exec license-server python docker/ensure_migrations.py
```

A migration `003_commercial_plan_prices` atualiza Cloud e Lab na VPS existente.
