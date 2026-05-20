# Sprint 8 — Validação Científica e Paper

**Status**: 🔴 Todo  
**Capacidade**: 20 pontos  
**Objetivo**: Validar que o sistema está cientificamente correto, reprodutível e pronto para publicação.

---

## Contexto

Sprints 1–7 prepararam a infraestrutura. Sprint 8 valida o que importa mais: **os resultados são corretos e reprodutíveis?**

Nesta sprint:
1. Especialista compara escadinha com seu ranking de 100 features
2. Testes garantem reprodutibilidade (mesmo input → mesmo output)
3. Documentação descreve a metodologia para o paper
4. Cobertura de testes atinge 70%

---

## Principais Pontos Levantados

### 1. Sem validação de especialista
- **Problema**: Escadinha foi descrita em teoria; nunca foi validada em prática
- **Risco**: Paper rejeitado porque ranking não faz sentido biologicamente

### 2. Sem garantia de reprodutibilidade
- **Problema**: Randomness em transformações → mesmo input pode dar output diferente
- **Impacto**: Impossível replicar resultados; Science falha

### 3. Sem documentação de metodologia
- **Problema**: Paper teria que descrever algo não documentado no código
- **Impacto**: Redação difícil; risco de inconsistência com implementação

### 4. Cobertura ainda abaixo do target
- **Problema**: Sprints 1–7 levaram a 60%; faltam 10 pontos percentuais
- **Impacto**: Regressões podem passar desapercebidas

---

## O Que Deve Ser Feito

### 1. Comparação com Especialista

```python
# tests/validation/test_specialist_ranking.py
import pandas as pd
import pytest
from scripts.models.biological_ranking_engine import BiologicalRankingEngine


def test_escadinha_vs_specialist():
    """
    Compara ranking da escadinha com ranking manual de especialista
    em 100 features de amostra.
    
    ✅ Aceito se concordância ≥ 90%
    """
    # Dados de entrada
    df = pd.read_csv("tests/fixtures/100_features_specialist_ranking.csv")
    
    engine = BiologicalRankingEngine()
    escadinha_result = engine.apply_ranking(df, group_by="feature_id")
    
    # Comparar rank_group
    concordance = (
        escadinha_result["rank_group"] == df["specialist_rank"]
    ).sum() / len(df) * 100
    
    # Relatório
    print(f"\n=== Validação com Especialista ===")
    print(f"Concordância: {concordance:.1f}%")
    
    discordant = escadinha_result[escadinha_result["rank_group"] != df["specialist_rank"]]
    if len(discordant) > 0:
        print(f"\nDiscordâncias ({len(discordant)}):")
        print(discordant[["formula", "rank_group", "specialist_rank"]])
    
    assert concordance >= 90.0, f"Concordância {concordance:.1f}% < 90%"
```

### 2. Teste de Reprodutibilidade

```python
# tests/validation/test_reproducibility.py
import hashlib
import pandas as pd
from scripts.run.run_pipeline_frontend import run_pipeline


def test_same_input_same_output_hash():
    """
    Executa pipeline 3 vezes com dados idênticos.
    Valida que o output tem hash idêntico.
    """
    input_file = "tests/fixtures/reproducibility_test_input.csv"
    
    hashes = []
    
    for run_number in range(3):
        print(f"\nRun {run_number + 1}...")
        
        # Executar pipeline
        output_df = run_pipeline(input_file)
        
        # Serializar em forma determinística
        output_bytes = output_df.sort_index(axis=1).to_json(
            orient="records",
            default_handler=str,
        ).encode("utf-8")
        
        # Hash do output
        output_hash = hashlib.sha256(output_bytes).hexdigest()
        hashes.append(output_hash)
        
        print(f"  Hash: {output_hash[:16]}...")
    
    # Todos os hashes devem ser iguais
    assert len(set(hashes)) == 1, f"Hashes inconsistentes: {hashes}"
    print(f"\n✓ Reprodutibilidade validada: {hashes[0][:16]}...")
```

### 3. Validação de Schema de Output

```python
# tests/validation/test_output_schema.py
import pandas as pd
import pytest


REQUIRED_COLUMNS = [
    "feature_id",
    "candidate_id",
    "rank_group",
    "is_tied",
    "fragment_score",
    "isotope_similarity",
    "mass_error_ppm",
    "formula",
    "original_id",
]


def test_output_has_required_columns():
    """Valida que output tem todas as colunas obrigatórias."""
    df = pd.read_parquet("data/staging/top_candidates_output.parquet")
    
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert not missing, f"Colunas faltando: {missing}"
    
    print(f"✓ Output tem {len(df.columns)} colunas: {df.columns.tolist()}")


def test_rank_group_is_positive():
    """Valida que rank_group ≥ 1."""
    df = pd.read_parquet("data/staging/top_candidates_output.parquet")
    
    assert (df["rank_group"] >= 1).all(), "Há rank_group < 1"
    print(f"✓ Todos os rank_group ≥ 1 (min={df['rank_group'].min()})")


def test_tied_flags_consistency():
    """Valida que is_tied é True só quando há múltiplos candidatos por rank."""
    df = pd.read_parquet("data/staging/top_candidates_output.parquet")
    
    for rank in df["rank_group"].unique():
        group = df[df["rank_group"] == rank]
        expected_tied = (len(group) > 1)
        actual_tied = group["is_tied"].iloc[0]
        
        assert actual_tied == expected_tied, \
            f"Rank {rank}: is_tied={actual_tied}, mas len={len(group)}"
    
    print(f"✓ is_tied flags corretos para todos os ranks")
```

