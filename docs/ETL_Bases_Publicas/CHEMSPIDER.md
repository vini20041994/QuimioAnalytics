# ChemSpider

## Visão Geral

Esta documentação descreve o pipeline ETL do ChemSpider no QuimioAnalytics.

Fluxo:
ChemSpider (scraping) -> staging/chemspider_raw.parquet -> staging/chemspider_trusted.parquet -> stg.chemspider_compound_raw

## Escopo do Pipeline

- Extract: coleta dados da página do composto no ChemSpider usando Scrapy
- Transform: padroniza nomes de colunas e tipos
- Load: grava na tabela stg.chemspider_compound_raw com upsert por chemspider_id
- Operação: pode rodar ponta a ponta com um único comando

## Execução

### Pré-requisitos

- Python 3.10+
- Ambiente virtual com pandas, pyarrow, scrapy e psycopg2-binary
- Banco PostgreSQL iniciado

Instalação de dependências:

```bash
source venv/bin/activate
pip install pandas pyarrow scrapy psycopg2-binary
```

### Pipeline completo

```bash
source venv/bin/activate
python3 run_etl_chemspider.py --file compound_list.txt
```

Outros exemplos:

```bash
python3 run_etl_chemspider.py --description Caffeine Aspirin
python3 run_etl_chemspider.py --compound_id 2424 171
```

### Execução passo a passo

```bash
python3 scripts/extract/extract_chemspider.py --file compound_list.txt
python3 scripts/transform/transform_chemspider.py
python3 scripts/load/load_chemspider.py
```

## Formatos de Entrada do Extract

O extrator aceita:

- --description: nomes/textos de compostos
- --compound_id: IDs ChemSpider (CSID)
- --file: arquivo com um item por linha (nome ou ID)

Exemplo:

```bash
python3 scripts/extract/extract_chemspider.py --description Caffeine
python3 scripts/extract/extract_chemspider.py --compound_id 2424
python3 scripts/extract/extract_chemspider.py --file chemspider_inputs.txt
```

## Dados Extraídos

Campos principais extraídos:

- ChemSpider_ID
- compound_name
- molecular_formula
- InChI
- InChIKey
- SMILES
- PubChem_CID
- ChEMBL_ID
- DrugBank_ID
- ChEBI_ID
- ChEBI_IDs
- HMDB_ID
- FooDB_ID
- LOTUS_ID
- ClassyFire_ID
- search_description

## Transformação

Arquivo: scripts/transform/transform_chemspider.py

A transformação:

- renomeia colunas para padrão snake_case
- converte colunas JSON (ex: chebi_ids)
- inclui source_name = ChemSpider
- salva em staging/chemspider_trusted.parquet

## Carga no Banco

Arquivo: scripts/load/load_chemspider.py

Características da carga:

- destino: stg.chemspider_compound_raw
- cria/usa batch_id em core.ingestion_batch
- upsert por chemspider_id com ON CONFLICT
- preenche json_payload para auditoria/reprocessamento
- preenche chebi_ids_text para leitura direta no SQL

## Estrutura da Tabela Staging

A tabela stg.chemspider_compound_raw contém, entre outras, as colunas:

- batch_id
- source_file_name
- chemspider_id (UNIQUE)
- compound_name
- search_description
- molecular_formula
- inchi
- inchikey
- canonical_smiles
- pubchem_cid
- chembl_id
- drugbank_id
- chebi_id
- chebi_ids (JSONB)
- hmdb_id
- foodb_id
- lotus_id
- classyfire_id
- chebi_ids_text
- json_payload
- loaded_at

Migration relacionada:

- database/migrations/007_update_chemspider_staging_table.sql

## Consultas Úteis

```sql
SELECT COUNT(*) AS total
FROM stg.chemspider_compound_raw;

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

SELECT
    chemspider_id,
    chebi_ids,
    chebi_ids_text
FROM stg.chemspider_compound_raw
WHERE chebi_ids IS NOT NULL
LIMIT 10;
```

## Troubleshooting

### Erro de tabela/coluna ausente

Aplique a migration:

```bash
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/migrations/007_update_chemspider_staging_table.sql
```

### Erro de dependência Scrapy

```bash
source venv/bin/activate
pip install scrapy
```

### Verificar estrutura da tabela

```bash
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics -c "\d stg.chemspider_compound_raw"
```

## Saída para Pipeline

O load imprime resumo em JSON:

```json
{
  "chemspider_loaded": 1,
  "errors": 0,
  "total": 1,
  "table": "stg.chemspider_compound_raw"
}
```
