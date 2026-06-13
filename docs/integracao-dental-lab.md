# Integração — Dental Lab

## Configuração

```env
LICENSE_SERVER_URL=https://licencas.inovatitech.com.br
LICENSE_API_KEY=sua-chave-produto
```

## Escopo de `clinica_id`

- **Lab:** `clinica_id` corresponde ao ID do laboratório (`clinica_id_lab` no gerenciador).
- Na ativação, o gerenciador grava `clinica_id_lab` se ainda vazio.

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

- [x] Migrar de `product_licenses` local para API central (híbrido: remoto + cache local)
- [x] Cache 5 min opcional
- [x] Heartbeat 6h + retry com backoff
- [ ] Fallback offline apenas leitura (opcional)
