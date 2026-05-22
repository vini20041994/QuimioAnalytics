# Sprint 4 — Integridade e Idempotência de Banco

**Status**: ✅ Done  
**Capacidade**: 28 pontos  
**Objetivo**: Garantir que reprocessamento de dados não cria duplicatas, que identificadores são padronizados entre sistemas e que há índices para suportar queries eficientes.

---

## Contexto

Atualmente o banco de dados é vulnerável a corrupção silenciosa:
- Reprocessar um extrator duplica registros (sem ON CONFLICT)
- Nomes de fonte não são padronizados entre loaders (`foodb.py` vs seed SQL)
- Sem índices de candidatos, queries de ranking ficam O(n²)
- Sem soft-delete, auditoria fica impossível

Sprint 4 implementa garantias de integridade que são pré-requisitos para Sprints 5–8.

### Andamento Atual (22/05/2026)

- Concluído: padronização de `source_name`, alinhamento de `ON CONFLICT`, timeouts e tratamento de erros específicos, índice de candidatos, `updated_at` e `deleted_at`.
- Concluído: migration 010 executada em banco limpo e reaplicada em banco inicializado sem erro.
- Concluído: `EXPLAIN ANALYZE` validou uso de `idx_candidate_by_feature_rank` em consulta de candidatos.

### Evidências Técnicas (execução local)

- Cenário 1 (banco limpo): `schema_postgresql_mvp_entrega2.sql` aplicado e `010_integridade_idempotencia_ref_core.sql` executada com sucesso.
- Cenário 2 (banco inicializado): rerun da `010_integridade_idempotencia_ref_core.sql` executado sem falha.
- Performance: `EXPLAIN ANALYZE` mostrou `Bitmap Index Scan on idx_candidate_by_feature_rank` para filtro por `feature_id`.

---

## Principais Pontos Levantados

### 1. Nomes de fonte externa inconsistentes
- **Arquivo**: `database/schema_postgresql_mvp_entrega2.sql`, `scripts/load/load_foodb.py` etc.
- **Problema**: Seed SQL tem `'FooDB'`, mas loader usa `'foodb'` ou `'FOODB'`
- **Impacto**: `get_source_id()` falha; fallback manual quebra idempotência

### 2. Sem constraints únicos em ref (external_identifier, compound_property, cross_reference)
- **Problema**: Reprocessar PubChem extrai 10 K registros; inserem mais 10 K (sem deduplicação)
- **Impacto**: Tabela `ref` cresce 2× a cada rerun; banco fica 10 GB em vez de 5 GB

### 3. ON CONFLICT mal configurado ou ausente
- **Arquivo**: `scripts/load/external_load_utils.py`
- **Problema**: `ON CONFLICT DO NOTHING` sem especificar a coluna única
- **Impacto**: Insere duplicata porque conflito não é detectado

### 4. Sem índice para query de candidatos
- **Problema**: Pipeline busca "ranking de candidatos candidatos por feature" — sem índice, é scan completo
- **Impacto**: Query leva minutos em lugar de milissegundos

### 5. Sem soft-delete nem updated_at
- **Problema**: Histórico de quando dado foi atualizado fica inacessível
- **Impacto**: Impossível auditar "este resultado mudou depois de eu revisá-lo?"

### 6. Tratamento de erro genérico em extratores legados
- **Problema**: `except Exception:` oculta erro real
- **Impacto**: Timeout em API aparece como "Script falhou" sem contexto

### 7. Sem timeout em requests HTTP
- **Problema**: Se API não responde, extrator fica pendurado indefinidamente
- **Impacto**: Pipeline inteiro trava

---

## O Que Deve Ser Feito

### 1. Padronizar `source_name` em TODAS as fontes

```sql
-- Seed SQL deve ter:
INSERT INTO ref.external_source (source_name, api_url) VALUES
  ('PubChem', 'https://pubchem.ncbi.nlm.nih.gov/'),
  ('ChEBI', 'https://www.ebi.ac.uk/chebi/'),
  ('ChemSpider', 'https://www.chemspider.com/'),
  ('HMDB', 'https://hmdb.ca/'),
  ('FooDB', 'https://foodb.ca/'),
  ('LOTUS', 'https://lotus.naturalproducts.net/'),
  ('ClassyFire', 'https://classyfire.wishartlab.com/'),
  ('User Input', NULL);
```

Todos os loaders (`load_foodb.py`, `load_hmdb.py`, etc.) usam **exatamente** estes nomes.

