# QuimioAnalytics

Plataforma de integração e enriquecimento de dados de metabolômica com pipeline ETL modular, banco PostgreSQL em camadas e ranqueamento probabilístico de candidatos.

Projeto Aplicado II · Ciência de Dados e Inteligência Artificial · SENAI Florianópolis · 2026/1

## 1. O que este projeto resolve

O projeto organiza dados laboratoriais internos e integra bases químicas públicas para apoiar análise preditiva.

Objetivos principais:

- Padronizar a ingestão de planilhas internas de identificação e abundância.
- Produzir um Top 10 probabilístico por feature e aduto.
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

Fontes internas e externas -> data/staging -> transformações -> core e ref -> ranking e análise

## 3. Estrutura do repositório

Arquivos e pastas de maior interesse:

- [database](database): schema principal e migrations.
- [scripts](scripts): código ETL e orquestração.
- [scripts/run/run_pipeline_frontend.py](scripts/run/run_pipeline_frontend.py): orquestrador unificado.
- [scripts/run/run_full_stack_etl.py](scripts/run/run_full_stack_etl.py): wrapper de compatibilidade para full stack.
- [scripts/features/analytics.py](scripts/features/analytics.py): cálculo do ranking Top 10.
- [docs](docs): documentação detalhada por tema.
- [data](data): entradas brutas e artefatos intermediários do pipeline.
- [runtime](runtime): logs e backups operacionais.

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

Execução completa (setup + banco + pipeline + externas):

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps

Ou sem integrações externas (mais rápido):

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps --no-external

Simulação sem executar comandos:

	python3 scripts/run/run_pipeline_frontend.py --full-stack --dry-run --json

## 6. Formas de execução por cenário

### Cenário A: laboratório ou novo ambiente (com integrações externas)

Use full stack para preparar tudo e executar ETL completo com bases externas:

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps

### Cenário A-B: laboratório ou novo ambiente (sem integrações externas - mais rápido)

Setup completo sem consultar bases públicas:

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps --no-external

### Cenário B: banco e venv já existentes (com externas)

Rode somente ETL + ranking + integrações externas (padrão):

	python3 scripts/run/run_pipeline_frontend.py --load-core

### Cenário C: apenas ETL interno e Top 10

Sem consultar bases externas:

	python3 scripts/run/run_pipeline_frontend.py --load-core --no-external

### Cenário D: entrada customizada de planilhas (com externas)

	python3 scripts/run/run_pipeline_frontend.py \
	  --identificacao /tmp/IDENTIFICACAO.xlsx \
	  --abundancia /tmp/ABUND.xlsx \
	  --compostos /tmp/Compostos_final.xlsx \
	  --overwrite-inputs --load-core

### Cenário E: apenas PubChem (não ChEBI ou ChemSpider)

	python3 scripts/run/run_pipeline_frontend.py --load-core --run-external --sources pubchem

## 7. Orquestradores e compatibilidade

O projeto possui um ponto principal de execução:

- [scripts/run/run_pipeline_frontend.py](scripts/run/run_pipeline_frontend.py)

Wrapper de compatibilidade (recomendado para produção):

- [scripts/run/run_full_stack_etl.py](scripts/run/run_full_stack_etl.py)
  - Automáticamente inclui `--full-stack` e `--run-external` com PubChem, ChEBI e ChemSpider
  - Pode ser desabilitado com `--no-external` para modo rápido
  - Suporta customização de sources com `--run-external --sources fonte1 fonte2`

## 8. Ranking Top 10

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

- [data/staging/top10_candidates.parquet](data/staging/top10_candidates.parquet)

## 9. ETLs externos (PubChem, ChEBI, ChemSpider)

O projeto integra automaticamente dados de três bases de referência química pública após o ranking Top 10.

### 9.1 Execução com integrações externas

**Opção A: Via wrapper full stack (recomendado)**

O wrapper `run_full_stack_etl.py` agora inclui integrações externas **por padrão**:

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps

Isto equivale a:

	python3 scripts/run/run_pipeline_frontend.py --full-stack --db-pass QuimioAnalytics --skip-db-init --skip-deps --run-external --sources pubchem chebi chemspider

**Opção B: Desabilitar integrações externas**

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps --no-external

**Opção C: Customizar fontes**

	python3 scripts/run/run_full_stack_etl.py --db-pass QuimioAnalytics --skip-db-init --skip-deps --run-external --sources pubchem chebi

