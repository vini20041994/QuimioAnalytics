# QuimioAnalytics

Plataforma de integração e enriquecimento de dados de metabolômica com pipeline ETL modular, banco PostgreSQL em camadas e ranqueamento probabilístico de candidatos.

Projeto Aplicado II · Ciência de Dados e Inteligência Artificial · SENAI Florianópolis · 2026/1

## 1. O que este projeto resolve

O projeto organiza dados laboratoriais internos e integra bases químicas públicas para apoiar análise preditiva.

Objetivos principais:

- Padronizar a ingestão de planilhas internas de identificação e abundância.
- Produzir um Top 5 probabilístico por feature e aduto.
- Enriquecer compostos com PubChem, ChEBI e ChemSpider.
- Disponibilizar estrutura confiável para análises, APIs e dashboards.

## 2. Arquitetura do sistema

O banco PostgreSQL é organizado em três schemas:

| Schema | Papel |
|--------|-------|
| stg | Dados brutos e dados intermediários |
| core | Modelo operacional normalizado para análise |
| ref | Referências externas e metadados de enriquecimento |

Fluxo macro:

Fontes internas e externas -> staging -> transformações -> core e ref -> ranking e análise

## 3. Estrutura do repositório

Arquivos e pastas de maior interesse:

- [database](database): schema principal e migrations.
- [scripts](scripts): código ETL e orquestração.
- [scripts/run/run_pipeline_frontend.py](scripts/run/run_pipeline_frontend.py): orquestrador unificado.
- [scripts/run/run_full_stack_etl.py](scripts/run/run_full_stack_etl.py): wrapper de compatibilidade para full stack.
- [scripts/features/analytics.py](scripts/features/analytics.py): cálculo do ranking Top 5.
- [docs](docs): documentação detalhada por tema.
- [staging](staging): artefatos temporários e saídas intermediárias.

## 4. Pré-requisitos

- Linux, macOS ou WSL.
- Python 3.10+ (recomendado 3.12).
- Docker + Docker Compose.
- Acesso à internet para ETLs externos.

Dependências Python principais:

- pandas
- pyarrow
- psycopg2-binary
- requests
- openpyxl
- lxml
- scrapy

## 5. Início rápido

### 5.0 Primeira execução em uma chamada (recomendado)

Para máquina nova (Linux Debian/Ubuntu), use o script integrado:

	chmod +x scripts/run/install_system_prereqs.sh scripts/run/primeira_execucao.sh
	./scripts/run/primeira_execucao.sh --db-pass <SUA_SENHA>

Com integração externa (PubChem, ChEBI e ChemSpider):

	./scripts/run/primeira_execucao.sh --db-pass <SUA_SENHA> --with-external

Manual completo passo a passo:

- [docs/SETUP_PRIMEIRA_EXECUCAO.md](docs/SETUP_PRIMEIRA_EXECUCAO.md)

### 5.1 Configuração manual mínima

	python3 -m venv venv
	source venv/bin/activate
	pip install --upgrade pip
	pip install pandas pyarrow psycopg2-binary requests openpyxl lxml scrapy
	docker compose up -d
	docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/schema_postgresql_mvp_entrega2.sql

Variáveis de ambiente:

	export DB_HOST=localhost
	export DB_PORT=5432
	export DB_NAME=quimioanalytics
	export DB_USER=quimio_user
	export DB_PASS=<SUA_SENHA>

### 5.2 Execução recomendada com orquestrador unificado

Execução completa (setup + banco + pipeline):

	python3 scripts/run/run_pipeline_frontend.py --full-stack --load-core --run-external

Execução somente pipeline (ambiente já pronto):

	python3 scripts/run/run_pipeline_frontend.py --load-core --run-external

Simulação sem executar comandos:

	python3 scripts/run/run_pipeline_frontend.py --full-stack --dry-run --json

## 6. Formas de execução por cenário

### Cenário A: laboratório ou novo ambiente

Use full stack para preparar tudo em uma chamada:

	python3 scripts/run/run_pipeline_frontend.py --full-stack --load-core --run-external --db-pass <SUA_SENHA>

### Cenário B: banco e venv já existentes

Rode somente ETL interno + ranking + integração externa:

	python3 scripts/run/run_pipeline_frontend.py --load-core --run-external

### Cenário C: apenas ETL interno e Top 5

	python3 scripts/run/run_pipeline_frontend.py --load-core --no-external

### Cenário D: entrada customizada de planilhas

	python3 scripts/run/run_pipeline_frontend.py \
	  --identificacao /tmp/IDENTIFICACAO.xlsx \
	  --abundancia /tmp/ABUND.xlsx \
	  --compostos /tmp/Compostos_final.xlsx \
	  --overwrite-inputs --load-core

