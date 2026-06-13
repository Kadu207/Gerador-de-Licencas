# 10 - Laravel + PostgreSQL + SDD (Padrao recomendado)

## # Escopo de aplicacao
- Projetos SaaS B2B, ERP, CRM e modulos financeiros com requisitos de seguranca e auditoria.

## # Stack padrao
- Backend: Laravel (PHP 8.2+)
- Banco: PostgreSQL
- Testes: Pest
- Lint/format: Pint
- Analise estatica: Larastan/PHPStan
- IA pesada (opcional): FastAPI em servico separado

## # Regras de implementacao
- Nenhuma feature entra sem `spec.md` aprovado.
- Controllers devem ficar finos; regra de negocio em Services/Actions.
- Toda feature nova exige teste Red antes de codigo Green.
- Query multi-tenant deve ter isolamento explicito (`tenant_id`, schema ou RLS).

## # Modelagem de dados minima
- PK com UUID.
- Indices para colunas de busca e filtros por tenant.
- JSONB para metadados e trilhas variaveis.
- Auditoria de alteracoes sensiveis.

## # Criterios de qualidade
- 100% dos testes obrigatorios da branch passando.
- Zero erro de linter no pipeline.
- Sem vulnerabilidade critica/alta em dependencias na etapa de seguranca.
