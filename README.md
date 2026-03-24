# QuimioAnalytics 🧪

> Banco de Dados Unificado para o **Instituto SENAI de Tecnologia Ambiental (IST Ambiental)**  
> Projeto Aplicado II · Ciência de Dados e Inteligência Artificial · SENAI Florianópolis · 2026/1

---

## 📌 Sobre o Projeto

O IST Ambiental gera grandes volumes de dados analíticos por meio de seu software interno — planilhas de **Identificação** (38.011 linhas, 1.063 features únicas) e **Abundância** (1.104 features, 12 replicatas dinâmicas). Esses dados precisam ser integrados entre si e enriquecidos com bibliotecas químicas públicas (PubChem, ChEBI, HMDB, FooDB) para viabilizar a priorização de compostos candidatos via ranking **Top 5**.

Este repositório contém o modelo lógico, schema físico e scripts de ETL do banco de dados unificado que sustenta esse pipeline.

---

## 🏗️ Arquitetura em Camadas

O banco é dividido em três schemas lógicos no PostgreSQL:

| Schema | Função |
|--------|--------|
| `stg` | Preserva o dado bruto de origem (staging), sem perda de informação |
| `core` | Verdade operacional normalizada — features, candidatos, replicatas, abundância |
| `ref` | Referência externa — compostos públicos, taxonomia, ontologia, usos e matches |
```
Fontes → [stg] → ETL → [core] → Match → [ref] → Top 5 / Dashboard
```

### Entidades principais

**Núcleo analítico (`core`)**
- `core.ingestion_batch` — controla lotes de importação (solvente, modo de ionização)
- `core.feature` — sinal analítico central; âncora entre Identificação e Abundância
- `core.sample_group` / `core.replicate` — normaliza as replicatas dinâmicas (1.1, 1.2 … 6.2)
- `core.abundance_measurement` — tabela fato com valor de abundância por feature × replicata
- `core.candidate_identification` — candidatos locais (relação 1:N com feature)

**Referência externa (`ref`)**
- `ref.external_source` / `ref.external_compound` — compostos canônicos das bibliotecas públicas
- `ref.external_identifier` / `ref.compound_property` — identificadores alternativos e propriedades físico-químicas
- `ref.taxonomy_node` / `ref.chemical_class` / `ref.use_application` — taxonomia, ontologia e usos
- `ref.candidate_match` — cruzamento N:N entre candidatos locais e compostos externos (com score e método)

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Banco de dados | PostgreSQL 15+ |
| ETL / processamento | Python 3 · Pandas · lxml |
| Integração com APIs | Requests (PubChem REST, ChEBI API) |
| Modelagem visual | DBeaver / brModelo |

---

## 📂 Estrutura do Repositório
```
quimioanalytics/
├── sql/
│   ├── schema_postgresql_mvp.sql   # DDL completo (stg + core + ref)
│   └── indexes.sql                 # Índices e constraints adicionais
├── etl/
│   ├── load_identification.py      # Leitura e staging de IDENTIFICACAO.xlsx
│   ├── load_abundance.py           # Leitura, melt e staging de ABUND.xlsx
│   ├── load_curated_catalog.py     # Staging de Compostos_final.xlsx
│   └── fetch_pubchem.py            # Ingestão incremental do PubChem XML
├── docs/
│   └── Entrega_2_MVP_Parcial.pdf   # Documento técnico completo
└── README.md
```

---

## ⚙️ Como Executar

### Pré-requisitos
- PostgreSQL 15+
- Python 3.10+
- Pacotes: `pandas`, `psycopg2`, `requests`, `lxml`

### 1. Criar o schema no banco
```bash
psql -U seu_usuario -d seu_banco -f sql/schema_postgresql_mvp.sql
```

### 2. Configurar variáveis de ambiente
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ist_ambiental
export DB_USER=seu_usuario
export DB_PASS=sua_senha
```

### 3. Executar o ETL (ordem recomendada)
```bash
python etl/load_identification.py    # stg → core.feature + core.candidate_identification
python etl/load_abundance.py         # stg → core.sample_group + core.replicate + core.abundance_measurement
python etl/load_curated_catalog.py   # stg → ref.curated_catalog_entry
python etl/fetch_pubchem.py          # stg.pubchem_compound_raw → ref.external_compound
```

---

## 📊 Dados de Referência (MVP Parcial)

| Fonte | Volume observado |
|-------|-----------------|
| IDENTIFICACAO.xlsx | 38.011 linhas · 1.063 features |
| ABUND.xlsx | 1.104 features · 12 replicatas (1.1 → 6.2) |
| Interseção Identificação ∩ Abundância | 962 features |
| Compostos_final.xlsx | 200 entradas curadas |
| PubChem XML (amostra) | Estrutura hierárquica analisada e mapeada |

---

## ✅ Status das Entregas

- [x] Diagnóstico empírico das fontes do IST
- [x] Mapa lógico dos dados (MER) com entidades e cardinalidades
- [x] Schema físico preliminar em PostgreSQL (`stg` + `core` + `ref`)
- [x] Dicionário de dados (22 entidades documentadas)
- [x] Mapeamento coluna-a-coluna das planilhas para as tabelas de destino
- [ ] ETL completo: leitura, melt e carga das planilhas do IST
- [ ] Integração com PubChem REST API (carga incremental)
- [ ] Integração com HMDB, ChEBI e FooDB
- [ ] Motor de matching e score Top 5
- [ ] Dashboard de visualização

---

## 👥 Equipe

| Membro | Frente principal |
|--------|-----------------|
| Guilherme da Silva Anselmo | Modelagem PostgreSQL e DER visual |
| Guilherme Zamboni Menegacio | ETL com Pandas (melt, pivot, carga) |
| Vinícius Joacir dos Anjos | Ingestão de bibliotecas públicas (PubChem, HMDB, ChEBI, FooDB) |
| Samuel Silva de Rezende | Documentação, apresentação e racional de arquitetura |

---

## 📄 Licença

Uso acadêmico interno — SENAI Florianópolis · 2026