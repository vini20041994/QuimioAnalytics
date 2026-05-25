# Sprint 7 - ETL Cientifico e Integracao das Tags

**Status**: Done  
**Capacidade**: 24 pontos  
**Origem**: IST-v2 (alocacao cronologica de IST-03)  
**Objetivo**: Garantir ingestao confiavel de metricas principais e tags de biblioteca do Progenesis.

---

## Estrutura de Agentes

- Agente lider: Data Engineering Agent
- Agentes de apoio: Backend Agent, Scientific Agent, Reviewer Agent

## Responsabilidades por Agente

- Data Engineering Agent: mapear tags, garantir idempotencia e consolidar relatorio de qualidade por lote.
- Backend Agent: suportar validacoes de consistencia e padronizacao de erros operacionais.
- Scientific Agent: validar interpretacao tecnica das tags e das metricas associadas.
- Reviewer Agent: revisar perdas de linha, cobertura de validacao e riscos de lineage.

## Contexto

Esta sprint consolida o tratamento ETL das informacoes exportadas pelo Progenesis, incluindo tags configuradas pela equipe laboratorial e controle de perdas de linha por etapa.

## Entregas

- Mapeamento e persistencia das tags: Branco, Abund > 500, Abund > 1000, Abund > 5000, Abund > 10000, Anova p-value <= 0.05, Max Fold Change >= 2, Not Fragmented.
- Validacoes de consistencia para campos estatisticos e isotopicos.
- Relatorio de qualidade por lote (linhas recebidas, rejeitadas e motivo).

## Criterios de Aceite

- Reprocessamento idempotente sem duplicar registros.
- Perdas de linha sem motivo identificado sao bloqueantes.

Status de aceite:

- [x] Reprocessamento idempotente aplicado com deduplicacao por `feature_group` + `original_id`.
- [x] Perdas de linha sem motivo identificado bloqueiam execucao via erro explicito.

## Evidencias de Implementacao

- Tags Progenesis normalizadas e persistidas no output (`tag_branco`, `tag_abund_gt_*`, `tag_anova_p_le_005`, `tag_max_fold_change_ge_2`, `tag_not_fragmented`).
- Validacoes de consistencia adicionadas para score, fragmentacao, isotopia e metrica estatistica opcional (`anova_p_value`, `max_fold_change`).
- Relatorio de qualidade por lote gerado em JSON com `rows_received`, `rows_output`, `rows_rejected` e `loss_reasons`.
- Caminho do relatorio anexado ao dataframe final em `quality_report_path` para rastreabilidade.

## Handoff entre Agentes

1. Data Engineering Agent entrega pipeline e relatorio de qualidade para Backend Agent.
2. Scientific Agent valida coerencia das tags e dos criterios aplicados.
3. Reviewer Agent libera passagem para Sprint 8 apos auditoria de rastreabilidade.

## Dependencias

- Depende de S6 para garantir contratos de ranking e validacao alinhados.

## Observacao de Cronologia

- S7 corresponde oficialmente ao bloco IST-03.
