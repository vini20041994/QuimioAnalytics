# ETL ChEBI - Guia de Uso

## Implementação Completa

A ETL do ChEBI agora inclui suporte completo para **relações ontológicas** na tabela staging `stg.chebi_compound_raw`.

⚠️ **Importante**: Por padrão, o ETL carrega apenas na tabela **staging** (`stg.chebi_compound_raw`). As tabelas de referência (`ref.*`) não são preenchidas automaticamente.

### ✨ Novos Recursos

#### Colunas adicionadas em `stg.chebi_compound_raw`:

- **`outgoing_relations`** (JSONB): Relações ontológicas que partem do composto
  - Exemplos: `is_a`, `has_role`, `has_part`, `is_conjugate_acid_of`
  
- **`incoming_relations`** (JSONB): Relações ontológicas que chegam ao composto
  
- **`chemical_role`** (JSONB): Papéis químicos do composto
  - Exemplos: `acid`, `base`, `catalyst`, `solvent`
  
- **`biological_roles`** (JSONB): Papéis biológicos do composto
  - Exemplos: `metabolite`, `drug`, `toxin`, `hormone`
  
- **`applications`** (JSONB): Aplicações do composto
  - Exemplos: `pharmaceutical`, `pesticide`, `food additive`

### 🚀 Como Executar

#### Opção 1: Script Python Completo (Recomendado)

```bash
# Com arquivo de texto (uma linha por composto)
python3 run_etl_chebi.py compound_list.txt

# Com arquivo de teste
python3 run_etl_chebi.py chebi_test_input.txt

# Com Parquet do staging
python3 run_etl_chebi.py staging/identificacao_trusted.parquet
```

O script `run_etl_chebi.py` executa automaticamente as 3 fases:
1. **Extract**: Busca dados na API ChEBI/OLS
2. **Transform**: Normaliza e prepara dados
3. **Load**: Carrega em `stg.chebi_compound_raw` (staging apenas)
4. **Validação**: Mostra estatísticas dos dados carregados

#### Opção 2: Executar Fases Manualmente

```bash
# 1. Extract
python3 scripts/extract/extract_chebi.py chebi_test_input.txt

# 2. Transform
python3 scripts/transform/transform_chebi.py

# 3. Load (staging apenas)
python3 scripts/load/load_chebi.py
```

#### Opção 3: Carregar também em tabelas ref.* (opcional)

Se você precisar dos dados normalizados em `ref.*`, após executar o ETL completo:

```bash
# Carregar em ref.external_compound e tabelas relacionadas
python3 load_chebi_to_ref.py
```

Este script:
- Lê `staging/chebi_trusted.parquet`
- Carrega em todas as tabelas `ref.*`
- Normaliza papéis, aplicações e identificadores

### 📊 Consultas Úteis

#### Ver estatísticas das relações ontológicas:

```sql
SELECT 
    COUNT(*) as total_registros,
    COUNT(outgoing_relations) as com_outgoing,
    COUNT(incoming_relations) as com_incoming,
    COUNT(chemical_role) as com_role_quimico,
    COUNT(biological_roles) as com_role_biologico,
    COUNT(applications) as com_aplicacoes
FROM stg.chebi_compound_raw;
```

#### Buscar compostos com relações específicas:

```sql
-- Compostos que são ácidos
SELECT chebi_accession, chemical_role
FROM stg.chebi_compound_raw
WHERE chemical_role @> '["acid"]'::jsonb;

-- Compostos com relações "is_a"
SELECT 
    chebi_accession,
    jsonb_array_length(outgoing_relations) as num_relacoes
FROM stg.chebi_compound_raw
WHERE outgoing_relations::text LIKE '%is_a%';
```

#### Explorar hierarquia ontológica:

```sql
-- Ver todas as relações de um composto específico
SELECT 
    chebi_accession,
    outgoing_relations,
    incoming_relations
FROM stg.chebi_compound_raw
WHERE chebi_accession = 'CHEBI:15365';
```

### 📁 Estrutura de Dados

#### Exemplo de `outgoing_relations`:
```json
[
  "aspirin (CHEBI:15365) is_a salicylate (CHEBI:26605)",
  "aspirin (CHEBI:15365) has_role antipyretic (CHEBI:35493)"
]
```

#### Exemplo de `chemical_role`:
```json
["non-steroidal anti-inflammatory drug", "antipyretic", "antiplatelet drug"]
```

### 🗄️ Tabelas Afetadas

**Carregadas automaticamente:**
- **`stg.chebi_compound_raw`**: Dados brutos com relações ontológicas em colunas JSONB dedicadas

**Disponíveis para carregamento manual (via `load_chebi_ref()`):**
- `ref.external_compound`: Compostos normalizados
- `ref.external_identifier`: IDs secundários, IUPAC names, sinônimos
- `ref.compound_property`: Massas e definições
- `ref.chemical_class`: Papéis químicos e biológicos (normalizados)
- `ref.use_application`: Aplicações (normalizadas)

### 🔧 Arquivos Modificados

1. **`database/migrations/004_add_chebi_relations_to_staging.sql`**
   - Adiciona colunas JSONB para relações ontológicas
   - Cria índices GIN para consultas eficientes

2. **`database/migrations/005_chebi_json_to_text_columns.sql`**
  - Adiciona colunas de texto legível (`*_text`) para facilitar leitura no banco
  - Realiza backfill dos registros já carregados

3. **`database/migrations/006_remove_duplicates_add_unique_chebi_constraint.sql`**
  - Remove duplicatas antigas por `chebi_accession`
  - Adiciona constraint `UNIQUE (chebi_accession)`

4. **`scripts/load/load_chebi.py`**
  - Estrutura alinhada ao padrão do `load_pubchem.py`
  - Cria/usa `batch_id` em `core.ingestion_batch`
  - Executa upsert com `ON CONFLICT (chebi_accession)`
  - Preenche tanto colunas JSONB quanto colunas texto (`*_text`)

5. **`run_etl_chebi.py`**
   - Script Python completo para ETL com validação

### ⚠️ Notas Importantes

- Os índices GIN permitem busca eficiente em campos JSONB
- Relações ontológicas são armazenadas como arrays de strings formatadas
- O campo `json_payload` mantém os dados brutos para auditoria e reprocessamento
- As colunas `*_text` facilitam leitura direta no SQL sem parse de JSON
- A constraint de unicidade evita duplicação de registros por `chebi_accession`