### 9.2 Fluxo de processamento (com externas)

1. **Extract** → Leitura de planilhas xlsx (IDENTIFICACAO, ABUND, Compostos)
2. **Transform** → Normalização e validação de dados
3. **Load** → Persistência no schema stg e geração de artefatos em data/staging
4. **Ranking Top 10** → Seleção de 10 melhores candidatos por feature_group
5. **ETL Externo** (ativado com `--run-external`)
   - Prepara entrada normalizada (top10_external_input.csv)
   - Consulta PubChem API para CIDs, propriedades, sinônimos
   - Consulta ChEBI para compostos e ontologia
   - Consulta ChemSpider para IDs complementares
   - Carrega resultados em tabelas de referência (stg.pubchem_compound_raw, etc)

### 9.3 Execução por fonte individual

Se preferir rodar apenas uma base:

- **PubChem**: `python3 scripts/run/run_etl_pubchem.py`
- **ChEBI**: `python3 scripts/run/run_etl_chebi.py`
- **ChemSpider**: `python3 scripts/run/run_etl_chemspider.py`

Ou via orquestrador:

	python3 scripts/run/run_pipeline_frontend.py --run-external --sources pubchem

### 9.4 Tempo estimado

- ETL Interno: ~12 segundos
- Ranking: ~9 segundos
- **ETL Externo: 20-120 minutos** (depende da quantidade de compostos e latência de rede)

Acompanhe progresso em tempo real:

	tail -f runtime/logs/*.log | grep "Processando\|Sucesso"

### 9.5 Bases de dados integradas

| Base | Cobertura | Implementação |
|------|-----------|----------------|
| PubChem | Compostos por nome, fórmula ou CID | REST API |
| ChEBI | Ontologia e relações químicas | REST API + XML parsing |
| ChemSpider | IDs complementares e propriedades | Web scraping com Scrapy |

Documentação individual:

- [docs/ETL_Bases_Publicas/PUBCHEM.md](docs/ETL_Bases_Publicas/PUBCHEM.md)
- [docs/ETL_Bases_Publicas/ETL_CHEBI.md](docs/ETL_Bases_Publicas/ETL_CHEBI.md)
- [docs/ETL_Bases_Publicas/CHEMSPIDER.md](docs/ETL_Bases_Publicas/CHEMSPIDER.md)

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
- Top 10 gerado em data/staging.
- Carga em core realizada quando load-core estiver ativo.

## 11. Erros comuns e solução

1. Porta 5432 ocupada
- Sintoma: PostgreSQL não sobe.
- Solução: liberar ou remapear porta no compose.

2. DB_PASS ausente no modo full stack
- Sintoma: execução interrompe no início.
- Solução: exportar DB_PASS ou usar --db-pass.

3. Falha de DNS no PubChem
- Sintoma: erro de resolução de nome nas integrações externas.
- Solução: repetir execução quando a rede estabilizar.

4. ChemSpider sem resultados
- Sintoma: zero linhas em stg.chemspider_compound_raw.
- Solução: comportamento esperado para parte dos compostos (nem todos têm ID no ChemSpider).

5. ETL Externo muito lento
- Sintoma: processamento de milhares de compostos demorando horas.
- Solução: esperado para 5000-10000+ compostos. Use `tail -f runtime/logs/*.log` para acompanhar progresso.

6. "Arquivo Top 10 não foi gerado"
- Sintoma: data/staging/top10_candidates.parquet não existe.
- Solução: verificar se ETL interno rodou sem erros; validar dados em stg.identification_row.

## 12. Documentação detalhada

Leia o índice de documentação em [docs/README.md](docs/README.md).

Guias importantes:

- [docs/Database/SETUP_DATABASE.md](docs/Database/SETUP_DATABASE.md)
- [docs/ETL_Bases_Publicas/PUBCHEM.md](docs/ETL_Bases_Publicas/PUBCHEM.md)
- [docs/ETL_Bases_Publicas/ETL_CHEBI.md](docs/ETL_Bases_Publicas/ETL_CHEBI.md)
- [docs/ETL_Bases_Publicas/CHEMSPIDER.md](docs/ETL_Bases_Publicas/CHEMSPIDER.md)
- [docs/Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md](docs/Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md)

## 13. Status do projeto

- ETL interno e artefatos em data/staging operacionais.
- Ranking Top 10 em produção no pipeline.
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