## 7. Orquestradores e compatibilidade

O projeto possui um ponto principal de execução:

- [scripts/run/run_pipeline_frontend.py](scripts/run/run_pipeline_frontend.py)

Compatibilidade com comandos antigos:

- [scripts/run/run_full_stack_etl.py](scripts/run/run_full_stack_etl.py) continua disponível e redireciona para o orquestrador unificado com o modo full stack.

## 8. Ranking Top 5

Script principal do ranking:

- [scripts/features/analytics.py](scripts/features/analytics.py)

Resumo do método:

1. Normalização dos componentes técnicos de score.
2. Score base pela média entre massa, fragmentação e isótopo.
3. Modulação pelo score do software normalizado.
4. Ajuste por abundância e estabilidade entre replicatas.
5. Softmax por feature_group.
6. Seleção dos 5 melhores candidatos por grupo.

Saída padrão:

- [staging/top5_candidates.parquet](staging/top5_candidates.parquet)

## 9. ETLs externos

Execução consolidada pelo orquestrador unificado:

	python3 scripts/run/run_pipeline_frontend.py --run-external --sources pubchem chebi chemspider

Execução por fonte:

- PubChem: [scripts/run/run_etl_pubchem.py](scripts/run/run_etl_pubchem.py)
- ChEBI: [scripts/run/run_etl_chebi.py](scripts/run/run_etl_chebi.py)
- ChemSpider: [scripts/run/run_etl_chemspider.py](scripts/run/run_etl_chemspider.py)

## 10. Validação rápida

Consultas SQL recomendadas após execução:

	SELECT COUNT(*) AS stg_identification_row FROM stg.identification_row;
	SELECT COUNT(*) AS stg_abundance_row FROM stg.abundance_row;
	SELECT COUNT(*) AS stg_curated_catalog_row FROM stg.curated_catalog_row;

	SELECT COUNT(*) AS stg_pubchem FROM stg.pubchem_compound_raw;
	SELECT COUNT(*) AS stg_chebi FROM stg.chebi_compound_raw;
	SELECT COUNT(*) AS stg_chemspider FROM stg.chemspider_compound_raw;

	SELECT COUNT(*) AS core_feature FROM core.feature;
	SELECT COUNT(*) AS core_candidate_identification FROM core.candidate_identification;

Critério mínimo:

- Dados internos carregados em stg.
- Top 5 gerado em staging.
- Carga em core realizada quando load-core estiver ativo.

## 11. Erros comuns e solução

1. Porta 5432 ocupada
- Sintoma: PostgreSQL não sobe.
- Solução: liberar ou remapear porta no compose.

2. DB_PASS ausente no modo full stack
- Sintoma: execução interrompe no início.
- Solução: exportar DB_PASS ou usar --db-pass.

3. Falha de DNS no PubChem
- Sintoma: erro de resolução de nome.
- Solução: repetir execução quando a rede estabilizar.

4. ChemSpider sem resultados
- Sintoma: zero linhas em stg.chemspider_compound_raw.
- Solução: comportamento esperado para parte dos compostos.

## 12. Documentação detalhada

Leia o índice de documentação em [docs/README.md](docs/README.md).

Guias importantes:

- [docs/Database/SETUP_DATABASE.md](docs/Database/SETUP_DATABASE.md)
- [docs/ETL_Bases_Publicas/PUBCHEM.md](docs/ETL_Bases_Publicas/PUBCHEM.md)
- [docs/ETL_Bases_Publicas/ETL_CHEBI.md](docs/ETL_Bases_Publicas/ETL_CHEBI.md)
- [docs/ETL_Bases_Publicas/CHEMSPIDER.md](docs/ETL_Bases_Publicas/CHEMSPIDER.md)
- [docs/Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md](docs/Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md)

## 13. Status do projeto

- ETL interno e staging operacional.
- Ranking Top 5 em produção no pipeline.
- Integração externa com PubChem, ChEBI e ChemSpider.
- Runner unificado para front-end e full stack.

## 14. Equipe

| Membro | Frente principal |
|--------|------------------|
| Guilherme da Silva Anselmo | Modelagem PostgreSQL e DER |
| Guilherme Zamboni Menegacio | ETL com Pandas |
| Vinícius Joacir dos Anjos | Integração com bases públicas |
| Samuel Silva de Rezende | Documentação e arquitetura |

## 15. Licença

Uso acadêmico interno. SENAI Florianópolis, 2026.
