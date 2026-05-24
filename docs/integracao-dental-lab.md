# Integração — Dental Lab

## Configuração

```env
LICENSE_SERVER_URL=https://licencas.inovatitech.com.br
LICENSE_API_KEY=sua-chave-produto
```

## Endpoints usados

- `POST /validate` — product=`lab`
- `POST /activate` — vincula `clinica_id` e `installation_id`
- `GET /heartbeat` — bloqueio pós-vencimento

## Exemplo activate

```python
httpx.post(f"{BASE}/activate", json={
    "license_key": key,
    "clinica_id": clinica_id,
    "unidade_id": unidade_id,
    "product": "lab",
    "installation_id": machine_id,
}, headers=HEADERS)
```

## Checklist

- [ ] Migrar de `product_licenses` local para API central
- [ ] Cache 5 min opcional
- [ ] Fallback offline apenas leitura (opcional)
