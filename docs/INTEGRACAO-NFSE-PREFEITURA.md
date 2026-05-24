# Integração NFS-e — API Prefeitura

> **Status:** aguardando documentação e credenciais do usuário.

## O que precisamos

1. URL base da API municipal (WSDL ou OpenAPI)
2. Certificado A1 (se exigido)
3. Código de serviço e alíquota ISS
4. Série/RPS e ambiente (homologação vs produção)

## Adapter

Implementação em `app/infra/nfse/prefeitura_adapter.py`:

- `emit_nfse()` — emite nota após pagamento confirmado
- `cancel_nfse()` — cancelamento
- `get_status()` — consulta protocolo

## Configuração (.env)

```env
NFSE_ENABLED=false
NFSE_API_URL=
NFSE_CERT_PATH=
NFSE_SERVICE_CODE=
```

## Fluxo alvo

Pagamento Stripe confirmado → job emite NFS-e → armazena XML/PDF em `invoices_nfse` → e-mail ao cliente.

## Limitações

- Stripe **não** emite NFS-e brasileira — sistemas paralelos
- Município específico — adapter por prefeitura
