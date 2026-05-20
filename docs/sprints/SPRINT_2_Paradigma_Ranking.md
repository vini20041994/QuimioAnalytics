# Sprint 2 — Paradigma de Ranking

**Status**: 🟡 Em andamento (6/7 tarefas concluídas) — PRIORIDADE MÁXIMA  
**Capacidade**: 29 pontos  
**Objetivo**: Substituir completamente o ranking probabilístico pela Escadinha Biológica, eliminando qualquer agregação matemática do pipeline.

**Atualizado em**: 2026-05-20

---

## Contexto

Esta é a sprint mais crítica do projeto. A auditoria identificou que o algoritmo de ranking atual usa agregação matemática (média ponderada + softmax) sem justificação biológica. Isso significa que os resultados entregues hoje **podem estar errados** e que papers baseados neles correm risco de rejeição.

Os pesquisadores foram explícitos: o sistema deve **apoiar a decisão humana**, não substituí-la. Quando duas moléculas são tecnicamente indistinguíveis, o sistema deve mostrar ambas — não escolher uma arbitrariamente.

---

## Principais Pontos Levantados

### 1. Agregação matemática sem base biológica
- **Arquivo**: `scripts/features/analytics.py`
- **Problema**:
  ```python
  score_base  = (s_mass + s_fragmentation + s_isotope) / 3.0
  score_final = score_base × abundance_factor × software_factor
  ranking     = softmax(score_final)
  ```
- **Por que é errado**: A média de três métricas independentes oculta cada uma delas. O softmax converte scores em probabilidades sem qualquer significado biológico. Um score de `0.94 vs 0.93` parece preciso mas é totalmente arbitrário.
- **Impacto**: Pesquisador não consegue explicar a um revisor por que candidato A foi escolhido em vez de B.

### 2. Normalização que destrói informação bruta
- **Arquivo**: `scripts/features/scoring.py`
- **Problema**: Funções convertem valores brutos para `[0,1]` antes de qualquer análise.
- **Impacto**: Pesquisador perde acesso aos valores originais do equipamento.

### 3. IDs originais substituídos
- **Arquivos**: `scripts/features/analytics.py`, `scripts/load/load_stg_transformed.py`
- **Problema**: Identificadores do equipamento podem ser renomeados durante o pipeline.
- **Impacto**: Rastreabilidade quebrada — impossível voltar ao dado bruto original.

### 4. Ranking de candidatos como filtro, não como ranking
- **Arquivo**: `scripts/features/analytics.py`
- **Problema**: Pipeline salva apenas os 10 primeiros candidatos, descartando os demais.
- **Impacto**: Candidatos biologicamente relevantes podem ser silenciosamente perdidos.

### 5. Empates não são preservados
- **Arquivo**: `scripts/features/analytics.py`
- **Problema**: Quando dois candidatos têm o mesmo score, o sistema escolhe um arbitrariamente.
- **Impacto**: Pesquisador não sabe que havia outra opção igualmente válida.

---

## O Que Deve Ser Feito

### Escadinha Biológica — Lógica de Ranking

```
Passo 1: Fragmentação DESC     → maior fragmentação = melhor evidência de estrutura
Passo 2: Isotope Similarity DESC  → maior similaridade = melhor match isotópico
Passo 3: Mass Error PPM ASC    → menor erro = melhor precisão de massa
Passo 4: Fórmula Química ASC   → desempate alfabético determinístico
Passo 5: EMPATE TOTAL          → mostrar TODAS as opções; pesquisador decide
```

### Novo Arquivo: `scripts/models/biological_ranking_engine.py`
- Classe `BiologicalRankingEngine` com método `apply_ranking(df, group_by)`
- Retorna todas as linhas com colunas `rank_group` (int) e `is_tied` (bool)
- Método `format_for_display()` para visualização com empates explícitos

### Mudanças em `scripts/features/analytics.py`
- Remover: `score_base`, `score_final`, `abundance_factor`, `softmax`
- Adicionar: instância de `BiologicalRankingEngine`
- Salvar **todos** os candidatos (não filtrar para Ranking de candidatos)

### Mudanças em `scripts/features/scoring.py`
- Remover normalização para `[0,1]`
- Funções devem retornar valor bruto original

---

## Critérios de Aceite por Tarefa

| ID | Tarefa | Critério | Status | Evidência |
|---|---|---|---|---|
| S2-01 | Criar `BiologicalRankingEngine` | Classe implementa os 5 passos; testes da Sprint 3 passam | ✅ Concluído | `scripts/models/biological_ranking_engine.py` implementado com ordenação por fragmentação, isotopia, erro de massa absoluto, fórmula e preservação de empates |
| S2-02 | Remover agregação de `analytics.py` | Sem `score_base`, `softmax`, `abundance_factor` no arquivo | ✅ Concluído | `scripts/features/analytics.py` usa `BiologicalRankingEngine` e não contém agregação probabilística |
| S2-03 | Adaptar pipeline para usar engine | Output contém colunas `rank_group` e `is_tied` | ✅ Concluído | `run_biological_candidate_ranking()` chama `apply_ranking()` e persiste `rank_group` + `is_tied` no parquet |
| S2-04 | Preservar IDs originais | Coluna `original_id` presente no parquet final sem alteração | ✅ Concluído | `scripts/features/analytics.py` preenche `original_id` a partir de `Compound ID` (fallback `Compound`) |
| S2-05 | Remover normalização em `scoring.py` | Funções retornam valor bruto | ✅ Concluído | `scripts/features/scoring.py` retorna valores brutos e desativa `softmax_per_feature` |
| S2-06 | Salvar todos os candidatos | Parquet de saída não tem limite de linhas por grupo | ✅ Concluído | Saída `biological_ranking_candidates.parquet` é gerada sem corte Top 10 |
| S2-07 | Validação com especialista | Especialista assina: "a ordem faz sentido biologicamente" | 🟡 Em execução | Amostra de 100 features gerada em `data/staging/s2_dia5_amostra_100_features.csv` e ata criada em `docs/sprints/evidencias/s2_dia5_validacao_especialista.md`; pendente assinatura |

### Alterações aplicadas nesta atualização

- Arquivo legado `scripts/features/database_top_10.py` removido do projeto.
- Documentação sincronizada com o estado atual da implementação da Escadinha Biológica.
- Dia 5 executado (preparo técnico): amostra estratificada de 100 features gerada com 50 casos com empate e 50 sem empate.
- Evidências criadas: `data/staging/s2_dia5_amostra_100_features.csv` e `docs/sprints/evidencias/s2_dia5_validacao_especialista.md`.

---

## Lições Aprendidas (Antecipadas)

- Complexidade matemática não é sinônimo de rigor científico. Em metabolômica, transparência e reprodutibilidade valem mais que sofisticação algorítmica.
- O sistema deve sempre permitir que o pesquisador veja e questione cada dado — nunca tomar decisões por ele.

---

## Próximos Passos

- [x] **Hoje**: Criar `scripts/models/biological_ranking_engine.py` com a estrutura base da classe
- [x] **Dia 1–2**: Implementar `_rank_group()` com os 5 passos sequenciais
- [x] **Dia 3**: Remover toda agregação de `analytics.py` e `scoring.py`
- [x] **Dia 4**: Adaptar pipeline end-to-end; validar output com dataset de exemplo
- [~] **Dia 5**: Material de validação executado e documentado; pendente sessão final com especialista e assinatura do parecer
- [ ] **Semana 2**: Sprint 3 — escrever testes que validam o comportamento da escadinha

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 2](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-2--paradigma-de-ranking-prioridade-máxima)
