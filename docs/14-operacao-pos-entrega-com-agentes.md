# 14 - Operacao pos-entrega com agentes

## # Objetivo
Manter qualidade, seguranca e evolucao do software apos entrega ao cliente usando papeis de agentes no Cursor.

## # Papeis operacionais recomendados
- `/suporte`: atendimento de chamados e triagem tecnica.
- `/incidente`: gerenciamento de incidente P1/P2 com mitigacao.
- `/sre`: observabilidade, capacidade e estabilidade.
- `/compliance`: revisoes LGPD, permissoes e trilha de auditoria.
- `/melhoria`: descoberta de oportunidades e roadmap.

## # Fluxo minimo de atendimento
1. Receber demanda e classificar severidade.
2. Reproduzir problema e anexar evidencias.
3. Definir acao: correcao, workaround ou melhoria.
4. Aplicar ajuste com teste de regressao.
5. Publicar changelog tecnico e retorno ao cliente.

## # SLOs sugeridos
- P1: acknowledge em 15 minutos, mitigacao inicial em ate 1 hora.
- P2: acknowledge em 1 hora, plano de acao no mesmo dia.
- P3/P4: backlog priorizado em ciclo semanal.

## # Entregaveis por ciclo
- Relatorio semanal de incidentes e melhorias.
- Top 5 riscos tecnicos + plano de mitigacao.
- Tendencia de bugs regressivos e cobertura de testes.
