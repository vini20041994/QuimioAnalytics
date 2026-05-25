---
description: "Use quando a tarefa envolver criação ou alteração de scripts de extract, transform, load, features ou run em pipelines científicos de dados. Cobre validação de schema, idempotência, lineage e reprocessamento seguro."
name: "Regras de Engenharia de Dados"
applyTo:
  - "scripts/extract/**/*.py"
  - "scripts/transform/**/*.py"
  - "scripts/load/**/*.py"
  - "scripts/features/**/*.py"
  - "scripts/run/**/*.py"
---
# Regras de Engenharia de Dados

- Valide schema, tipos, unidades e ranges antes de gravar saídas.
- Torne pipelines idempotentes quando viável e explícitos quando não forem.
- Mantenha o lineage visível da origem até a saída transformada.
- Registre volumes, rejeições, falhas e identificadores de processamento.
- Preserve chaves e metadados necessários para auditoria e reprocessamento.