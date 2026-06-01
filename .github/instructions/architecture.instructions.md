---
description: "Use quando a tarefa envolver desenho de módulos, refatoração de fronteiras, separação de responsabilidades ou definição de camadas de service e repository no QuimioAnalytics. Cobre arquitetura modular, baixo acoplamento e rastreabilidade científica."
name: "Regras de Arquitetura"
---
# Regras de Arquitetura
> Consulte também as diretrizes gerais em .github/copilot-instructions.md para validação de sugestões, alternativas, simplicidade e documentação.

- Separe domínio, aplicação, infraestrutura, apresentação e scripts operacionais ao introduzir novo código.
- Mantenha regras de negócio fora de controllers, rotas e componentes de UI.
- Prefira DTOs explícitos, contratos de serviço e módulos pequenos e componíveis.
- Estruture mudanças para que a origem, a transformação e a saída dos dados científicos permaneçam rastreáveis.
- Evite atalhos entre módulos que escondam ownership ou dificultem testes.