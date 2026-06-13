# 11 - Agentes e operacao no Cursor

## # Premissa
No Cursor, o uso de "multi-agente" e feito por papeis acionados por prompt e regras persistentes, nao por swarm autonomo nativo.

## # Tags operacionais
- `/pesquisador`: pesquisa mercado, referencia tecnica e alternativas.
- `/roteirista`: cria plano de entrega por fases.
- `/estrutural`: cria ou revisa `spec.md`.
- `/orquestrador`: informa status real, bloqueios e proximo passo.
- `/testador`: escreve testes Red (sem pular para implementacao).
- `/validador`: revisa seguranca, qualidade e conformidade.
- `/finalizador`: consolida documentacao e prepara exportacoes.

## # Contrato de cada etapa
- Entrada clara: objetivo + contexto + restricoes.
- Saida objetiva: artefato verificavel (`spec.md`, testes, checklist, relatorio).
- Gate de qualidade: criterios de aceite explicitos.

## # Anti-padroes
- Pedir "faca tudo" sem spec.
- Aceitar merge sem testes automatizados.
- Misturar credenciais reais em exemplos/versionamento.