### 2. Criar Migration 010 — Constraints Únicos

```sql
-- database/migrations/010_integridade_idempotencia_ref_core.sql
ALTER TABLE ref.external_identifier 
  ADD CONSTRAINT uk_external_identifier 
  UNIQUE (external_source_id, external_id);

ALTER TABLE ref.compound_property 
  ADD CONSTRAINT uk_compound_property 
  UNIQUE (compound_id, property_name, property_value);

ALTER TABLE ref.compound_cross_reference 
  ADD CONSTRAINT uk_compound_cross_reference 
  UNIQUE (compound_id, external_source_id, external_id);

-- Índice para queries de candidatos
CREATE INDEX idx_candidate_by_feature_rank 
  ON core.candidate_identification(feature_id, rank_group, is_tied);
```

### 3. Alinhar ON CONFLICT

```python
# scripts/load/external_load_utils.py
def upsert_identifier(conn, df):
    buffer = io.StringIO()
    df[['compound_id', 'external_source_id', 'external_id']].to_csv(buffer, ...)
    
    cursor.copy_from(buffer, 'ref.external_identifier', ...)
    
    # SQL garante idempotência:
    cursor.execute("""
        INSERT INTO ref.external_identifier (compound_id, external_source_id, external_id)
        SELECT * FROM ... 
        ON CONFLICT (external_source_id, external_id) 
        DO NOTHING;
    """)
```

### 4. Normalizar tratamento de erro

```python
# scripts/extract/extract_foodb.py — ANTES:
try:
    r = requests.get(url)
    data = json.loads(r.text)
except Exception as e:
    print(f"Erro: {e}")  # ❌ Genérico

# DEPOIS:
try:
    r = requests.get(url, timeout=30)  # ✓ Timeout explícito
    r.raise_for_status()
    data = r.json()
except requests.Timeout:
    logger.error(f"Timeout ao chamar {url}", exc_info=True)
    raise
except requests.HTTPError as e:
    logger.error(f"HTTP {e.response.status_code}: {url}", exc_info=True)
    raise
except json.JSONDecodeError as e:
    logger.error(f"JSON inválido de {url}: {e}", exc_info=True)
    raise
```

### 5. Adicionar soft-delete e updated_at

```sql
-- Adicionar colunas às tabelas CORE
ALTER TABLE core.feature 
  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

ALTER TABLE core.candidate_identification 
  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Índice para querys de soft-delete
CREATE INDEX idx_feature_not_deleted 
  ON core.feature(id) WHERE deleted_at IS NULL;
```

---

## Critérios de Aceite

| ID | Tarefa | Critério |
|---|---|---|
| S4-01 | Padronizar source_name | `get_source_id()` encontra todas as fontes; sem fallback |
| S4-02/03/04 | Constraints únicos | Migration 010 aplica sem erro; rerun não falha |
| S4-05 | ON CONFLICT alinhado | ON CONFLICT referencia coluna de constraint |
| S4-06 | Erros específicos | Capturas para `requests.Timeout`, `HTTPError`, `JSONDecodeError` |
| S4-07 | Timeouts explícitos | `timeout=30` em todas as chamadas HTTP |
| S4-08 | Idempotência validada | Rodar migrations em banco limpo e já-inicializado — ambos com sucesso |
| S4-09 | Índice de candidatos | `EXPLAIN ANALYZE` mostra Index Scan para Ranking de candidatos |
| S4-10 | Soft-delete + updated_at | Colunas existem em `core.feature` e `core.candidate_identification` |

---

## Lições Aprendidas (Antecipadas)

- Constraints únicos no banco não são opcionais — são o contrato entre extrator e banco.
- Timeout deve ser **explícito e curto** (~30s máximo) para evitar travamento.
- ON CONFLICT precisa da coluna exata do constraint — caso contrário, falha silenciosa.

---

## Próximos Passos

- [x] **Dia 1**: Revisar seed SQL e alinhar nomes de fonte
- [x] **Dia 2**: Criar migration 010 com constraints únicos
- [x] **Dia 3**: Refatorar loaders para usar ON CONFLICT correto
- [x] **Dia 4**: Adicionar timeout e tratamento de erro aos extratores legados
- [x] **Dia 5**: Rodar testes de idempotência (Sprint 3)
- [x] **Dia 6**: Validar índices com EXPLAIN ANALYZE
- [x] **Dia 7**: Adicionar soft-delete e updated_at

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 4](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-4--integridade-e-idempotência-de-banco)
