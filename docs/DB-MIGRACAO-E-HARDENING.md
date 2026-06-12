# DB migracao e hardening

## Objetivo
Aplicar melhorias de banco e seguranca sem downtime desnecessario e com rollback simples.

## Sequencia recomendada (local e VPS)
1. Subir stack com `docker compose up -d --build`.
2. Gerar backup pre-migracao:
   - Linux/macOS/WSL: `bash scripts/db_backup.sh`
   - PowerShell: `./scripts/db_backup.ps1`
3. Aplicar migracoes de forma segura:
   - Linux/macOS/WSL: `bash scripts/db_migrate_safe.sh`
   - PowerShell: `./scripts/db_migrate_safe.ps1`
4. Validar saude:
   - `curl http://127.0.0.1:8195/health`
5. Validar operacao funcional (painel + API de licencas).

## Hardening aplicado nesta rodada
- Pipeline alinhado ao stack Python (quality, tests, security).
- Varredura de vulnerabilidades (pip-audit/bandit) em modo transicao.
- Atualizacao de dependencia `jinja2` para versao corrigida.
- Remocao de senha forte hardcoded em `.env.example`.

## Proximo passo recomendado
- Tornar `pip-audit` e `bandit` bloqueantes apos estabilizar backlog de vulnerabilidades.
- Adicionar job de container scanning (Trivy/Grype) para imagem Docker.
