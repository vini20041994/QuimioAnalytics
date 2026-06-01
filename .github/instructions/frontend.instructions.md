---
description: "Use quando a tarefa envolver criação ou edição de componentes React, páginas, hooks, estilos ou fluxos analíticos de interface. Cobre legibilidade, estados, reuso e UX científica orientada a dashboards."
name: "Regras de Frontend"
applyTo:
  - "fron_test/src/**/*.jsx"
  - "fron_test/src/**/*.js"
  - "fron_test/src/**/*.css"
---
# Regras de Frontend
> Consulte também as diretrizes gerais em .github/copilot-instructions.md para validação de sugestões, alternativas, simplicidade e documentação.

- Construa interfaces analíticas com hierarquia clara, não com estética de landing page.
- Trate estados de carregamento, vazio e erro como comportamento de primeira classe.
- Mantenha a transformação de dados fora dos componentes puramente visuais quando possível.
- Prefira componentes reutilizáveis e estado previsível em vez de ramificações específicas de página.
- Garanta que tabelas, filtros e gráficos sejam legíveis em desktop e mobile.