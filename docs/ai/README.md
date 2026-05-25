# Guia de Governança de IA

Este diretório documenta como a IA deve ser usada no QuimioAnalytics. A ativação operacional acontece em `.github/`, enquanto `docs/ai/` funciona como base documental para contexto, modelos de saída e workflows.

## Estrutura

- `.github/copilot-instructions.md`: regras globais sempre ativas para o repositório.
- `.github/instructions/*.instructions.md`: instruções ativas por área, com `description` para descoberta e `applyTo` quando o comportamento deve ser anexado automaticamente a certos arquivos.
- `docs/ai/instructions/*.instructions.md`: espelho documental das instruções ativas, útil para leitura, governança e revisão humana.
- `.github/prompts/quick-tasks/*.prompt.md`: prompts rápidos para análise, testes, rastreamento de pipeline e refatorações pontuais.
- `.github/prompts/reviews/*.prompt.md`: prompts de revisão técnica, segurança, auditoria e integridade científica.
- `.github/prompts/backend/*.prompt.md`: prompts operacionais para criação e refatoração de backend.
- `.github/prompts/frontend/*.prompt.md`: prompts operacionais para dashboards, tabelas e refatorações de interface.
- `.github/prompts/data-engineering/*.prompt.md`: prompts operacionais para pipelines, validação e lineage.
- `docs/ai/templates/`: modelos para API, serviço, pipeline, dashboard, review e auditoria.
- `docs/ai/workflows/`: sequências recomendadas para desenvolvimento, validação científica, release, code review e processamento de dados.
- `docs/ai/context/`: contexto de negócio, científico, metabolômico e arquitetural.

## Como usar

1. Mantenha regras globais curtas em `.github/copilot-instructions.md`.
2. Coloque regras específicas e reutilizáveis em `.github/instructions/`.
3. Use `docs/ai/instructions/` como cópia documental e referência de governança, não como camada operacional do Copilot.
4. Use `applyTo` apenas quando a instrução realmente precisar ser carregada automaticamente.
5. Use `description` com palavras-chave claras para descoberta on-demand.
6. Use prompts em `.github/prompts/` para tarefas repetíveis da equipe, separando tarefas rápidas, revisões e funções especializadas.
7. Consulte `docs/ai/context/` e `docs/ai/workflows/` antes de criar automações ou análises maiores.

## Critérios de qualidade

- toda orientação deve reforçar integridade científica e rastreabilidade;
- mudanças estruturais devem priorizar modularidade, legibilidade e baixo acoplamento;
- prompts devem ser focados em uma única tarefa;
- instruções não devem duplicar documentação extensa quando um link ou referência local resolve;
- qualquer automação deve deixar claros riscos, limites e validações necessárias.

## Quando atualizar

Atualize esta governança quando houver:

- mudança de arquitetura relevante;
- novo fluxo científico ou pipeline crítico;
- padrão recorrente de revisão;
- nova necessidade operacional para prompts reutilizáveis;
- ajuste na forma como o Copilot deve anexar contexto por tipo de arquivo.