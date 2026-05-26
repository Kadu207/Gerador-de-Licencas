# Tasks — 001 Gerenciador de Licenças

## Fase 0 ✅
- [x] is_valid_license_key_format + testes
- [x] daysRemaining corrigido
- [x] validate Cloud/Lab/VDE
- [x] revoke UI + service
- [x] período 3y + produto vde
- [x] git init + .gitignore

## Fase 1 ✅
- [x] .specify/ + .cursor/rules/
- [x] docs/PREMISSAS.md
- [x] Docker Postgres + Alembic
- [x] timestamptz nos modelos
- [x] compute_effective_status separado

## Fase 2 ✅
- [x] Schema clients/addresses matriz-filial
- [x] Form máscaras + ViaCEP
- [x] Validação CPF/CNPJ + RF
- [x] Job alertas 20-1
- [x] Contador dias/meses/anos

## Fase 3 ✅
- [x] API-PRODUTOS.md
- [x] heartbeat + revoke API
- [x] SYNC_REMOTE_ENABLED=false default
- [x] Guias integração 3 MD
- [x] Cliente remoto Dental Lab (retry, cache, heartbeat)
- [x] Cliente remoto Excellence Cloud (license_remote.py)
- [x] Pacote drop-in VDE (`vde-incorporadora-license/`)

## Fase 4 ✅
- [x] Stripe Checkout
- [x] Webhooks + tabela payments
- [x] Planos mensal/semestral/anual
- [x] Botão link pagamento

## Fase 5 ⏳
- [x] Adapter stub prefeitura
- [ ] Credenciais/documentação usuário
- [ ] Homologação NFS-e

## Fase 6 ✅
- [x] Landing responsiva
- [x] Deploy VPS docs
- [ ] Push GitHub kadu207 (requer auth usuário)
- [x] Testes E2E pytest

## E2E manual produção

1. `docker compose up -d`
2. `curl https://licencas.inovatitech.com.br/health`
3. Cadastrar cliente → emitir licença → validate API
4. Simular alerta (ends_at T+7)
5. Link Stripe test mode
6. Revogar licença → valid=false