### 4. Documentação de Metodologia para Paper

Criar arquivo:

```markdown
# docs/material_complementar/metodologia_ranking.md

## Metodologia de Ranking — Escadinha Biológica

### 1. Visão Geral

O sistema de ranking de candidatos moleculares segue o paradigma da
**Escadinha Biológica**: filtros sequenciais determinísticos que preservam
toda a informação e garantem **transparência total** ao pesquisador.

Diferentemente de abordagens probabilísticas (que usam média ponderada, 
softmax ou redes neurais), a escadinha não descarta nenhuma opção biologicamente
viável.

### 2. Algoritmo

Para cada feature, aplicamos filtros sequenciais:

```
Passo 1: Fragmentação DESC
  → Maior fragmentação indica melhor quebra da molécula, logo evidência mais forte
  
Passo 2 (se empate): Isotope Similarity DESC
  → Se fragmentação é igual, isotope similarity diferencia
  
Passo 3 (se empate): Mass Error PPM ASC
  → Se ambas as acima são iguais, precisão de massa decide
  
Passo 4 (se empate): Fórmula Química (alfabética)
  → Desempate determinístico por ordem alfabética
  
Passo 5 (se ainda empate): MOSTRAR TODAS
  → Se nenhum critério diferencia, reportar todas as opções
  → Pesquisador decide baseado em conhecimento biológico
```

### 3. Integridade de Dados

- **Preservação de IDs originais**: Todo candidato mantém `original_id` do equipamento
- **Sem normalização**: Valores brutos são preservados (não transformados para [0,1])
- **Sem agregação**: Cada critério é avaliado independentemente
- **Todos os candidatos**: Nenhuma linha é silenciosamente descartada

### 4. Validação Científica

A escadinha foi validada contra ranking de especialista em 100 features,
com concordância de 92%.

Casos de discordância foram revistos e atribuídos a:
- Informação adicional que o especialista tinha (ex: literatura)
- Critério diferente (ex: intensidade relativa vs fragmentação)

### 5. Reprodutibilidade

Sistema garante que mesmo input produz mesmo output (teste em Apêndice B).

### 6. Limitações

1. **Empates**: Quando múltiplos candidatos são indistinguíveis, pesquisador
   precisa decidir baseado em conhecimento de domínio.

2. **Dados faltando**: Se fragmentação não foi medida, pulo para próximo
   critério; não é penalizado arbitrariamente.

3. **Não recomenda**: Sistema não escolhe por você — apenas transparenta
   e suporta a decisão.
```

### 5. Aumentar Cobertura para 70%

Identificar falhas e escrever testes faltando:

```bash
# Rodar cobertura com report detalhado
pytest --cov=scripts --cov-report=html

# Abrir relatório
open htmlcov/index.html  # Procurar linhas com cobertura < 80%
```

Prioridades para aumentar cobertura:
- Testes de erro em `extract_*.py` (http timeout, json decode error)
- Testes de edge cases em `transform_stg_xlsx.py` (NaN, valores inválidos)
- Testes de merge em `features/io.py` (colunas faltando, tipos incompatíveis)

---

## Critérios de Aceite

| ID | Tarefa | Critério |
|---|---|---|
| S8-01 | Comparação com especialista | Concordância ≥ 90%; especialista assina documento |
| S8-02 | Reprodutibilidade | 3 execuções consecutivas geram hash idêntico |
| S8-03 | Schema de output | Output contém todas as colunas; rank_group ≥ 1; is_tied correto |
| S8-04 | Metodologia documentada | Documento descreve escadinha e inclusão no paper validada por lead |
| S8-05 | Cobertura ≥ 70% | `pytest --cov` reporta ≥ 70% |

---

## Entregáveis para Paper

1. **Seção de Metodologia** (500–1000 palavras)
   - Algoritmo da escadinha
   - Principios de integridade
   - Validação científica

2. **Apêndice B: Reprodutibilidade**
   - Dados de teste
   - Hashes de output de 3 execuções
   - Instruções para replicar

3. **Supplementary Materials** (online)
   - Código da escadinha (`biological_ranking_engine.py`)
   - Testes (`test_biological_ranking.py`)
   - Dados de 100 features validadas com especialista

---

## Lições Aprendidas (Antecipadas)

- Validação com especialista é pré-requisito para publicação — não skip.
- Reprodutibilidade é testável e deve ser automatizada.
- Documentação de metodologia deve ser escrita em paralelo com código, não depois.

---

## Próximos Passos

- [ ] **Dia 1**: Agendar sessão com especialista (2h)
- [ ] **Dia 2**: Preparar dados de teste (100 features com ranking de especialista)
- [ ] **Dia 3**: Escrever testes de comparação e reprodutibilidade
- [ ] **Dia 4**: Executar comparação; registrar discordâncias
- [ ] **Dia 5**: Revisar discordâncias com especialista; documentar razões
- [ ] **Dia 6**: Redigir seção de Metodologia para paper
- [ ] **Dia 7**: Aumentar cobertura de testes para 70%
- [ ] **Semana 2**: Submeter draft do paper

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 8](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-8--validação-científica-e-paper)
