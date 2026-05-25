---
description: "Use quando a tarefa envolver adição de logs, métricas, monitoramento ou comportamento de diagnóstico em services e pipelines. Cobre logging estruturado, correlação de execução e sinais operacionais acionáveis."
name: "Regras de Observabilidade"
applyTo:
  - "scripts/**/*.py"
---
# Regras de Observabilidade

- Emita logs estruturados com contexto suficiente para rastrear uma execução ou lote.
- Monitore sucesso, falha, duração e volume nos fluxos críticos.
- Correlacione eventos por execução, arquivo, lote ou identificador de processo.
- Mantenha logs acionáveis; evite ruído sem valor operacional.
- Não registre segredos sensíveis nem payloads confidenciais brutos.