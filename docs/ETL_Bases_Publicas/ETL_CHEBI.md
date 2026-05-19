# ETL ChEBI

## 1. Objetivo

Este guia descreve o pipeline ChEBI para extração, transformação e carga em staging, incluindo relações ontológicas e papéis químicos/biológicos.

Fluxo:

Entrada -> Extract -> Transform -> Load -> stg.chebi_compound_raw

## 2. Quando usar este pipeline

Use ChEBI quando você precisa:

- Enriquecer compostos com ontologia química.
- Carregar relações como is_a e has_role.
- Obter papéis químicos, papéis biológicos e aplicações.

## 3. Pré-requisitos

- Ambiente virtual ativo.
- Dependências instaladas: pandas, pyarrow, requests, psycopg2-binary, openpyxl.
- Banco PostgreSQL em execução.

Instalação rápida:

    source venv/bin/activate
    pip install pandas pyarrow requests psycopg2-binary openpyxl

## 4. Execução recomendada

### 4.1 Via orquestrador unificado

    python3 scripts/run/run_pipeline_frontend.py --run-external --sources chebi

### 4.2 Via runner da fonte

    python3 scripts/run/run_etl_chebi.py <arquivo_entrada>

Exemplos:

    python3 scripts/run/run_etl_chebi.py chebi_test_input.txt
    python3 scripts/run/run_etl_chebi.py data/staging/top10_external_input.csv

## 5. Execução etapa por etapa

    python3 scripts/extract/extract_chebi.py <arquivo_entrada>
    python3 scripts/transform/transform_chebi.py
    python3 scripts/load/load_chebi.py

## 6. Saídas e tabela de destino

Arquivos gerados:

- data/staging/chebi_raw.parquet
- data/staging/chebi_raw.csv
- data/staging/chebi_trusted.parquet

Tabela de carga:

- stg.chebi_compound_raw

Observação importante:

- O ETL padrão carrega automaticamente os artefatos em data/staging e a tabela stg.chebi_compound_raw.
- Carga em tabelas ref pode ser executada separadamente quando necessário.

## 7. Colunas ontológicas relevantes

Em stg.chebi_compound_raw:

- outgoing_relations (JSONB)
- incoming_relations (JSONB)
- chemical_role (JSONB)
- biological_roles (JSONB)
- applications (JSONB)

Também existem colunas de texto para leitura direta no SQL (sufixo _text).

## 8. Migrations relacionadas

- database/migrations/004_add_chebi_relations_to_staging.sql
- database/migrations/005_chebi_json_to_text_columns.sql
- database/migrations/006_remove_duplicates_add_unique_chebi_constraint.sql
- database/migrations/008_add_definition_to_chebi_staging.sql
- database/migrations/009_complete_chebi_staging_and_ref_constraints.sql

## 9. Validação rápida

    SELECT COUNT(*) AS total FROM stg.chebi_compound_raw;

    SELECT
        COUNT(outgoing_relations) AS com_outgoing,
        COUNT(incoming_relations) AS com_incoming,
        COUNT(chemical_role) AS com_role_quimico,
        COUNT(biological_roles) AS com_role_biologico,
        COUNT(applications) AS com_aplicacoes
    FROM stg.chebi_compound_raw;

    SELECT chebi_accession, chemical_role
    FROM stg.chebi_compound_raw
    WHERE chemical_role IS NOT NULL
    LIMIT 10;

## 10. Troubleshooting

1. Constraint/migration ausente

    for f in database/migrations/*.sql; do
      echo "Aplicando $f"
      docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < "$f"
    done

2. Ver estrutura da tabela

    docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics -c "\d stg.chebi_compound_raw"

3. Dependências ausentes

    source venv/bin/activate
    pip install pandas pyarrow requests psycopg2-binary openpyxl
