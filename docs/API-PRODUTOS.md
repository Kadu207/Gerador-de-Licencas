# API para Produtos — Contrato v1

Base URL: `https://licencas.inovatitech.com.br/api/v1/licenses`

Autenticação: header `X-License-Api-Key`

## Endpoints

### POST /validate

Valida chave + produto + escopo (clínica/unidade).

```json
{
  "license_key": "ABCDEFGHIJKLMNOPQRSTUVWXY",
  "clinica_id": 1,
  "unidade_id": "opcional",
  "product": "lab|cloud|vde"
}
```

Resposta:

```json
{
  "valid": true,
  "daysRemaining": 25,
  "daysOverdue": 0,
  "licenseExpired": false,
  "paymentPhase": "active",
  "alertLevel": "none"
}
```

### POST /activate

Primeira ativação; grava `installation_id`.

### GET /status

Status por `license_key` ou `clinica_id` + `product`.

### GET /heartbeat

Poll leve: `{ "valid": bool, "blocked": bool, "daysRemaining": int }`

### POST /revoke

Revogação imediata (admin + API).

## SDK recomendado

- Retry com backoff (3 tentativas)
- Cache local 5 minutos (opcional)
- Header `X-License-Api-Key` em todas as requisições

## Códigos de erro

| HTTP | Código |
|------|--------|
| 401 | Chave API inválida |
| 404 | LICENSE_NOT_FOUND |
| 409 | LICENSE_SCOPE_MISMATCH |
| 422 | INVALID_LICENSE_KEY, LICENSE_PRODUCT_MISMATCH |
