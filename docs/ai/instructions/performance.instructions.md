# Regras de Performance

Referência documental da instrução ativa em `.github/instructions/performance.instructions.md`.

- Meça o gargalo antes de alterar o comportamento.
- Remova primeiro queries, loops, transformações ou renders redundantes.
- Prefira processamento em lotes e incremental para grandes volumes.
- Leve filtros pesados e paginação para o servidor quando isso reduzir o custo total.
- Documente trade-offs e risco de regressão de cada otimização.