---
description: "Use quando o trabalho tocar autenticação, autorização, entrada do usuário, segredos, manipulação de arquivos, acesso a banco ou endpoints expostos externamente. Cobre validação, menor privilégio e proteção de dados sensíveis."
name: "Regras de Segurança"
---
# Regras de Segurança

- Valide e sanitize todos os dados de entrada.
- Não confie na validação do frontend como fronteira de segurança.
- Nunca exponha segredos em código, logs, prompts ou respostas.
- Prefira menor privilégio para acesso a dados e ações críticas.
- Registre operações críticas sem vazar valores sensíveis.