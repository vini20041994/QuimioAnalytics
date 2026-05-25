---
description: "Use quando refatorar um trecho de backend para reduzir acoplamento, melhorar legibilidade e preservar comportamento com validação enxuta."
name: "Refatorar Trecho de Backend"
argument-hint: "Arquivo ou trecho de backend para refatorar"
agent: "agent"
---
Refatore o trecho de backend selecionado com escopo mínimo.

Foque em:

- reduzir duplicação e funções grandes demais;
- mover regras de negócio para unidades reutilizáveis;
- melhorar clareza de validação e tratamento de erro;
- preservar o comportamento atual;
- executar a validação mínima relevante após a mudança.