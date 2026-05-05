# PubChem

## Visão Geral

Esta documentação consolida o fluxo de extração, transformação e carga do PubChem no QuimioAnalytics.

Fluxo: API PubChem -> staging/pubchem_raw.parquet -> staging/pubchem_trusted.parquet -> stg.pubchem_compound_raw

## Escopo do Pipeline

- Extract: consulta a API do PubChem com fallback entre múltiplos identificadores
- Transform: normaliza nomes de colunas, tipos e estruturas como sinônimos e payloads
- Load: grava os dados na tabela stg.pubchem_compound_raw com suporte a JSONB
- Operação: pode rodar ponta a ponta com um único comando ou etapa por etapa

## Execução

### Pré-requisitos

- Python 3.8+
- Ambiente virtual com pandas, pyarrow, requests, psycopg2-binary e openpyxl
- Banco PostgreSQL iniciado via docker-compose ou scripts/manage_db.py

### Pipeline completo

```bash
source venv/bin/activate
python3 run_etl_pubchem.py <arquivo_de_entrada>
```

Exemplos:

```bash
python3 run_etl_pubchem.py compound_list.txt
python3 run_etl_pubchem.py compound_list_test.txt
python3 run_etl_pubchem.py staging/identificacao_trusted.parquet
```

### Execução passo a passo

```bash
python3 scripts/extract/extract_pubchem.py compound_list.txt
python3 scripts/transform/transform_pubchem.py
python3 scripts/load/load_pubchem.py
```

## Formatos de Entrada

### TXT

Uma linha por composto:

```text
Glucose
Caffeine
Aspirin
```

### CSV

Arquivos com colunas como nome, fórmula, InChIKey e SMILES:

```csv
compound_name,molecular_formula,inchikey,smiles
Glucose,C6H12O6,WQZGKKKJIJFFOK-GASJEMHNSA-N,C(C1C(C(C(C(O1)O)O)O)O)O
Caffeine,C8H10N4O2,RYYVLZVUVIJVGH-UHFFFAOYSA-N,CN1C=NC2=C1C(=O)N(C(=O)N2C)C
```

### Parquet

Também aceita arquivos já gerados no staging, como staging/identificacao_trusted.parquet.

## Estratégia de Busca

O extrator tenta localizar compostos com fallback nesta ordem:

1. InChIKey
2. SMILES
3. Nome do composto
4. Fórmula molecular
5. Sinônimos

Isso melhora a taxa de acerto quando a entrada não possui um identificador canônico.

## Dados Extraídos

### Identificadores

- CID
- InChI
- InChIKey
- Canonical SMILES
- Isomeric SMILES
- Nome IUPAC

### Propriedades

- Fórmula molecular
- Peso molecular
- Massa exata
- XLogP
- TPSA
- Complexidade
- Carga

### Contadores estruturais

- HBondDonorCount
- HBondAcceptorCount
- RotatableBondCount
- HeavyAtomCount

### Dados adicionais

- Até 15 sinônimos por composto
- Classificação química quando disponível
- Descrição textual do PubChem
- Payload bruto da API para auditoria e reprocessamento

## Arquivos Gerados

### Durante o extract

- staging/pubchem_raw.parquet
- staging/pubchem_raw.csv
- logs/pubchem_extract_YYYYMMDD_HHMMSS.log

### Durante o transform

- staging/pubchem_trusted.parquet

### Após o load

- Registros persistidos em stg.pubchem_compound_raw

## Estrutura no Banco

A carga é feita na tabela stg.pubchem_compound_raw, que armazena:

- metadados da extração
- identificadores químicos
- propriedades moleculares e físico-químicas
- sinônimos e classificação em JSONB
- payload original da API

Índices principais:

- pubchem_cid
- inchikey
- molecular_formula

Migração relacionada:

- database/migrations/001_update_pubchem_table.sql

## Consultas Úteis

```sql
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

SELECT
    search_method,
    COUNT(*) AS total
FROM stg.pubchem_compound_raw
GROUP BY search_method
ORDER BY total DESC;

SELECT
    pubchem_cid,
    synonym_count,
    synonyms
FROM stg.pubchem_compound_raw
WHERE pubchem_cid = 1983;
```

## Performance e Limites

- Limite alvo: 5 requisições por segundo
- Retry automático: 3 tentativas
- Delay entre requisições: 200 ms por padrão

Estimativas observadas:

- 10 compostos: 2 a 3 minutos
- 50 compostos: 10 a 15 minutos
- 100 compostos: 20 a 30 minutos
- 1000 compostos: 3 a 5 horas

Para lotes grandes, prefira execução noturna ou processamento em blocos menores.

## Troubleshooting

### Dependências ausentes

```bash
source venv/bin/activate
pip install pandas pyarrow requests psycopg2-binary openpyxl
```

### Banco indisponível

```bash
python3 scripts/manage_db.py start
python3 scripts/manage_db.py status
```

### Timeout ou instabilidade de rede

Ajuste as constantes no extrator para aumentar timeout e reduzir agressividade de chamadas.

- TIMEOUT: aumentar de 15 para 30
- RATE_LIMIT_DELAY: aumentar de 0.2 para 0.3

### Validar a estrutura da tabela

```bash
docker exec quimio_postgres psql -U quimio_user -d quimioanalytics -c "\d stg.pubchem_compound_raw"
```

### Reaplicar migração

```bash
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/migrations/001_update_pubchem_table.sql
```

## Integração com o Pipeline Principal

Fluxo recomendado:

1. Rodar o ETL principal com run_etl.py
2. Extrair identificadores ou fórmulas de stg.identification_row
3. Executar o enriquecimento com run_etl_pubchem.py
4. Validar o conteúdo carregado na staging do PubChem

Exemplo:

```bash
python3 run_etl.py

docker exec quimio_postgres psql -U quimio_user -d quimioanalytics -c "
COPY (
    SELECT DISTINCT molecular_formula
    FROM stg.identification_row
    WHERE molecular_formula IS NOT NULL
    LIMIT 100
) TO STDOUT
" > formulas_to_enrich.txt

python3 run_etl_pubchem.py formulas_to_enrich.txt
```

## Arquivos Relacionados

- run_etl_pubchem.py
- scripts/extract/extract_pubchem.py
- scripts/transform/transform_pubchem.py
- scripts/load/load_pubchem.py
- database/migrations/001_update_pubchem_table.sql
- docs/SETUP_DATABASE.md

## Próximos Passos

1. Enriquecer compostos já presentes em stg.identification_row
2. Popular camadas de referência além do staging
3. Criar views de matching entre dados locais e fontes externas
4. Estender o padrão para HMDB, ChEBI e FooDB