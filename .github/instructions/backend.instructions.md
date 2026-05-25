---
description: "Use quando a tarefa envolver criação ou edição de services, validadores, handlers ou testes Python de backend. Cobre tratamento de erros, contratos fortes, paginação, filtros e logging estruturado."
name: "Regras de Backend"
applyTo:
  - "scripts/**/*.py"
  - "tests/**/*.py"
---
# Regras de Backend

- Valide entradas de forma explícita e falhe com mensagens de erro acionáveis.
- Mantenha a orquestração enxuta; mova regras de negócio para services reutilizáveis.
- Adicione logs estruturados em operações críticas, chamadas externas e fluxos de falha.
- Ao retornar coleções, considere paginação, filtros e requisitos de ordenação.
- Proteja o sistema contra escritas inconsistentes, processamento duplicado e fallbacks silenciosos.