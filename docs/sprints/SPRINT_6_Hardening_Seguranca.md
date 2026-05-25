# Sprint 6 - Ranking Biologico v2 com Score

**Status**: Todo  
**Capacidade**: 20 pontos  
**Origem**: IST-v2 (alocacao cronologica de IST-02)  
**Objetivo**: Atualizar a escadinha biologica para incluir score como segundo criterio oficial.

---

## Estrutura de Agentes

- Agente lider: Backend Agent
- Agentes de apoio: Data Engineering Agent, Scientific Agent, Reviewer Agent

## Responsabilidades por Agente

- Backend Agent: implementar regra de ordenacao oficial no motor de ranking e atualizar contrato de output.
- Data Engineering Agent: garantir persistencia dos campos obrigatorios sem perda de dados.
- Scientific Agent: validar coerencia da ordem biologica com os criterios acordados no IST.
- Reviewer Agent: revisar regressao de ranking, risco de empate mal sinalizado e completude de testes.

## Contexto

A ordenacao biologica foi redefinida na reuniao com IST. Esta sprint materializa a nova prioridade e garante validacao tecnica com contrato de output consistente.

## Entregas

- Atualizacao do motor de ranking para ordem: fragmentation_score -> score -> isotope_similarity -> mass_error -> formula.
- Atualizacao de testes unitarios e de validacao para incluir score.
- Atualizacao do contrato de output com campos obrigatorios de ordenacao.

## Criterios de Aceite

- Ranking deterministico reproduzivel em execucoes repetidas com mesmo input.
- Campos obrigatorios presentes no output: feature_group, original_id, fragmentation_score, score, isotope_similarity, mass_error, formula, rank_group, is_tied.

## Handoff entre Agentes

1. Backend Agent entrega ranking implementado para Data Engineering Agent validar no pipeline.
2. Scientific Agent emite parecer tecnico sobre a ordenacao final.
3. Reviewer Agent valida testes e aprova passagem para Sprint 7.

## Dependencias

- Depende de S5 (contrato de dados e rastreabilidade de entrada).

## Observacao de Cronologia

- S6 corresponde oficialmente ao bloco IST-02.
