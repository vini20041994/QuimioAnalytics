# Sprint 9 - Saida Analitica Final

**Status**: Todo  
**Capacidade**: 24 pontos  
**Origem**: IST-v2 (alocacao cronologica de IST-05)  
**Objetivo**: Entregar visao analitica final orientada a decisao cientifica em Excel, CSV e Dashboard.

---

## Estrutura de Agentes

- Agente lider: Frontend Agent
- Agentes de apoio: Backend Agent, Data Engineering Agent, Scientific Agent, Reviewer Agent

## Responsabilidades por Agente

- Frontend Agent: implementar experiencia de dashboard, filtros, busca e visualizacao de ranking.
- Backend Agent: expor dados finais com contrato estavel para exportacao e tela.
- Data Engineering Agent: garantir consistencia das colunas finais entre canais.
- Scientific Agent: validar legibilidade cientifica e interpretacao das metricas na saida.
- Reviewer Agent: revisar consistencia funcional entre CSV, Excel e dashboard.

## Contexto

Sprint 9 concentra a entrega visivel para especialistas e pesquisadores, com estrutura final de colunas, exportacao e navegacao analitica consistente entre canais.

## Entregas

- Estrutura final com colunas esperadas:
  - Composto
  - Composto ID
  - Modo de aquisicao
  - Score
  - Fragmentacao
  - Abund. relativa
  - Amostra mais abundante
  - Descricao
  - Classe geral
  - Subclasse
- Exportacao Excel/CSV com rastreabilidade de origem dos dados.
- Dashboard com filtros por classe, abundancia, busca por composto e visualizacao de ranking.

## Criterios de Aceite

- Especialista encontra e exporta candidatos prioritarios em um unico fluxo.
- Colunas finais ficam consistentes entre CSV, Excel e dashboard.
- Output final preserva rastreabilidade da origem e versao de processamento.

## Handoff entre Agentes

1. Backend Agent e Data Engineering Agent entregam dataset final para Frontend Agent.
2. Frontend Agent entrega experiencia completa para revisao cientifica.
3. Reviewer Agent valida consistencia de saida e libera Sprint 10.

## Dependencias

- Depende de S6 (Ranking Biologico v2 com score).
- Depende de S7 (ETL cientifico e tags Progenesis).
- Depende de S8 (Enriquecimento quimico externo).
