# Sprint 8 - Enriquecimento Quimico Externo

**Status**: Done  
**Capacidade**: 20 pontos  
**Origem**: IST-v2 (alocacao cronologica de IST-04)  
**Objetivo**: Integrar enriquecimento por APIs externas com rastreabilidade e fallback.

---

## Estrutura de Agentes

- Agente lider: Backend Agent
- Agentes de apoio: Data Engineering Agent, DevOps Agent, Scientific Agent, Reviewer Agent

## Responsabilidades por Agente

- Backend Agent: implementar fluxo de enriquecimento e persistencia das respostas externas.
- Data Engineering Agent: garantir estrutura de dados enriquecidos e lineage por fonte.
- DevOps Agent: suportar configuracao de timeout, retry e observabilidade operacional.
- Scientific Agent: revisar coerencia biologica/quimica dos dados enriquecidos.
- Reviewer Agent: auditar resiliencia de fallback e risco de lacuna de metadados.

## Contexto

Esta sprint conecta os resultados internos do pipeline com bases quimicas externas, preservando rastreabilidade por fonte e evitando falha total em caso de indisponibilidade pontual.

## Entregas

- Fluxo de enriquecimento com PubChem, ChEBI e ClassyFire.
- Politica de retry, timeout e registro de falhas por fonte.
- Persistencia de nome padronizado, descricao, classe geral e subclasse.

## Criterios de Aceite

- Falha em uma API nao interrompe lote completo; registrar pendencias para retentativa.
- Toda informacao enriquecida referencia fonte e timestamp de consulta.

Status de aceite:

- [x] Falha por fonte nao interrompe lote completo; pendencias gravadas em `external_enrichment_pending_retry.json`.
- [x] Snapshot enriquecido inclui `enrichment_source` e `enrichment_queried_at` para rastreabilidade.

## Evidencias de Implementacao

- Orquestrador externo atualizado para fallback por fonte com status individual de execucao.
- Integracao de entrada ClassyFire adicionada ao fluxo (`candidates_classyfire_input.txt`).
- Consolidacao de snapshot enriquecido em `data/staging/external_enrichment_snapshot.parquet`.
- Relatorio operacional em `data/staging/external_enrichment_report.json` com estado por fonte.

## Handoff entre Agentes

1. Backend Agent entrega pipeline de enriquecimento para Data Engineering Agent validar saidas.
2. DevOps Agent valida comportamento operacional em falhas externas.
3. Scientific Agent e Reviewer Agent concluem parecer para liberar Sprint 9.

## Dependencias

- Depende de S7 para estabilidade de dados de entrada e tags.

## Observacao de Cronologia

- S8 corresponde oficialmente ao bloco IST-04.
