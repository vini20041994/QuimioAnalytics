# QuimioAnalytics

Banco de dados unificado e pipeline ETL para integrar dados analíticos do IST Ambiental com bases químicas públicas.

> Projeto Aplicado II · Ciência de Dados e Inteligência Artificial · SENAI Florianópolis · 2026/1

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Início em 5 Minutos](#início-em-5-minutos)
- [Configuração Rápida](#configuração-rápida)
- [Como Executar](#como-executar)
- [Pipelines Externos](#pipelines-externos)
- [Top 5 Candidatos](#top-5-candidatos)
- [Validação Rápida](#validação-rápida)
- [Erros Comuns](#erros-comuns)
- [Regras de Negócio](#regras-de-negócio)
- [Consultas Úteis](#consultas-úteis)
- [Status do Projeto](#status-do-projeto)
- [Equipe](#equipe)
- [Licença](#licença)

## Visão Geral

O IST Ambiental gera dados em alto volume por meio de planilhas internas de Identificação e Abundância. O QuimioAnalytics organiza esse fluxo em camadas de staging, processamento operacional e enriquecimento com referências externas.

Objetivos principais:

- Integrar dados internos sem perda de granularidade.
- Ranquear candidatos com abordagem probabilística (Top 5).
- Enriquecer compostos com fontes externas como PubChem, ChEBI e ChemSpider.
- Preparar base consistente para matching, análise e dashboard.

## Arquitetura

O banco usa três schemas lógicos no PostgreSQL:

| Schema | Função |
|--------|--------|
| `stg` | Persistência dos dados brutos e estágio intermediário |
| `core` | Verdade operacional normalizada (features, candidatos, replicatas, abundância) |
| `ref` | Referência externa (compostos, identificadores, taxonomia, usos e matches) |

Fluxo macro:

```text
Fontes internas/externas → stg → transformações → core / ref → ranking e análise
```

Entidades centrais de análise:

- `core.ingestion_batch`
- `core.feature`
- `core.sample_group`
- `core.replicate`
- `core.abundance_measurement`
- `core.candidate_identification`

## Estrutura do Repositório

```text
QuimioAnalytics/
├── database/
│   ├── schema_postgresql_mvp_entrega2.sql
│   └── migrations/
├── dados_brutos/
├── docs/
│   ├── Database/
│   └── ETL_Bases_Publicas/
├── logs/
├── scripts/
│   ├── extract/
│   ├── transform/
│   ├── load/
│   ├── run/
│   └── features/
├── staging/
├── docker-compose.yml
└── README.md
```

## Pré-requisitos

- Linux/macOS/WSL com acesso a terminal
- Python 3.10+ (recomendado: Python 3.12)
- Docker Engine + Docker Compose v2 (comando `docker compose`)
- Porta `5432` livre no host (ou ajuste no `docker-compose.yml`)
- Ambiente virtual Python
- Dependências Python: `pandas`, `pyarrow`, `psycopg2-binary`, `requests`, `openpyxl`, `lxml`, `scrapy`
- Internet para integração externa (PubChem, ChEBI e ChemSpider)

## Início em 5 Minutos

Copie e execute os comandos abaixo na raiz do projeto:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pandas pyarrow psycopg2-binary requests openpyxl lxml scrapy
docker compose up -d
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/schema_postgresql_mvp_entrega2.sql
```

Configure as variáveis de ambiente (mesmo terminal):

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=quimioanalytics
export DB_USER=quimio_user
export DB_PASS=quimio_pass_2024
```

Execute o fluxo completo:

```bash
python3 scripts/run/run_etl.py
python3 scripts/features/analitcs.py --load-core --batch-name TOP5_RANKING_MERGE
python3 scripts/run/run_etl_top5_external.py --top5 staging/top5_candidates.parquet
```

## Configuração Rápida

1. Criar e ativar o ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instalar dependências:

```bash
pip install pandas pyarrow psycopg2-binary requests openpyxl lxml scrapy
```

3. Subir o banco com Docker Compose:

```bash
docker compose up -d
```

4. Aplicar o schema principal:

```bash
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/schema_postgresql_mvp_entrega2.sql
```

5. (Opcional, recomendado) Aplicar migrations incrementais em ordem:

```bash
for f in database/migrations/*.sql; do
	echo "Aplicando $f"
	docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < "$f"
done
```

6. Configurar variáveis de ambiente:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=quimioanalytics
export DB_USER=quimio_user
export DB_PASS=quimio_pass_2024
```

## Como Executar

### 1) ETL principal (dados internos)

Entrada padrão: `dados_brutos/merge_resultado.csv`

```bash
python3 scripts/run/run_etl.py
```

Entrada interativa de planilhas:

```bash
python3 scripts/run/run_etl_user_input.py
```

### 2) Ranking Top 5

Gerar Top 5 em parquet:

```bash
python3 scripts/features/analitcs.py
```

Gerar Top 5 e persistir no schema `core`:

```bash
python3 scripts/features/analitcs.py --load-core --batch-name TOP5_RANKING_MERGE
```

### 3) Integração Top 5 com bases externas

Executa PubChem, ChEBI e ChemSpider usando o arquivo de Top 5 como entrada:

```bash
python3 scripts/run/run_etl_top5_external.py --top5 staging/top5_candidates.parquet
```

Selecionar fontes específicas:

```bash
python3 scripts/run/run_etl_top5_external.py --top5 staging/top5_candidates.parquet --sources pubchem chebi
```

Executar apenas PubChem:

```bash
python3 scripts/run/run_etl_top5_external.py --top5 staging/top5_candidates.parquet --sources pubchem
```

Observações operacionais:

- Se PubChem falhar por DNS (`Temporary failure in name resolution`), aguarde e tente novamente.
- O ChemSpider pode retornar 0 resultados para alguns nomes IUPAC complexos (limitação de scraping).

## Pipelines Externos

Execução consolidada por fonte:

- **PubChem:**

```bash
python3 scripts/run/run_etl_pubchem.py <arquivo_entrada>
```

- **ChEBI:**

```bash
python3 scripts/run/run_etl_chebi.py <arquivo_entrada>
```

- **ChemSpider:**

```bash
python3 scripts/run/run_etl_chemspider.py --file <arquivo_entrada>
python3 scripts/run/run_etl_chemspider.py --description Caffeine Aspirin
```

Documentação detalhada por fonte:

- `docs/ETL_Bases_Publicas/PUBCHEM.md`
- `docs/ETL_Bases_Publicas/ETL_CHEBI.md`
- `docs/ETL_Bases_Publicas/CHEMSPIDER.md`

## Top 5 Candidatos

| Parâmetro | Valor padrão |
|-----------|--------------|
| Entrada | `dados_brutos/merge_resultado.csv` |
| Saída | `staging/top5_candidates.parquet` |
| Script | `scripts/features/analitcs.py` |

Resumo do método probabilístico:

1. Normalização dos componentes técnicos: `mass_error_ppm`, fragmentação, isótopo e score original.
2. Score ponderado por critério analítico (erro de massa 40 %, fragmentação 30 %, score software 20 %, isótopo 10 %).
3. Ajuste pelo fator de abundância e estabilidade entre replicatas.
4. Conversão para probabilidade global via softmax.
5. Seleção dos 5 candidatos com maior probabilidade por feature.

## Validação Rápida

Após executar o fluxo, valide com:

```sql
SELECT COUNT(*) AS stg_identification_row FROM stg.identification_row;
SELECT COUNT(*) AS stg_abundance_row FROM stg.abundance_row;
SELECT COUNT(*) AS stg_curated_catalog_row FROM stg.curated_catalog_row;

SELECT COUNT(*) AS stg_pubchem FROM stg.pubchem_compound_raw;
SELECT COUNT(*) AS stg_chebi FROM stg.chebi_compound_raw;
SELECT COUNT(*) AS stg_chemspider FROM stg.chemspider_compound_raw;

SELECT COUNT(*) AS ref_curated_catalog_entry FROM ref.curated_catalog_entry;
SELECT COUNT(*) AS ref_chemical_class FROM ref.chemical_class;
SELECT COUNT(*) AS ref_compound_class FROM ref.compound_class;
SELECT COUNT(*) AS ref_external_import_log FROM ref.external_import_log;
```

Critério de sucesso mínimo:

- `stg.identification_row`, `stg.abundance_row` e `stg.curated_catalog_row` com registros > 0
- `staging/top5_candidates.parquet` gerado
- Pelo menos uma fonte externa carregada com sucesso (quando houver conectividade)

## Erros Comuns

1. Porta `5432` ocupada
	- Sintoma: container PostgreSQL não sobe.
	- Ação: liberar a porta ou remapear no `docker-compose.yml`.

2. `ON CONFLICT` sem constraint única
	- Sintoma: erro ao carregar dados externos.
	- Ação: aplicar as migrations em `database/migrations/` na ordem.

3. Falha DNS no PubChem
	- Sintoma: `Temporary failure in name resolution`.
	- Ação: problema de rede externo; repetir execução depois.

4. ChemSpider retornando 0
	- Sintoma: nenhuma linha em `stg.chemspider_compound_raw`.
	- Ação: esperado para parte dos compostos com nomes complexos.

## Regras de Negócio

**Tratamento de replicatas:** as replicatas biológicas são agregadas pela média, o que reduz ruído e favorece a comparabilidade no ranking probabilístico. A estratégia pode ser alterada para manter replicatas separadas quando a análise individual for necessária.

## Consultas Úteis

Contagem de registros por fonte:

```sql
SELECT COUNT(*) FROM stg.pubchem_compound_raw;
SELECT COUNT(*) FROM stg.chebi_compound_raw;
SELECT COUNT(*) FROM stg.chemspider_compound_raw;
```

Verificação rápida — PubChem:

```sql
SELECT pubchem_cid, molecular_formula, inchikey
FROM stg.pubchem_compound_raw
LIMIT 10;
```

## Status do Projeto

- [x] Diagnóstico das fontes internas
- [x] Modelagem lógica e schema físico (`stg`, `core`, `ref`)
- [x] ETL principal para planilhas internas
- [x] Ranking Top 5 com exportação e carga opcional em `core`
- [x] ETL por fonte para PubChem, ChEBI e ChemSpider
- [x] Runner integrado Top 5 → bases externas
- [ ] Matching consolidado `core` × `ref`
- [ ] Dashboard analítico

## Equipe

| Membro | Frente principal |
|--------|------------------|
| Guilherme da Silva Anselmo | Modelagem PostgreSQL e DER |
| Guilherme Zamboni Menegacio | ETL com Pandas |
| Vinícius Joacir dos Anjos | Integração com bases públicas |
| Samuel Silva de Rezende | Documentação e arquitetura |

## Licença

Uso acadêmico interno — SENAI Florianópolis — 2026.
