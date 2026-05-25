---
description: "Use quando a tarefa envolver edição de schemas SQL, migrations, constraints, índices ou código de administração de banco. Cobre integridade referencial, auditabilidade, rollback e modelagem orientada à performance."
name: "Regras de Banco de Dados"
applyTo:
  - "database/**/*.sql"
  - "scripts/manage_db.py"
---
# Regras de Banco de Dados

- Modele para integridade referencial, rastreabilidade e prevenção de duplicidade.
- Explique o impacto de migrations e mantenha claros os caminhos de rollback ou mitigação.
- Adicione índices coerentes com padrões reais de filtro e join.
- Evite mudanças destrutivas sem um plano de compatibilidade.
- Considere trilha de auditoria e histórico de registros ao alterar estruturas persistentes.