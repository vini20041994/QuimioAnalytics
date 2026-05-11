# Documentação do Projeto

Este diretório é o índice técnico do QuimioAnalytics. O ponto de entrada geral do projeto está em [../README.md](../README.md).

## 1. Como usar este índice

Se você está chegando agora:

1. Leia [../README.md](../README.md).
2. Siga para [Database/SETUP_DATABASE.md](Database/SETUP_DATABASE.md) se precisar preparar banco local.
3. Siga para os guias de ETL externo conforme a fonte de interesse.

## 2. Mapa da documentação

| Área | Arquivo | Quando ler |
|------|---------|------------|
| Banco de dados | [Database/SETUP_DATABASE.md](Database/SETUP_DATABASE.md) | Setup inicial, reset local, troubleshooting do PostgreSQL |
| PubChem | [ETL_Bases_Publicas/PUBCHEM.md](ETL_Bases_Publicas/PUBCHEM.md) | Operar pipeline PubChem ponta a ponta |
| ChEBI | [ETL_Bases_Publicas/ETL_CHEBI.md](ETL_Bases_Publicas/ETL_CHEBI.md) | Operar pipeline ChEBI e transformações associadas |
| ChemSpider | [ETL_Bases_Publicas/CHEMSPIDER.md](ETL_Bases_Publicas/CHEMSPIDER.md) | Operar extração e carga via scraping do ChemSpider |
| Modelagem | [Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md](Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md) | Entender MER, schema físico e dicionário de dados |
| Escopo das fontes | [Modelagem_Lógica_e_Schema/Alinhamento_e_Scoping_das_Fontes.md](Modelagem_Lógica_e_Schema/Alinhamento_e_Scoping_das_Fontes.md) | Entender decisões de integração e cobertura |

## 3. Rotas de leitura por perfil

### Perfil A: desenvolvimento e operação

1. [../README.md](../README.md)
2. [Database/SETUP_DATABASE.md](Database/SETUP_DATABASE.md)
3. Guia da fonte externa que você vai executar

### Perfil B: modelagem e banco

1. [Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md](Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md)
2. [Database/SETUP_DATABASE.md](Database/SETUP_DATABASE.md)

### Perfil C: visão acadêmica do projeto

1. [../README.md](../README.md)
2. [Modelagem_Lógica_e_Schema/Alinhamento_e_Scoping_das_Fontes.md](Modelagem_Lógica_e_Schema/Alinhamento_e_Scoping_das_Fontes.md)
3. Materiais históricos em [Modelagem_Lógica_e_Schema](Modelagem_Lógica_e_Schema)

## 4. Estrutura física da pasta docs

	docs/
	├── Database/
	│   └── SETUP_DATABASE.md
	├── ETL_Bases_Publicas/
	│   ├── PUBCHEM.md
	│   ├── ETL_CHEBI.md
	│   └── CHEMSPIDER.md
	├── Modelagem_Lógica_e_Schema/
	│   ├── Modelagem_logica_e_schema.md
	│   ├── Alinhamento_e_Scoping_das_Fontes.md
	│   ├── modelo_logico_schema_core.png
	│   ├── modelo_logico_schema_ref.png
	│   ├── modelo_logico_schema_stg.png
	│   ├── Entrega_2_MVP_Parcial_Banco_de_Dados_IST.pdf
	│   └── Entrega_2_MVP_Parcial_Banco_de_Dados_IST.docx
	├── report_assets/
	├── Entrega3_Transformacao_e_FeatureEngineering_Requisitos.pdf
	└── material_complementar/

## 5. Observações de manutenção

- O orquestrador principal do projeto é [../scripts/run/run_pipeline_frontend.py](../scripts/run/run_pipeline_frontend.py).
- O arquivo [../scripts/run/run_full_stack_etl.py](../scripts/run/run_full_stack_etl.py) permanece apenas para compatibilidade de comando.
- Sempre que um fluxo novo for adicionado em scripts/run, atualize este índice e o README principal.