# Sprint 5 - Contrato de Dados e Rastreabilidade de Entrada

**Status**: Todo  
**Capacidade**: 24 pontos  
**Origem**: IST-v2 (alocacao cronologica de IST-01)  
**Objetivo**: Formalizar contrato dos dados exportados do Progenesis e padrao de rastreabilidade desde a origem.

---

## Estrutura de Agentes

- Agente lider: Data Engineering Agent
- Agentes de apoio: Backend Agent, Scientific Agent, Reviewer Agent

## Responsabilidades por Agente

- Data Engineering Agent: definir contrato de entrada, validar schema e lineage, e registrar metadados de execucao.
- Backend Agent: garantir validacao de entrada com erros acionaveis e logging estruturado.
- Scientific Agent: revisar coerencia de metricas e preservacao de contexto experimental.
- Reviewer Agent: auditar risco de perda silenciosa, rastreabilidade incompleta e lacunas de validacao.

## Contexto

Esta sprint abre o ciclo IST-v2 dentro da cronologia legada. O foco e garantir que a entrada proveniente do Progenesis seja validada de forma deterministica, com lineage e auditoria de execucao.

## Entregas

- Dicionario tecnico das colunas principais e metricas (incluindo tags configuradas).
- Especificacao de entrada para planilhas de identificacao e abundancia.
- Registro de lineage minimo (arquivo origem, timestamp, hash e versao do pipeline).

## Criterios de Aceite

- Pipeline recusa schema invalido com erro explicito.
- Entrada valida gera log rastreavel com identificador de execucao.

## Handoff entre Agentes

1. Data Engineering Agent entrega contrato validado para Backend Agent.
2. Backend Agent entrega validacao e logs para Scientific Agent revisar consistencia.
3. Reviewer Agent emite parecer de risco e aprova passagem para Sprint 6.

## Dependencias

- Sem dependencia bloqueante de sprint anterior alem do historico concluido (S1-S4).

## Observacao de Cronologia

- S5 corresponde oficialmente ao bloco IST-01.
