# Workflow SDD + TDD — Gerenciador de Licenças

## SDD (Spec-Driven Development)

1. Escrever `specs/00N-feature/spec.md` antes de codar.
2. Validar com `/validador`.
3. Implementar via `speckit-implement`.
4. Atualizar `docs/PREMISSAS.md`.

## TDD (Test-Driven Development)

1. **Red** — `npm test` em `apps/web` com teste falhando.
2. **Green** — implementação mínima em `src/domain/` ou `src/lib/services/`.
3. **Refactor** — limpeza sem quebrar testes.

## Comandos

```bash
cd apps/web
npm test          # Vitest — domínio licensing
npm run build     # Next.js produção
```

## Papéis Cursor

`/pesquisador` → `/roteirista` → `/estrutural` → `/testador` → `/validador` → `/finalizador`
