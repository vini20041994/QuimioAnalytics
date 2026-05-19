# ETL PubChem

## 1. Objetivo

Este guia explica como executar o enriquecimento com PubChem no QuimioAnalytics, desde a entrada até a carga em staging.

Fluxo:

Entrada -> Extract -> Transform -> Load -> stg.pubchem_compound_raw

## 2. Quando usar este pipeline

Use PubChem quando você precisa:

- Resolver identificadores químicos (CID, InChIKey, SMILES).
- Enriquecer propriedades físico-químicas.
- Adicionar sinônimos e metadados externos.

## 3. Pré-requisitos

- Ambiente virtual ativo.
- Dependências instaladas: pandas, pyarrow, requests, psycopg2-binary, openpyxl.
- Banco PostgreSQL em execução.

Instalação rápida:

    source venv/bin/activate
    pip install pandas pyarrow requests psycopg2-binary openpyxl

## 4. Execução recomendada

### 4.1 Via orquestrador unificado

    python3 scripts/run/run_pipeline_frontend.py --run-external --sources pubchem

### 4.2 Via runner da fonte

    python3 scripts/run/run_etl_pubchem.py <arquivo_entrada>

Exemplos:

    python3 scripts/run/run_etl_pubchem.py compound_list.txt
    python3 scripts/run/run_etl_pubchem.py staging/top10_external_input.csv

## 5. Execução etapa por etapa

    python3 scripts/extract/extract_pubchem.py <arquivo_entrada>
    python3 scripts/transform/transform_pubchem.py
    python3 scripts/load/load_pubchem.py

## 6. Entradas aceitas

- TXT: um composto por linha.
- CSV: colunas como nome, fórmula, InChIKey ou SMILES.
- Parquet: arquivos de staging já processados.

## 7. Estratégia de busca

O extractor tenta, em ordem:

1. InChIKey
2. SMILES
3. Nome do composto
4. Fórmula molecular
5. Sinônimos

Isso melhora a taxa de acerto em entradas heterogêneas.

## 8. Saídas e tabela de destino

Arquivos gerados:

- staging/pubchem_raw.parquet
- staging/pubchem_raw.csv
- staging/pubchem_trusted.parquet
- logs/pubchem_extract_YYYYMMDD_HHMMSS.log

Tabela de carga:

- stg.pubchem_compound_raw

Migração relacionada:

- database/migrations/001_update_pubchem_table.sql

## 9. Validação rápida

    SELECT COUNT(*) AS total FROM stg.pubchem_compound_raw;

    SELECT
        pubchem_cid,
        molecular_formula,
        molecular_weight,
        inchikey,
        search_method,
        loaded_at
    FROM stg.pubchem_compound_raw
    ORDER BY loaded_at DESC
    LIMIT 10;

## 10. Performance

Configuração operacional padrão:

- Limite alvo: 5 requests por segundo
- Retry: 3 tentativas
- Delay: 200 ms

## 11. Troubleshooting

1. Dependências ausentes

    source venv/bin/activate
    pip install pandas pyarrow requests psycopg2-binary openpyxl

2. Banco indisponível

    python3 scripts/manage_db.py start
    python3 scripts/manage_db.py status

3. Problemas de rede/DNS

- Tente novamente em outro momento.
- Se necessário, aumente timeout e delay no extractor.

4. Estrutura da tabela

    docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics -c "\d stg.pubchem_compound_raw"
