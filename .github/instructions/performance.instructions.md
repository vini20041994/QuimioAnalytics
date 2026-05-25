---
description: "Use quando a tarefa envolver otimização de queries, transformações grandes, renderização React ou qualquer fluxo lento. Cobre otimização orientada por medição, processamento em lotes, paginação e remoção de trabalho redundante."
name: "Regras de Performance"
---
# Regras de Performance

- Meça o gargalo antes de alterar o comportamento.
- Remova primeiro queries, loops, transformações ou renders redundantes.
- Prefira processamento em lotes e incremental para grandes volumes.
- Leve filtros pesados e paginação para o servidor quando isso reduzir o custo total.
- Documente trade-offs e risco de regressão de cada otimização.