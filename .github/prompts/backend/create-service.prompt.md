---
description: "Use quando implementar service de backend com regras de negócio claras, entradas e saídas tipadas, logging e comportamento testável."
name: "Criar Service de Backend"
argument-hint: "Responsabilidade do service"
agent: "agent"
---
Crie um service de backend para o caso de uso solicitado.

Requisitos:

- definir a responsabilidade do service em uma frase;
- separar orquestração de persistência e validação;
- explicitar entradas, saídas e modos de falha;
- incluir logging estruturado onde houver valor operacional;
- preservar rastreabilidade científica se houver transformação de dados;
- propor testes unitários focados.