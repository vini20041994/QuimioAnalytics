# Atividade — Integração de Dados Químicos via Excel e APIs Públicas

## Linguagem e Ambiente

A atividade deve ser desenvolvida utilizando:

- Linguagem: **Python**
- Ambiente: **Anaconda**
- Editor: **VSCode**
- Biblioteca principal: **pandas**
- Biblioteca para requisições HTTP: **requests**

---

## Objetivos da Atividade

Desenvolver scripts capazes de:

### 1. Leitura de Arquivo Excel com Critérios Técnicos

Criar um script responsável por:

- Ler o arquivo Excel contendo critérios técnicos
- Utilizar a biblioteca **pandas**
- Estruturar os dados para posterior processamento

📄 Script:
```python scripts/extract_excel.py
```

Responsabilidades do script:

- Carregar o arquivo `.xlsx`
- Selecionar colunas relevantes
- Validar dados ausentes
- Preparar estrutura para integração com APIs

---

### 2. Requisições às APIs Públicas de Bases Químicas

Criar um script responsável por:

- Realizar requisições HTTP utilizando **requests**
- Consultar bases públicas de compostos químicos
- Capturar informações de **ontologia e taxonomia química**

Exemplos de informações esperadas:

- Espécie
- Gênero
- Reino
- Classificação química
- Origem biológica (produto natural ou sintético)

📄 Script:
```python scripts/api_requests.py
```


Responsabilidades do script:

- Consumir APIs públicas (ex.: PubChem, ChEBI, HMDB, FooDB)
- Tratar respostas JSON
- Extrair informações taxonômicas
- Integrar resultados com dados do Excel

---

## Resultado Esperado

Ao final da atividade, o pipeline deverá:

1. Ler critérios do Excel
2. Consultar APIs químicas públicas
3. Enriquecer os dados com ontologia e taxonomia
4. Preparar dataset estruturado para análises posteriores

---

## Competências Desenvolvidas

Durante a atividade serão trabalhadas:

- Leitura de arquivos Excel com pandas
- Consumo de APIs REST
- Tratamento de dados JSON
- Integração de múltiplas fontes de dados
- Estruturação de pipelines científicos em Python
- Enriquecimento semântico de dados químicos 🧪


# Especificação de Requisitos de Dados e Avaliação de Pré‑processamento

## Objetivo

Este documento descreve os requisitos mínimos de dados e as etapas necessárias de pré‑processamento para integração com bases químicas públicas e enriquecimento automático de compostos em pipelines de metabolômica computacional.

---

# 1. Requisitos mínimos de entrada

Campos obrigatórios para execução do pipeline:

| Campo               | Prioridade | Justificativa                              |
| ------------------- | ---------- | ------------------------------------------ |
| Compound            | Alta       | Identificador principal para busca textual |
| ExactMass           | Alta       | Matching espectral                         |
| Formula             | Média      | Validação estrutural                       |
| m/z                 | Média      | Confirmação LC‑MS                          |
| Retention Time (RT) | Baixa      | Refinamento posterior                      |

Formato esperado:

```
Compound | ExactMass | Formula | mz | RT
```

Exemplo:

```
caffeine | 194.08038 | C8H10N4O2 | 195.087 | 5.32
```

---

# 2. Requisitos para integração com APIs químicas

Identificadores recomendados por base:

| Base       | Melhor identificador |
| ---------- | -------------------- |
| PubChem    | Name / InChIKey      |
| ChEBI      | Name                 |
| ClassyFire | InChIKey             |
| LOTUS      | Name                 |
| HMDB       | Name                 |

Fluxo ideal:

```
Compound → PubChem → InChIKey → ClassyFire
```

---

# 3. Pré‑processamento obrigatório antes das requisições

## 3.1 Limpeza textual

Operações recomendadas:

* converter para lowercase
* remover espaços extras
* remover caracteres especiais

Exemplo:

```
"Caffeine " → "caffeine"
```

---

## 3.2 Normalização de nomes químicos

Problema comum:

```
Glucose
D‑glucose
β‑D‑glucose
```

Solução recomendada:

priorizar uso de:

```
InChIKey
SMILES
```

quando disponíveis.

---

## 3.3 Remoção de duplicatas

Aplicar antes de chamadas às APIs:

```
df["Compound"].drop_duplicates()
```

Benefícios:

* redução de tempo de execução
* redução de requisições externas
* maior eficiência computacional

---

## 3.4 Validação de massa espectral

Aplicar tolerância típica LC‑MS:

```
±5 ppm
```

Exemplo:

```
abs(massa_exp − massa_teorica) < tolerancia
```

---

# 4. Tratamento de valores ausentes

Verificação inicial:

```
df.isnull().sum()
```

Campos críticos:

| Campo     | Obrigatório |
| --------- | ----------- |
| Compound  | Sim         |
| ExactMass | Recomendado |
| Formula   | Recomendado |

---

# 5. Padronização estrutural recomendada

Transformar:

```
Compound
```

em:

```
CID
InChIKey
SMILES
```

Benefícios:

* redução de ambiguidade estrutural
* integração entre bases químicas
* maior robustez do pipeline

---

# 6. Critérios de qualidade do dado

Checklist antes do enriquecimento:

```
✔ nomes normalizados
✔ duplicatas removidas
✔ massa validada
✔ fórmula validada
✔ encoding UTF‑8 garantido
✔ unidades padronizadas
```

---

# 7. Requisitos de saída do pipeline enriquecido

Estrutura esperada do dataset final:

```
Compound
CID
ExactMass
Formula
InChIKey
SMILES
Superclass
Class
Subclass
Chemical_Kingdom
Kingdom
Family
Genus
Species
Natural_product
Human_metabolite
Food_component
```

---

# 8. Matriz de avaliação do pré‑processamento

| Etapa                   | Necessidade           | Justificativa            |
| ----------------------- | --------------------- | ------------------------ |
| Limpeza textual         | Obrigatório           | evitar erro em APIs      |
| Remover duplicatas      | Obrigatório           | otimização computacional |
| Padronização de massa   | Obrigatório           | matching espectral       |
| Normalização de fórmula | Recomendado           | validação estrutural     |
| Conversão para InChIKey | Altamente recomendado | integração multi‑bases   |

---

# 9. Arquitetura do pipeline recomendada

Fluxo completo:

```
IDENTIFICACAO.xlsx
↓
limpeza textual
↓
remoção duplicatas
↓
validação massa
↓
enriquecimento estrutural (PubChem)
↓
ontologia química (ChEBI)
↓
taxonomia química (ClassyFire)
↓
origem biológica (LOTUS)
↓
status metabólico humano (HMDB)
↓
dataset enriquecido final
```

---

# 10. Resultado esperado

Após execução correta do pipeline:

* integração entre múltiplas bases químicas
* classificação ontológica automática
* identificação de origem biológica
* suporte à anotação metabolômica LC‑MS
* geração de dataset pronto para análise estatística e interpretação biológica
