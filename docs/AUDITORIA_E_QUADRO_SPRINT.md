# AUDITORIA TÉCNICA E QUADRO DE SPRINT — QUIMIOANALYTICS

**Data**: 19 de Maio de 2026  
**Versão**: 3.0 — Incorpora feedback científico dos pesquisadores  
**Escopo**: Auditoria consolidada + planejamento executável por arquivo  

---

## ÍNDICE

1. [Situação Geral](#1-situação-geral)
2. [Descoberta Crítica — Paradigma Errado](#2-descoberta-crítica--paradigma-errado)
3. [Problemas por Severidade](#3-problemas-por-severidade)
4. [Arquitetura Recomendada](#4-arquitetura-recomendada)
5. [Guia de Implementação — Escadinha Biológica](#5-guia-de-implementação--escadinha-biológica)
6. [Quadro de Sprint — Visão Consolidada](#6-quadro-de-sprint--visão-consolidada)
7. [Definição de Pronto e Cerimônias](#7-definição-de-pronto-e-cerimônias)
8. [Impacto Financeiro e Roadmap](#8-impacto-financeiro-e-roadmap)

---

## 1. Situação Geral

O **QuimioAnalytics** apresenta **maturidade intermediária (~50%)** com arquitetura conceitual sólida mas lacunas operacionais e um **erro fundamental de metodologia** no algoritmo de ranking.

### Índice de Confiabilidade por Dimensão

| Dimensão | Score Atual | Score Pós-Refatoração | Delta |
|---|---:|---:|---:|
| Integridade Científica | 55/100 | **90/100** | +35 |
| Ranking / Transparência | 10/100 | **95/100** | +85 |
| Arquitetura | 60/100 | **75/100** | +15 |
| Segurança | 65/100 | **75/100** | +10 |
| Performance | 40/100 | **85/100** | +45 |
| Testes / QA | 0/100 | **70/100** | +70 |
| DevOps / Deploy | 70/100 | **80/100** | +10 |
| Rastreabilidade | 70/100 | **95/100** | +25 |
| Observabilidade | 40/100 | **75/100** | +35 |
| **GERAL** | **50/100** | **87/100** | **+37** |

---

## 2. Descoberta Crítica — Paradigma Errado

### O Que o Sistema Faz Hoje (INCORRETO)

```python
# scripts/features/analytics.py — Ranking atual
score_base    = (s_mass + s_fragmentation + s_isotope) / 3.0
score_final   = score_base × abundance_factor × software_factor
ranking       = softmax(score_final)       # probabilístico
```

**Por que é errado**:
- Agregação oculta informação individual de cada critério
- Não tem justificação biológica
- Resultado impossível de explicar a um revisor
- Viola o princípio de transparência exigido pelos pesquisadores

### O Que Deve Ser Feito (CORRETO — Escadinha Biológica)

```
Passo 1  →  Fragmentação DESC (maior fragmentação = melhor identificação)
Passo 2  →  Se empate: Isotope Similarity DESC
Passo 3  →  Se empate: Mass Error PPM ASC (menor = melhor)
Passo 4  →  Se empate: Fórmula Química (ordem alfabética)
Passo 5  →  Se ainda empate: MOSTRAR TODAS as opções → pesquisador decide
```

### Princípios Impostos pelos Pesquisadores

| # | Princípio | Descrição |
|---|---|---|
| 1 | **Integridade total** | Nada de normalizar, desduplicar ou descartar silenciosamente |
| 2 | **Transparência** | Exibir dados brutos, sem máscaras |
| 3 | **Suporte à decisão** | Sistema ajuda, pesquisador decide |
| 4 | **IDs originais** | Manter identificação original do equipamento |
| 5 | **Empates explícitos** | Quando há dúvida técnica, mostrar TODAS as opções |
| 6 | **"Tem que aparecer tudo"** | Nenhuma exclusão silenciosa |

### Exemplo Ilustrativo

```
Feature: m/z = 100.5, RT = 5.3 min

Candidatos:
  A: Fragmentação=95, Isotope=92, MassError=1.2 ppm, Formula=C5H8O2
  B: Fragmentação=95, Isotope=92, MassError=1.2 ppm, Formula=C6H4O
  C: Fragmentação=90, Isotope=88, MassError=0.8 ppm, Formula=C5H10O

RANKING ATUAL (ERRADO):
  score_A = 0.94 → sistema escolhe A arbitrariamente
  score_B = 0.93 → descarta B sem mostrar ao pesquisador
  → Pesquisador nunca saberá que A e B são biologicamente equivalentes

ESCADINHA BIOLÓGICA (CORRETO):
  Passo 1 (Frag):  A=95, B=95, C=90  → EMPATE entre A e B
  Passo 2 (Iso):   A=92, B=92        → EMPATE entre A e B
  Passo 3 (Mass):  A=1.2, B=1.2      → EMPATE entre A e B
  Passo 4 (Form):  A=C5H8O2, B=C6H4O → DIFERENTES

  Resultado: "Rank 1 (EMPATE — 2 opções): A e B.
              C5H10O é Rank 2.
              → Avalie biologicamente qual faz sentido."
```

---

## 3. Problemas por Severidade

### 🔴 Severidade CRÍTICA

| ID | Problema | Arquivo(s) Afetados | Impacto |
|---|---|---|---|
| P1 | **Ranking probabilístico — conceito errado** | `scripts/features/analytics.py`, `scripts/features/scoring.py` | Invalida toda a metodologia |
| P2 | **INSERTs row-by-row — inescalável** | `scripts/load/load_stg_transformed.py` | 45–60 min para 50 K linhas |
| P3 | **Perda silenciosa de dados** | `scripts/transform/transform_stg_xlsx.py` | 1–5% de linhas descartadas sem aviso |
| P4 | **Zero cobertura de testes** | Todo o diretório `scripts/` | Bugs não detectados; publicações arriscadas |
| P5 | **Nenhum audit trail de transformações** | `scripts/transform/*.py`, `scripts/load/*.py` | Impossível auditar resultados |

### 🟠 Severidade ALTA

| ID | Problema | Arquivo(s) Afetados | Impacto |
|---|---|---|---|
| A1 | Lógica de negócio espalhada (sem Service Layer) | `scripts/run/*.py`, `scripts/features/*.py` | Alto acoplamento; difícil manter |
| A2 | SQL espalhado (sem Repository Pattern) | `scripts/load/*.py`, `scripts/features/database_candidates.py` | Schema drift silencioso |
| A3 | Credenciais podem vazar em logs | `scripts/config.py` | PGPASSWORD exposto no `ps aux` |
| A4 | Porta 5432 exposta sem restrição | `docker-compose.yml` | Acesso não-autorizado ao banco |
| A5 | Sem validação de path input | `scripts/run/run_etl_user_input.py` | Path traversal possível |

### 🟡 Severidade MÉDIA

| ID | Problema | Arquivo(s) Afetados | Impacto |
|---|---|---|---|
| M1 | Sem CI/CD pipeline | Ausente | Risco de regressão em produção |
| M2 | Sem backup strategy | `docker-compose.yml` | Perda de dados sem recuperação |
| M3 | Magic numbers sem centralização | `scripts/features/scoring.py`, extratores | Parâmetros inconsistentes |
| M4 | Logging não-estruturado em pipelines | Vários `scripts/transform/` e `scripts/load/` | Debugging difícil |
| M5 | Sem índice para query de candidatos | `database/schema_postgresql_mvp_entrega2.sql` | Ranking lento em produção |

---

## 4. Arquitetura Recomendada

### Estrutura de Pastas Proposta

```
scripts/
├── models/
│   ├── biological_ranking_engine.py   ← NOVO (substitui scoring)
│   └── domain_models.py
├── repositories/
│   ├── identification_repository.py   ← NOVO (otimização COPY)
│   └── base_repository.py
├── services/
│   ├── etl_service.py
│   └── ranking_service.py
├── clients/
│   ├── http_client.py                 ← NOVO (retry/backoff unificado)
│   └── pubchem_client.py
├── loggers/
│   └── quality_reporter.py            ← NOVO (data quality report)
└── constants.py                       ← NOVO (centralizar parâmetros)

tests/
├── unit/
│   ├── test_biological_ranking.py     ← NOVO
│   ├── test_scoring.py
│   └── test_transform_stg_xlsx.py
├── integration/
│   └── test_runners_smoke.py
└── validation/
    └── test_candidates_schema.py

database/migrations/
└── 010_add_unique_constraints_ref.sql ← NOVO
```

---

## 5. Guia de Implementação — Escadinha Biológica

### O Que Remover de `analytics.py`

```python
# DELETAR estas linhas:
df["score_base"] = (df["s_mass"] + df["s_fragmentation"] + df["s_isotope"]) / 3.0
df["score_software"] = (df["score_original"] - score_min) / (score_max - score_min)
abundance_factor = np.log1p(df["media_abundancia"]) / (1 + df["cv"])
df["score_final"] = (
    df["score_base"] * (0.5 + 0.5 * df["score_software"]) * abundance_factor
).fillna(0)
from scipy.special import softmax
ranking_probabilities = softmax(df["score_final"])
```

### `scripts/models/biological_ranking_engine.py` — Código Completo

```python
"""
Escadinha Biológica — ranking sequencial sem agregação matemática.

Princípios:
  - Sem média ponderada, sem softmax, sem probabilidade
  - Filtros sequenciais transparentes
  - Empates são preservados e exibidos ao pesquisador
  - Pesquisador decide; o sistema suporta
"""
from __future__ import annotations

import pandas as pd


RANKING_STEPS = [
    ("fragment_score",    False),   # DESC — maior fragmentação é melhor
    ("isotope_similarity", False),  # DESC — maior similaridade é melhor
    ("mass_error_ppm",    True),    # ASC  — menor erro é melhor
    ("formula",           True),    # ASC  — desempate alfabético
]


class BiologicalRankingEngine:
    """Aplica a Escadinha Biológica a um DataFrame de candidatos."""

    def apply_ranking(
        self,
        df: pd.DataFrame,
        group_by: str = "feature_group",
    ) -> pd.DataFrame:
        """
        Retorna o DataFrame original acrescido de:
          - rank_group : inteiro (1 = melhor grupo de candidatos)
          - is_tied    : bool (True quando rank_group contém > 1 candidato)

        Todos os candidatos são preservados — nenhuma linha é descartada.
        """
        result = df.copy()
        result["rank_group"] = 0
        result["is_tied"] = False

        for group_key in result[group_by].unique():
            mask = result[group_by] == group_key
            result.loc[mask] = self._rank_group(result.loc[mask].copy())

        return result

    def _rank_group(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["rank_group"] = 0
        df["is_tied"] = False

        rank = 1
        pool = df.copy()

        for column, ascending in RANKING_STEPS:
            if pool.empty:
                break

            pool = pool.sort_values(column, ascending=ascending, na_position="last")
            top_value = pool[column].iloc[0]
            tied = pool[column] == top_value

            for idx in pool[tied].index:
                df.loc[idx, "rank_group"] = rank
                df.loc[idx, "is_tied"] = tied.sum() > 1

            if tied.sum() == 1:
                pool = pool[~tied].copy()
                rank += 1
            else:
                pool = pool[tied].copy()

        # Candidatos que sobraram (completamente empatados em todos os critérios)
        unranked = df[df["rank_group"] == 0]
        if not unranked.empty:
            for idx in unranked.index:
                df.loc[idx, "rank_group"] = rank
                df.loc[idx, "is_tied"] = len(unranked) > 1

        return df

    def format_for_display(self, ranked_df: pd.DataFrame) -> str:
        """Texto legível com empates explícitos para o pesquisador."""
        lines = []

        for rank in sorted(ranked_df["rank_group"].unique()):
            if rank == 0:
                continue
            group = ranked_df[ranked_df["rank_group"] == rank]

            if len(group) == 1:
                r = group.iloc[0]
                lines.append(
                    f"Rank {rank}: {r['formula']}  "
                    f"(frag={r['fragment_score']}, "
                    f"iso={r['isotope_similarity']}, "
                    f"Δm={r['mass_error_ppm']:.2f} ppm)"
                )
            else:
                lines.append(f"Rank {rank} — EMPATE ({len(group)} opções equivalentes):")
                for i, (_, r) in enumerate(group.iterrows(), 1):
                    lines.append(
                        f"  {rank}.{chr(96+i)}: {r['formula']}  "
                        f"[frag={r['fragment_score']}, "
                        f"iso={r['isotope_similarity']}, "
                        f"Δm={r['mass_error_ppm']:.2f} ppm]"
                    )
                lines.append("  → Avalie biologicamente qual candidato faz sentido")

        return "\n".join(lines)
```

### Otimização de Banco — `load_stg_transformed.py`

```python
# ANTES (45–60 min para 50 K linhas):
for i, row in df.iterrows():
    cur.execute("INSERT INTO stg.identification_row VALUES (...)", row_params)

# DEPOIS (<5 min — uso de COPY):
import io

def bulk_insert(conn, df: pd.DataFrame, table: str, columns: list[str]) -> int:
    buffer = io.StringIO()
    df[columns].to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
    buffer.seek(0)
    with conn.cursor() as cur:
        cur.copy_from(buffer, table, columns=columns, null="\\N")
    conn.commit()
    return len(df)
```

### Testes Mínimos (`tests/unit/test_biological_ranking.py`)

```python
import pandas as pd
import pytest
from scripts.models.biological_ranking_engine import BiologicalRankingEngine


@pytest.fixture
def engine():
    return BiologicalRankingEngine()


def test_ordem_por_fragmentacao(engine):
    df = pd.DataFrame({
        "feature_group": ["F1", "F1"],
        "fragment_score": [90, 95],
        "isotope_similarity": [88, 92],
        "mass_error_ppm": [2.0, 1.2],
        "formula": ["C5H10O", "C5H8O2"],
    })
    result = engine.apply_ranking(df)
    assert result.loc[result["formula"] == "C5H8O2", "rank_group"].iloc[0] == 1
    assert result.loc[result["formula"] == "C5H10O", "rank_group"].iloc[0] == 2


def test_empate_preservado(engine):
    df = pd.DataFrame({
        "feature_group": ["F1", "F1", "F1"],
        "fragment_score": [95, 95, 90],
        "isotope_similarity": [92, 92, 88],
        "mass_error_ppm": [1.2, 1.2, 0.8],
        "formula": ["C5H8O2", "C6H4O", "C5H10O"],
    })
    result = engine.apply_ranking(df)
    empate = result[result["formula"].isin(["C5H8O2", "C6H4O"])]
    assert (empate["rank_group"] == 1).all()
    assert (empate["is_tied"] == True).all()
    assert result.loc[result["formula"] == "C5H10O", "rank_group"].iloc[0] == 2


def test_dados_brutos_inalterados(engine):
    original = pd.DataFrame({
        "feature_group": ["F1"],
        "fragment_score": [100],
        "isotope_similarity": [99],
        "mass_error_ppm": [0.1],
        "formula": ["C6H12O6"],
    })
    result = engine.apply_ranking(original.copy())
    assert result["fragment_score"].iloc[0] == 100
    assert result["mass_error_ppm"].iloc[0] == 0.1


def test_ids_originais_mantidos(engine):
    df = pd.DataFrame({
        "feature_group": ["F1", "F1"],
        "original_id": ["EQUIP_001", "EQUIP_002"],
        "fragment_score": [95, 90],
        "isotope_similarity": [92, 88],
        "mass_error_ppm": [1.2, 2.0],
        "formula": ["C5H8O2", "C6H4O"],
    })
    result = engine.apply_ranking(df)
    assert set(result["original_id"]) == {"EQUIP_001", "EQUIP_002"}
```

---

## 6. Quadro de Sprint — Visão Consolidada

### Escala de Pontos

| Pontos | Esforço |
|---:|---|
| 1 | Ajuste simples, sem risco |
| 2 | Ajuste com validação |
| 3 | Alteração média (1 arquivo principal + efeitos locais) |
| 5 | Alteração multi-arquivo |
| 8 | Iniciativa ampla com impacto transversal |

**Papéis**: `Dados` · `Backend` · `DevOps` · `QA`  
**Status**: `Todo` · `Doing` · `Review` · `Done` · `Blocked`

---

### Sprint 1 — Estabilização Crítica  *(já concluída)*
Objetivo: remover falhas de execução e tornar bootstrap/migrações reexecutáveis.  
Capacidade: **24 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S1-01 | Corrigir assinatura inválida do spider ChemSpider | `scripts/extract/extract_chemspider.py` | 3 | Backend | Done | Script executa sem erro de sintaxe e gera parquet de saída |
| S1-02 | Ajustar leitura de arquivo com encoding explícito | `scripts/extract/extract_chemspider.py` | 1 | Backend | Done | Sem alerta de `open` sem encoding |
| S1-03 | Remover bloco duplicado de execução no runner PubChem | `scripts/run/run_etl_pubchem.py` | 2 | Backend | Done | Runner executa uma única vez por chamada |
| S1-04 | Tornar criação de tabelas finais idempotente | `database/schema_postgresql_mvp_entrega2.sql` | 5 | Dados | Done | Reaplicar schema não falha por tabela existente |
| S1-05 | Tornar migration 003 reexecutável | `database/migrations/003_remove_duplicates_add_unique_constraint.sql` | 3 | Dados | Done | Migration pode rodar novamente sem erro |
| S1-06 | Tornar migration 006 reexecutável | `database/migrations/006_remove_duplicates_add_unique_chebi_constraint.sql` | 3 | Dados | Done | Migration pode rodar novamente sem erro |
| S1-07 | Corrigir links de documentação de primeira execução | `README.md`, `docs/README.md`, `scripts/run/install_system_prereqs.sh` | 2 | DevOps | Done | Nenhuma referência a arquivo inexistente |
| S1-08 | Verificar lint dos extratores legados | `scripts/extract/extract_foodb.py`, `extract_hmdb.py`, `extract_classyfire.py`, `extract_lotus.py` | 5 | QA | Done | Sem erros bloqueantes no VS Code Problems |

---

### Sprint 2 — Paradigma de Ranking *(PRIORIDADE MÁXIMA)*
Objetivo: substituir o ranking probabilístico pela Escadinha Biológica.  
Capacidade: **29 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S2-01 | Criar `BiologicalRankingEngine` | `scripts/models/biological_ranking_engine.py` *(novo)* | 8 | Backend | Todo | Classe implementa os 5 passos; testes S3-01 passam |
| S2-02 | Remover agregação matemática de `analytics.py` | `scripts/features/analytics.py` | 5 | Backend | Todo | Sem `score_base`, `softmax`, `abundance_factor` no arquivo |
| S2-03 | Adaptar `analytics.py` para usar `BiologicalRankingEngine` | `scripts/features/analytics.py` | 3 | Backend | Todo | Pipeline roda; output contém colunas `rank_group` e `is_tied` |
| S2-04 | Preservar IDs originais do equipamento no pipeline | `scripts/features/analytics.py`, `scripts/load/load_stg_transformed.py` | 3 | Dados | Todo | Coluna `original_id` presente no parquet final sem alteração |
| S2-05 | Remover normalização de scores em `scoring.py` | `scripts/features/scoring.py` | 2 | Backend | Todo | Funções retornam valor bruto sem transformação para \[0,1\] |
| S2-06 | Atualizar output para salvar TODOS os candidatos | `scripts/features/analytics.py` | 3 | Backend | Todo | Parquet de saída contém todos os candidatos (não só Ranking de candidatos) |
| S2-07 | Validar escadinha com especialista (100 features amostra) | — | 5 | Dados | Todo | Especialista assina: "a ordem faz sentido biologicamente" |

---

### Sprint 3 — Testes e Qualidade
Objetivo: implantar suite mínima de testes e gate de qualidade no CI.  
Capacidade: **33 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S3-01 | Testes unitários da Escadinha Biológica | `tests/unit/test_biological_ranking.py` *(novo)* | 5 | QA | Todo | 4 cenários: ordem, empate, dados brutos, IDs originais |
| S3-02 | Estruturar pastas de testes | `tests/unit/`, `tests/integration/`, `tests/validation/` *(novos)* | 2 | QA | Todo | `pytest` descobre e executa sem erro |
| S3-03 | Testes unitários de transformação stg xlsx | `tests/unit/test_transform_stg_xlsx.py` *(novo)* | 5 | QA | Todo | Cobrir `safe_numeric`, `safe_int`, colunas obrigatórias |
| S3-04 | Testes de merge e colunas obrigatórias do ranking | `tests/unit/test_features_io.py` *(novo)* | 3 | QA | Todo | Merge inválido falha com mensagem clara |
| S3-05 | Testes de smoke para runners críticos | `tests/integration/test_runners_smoke.py` *(novo)* | 5 | Backend | Todo | Entradas mínimas executam sem crash |
| S3-06 | Testes de validação de schema de output | `tests/validation/test_output_schema.py` *(novo)* | 3 | QA | Todo | Output atende colunas obrigatórias e `rank_group ≥ 1` |
| S3-07 | Habilitar cobertura mínima 60% no CI | `.github/workflows/ci.yml`, `requirements-dev.txt` | 5 | DevOps | Todo | PR falha abaixo da meta |
| S3-08 | Ajustar escopo de lint (ruff) para pacotes principais | `.github/workflows/ci.yml` | 2 | DevOps | Todo | Ruff executa em `scripts/` e `tests/` sem erros E/W bloqueantes |
| S3-09 | Testes de data quality report | `tests/unit/test_quality_reporter.py` *(novo)* | 3 | QA | Todo | Report indica corretamente linhas perdidas e motivo |

---

### Sprint 4 — Integridade e Idempotência de Banco
Objetivo: garantir consistência de chaves, deduplicação real e padronização de fontes externas.  
Capacidade: **28 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S4-01 | Padronizar `source_name` entre seed SQL e loaders legados | `database/schema_postgresql_mvp_entrega2.sql`, `scripts/load/load_foodb.py`, `load_hmdb.py`, `load_lotus.py`, `load_classyfire.py` | 5 | Dados | Todo | `get_source_id` encontra fontes sem fallback manual |
| S4-02 | Criar constraints únicas para `external_identifier` | `database/migrations/010_add_unique_constraints_ref.sql` *(novo)* | 3 | Dados | Todo | ON CONFLICT DO NOTHING deduplica por chave natural |
| S4-03 | Criar constraints únicas para `compound_property` | `database/migrations/010_add_unique_constraints_ref.sql` | 3 | Dados | Todo | Reprocessamento não gera duplicatas |
| S4-04 | Criar constraints únicas para `compound_cross_reference` | `database/migrations/010_add_unique_constraints_ref.sql` | 3 | Dados | Todo | Idempotência confirmada |
| S4-05 | Revisar e alinhar ON CONFLICT com novas constraints | `scripts/load/external_load_utils.py` | 3 | Backend | Todo | ON CONFLICT referencia alvo válido |
| S4-06 | Normalizar tratamento de erros nos extratores legados | `scripts/extract/extract_foodb.py`, `extract_hmdb.py`, `extract_classyfire.py`, `extract_lotus.py` | 3 | Backend | Todo | Capturas específicas para `requests`/parsing; sem `Exception` genérica |
| S4-07 | Adicionar timeout explícito em todos os requests HTTP | `scripts/extract/extract_foodb.py`, `extract_hmdb.py`, `extract_classyfire.py`, `extract_lotus.py` | 2 | Backend | Todo | Toda chamada HTTP tem `timeout=` explícito |
| S4-08 | Rodar validação de migrations em banco limpo e inicializado | `scripts/run/run_pipeline_frontend.py`, `scripts/manage_db.py` | 2 | DevOps | Todo | Evidência de sucesso nos dois cenários |
| S4-09 | Criar índice de candidatos para query de ranking | `database/schema_postgresql_mvp_entrega2.sql` | 3 | Dados | Todo | `EXPLAIN ANALYZE` para Ranking de candidatos mostra Index Scan |
| S4-10 | Adicionar soft-delete e `updated_at` em tabelas CORE | `database/schema_postgresql_mvp_entrega2.sql` | 1 | Dados | Todo | Colunas `deleted_at`, `updated_at` existem em `core.feature` e `core.candidate_identification` |

---

### Sprint 5 — Performance e Observabilidade
Objetivo: aumentar throughput, rastreabilidade e governança de dados.  
Capacidade: **37 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S5-01 | Substituir INSERT row-by-row por COPY no staging | `scripts/load/load_stg_transformed.py` | 8 | Dados | Todo | Tempo de carga ≥ 10× menor no dataset de referência |
| S5-02 | Aplicar COPY no load Ranking de candidatos core | `scripts/features/database_candidates.py` | 5 | Dados | Todo | Redução mensurável de latência |
| S5-03 | Criar `http_client.py` com retry/backoff/timeout unificado | `scripts/extract/http_client.py` *(novo)*, `scripts/extract/extract_pubchem.py`, `extract_chebi.py` | 8 | Backend | Todo | Extratores usam cliente único; timeout e retry configuráveis |
| S5-04 | Criar `quality_reporter.py` — data quality por transformação | `scripts/loggers/quality_reporter.py` *(novo)*, `scripts/transform/transform_stg_xlsx.py` | 5 | Backend | Todo | Report JSON com `rows_input`, `rows_output`, `rows_lost`, `loss_reasons` |
| S5-05 | Padronizar logging estruturado por batch | `scripts/run/run_pipeline_frontend.py`, `scripts/load/load_pubchem.py`, `load_chebi.py`, `load_chemspider.py` | 5 | Backend | Todo | Logs contêm `timestamp`, `level`, `batch_id`, `stage` |
| S5-06 | Restringir exposição de porta 5432 por ambiente | `docker-compose.yml`, `.env.example` *(novo)* | 3 | DevOps | Todo | Porta só exposta quando `EXPOSE_DB_PORT=true` |
| S5-07 | Documentar runbook de produção | `docs/Database/SETUP_DATABASE.md`, `docs/README.md` | 3 | DevOps | Todo | Procedimento de backup, restore e rollback documentado e testado |

---

### Sprint 6 — Hardening de Segurança
Objetivo: eliminar vetores de ataque identificados.  
Capacidade: **16 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S6-01 | Remover uso de `PGPASSWORD` em variável de ambiente | `scripts/config.py` | 3 | Backend | Todo | Conexão usa `.pgpass` ou `libpq service file`; `PGPASSWORD` não aparece em `ps aux` |
| S6-02 | Validar path de arquivo de entrada (prevenir traversal) | `scripts/run/run_etl_user_input.py` | 3 | Backend | Todo | Caminho fora de `RAW_INPUTS_DIR` lança `ValueError` |
| S6-03 | Substituir serialização `to_json()` por `json.dumps` com `default=str` | `scripts/load/load_stg_transformed.py` | 2 | Backend | Todo | JSONB inserido é válido; encoding UTF-8 explícito |
| S6-04 | Criar roles mínimos (read/write/etl) no schema | `database/schema_postgresql_mvp_entrega2.sql` | 5 | Dados | Todo | Script de extração não tem GRANT de INSERT; script de load não tem GRANT de SELECT em REF |
| S6-05 | Configurar `127.0.0.1` como bind padrão da porta 5432 | `docker-compose.yml` | 3 | DevOps | Todo | `nmap` externo não enxerga a porta |

---

### Sprint 7 — Arquitetura e CI/CD
Objetivo: introduzir padrões de projeto e pipeline de entrega automatizado.  
Capacidade: **34 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S7-01 | Criar `IdentificationRepository` com `bulk_insert` via COPY | `scripts/repositories/identification_repository.py` *(novo)* | 5 | Backend | Todo | `insert_batch` usa COPY; `get_by_batch` e `get_by_feature` funcionam |
| S7-02 | Extrair `RankingService` (orquestra engine + repository) | `scripts/services/ranking_service.py` *(novo)* | 5 | Backend | Todo | `analytics.py` delega para `RankingService`; sem SQL direto |
| S7-03 | Centralizar constantes em `constants.py` | `scripts/constants.py` *(novo)* | 2 | Backend | Todo | `TOLERANCE_PPM`, `RATE_LIMIT_DELAY` etc. em único lugar |
| S7-04 | Adicionar type hints em arquivos refatorados | `scripts/features/analytics.py`, `scripts/models/biological_ranking_engine.py` | 3 | Backend | Todo | `mypy --strict` não reporta erros nesses arquivos |
| S7-05 | Criar workflow CI com testes + lint + coverage | `.github/workflows/ci.yml` *(novo)* | 8 | DevOps | Todo | PR no `main` executa testes; falha abaixo de 60% |
| S7-06 | Configurar build de imagem Docker no CI | `.github/workflows/ci.yml` | 3 | DevOps | Todo | Imagem construída sem erro em cada push |
| S7-07 | Criar `docker-compose.dev.yml` e `docker-compose.prod.yml` | `docker-compose.dev.yml` *(novo)*, `docker-compose.prod.yml` *(novo)* | 3 | DevOps | Todo | `dev` expõe porta; `prod` não expõe; variáveis distintas |
| S7-08 | Implementar backup automático diário via serviço Docker | `docker-compose.prod.yml` | 5 | DevOps | Todo | Arquivo `.sql.gz` criado diariamente em `./backups/` |

---

### Sprint 8 — Validação Científica e Paper
Objetivo: garantir que o sistema está pronto para publicação.  
Capacidade: **20 pontos**

| ID | Tarefa | Arquivo(s) | Pts | Dono | Status | Critério de aceite |
|---|---|---|---:|---|---|---|
| S8-01 | Comparar escadinha com ranking de especialista (100 features) | Script de comparação ad-hoc | 5 | Dados | Todo | Relatório de concordância assinado pelo especialista |
| S8-02 | Criar script de reprodutibilidade (mesmo input → mesmo output) | `tests/validation/test_reproducibility.py` *(novo)* | 5 | QA | Todo | 3 execuções consecutivas geram hash idêntico do output |
| S8-03 | Redigir seção de Metodologia para paper | `docs/material_complementar/metodologia_ranking.md` *(novo)* | 5 | Dados | Todo | Descreve escadinha, IDs originais, preservação de empates |
| S8-04 | Atingir 70% de cobertura de testes | Todos os módulos refatorados | 5 | QA | Todo | `pytest --cov` reporta ≥ 70% |

---

## 7. Definição de Pronto e Cerimônias

### Definição de Pronto (DoD)

Uma tarefa só pode ser marcada como **Done** se:

1. Código revisado por ao menos 1 pessoa.
2. Lint (`ruff`) e testes relacionados passam sem erros.
3. Evidência de execução anexada (log, screenshot ou saída de comando).
4. Documentação atualizada quando há impacto operacional.
5. Sem regressão nos runners principais (`run_etl.py` e `run_pipeline_frontend.py`).

### Cerimônias Sugeridas

| Cerimônia | Frequência | Duração |
|---|---|---|
| Planejamento de Sprint | A cada sprint | 90 min |
| Daily standup | Diário | 15 min |
| Review técnica | Sexta-feira | 45 min |
| Retrospectiva | Fim da sprint | 30 min |

---

## 8. Impacto Financeiro e Roadmap

### Custo × Benefício

| Item | Valor estimado |
|---|---|
| Custo de implementar (2 devs, 4 meses) | R$ 150 K – 200 K |
| Custo de **não** implementar (papers rejeitados, retrabalho, reputação) | R$ 500 K – 1 M+ |
| ROI em 12 meses | 3–5× |

### Roadmap de Alto Nível

```
Sprint 2  (3 semanas)  → Escadinha Biológica — validação científica imediata
Sprint 3  (3 semanas)  → Testes & CI — base segura para refatorar
Sprint 4  (3 semanas)  → Integridade de banco — dados confiáveis
Sprint 5  (3 semanas)  → Performance & observabilidade — escala real
Sprint 6  (2 semanas)  → Hardening de segurança
Sprint 7  (4 semanas)  → Arquitetura & DevOps
Sprint 8  (4 semanas)  → Validação científica & paper

Julho 2026 → Sistema cientificamente válido e pronto para produção ✓
```

---


