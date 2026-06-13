# 12 - Seguranca aplicada e ferramentas

## # Objetivo
Definir um baseline pratico para procurar, priorizar e corrigir vulnerabilidades em codigo, dependencias e aplicacao em execucao.

## # Camadas de defesa

### SCA (dependencias)
- Composer Audit
- NPM Audit
- Dependabot/Renovate
- Snyk (opcional)

### SAST (codigo-fonte)
- Larastan/PHPStan
- SonarQube (opcional corporativo)
- Semgrep (opcional)

### DAST (aplicacao em execucao)
- OWASP ZAP em ambiente de homologacao

## # Regra de priorizacao
- Critico/Alto: corrigir antes de merge em `main`.
- Medio: corrigir na sprint atual com prazo definido.
- Baixo: backlog com dono e data.

## # Regras nao negociaveis
- Nunca commitar segredo real.
- Nunca usar senha default em scripts de exemplo.
- Nunca usar tag Docker `latest` para artefato critico.
- Sempre registrar excecao de risco (quem aprovou, prazo, mitigacao).
