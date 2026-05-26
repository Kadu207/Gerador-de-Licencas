# Integração — VDE Incorporadora

## Configuração

```env
LICENSE_SERVER_URL=https://licencas.inovatitech.com.br
LICENSE_API_KEY=sua-chave-produto
```

## Produto

Use `product=vde` em todas as chamadas.

## Endpoints

- `POST /validate`
- `POST /activate`
- `GET /status?clinica_id=N&product=vde`
- `GET /heartbeat`
- `POST /revoke`

## Checklist

- [x] Implementar cliente HTTP com retry (`VDE Incorporadora/backend/licensing/license_client.py`)
- [x] Respeitar `validForSoftware` / `licenseExpired`
- [x] Exibir alertas conforme `alertLevel`
- [x] Copiar módulo para repositório VDE — `backend/licensing/` em https://github.com/Kadu207/vde-incorporadora
