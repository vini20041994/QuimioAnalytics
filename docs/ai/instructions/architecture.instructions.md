# Regras de Arquitetura

Referência documental da instrução ativa em `.github/instructions/architecture.instructions.md`.

- Separe domínio, aplicação, infraestrutura, apresentação e scripts operacionais ao introduzir novo código.
- Mantenha regras de negócio fora de controllers, rotas e componentes de UI.
- Prefira DTOs explícitos, contratos de serviço e módulos pequenos e componíveis.
- Estruture mudanças para que a origem, a transformação e a saída dos dados científicos permaneçam rastreáveis.
- Evite atalhos entre módulos que escondam ownership ou dificultem testes.