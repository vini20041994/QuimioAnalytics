---
description: "Use quando criar etapa de pipeline científico de dados com validação, lineage, logging e processamento reproduzível."
name: "Criar Pipeline de Dados"
argument-hint: "Etapa ou objetivo do pipeline"
agent: "agent"
---
Crie o trecho de pipeline de dados solicitado.

Requisitos:

- definir origem, transformação e destino com clareza;
- validar schema, tipos e ranges de chaves;
- preservar identificadores necessários para rastreabilidade;
- registrar execução, volume e falhas;
- evitar descartes silenciosos e fallbacks ambíguos;
- explicar como reprocessar com segurança.