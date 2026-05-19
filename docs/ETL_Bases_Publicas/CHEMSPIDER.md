# ETL ChemSpider

## 1. Objetivo

Este guia descreve o pipeline ChemSpider no QuimioAnalytics para extração por scraping, transformação e carga em staging.

Fluxo:

Entrada -> Extract (Scrapy) -> Transform -> Load -> stg.chemspider_compound_raw

## 2. Quando usar este pipeline

Use ChemSpider quando você precisa:

- Enriquecer compostos por CSID e identificadores associados.
- Complementar cobertura de fontes externas para compostos sem match em outras bases.

## 3. Pré-requisitos

- Ambiente virtual ativo.
- Dependências instaladas: pandas, pyarrow, scrapy, psycopg2-binary.
- Banco PostgreSQL em execução.

Instalação rápida:

    source venv/bin/activate
    pip install pandas pyarrow scrapy psycopg2-binary

## 4. Execução recomendada

### 4.1 Via orquestrador unificado

    python3 scripts/run/run_pipeline_frontend.py --run-external --sources chemspider

### 4.2 Via runner da fonte

    python3 scripts/run/run_etl_chemspider.py --file chemspider_inputs.txt

Exemplos alternativos:

    python3 scripts/run/run_etl_chemspider.py --description Caffeine Aspirin
    python3 scripts/run/run_etl_chemspider.py --compound_id 2424 171

## 5. Execução etapa por etapa

    python3 scripts/extract/extract_chemspider.py --file chemspider_inputs.txt
    python3 scripts/transform/transform_chemspider.py
    python3 scripts/load/load_chemspider.py

## 6. Entradas aceitas

- --description: nomes de compostos.
- --compound_id: IDs ChemSpider.
- --file: arquivo texto com um item por linha.

## 7. Saídas e tabela de destino

Arquivos gerados:

- data/staging/chemspider_raw.parquet
- data/staging/chemspider_trusted.parquet

Tabela de carga:

- stg.chemspider_compound_raw

Migração relacionada:

- database/migrations/007_update_chemspider_staging_table.sql

## 8. Campos principais extraídos

- chemspider_id
- compound_name
- molecular_formula
- inchi
- inchikey
- canonical_smiles
- pubchem_cid
- chembl_id
- drugbank_id
- chebi_id
- chebi_ids
- hmdb_id
- foodb_id
- lotus_id
- classyfire_id

## 9. Validação rápida

    SELECT COUNT(*) AS total FROM stg.chemspider_compound_raw;

    SELECT
        chemspider_id,
        compound_name,
        molecular_formula,
        inchikey,
        pubchem_cid,
        loaded_at
    FROM stg.chemspider_compound_raw
    ORDER BY loaded_at DESC
    LIMIT 20;

## 10. Troubleshooting

1. Erro de coluna/tabela

    docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/migrations/007_update_chemspider_staging_table.sql

2. Dependência Scrapy ausente

    source venv/bin/activate
    pip install scrapy

3. Sem resultados para alguns compostos

- Isso pode acontecer com descrições ambíguas ou nomes muito complexos.
- Tente por compound_id quando disponível.

4. Ver estrutura da tabela

    docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics -c "\d stg.chemspider_compound_raw"
