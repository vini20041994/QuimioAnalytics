# Sprint 3 — Testes e Qualidade

**Status**: 🔴 Todo  
**Capacidade**: 33 pontos  
**Objetivo**: Implantar suite mínima de testes e gate de qualidade no CI para detectar regressões cedo e viabilizar refatorações futuras.

---

## Contexto

Com a Escadinha Biológica implementada (Sprint 2), o projeto precisa de testes automatizados para:
1. Validar que a nova lógica de ranking se comporta corretamente
2. Proteger transformações existentes contra regressão
3. Criar gate de qualidade no CI para bloquear PRs problemáticas
4. Suportar refatorações seguras das Sprints 4–7

Atualmente o projeto tem **zero cobertura de testes**. Esta sprint estabelece a base.

---

## Principais Pontos Levantados

### 1. Nenhuma validação automatizada de transformações
- **Impacto**: Bugs em `transform_stg_xlsx.py`, `scoring.py` só descobertos em produção
- **Risco**: Papers baseados em dados transformados incorretamente

### 2. Comportamento de ranking impossível de validar
- **Problema**: Não há testes que confirmem que a Escadinha Biológica funciona como descrito
- **Risco**: Sprint 2 pode estar parcialmente implementada sem que ninguém saiba

### 3. Perda de dados silenciosa em transformações
- **Problema**: Funções como `safe_numeric` descartam valores sem logging
- **Impacto**: Relatório de qualidade inexistente; pesquisador não sabe quantas moléculas foram perdidas

### 4. Runners podem quebrar sem aviso
- **Problema**: Sem testes de smoke, um erro num arquivo novo só é detectado em produção
- **Risco**: Pipeline todo falha no meio

### 5. Sem cobertura mínima no CI
- **Problema**: PRs sem qualquer teste são aceitas
- **Impacto**: Código legado acumula débito técnico sem freio

---

## O Que Deve Ser Feito

### Estrutura de Pastas

```
tests/
├── __init__.py
├── conftest.py                                 ← Fixtures compartilhadas
├── unit/
│   ├── __init__.py
│   ├── test_biological_ranking.py              ← NOVO (Sprint 2)
│   ├── test_scoring.py                         ← Testes de scoring bruto
│   ├── test_transform_stg_xlsx.py              ← Testes de transformação
│   ├── test_features_io.py                     ← Testes de merge/validação
│   └── test_quality_reporter.py                ← Testes do relatório de qualidade
├── integration/
│   ├── __init__.py
│   ├── test_runners_smoke.py                   ← Testes mínimos de runners
│   └── test_database_migrations.py             ← Testes de migrations
└── validation/
    ├── __init__.py
    └── test_output_schema.py                   ← Validação de output final
```

### Arquivos de Configuração

**`pytest.ini`** (novo)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --tb=short -v
markers =
    unit: testes unitários
    integration: testes de integração com banco de dados
    validation: testes de validação de output
    slow: testes lentos (> 5s)
```

**`requirements-dev.txt`** (atualizar)
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-postgresql==5.1.0
pandas==2.2.2
ruff==0.1.8
mypy==1.7.1
```

### Critérios de Aceite por Tarefa

| ID | Tarefa | Critério |
|---|---|---|
| S3-01 | Testes da Escadinha Biológica | 4 cenários passam (ordem, empate, dados brutos, IDs) |
| S3-02 | Estrutura de pastas | `pytest --collect-only` descobre todos os testes |
| S3-03 | Testes de transformação stg xlsx | Cobrir `safe_numeric`, `safe_int`, validação de colunas obrigatórias |
| S3-04 | Testes de merge e validação | Merge inválido lança erro com mensagem clara |
| S3-05 | Testes de smoke | `run_etl.py` com inputs mínimos roda sem crash |
| S3-06 | Validação de schema de output | Output contém colunas obrigatórias; `rank_group ≥ 1` |
| S3-07 | CI gate 60% cobertura | PR falha se `pytest --cov` reporta < 60% |
| S3-08 | Lint com ruff | Ruff executa em `scripts/` e `tests/` sem erros bloqueantes |
| S3-09 | Testes de relatório de qualidade | Relatório JSON mostra `rows_lost` corretamente |

---

## Lições Aprendidas (Antecipadas)

- Testes escritos DEPOIS do código tendem a ser incompletos. Ideal: TDD. Aceitável: testes após, mas cobertura ≥ 60%.
- Smoke tests são essenciais para regredir runners — investir em CI rápido.
- Cobertura mínima força código testável; refactora implicitamente a arquitetura.

---

## Próximos Passos

- [ ] **Dia 1**: Criar estrutura de pastas e `conftest.py` com fixtures de DataFrame
- [ ] **Dia 2**: Escrever testes de Escadinha Biológica (S3-01) validar Sprint 2
- [ ] **Dia 3**: Escrever testes de transformações (S3-03, S3-04, S3-09)
- [ ] **Dia 4**: Escrever testes de smoke e validação (S3-05, S3-06)
- [ ] **Dia 5**: Configurar CI no GitHub Actions; validar gate de cobertura
- [ ] **Semana 2**: Refinar cobertura até ≥ 70% antes de Sprint 4

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 3](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-3--testes-e-qualidade)
