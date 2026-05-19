# Sprint 1 — Estabilização Crítica

**Status**: ✅ Concluída  
**Capacidade**: 24 pontos  
**Objetivo**: Remover falhas de execução que impediam o bootstrap do projeto e tornar migrações reexecutáveis sem erro.

---

## Contexto

Antes desta sprint o projeto não era inicializável de forma confiável. Problemas de sintaxe em extratores, blocos duplicados de execução e DDL/migrations não-idempotentes causavam falhas toda vez que o ambiente era recriado ou o pipeline era reexecutado. Esta sprint foi a base que permitiu avançar com segurança para as sprints seguintes.

---

## Principais Pontos Levantados

### 1. Assinatura inválida no spider ChemSpider
- **Arquivo**: `scripts/extract/extract_chemspider.py`
- **Problema**: Método `__init__` com assinatura inválida em Python impedia qualquer importação do módulo.
- **Impacto**: Extração de dados ChemSpider completamente bloqueada.

### 2. Leitura de arquivo sem encoding explícito
- **Arquivo**: `scripts/extract/extract_chemspider.py`
- **Problema**: `open()` sem parâmetro `encoding=` gera comportamento dependente de plataforma e warning em Python 3.11+.
- **Impacto**: Risco de corrupção silenciosa de caracteres especiais em nomes de compostos.

### 3. Bloco duplicado `if __name__ == "__main__"` no runner PubChem
- **Arquivo**: `scripts/run/run_etl_pubchem.py`
- **Problema**: Dois blocos de execução causavam execução dupla do pipeline ao chamar o script diretamente.
- **Impacto**: Requisições duplicadas às APIs, possível duplicação de dados no banco.

### 4. Schema e migrations não-idempotentes
- **Arquivos**: `database/schema_postgresql_mvp_entrega2.sql`, migrations 003 e 006
- **Problema**: Reaplicar o schema ou as migrations em um banco já inicializado falhava com erros de "tabela já existe" ou "constraint já existe".
- **Impacto**: Impossível recriar ambiente do zero ou realizar rollback seguro.

### 5. Links quebrados na documentação de primeira execução
- **Arquivos**: `README.md`, `docs/README.md`, `scripts/run/install_system_prereqs.sh`
- **Problema**: Referências a arquivos inexistentes confundiam novos desenvolvedores durante o onboarding.

### 6. Erros de lint nos extratores legados
- **Arquivos**: `extract_foodb.py`, `extract_hmdb.py`, `extract_classyfire.py`, `extract_lotus.py`
- **Problema**: Erros bloqueantes detectados pelo VS Code Problems — imports não-resolvidos, variáveis não-definidas.
- **Impacto**: Risco de falhas em tempo de execução sem aviso prévio.

---

## O Que Foi Feito

| ID | Ação | Resultado |
|---|---|---|
| S1-01 | Corrigiu assinatura de `__init__` no spider ChemSpider | Script importável e funcional |
| S1-02 | Adicionou `encoding="utf-8"` em todos os `open()` | Sem warning de encoding |
| S1-03 | Removeu bloco `if __name__` duplicado no PubChem runner | Uma única execução por chamada |
| S1-04 | Adicionou `IF NOT EXISTS` no schema SQL | Schema reaplicável sem erro |
| S1-05 | Tornou migration 003 idempotente com `IF NOT EXISTS` | Migration reexecutável |
| S1-06 | Tornou migration 006 idempotente com `IF NOT EXISTS` | Migration reexecutável |
| S1-07 | Corrigiu links na documentação | Onboarding funcional |
| S1-08 | Resolveu erros de lint nos extratores legados | Sem erros bloqueantes |

---

## Lições Aprendidas

- Idempotência em DDL e migrations é pré-requisito, não opcional — qualquer ambiente de CI ou onboarding depende disso.
- Erros de sintaxe silenciados (lint não configurado no CI) acumulam débito técnico que bloqueia o desenvolvimento.
- A ausência de um pipeline de CI foi o fator que permitiu esses problemas se acumularem.

---

## Próximos Passos

Esta sprint desbloqueou o ambiente. A **Sprint 2** é a próxima prioridade crítica — o algoritmo de ranking precisa ser substituído antes que qualquer resultado científico seja confiável.

- [ ] Iniciar Sprint 2: implementar `BiologicalRankingEngine` e remover ranking probabilístico
- [ ] Configurar lint automático (`ruff`) no CI para evitar regressão dos problemas resolvidos aqui
- [ ] Documentar procedimento de bootstrap no `docs/Database/SETUP_DATABASE.md`

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 1](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-1--estabilização-crítica--já-concluída)
