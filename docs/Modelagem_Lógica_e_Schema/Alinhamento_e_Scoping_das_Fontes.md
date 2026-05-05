# Alinhamento e Scoping das Fontes

## Atividade Inicial

Cada grupo (squad) deve abrir o arquivo Excel de critérios fornecido pelo IST Ambiental e mapear os atributos essenciais para o ranking (ex: massa molecular, tempo de retenção).

## Atributos Essenciais para o Ranking

### 1. Identificação do Composto (Chave Primária)

Esses campos conectam as tabelas e permitem rastreabilidade:

- Compound
- Compound ID
- Formula
- Description
- Link

### 2. Propriedades Físico-Químicas (Priorização Estrutural)

Campos encontrados:

- Neutral mass (Da) → massa molecular neutra
- m/z → razão massa/carga
- Retention time (min) → tempo de retenção cromatográfico
- Chromatographic peak width (min) → largura do pico

### 3. Qualidade da Identificação (Confiança Analítica)

Campos principais:

- Score
- Fragmentation Score
- Mass Error (ppm)
- Isotope Similarity
- Adducts
- Identifications

### 4. Intensidade / Abundância (Importância Ambiental)

Arquivo ABUND.xlsx contém colunas 1.1 até 6.2, que representam:

- Replicatas experimentais
- Amostras diferentes
- Campanhas distintas

### 5. Tempo de Retenção (Critério Obrigatório do IST)

Campo: Retention time (min)

Importante porque:

- Valida plausibilidade cromatográfica
- Diferencia isômeros
- Aumenta confiança da identificação

### 6. Massa Molecular (Critério Obrigatório do IST)

Campo: Neutral mass (Da)

Usos:

- Valida fórmula
- Compara com banco de dados
- Reduz falsos positivos

### Conjunto Mínimo Recomendado para Ranking Automático

Se o squad precisar montar um ranking funcional rápido, use:

**Prioridade Alta:**
- Neutral mass
- m/z
- Retention time
- Score
- Fragmentation Score
- Mass Error
- Isotope Similarity

**Prioridade Média:**
- Chromatographic peak width
- Identifications
- Adducts

**Prioridade Ambiental:**
- Intensidade média (colunas 1.x–6.x)
- Frequência de ocorrência

## Guia de Endpoints – APIs PubChem e ChEBI

Abrir o "Guia de Endpoints" básico para as APIs PubChem e ChEBI, focando em como buscar compostos por nome ou massa.

### 1. API do PubChem (PUG REST)

**Endpoint para buscar por nome:**
```
https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome_composto}/property/MolecularWeight,CanonicalSMILES/JSON
```

**Exemplo:**
```
https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/property/MolecularWeight,MolecularFormula,CanonicalSMILES/JSON
```

### 2. API do ChEBI (A API do European Bioinformatics Institute OLS)

**Endpoint para buscar por nome:**
```
https://www.ebi.ac.uk/ols/api/search?q={nome_composto}&ontology=chebi
```

**Exemplo:**
```
https://www.ebi.ac.uk/ols/api/search?q=aspirin&ontology=chebi
```

**Endpoint para entidade completa:**
```
https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F{chebi_formatado}
```

**Exemplo:**
```
https://www.ebi.ac.uk/ols4/api/ontologies/chebi/terms/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FCHEBI_27732
```

## Lista Preliminar de Campos que Serão Cruzados

Evidência: Sinal Bruto vs. Critério Técnico vs. Dados da API.

### 1. Sinal Bruto (Dados Experimentais — ABUND.xlsx)

**Campos utilizados:**
- m/z
- Retention time (min)
- Chromatographic peak width (min)
- Intensidades (colunas 1.1–6.2)

**Métricas derivadas:**
- Intensidade média
- Frequência de detecção entre amostras

**Função:** Medir relevância ambiental e consistência experimental.

### 2. Critério Técnico (Qualidade da Identificação — IDENTIFICACAO.xlsx)

**Campos utilizados:**
- Compound
- Compound ID
- Formula
- Neutral mass (Da)
- Score
- Fragmentation Score
- Mass Error (ppm)
- Isotope Similarity
- Adducts
- Identifications

**Função:** Avaliar confiança analítica, reduzir falsos positivos e sustentar o score técnico do ranking.

### 3. Dados Complementares via APIs Químicas

(Ex.: PubChem, ChEBI, ChemSpider)

**Campos previstos:**
- CID / ChEBI ID / CSID
- Exact mass
- InChIKey
- SMILES
- Classe química
- Propriedades moleculares (ex.: logP)

**Função:** Validação estrutural, enriquecimento químico e integração entre bases.

### Campos Principais de Integração entre Tabelas

**Prioridade de cruzamento:**
1. InChIKey
2. Exact mass
3. Formula
4. Compound name