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

- [ ] Implementar cliente HTTP com retry
- [ ] Respeitar `validForSoftware` / `licenseExpired`
- [ ] Exibir alertas conforme `alertLevel`
