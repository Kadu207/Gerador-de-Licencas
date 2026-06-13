# Integração — Excellence Dental Cloud

## Configuração

```env
LICENSE_SERVER_URL=https://licencas.inovatitech.com.br
LICENSE_API_KEY=sua-chave-produto
```

## Escopo de `clinica_id`

- **Cloud / VDE:** `clinica_id` corresponde ao ID da clínica no ERP (`clinica_id_erp` no gerenciador).
- Na ativação, o gerenciador grava `clinica_id_erp` se ainda vazio.

## Cliente HTTP (Python)

```python
import httpx

BASE = "https://licencas.inovatitech.com.br/api/v1/licenses"
HEADERS = {"X-License-Api-Key": LICENSE_API_KEY}

def validate(key: str, clinica_id: int) -> dict:
    r = httpx.post(f"{BASE}/validate", json={
        "license_key": key,
        "clinica_id": clinica_id,
        "product": "cloud",
    }, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()
```

## Heartbeat periódico

Poll `GET /heartbeat?license_key=...&product=cloud` a cada 6–24h para detectar bloqueio.

## Checklist

- [x] Remover dependência de sync push local
- [x] Usar `daysRemaining` e `licenseExpired` da API
- [x] Tratar `alertLevel` warning/critical
- [x] Cliente `license_remote.py` + heartbeat 6h
