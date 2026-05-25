# Regras de Backend

Referência documental da instrução ativa em `.github/instructions/backend.instructions.md`.

- Valide entradas de forma explícita e falhe com mensagens de erro acionáveis.
- Mantenha a orquestração enxuta; mova regras de negócio para services reutilizáveis.
- Adicione logs estruturados em operações críticas, chamadas externas e fluxos de falha.
- Ao retornar coleções, considere paginação, filtros e requisitos de ordenação.
- Proteja o sistema contra escritas inconsistentes, processamento duplicado e fallbacks silenciosos.