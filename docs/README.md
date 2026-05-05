# Documentação

Este diretório concentra a documentação operacional e técnica do projeto. O único documento mantido fora desta pasta é o README principal na raiz do repositório.

## Estrutura

```
docs/
├── Database/
│   └── SETUP_DATABASE.md        — preparação, operação e troubleshooting do PostgreSQL local
├── ETL_Bases_Publicas/
│   ├── PUBCHEM.md               — extração, transformação, carga e operação do pipeline PubChem
│   ├── ETL_CHEBI.md             — extração, transformação e carga do ChEBI (staging + ref)
│   └── CHEMSPIDER.md            — extração por scraping, transformação e carga em stg.chemspider_compound_raw
├── Modelagem_Lógica_e_Schema/
│   ├── Modelagem_logica_e_schema.md     — MER, schema físico e dicionário de dados
│   ├── Alinhamento_e_Scoping_das_Fontes.md
│   ├── modelo_logico_schema_core.png
│   ├── modelo_logico_schema_ref.png
│   ├── modelo_logico_schema_stg.png
│   ├── Entrega_2_MVP_Parcial_Banco_de_Dados_IST.pdf
│   └── Entrega_2_MVP_Parcial_Banco_de_Dados_IST.docx
└── material_complementar/       — referências de apoio
```

## Guias Ativos

| Arquivo | Conteúdo |
|---------|----------|
| [Database/SETUP_DATABASE.md](Database/SETUP_DATABASE.md) | Preparação, operação e troubleshooting do PostgreSQL local |
| [ETL_Bases_Publicas/PUBCHEM.md](ETL_Bases_Publicas/PUBCHEM.md) | Pipeline PubChem ponta a ponta |
| [ETL_Bases_Publicas/ETL_CHEBI.md](ETL_Bases_Publicas/ETL_CHEBI.md) | Pipeline ChEBI — staging, JSONB e colunas texto legíveis |
| [ETL_Bases_Publicas/CHEMSPIDER.md](ETL_Bases_Publicas/CHEMSPIDER.md) | Pipeline ChemSpider — scraping, transformação e carga |
| [Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md](Modelagem_Lógica_e_Schema/Modelagem_logica_e_schema.md) | Modelagem lógica, schema físico e dicionário de dados |

## Organização Aplicada

- O conteúdo histórico de PubChem foi consolidado em `ETL_Bases_Publicas/PUBCHEM.md`
- A documentação de ChEBI está centralizada em `ETL_Bases_Publicas/ETL_CHEBI.md`
- A documentação do pipeline ChemSpider está em `ETL_Bases_Publicas/CHEMSPIDER.md`
- Os materiais de modelagem e os entregáveis históricos estão em `Modelagem_Lógica_e_Schema/`
- A configuração do banco está em `Database/SETUP_DATABASE.md`
- O README da raiz permanece como porta de entrada do projeto