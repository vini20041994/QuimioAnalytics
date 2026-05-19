# Quadro de Sprint - Evolucao Tecnica

Este quadro transforma a auditoria tecnica em tarefas executaveis por arquivo.

## Escala de Pontos

- 1 ponto: ajuste simples (baixo risco)
- 2 pontos: ajuste pequeno com validacao
- 3 pontos: alteracao media (1 arquivo principal + efeitos locais)
- 5 pontos: alteracao relevante multi-arquivo
- 8 pontos: iniciativa ampla com impacto transversal

## Colunas de Acompanhamento

- Status sugerido: `Todo`, `Doing`, `Review`, `Done`, `Blocked`
- Dono sugerido: `Dados`, `Backend`, `DevOps`, `QA`

---

## Sprint 1 (Estabilizacao Critica)

Objetivo: remover falhas de execucao e tornar bootstrap/migracoes reexecutaveis.

Capacidade sugerida: 24 pontos

| ID | Tarefa | Arquivo(s) | Pontos | Dono | Status | Criterio de aceite |
|---|---|---|---:|---|---|---|
| S1-01 | Corrigir assinatura invalida do spider ChemSpider | `scripts/extract/extract_chemspider.py` | 3 | Backend | Todo | Script executa sem erro de sintaxe e gera parquet de saida |
| S1-02 | Ajustar leitura de arquivo com encoding explicito no ChemSpider | `scripts/extract/extract_chemspider.py` | 1 | Backend | Todo | Sem alerta de open sem encoding |
| S1-03 | Remover bloco duplicado de execucao no runner PubChem | `scripts/run/run_etl_pubchem.py` | 2 | Backend | Todo | Runner executa uma unica vez por chamada |
| S1-04 | Tornar criacao de tabelas finais idempotente no schema base | `database/schema_postgresql_mvp_entrega2.sql` | 5 | Dados | Todo | Reaplicar schema nao falha por tabela existente |
| S1-05 | Tornar migration 003 reexecutavel para constraint UNIQUE | `database/migrations/003_remove_duplicates_add_unique_constraint.sql` | 3 | Dados | Todo | Migration pode rodar novamente sem erro de constraint duplicada |
| S1-06 | Tornar migration 006 reexecutavel para constraint UNIQUE | `database/migrations/006_remove_duplicates_add_unique_chebi_constraint.sql` | 3 | Dados | Todo | Migration pode rodar novamente sem erro de constraint duplicada |
| S1-07 | Corrigir links de documentacao de primeira execucao | `README.md`, `scripts/run/install_system_prereqs.sh`, `docs/README.md` | 2 | DevOps | Todo | Nao ha referencia para arquivo inexistente |
| S1-08 | Verificar sintaxe/lint dos extratores legados apos ajustes | `scripts/extract/extract_foodb.py`, `scripts/extract/extract_hmdb.py`, `scripts/extract/extract_classyfire.py`, `scripts/extract/extract_lotus.py` | 5 | QA | Todo | Sem erros bloqueantes no VS Code Problems |

Total Sprint 1: 24 pontos

---

## Sprint 2 (Integridade e Confiabilidade)

Objetivo: garantir consistencia de chaves, deduplicacao real e padronizacao de fontes externas.

Capacidade sugerida: 26 pontos

| ID | Tarefa | Arquivo(s) | Pontos | Dono | Status | Criterio de aceite |
|---|---|---|---:|---|---|---|
| S2-01 | Padronizar source_name entre seed SQL e loaders legados | `database/schema_postgresql_mvp_entrega2.sql`, `scripts/load/load_foodb.py`, `scripts/load/load_hmdb.py`, `scripts/load/load_lotus.py`, `scripts/load/load_classyfire.py` | 5 | Dados | Todo | `get_source_id` encontra fontes sem fallback manual |
| S2-02 | Criar constraints unicas para external_identifier | `database/migrations/010_add_unique_constraints_ref.sql` (novo) | 3 | Dados | Todo | Insercoes com ON CONFLICT DO NOTHING passam a deduplicar por chave natural |
| S2-03 | Criar constraints unicas para compound_property | `database/migrations/010_add_unique_constraints_ref.sql` (novo) | 3 | Dados | Todo | Nao ha crescimento de duplicatas por reprocessamento |
| S2-04 | Criar constraints unicas para compound_cross_reference | `database/migrations/010_add_unique_constraints_ref.sql` (novo) | 3 | Dados | Todo | Reprocessamento preserva idempotencia |
| S2-05 | Revisar e alinhar ON CONFLICT com novas constraints | `scripts/load/external_load_utils.py` | 3 | Backend | Todo | ON CONFLICT referencia alvo valido ou constraint implicita |
| S2-06 | Normalizar estrategia de erros (evitar Exception generica) | `scripts/extract/extract_foodb.py`, `scripts/extract/extract_hmdb.py`, `scripts/extract/extract_classyfire.py`, `scripts/extract/extract_lotus.py` | 3 | Backend | Todo | Capturas especificas para requests/parsing |
| S2-07 | Adicionar timeout explicito em requests legados | `scripts/extract/extract_foodb.py`, `scripts/extract/extract_hmdb.py`, `scripts/extract/extract_classyfire.py`, `scripts/extract/extract_lotus.py` | 2 | Backend | Todo | Todas as chamadas HTTP possuem timeout |
| S2-08 | Criar checklist de validacao de rerun de pipeline | `docs/QUADRO_SPRINT_EVOLUCAO.md`, `docs/Database/SETUP_DATABASE.md` | 2 | QA | Todo | Existe procedimento de teste de idempotencia documentado |
| S2-09 | Rodar validacao de migrations em banco limpo e banco ja inicializado | `scripts/run/run_pipeline_frontend.py`, `scripts/manage_db.py` | 2 | DevOps | Todo | Evidencia de sucesso nos dois cenarios |

Total Sprint 2: 26 pontos

---

## Sprint 3 (Testes e Qualidade)

Objetivo: implantar suite minima de testes e gate de qualidade no CI.

Capacidade sugerida: 30 pontos

| ID | Tarefa | Arquivo(s) | Pontos | Dono | Status | Criterio de aceite |
|---|---|---|---:|---|---|---|
| S3-01 | Estruturar pasta de testes unitarios e integracao | `tests/unit/`, `tests/integration/`, `tests/validation/` (novos) | 3 | QA | Todo | Estrutura criada e reconhecida pelo pytest |
| S3-02 | Testes unitarios de scoring | `tests/unit/test_scoring.py`, `scripts/features/scoring.py` | 3 | QA | Todo | Cobrir limites e casos nulos |
| S3-03 | Testes unitarios de transformacao stg xlsx | `tests/unit/test_transform_stg_xlsx.py`, `scripts/transform/transform_stg_xlsx.py` | 5 | QA | Todo | Cobrir safe_numeric/safe_int/colunas obrigatorias |
| S3-04 | Testes de merge e colunas obrigatorias do ranking | `tests/unit/test_features_io.py`, `scripts/features/io.py` | 3 | QA | Todo | Merge invalido falha com mensagem clara |
| S3-05 | Teste de smoke para runners criticos | `tests/integration/test_runners_smoke.py`, `scripts/run/run_etl.py`, `scripts/run/run_pipeline_frontend.py` | 5 | Backend | Todo | Entradas minimas executam sem crash |
| S3-06 | Testes de validacao de schema de top10 | `tests/validation/test_top10_schema.py`, `scripts/features/analytics.py` | 3 | QA | Todo | Arquivo top10 atende colunas e regras de rank |
| S3-07 | Habilitar cobertura minima no CI (60%) | `.github/workflows/ci.yml`, `requirements-dev.txt` | 5 | DevOps | Todo | PR falha abaixo da meta de cobertura |
| S3-08 | Ajustar escopo de lint para pacotes principais | `.github/workflows/ci.yml` | 3 | DevOps | Todo | Ruff executa em scripts e tests completos |

Total Sprint 3: 30 pontos

---

## Sprint 4 (Performance, Observabilidade e Hardening)

Objetivo: aumentar throughput, rastreabilidade e seguranca operacional.

Capacidade sugerida: 32 pontos

| ID | Tarefa | Arquivo(s) | Pontos | Dono | Status | Criterio de aceite |
|---|---|---|---:|---|---|---|
| S4-01 | Substituir insercao row-by-row por batch no load staging interno | `scripts/load/load_stg_transformed.py` | 8 | Dados | Todo | Ganho de tempo >= 40% no dataset referencia |
| S4-02 | Aplicar batch insert no load top10 core | `scripts/features/database_top_10.py` | 5 | Dados | Todo | Reducao mensuravel de latencia na carga |
| S4-03 | Criar utilitario HTTP comum com retry/backoff/timeout | `scripts/extract/http_client.py` (novo), `scripts/extract/extract_pubchem.py`, `scripts/extract/extract_chebi.py` | 8 | Backend | Todo | Chamadas externas usam cliente unico |
| S4-04 | Padronizar logging estruturado por batch | `scripts/run/run_pipeline_frontend.py`, `scripts/load/load_pubchem.py`, `scripts/load/load_chebi.py`, `scripts/load/load_chemspider.py` | 5 | Backend | Todo | Logs possuem timestamp, nivel e batch_id |
| S4-05 | Restringir exposicao de porta de banco por perfil de ambiente | `docker-compose.yml`, `.env.example` | 3 | DevOps | Todo | Porta exposta apenas quando explicitamente habilitada |
| S4-06 | Documentar runbook de producao inicial | `docs/Database/SETUP_DATABASE.md`, `docs/README.md` | 3 | DevOps | Todo | Existe procedimento de backup, restore e rollback |

Total Sprint 4: 32 pontos

---

## Quadro Consolidado de Acompanhamento

Sugestao de visao rapida para daily/weekly:

| Sprint | Pontos planejados | Pontos concluidos | % Conclusao | Risco | Observacoes |
|---|---:|---:|---:|---|---|
| Sprint 1 | 24 | 0 | 0% | Alto | Estabilizacao critica |
| Sprint 2 | 26 | 0 | 0% | Alto | Integridade e idempotencia |
| Sprint 3 | 30 | 0 | 0% | Medio | Testes e cobertura |
| Sprint 4 | 32 | 0 | 0% | Medio | Performance e hardening |

---

## Definicao de Pronto (DoD)

Uma tarefa so pode ser marcada como `Done` se:

1. Codigo revisado por pelo menos 1 pessoa.
2. Lint e testes relacionados passam.
3. Evidencia de execucao anexada (saida de comando, log ou screenshot).
4. Documentacao atualizada quando houver impacto operacional.
5. Sem regressao nos runners principais (`run_etl.py` e `run_pipeline_frontend.py`).

---

## Sugestao de Cerimonias

- Planejamento: 1x por sprint (90 min)
- Daily: 15 min
- Review tecnica: 45 min na sexta
- Retro: 30 min no fim da sprint

---

## 5. Issues prontas para GitHub

Use cada item abaixo como uma issue individual. O formato ja inclui objetivo, criterio de aceite e arquivos afetados.

### Epic 1 - Estabilizacao Critica

#### Issue 1.1 - Corrigir assinatura invalida do spider ChemSpider
- Arquivo: `scripts/extract/extract_chemspider.py`
- Pontos: 3
- Prioridade: P0
- Descricao: corrigir a assinatura de `__init__` para uma forma valida em Python e garantir que o spider inicialize corretamente.
- Criterio de aceite: o script executa sem erro de sintaxe e gera `data/staging/chemspider_raw.parquet`.

#### Issue 1.2 - Remover duplicidade no runner PubChem
- Arquivo: `scripts/run/run_etl_pubchem.py`
- Pontos: 2
- Prioridade: P0
- Descricao: remover o segundo bloco `if __name__ == "__main__"` e evitar dupla execucao do pipeline.
- Criterio de aceite: a execucao eh feita uma unica vez por chamada.

#### Issue 1.3 - Tornar schema e migrations idempotentes
- Arquivos: `database/schema_postgresql_mvp_entrega2.sql`, `database/migrations/003_remove_duplicates_add_unique_constraint.sql`, `database/migrations/006_remove_duplicates_add_unique_chebi_constraint.sql`
- Pontos: 8
- Prioridade: P0
- Descricao: reestruturar DDL e migrations para permitir rerun seguro em ambiente limpo ou ja inicializado.
- Criterio de aceite: reaplicar bootstrap nao produz erro de tabela/constraint existente.

### Epic 2 - Integridade e Confiabilidade

#### Issue 2.1 - Padronizar nomes de fonte externa
- Arquivos: `database/schema_postgresql_mvp_entrega2.sql`, `scripts/load/load_foodb.py`, `scripts/load/load_hmdb.py`, `scripts/load/load_lotus.py`, `scripts/load/load_classyfire.py`
- Pontos: 5
- Prioridade: P1
- Descricao: alinhar `source_name` entre seed SQL e loaders legados para evitar falhas de lookup.
- Criterio de aceite: `get_source_id` encontra todas as fontes sem fallback manual.

#### Issue 2.2 - Criar constraints unicas para ref
- Arquivos: `database/migrations/010_add_unique_constraints_ref.sql` (novo), `scripts/load/external_load_utils.py`
- Pontos: 8
- Prioridade: P1
- Descricao: adicionar unicidade em identificadores, propriedades e cross references para suportar idempotencia real.
- Criterio de aceite: rerun nao duplica registros de ref.

### Epic 3 - Testes e Qualidade

#### Issue 3.1 - Criar suite inicial de testes
- Arquivos: `tests/unit/`, `tests/integration/`, `tests/validation/` (novos)
- Pontos: 13
- Prioridade: P1
- Descricao: adicionar testes para scoring, transformacoes, merges, cargas e validacao de dados.
- Criterio de aceite: suite executa localmente e no CI.

#### Issue 3.2 - Habilitar cobertura minima no CI
- Arquivos: `.github/workflows/ci.yml`, `requirements-dev.txt`
- Pontos: 5
- Prioridade: P1
- Descricao: bloquear merges abaixo da cobertura minima definida.
- Criterio de aceite: PR falha se cobertura ficar abaixo da meta.

### Epic 4 - Performance e Operacao

#### Issue 4.1 - Trocar carga linha a linha por batch
- Arquivos: `scripts/load/load_stg_transformed.py`, `scripts/features/database_top_10.py`
- Pontos: 13
- Prioridade: P2
- Descricao: substituir `iterrows` em cargas quentes por insercao em lote.
- Criterio de aceite: tempo total reduzido em relacao ao baseline.

#### Issue 4.2 - Criar cliente HTTP comum com retry
- Arquivos: `scripts/extract/http_client.py` (novo), `scripts/extract/extract_pubchem.py`, `scripts/extract/extract_chebi.py`
- Pontos: 8
- Prioridade: P2
- Descricao: padronizar timeout, retry e backoff para chamadas externas.
- Criterio de aceite: todos os extratores usam o mesmo cliente HTTP.

---

## 6. Dependencias entre tarefas

Mapa de dependencias principais para evitar retrabalho:

1. A correção do spider ChemSpider depende apenas do proprio arquivo e deve vir primeiro.
2. A remoção do runner duplicado em PubChem deve acontecer antes de qualquer teste de smoke do pipeline.
3. A idempotencia do schema e das migrations deve ser concluida antes de criar testes de integração que recriem banco do zero.
4. A padronizacao de `source_name` deve vir antes das constraints unicas de `ref`, para evitar migracoes e loads desalinhados.
5. As constraints unicas de `ref` devem ser criadas antes da suite de testes de idempotencia de reprocessamento.
6. A suite de testes deve ser escrita antes do aumento de paralelismo ou batch loading, para evitar regressao silenciosa.
7. O cliente HTTP comum deve ser criado antes de refatorar os extratores PubChem e ChEBI para reaproveitamento de codigo.
8. A troca de `iterrows` por batch insert deve vir depois dos testes basicos de carga, para comparar baseline e ganho real.

Sugestao de ordem executiva:

1. S1-01, S1-03, S1-04, S1-05, S1-06.
2. S2-01, S2-02, S2-03, S2-04, S2-05.
3. S3-01 a S3-08.
4. S4-01 a S4-06.

---

## 7. Distribuicao semanal sugerida

Assumindo 1 sprint por semana e capacidade media de 24 a 30 pontos semanais:

### Semana 1

- Corrigir ChemSpider e PubChem runner.
- Tornar schema e migrations idempotentes.
- Atualizar documentacao de bootstrap.
- Meta: reduzir risco de falha em execucao local.

### Semana 2

- Padronizar nomes de fontes externas.
- Criar constraints unicas de ref.
- Ajustar loaders para refletir o novo contrato do banco.
- Meta: rerun idempotente sem duplicacao.

### Semana 3

- Criar estrutura de testes.
- Escrever testes unitarios de scoring e transformacao.
- Escrever testes de merge e validacao de schema.
- Meta: detectar regressao de transformacao cedo.

### Semana 4

- Escrever testes de integracao com PostgreSQL.
- Habilitar cobertura minima no CI.
- Ajustar lint e escopo de validacao automatica.
- Meta: gates de qualidade operando no PR.

### Semana 5

- Refatorar cargas linha a linha para batch.
- Melhorar carga do Top 10 no core.
- Medir ganho de throughput em dataset de referencia.
- Meta: reduzir tempo de carga com resultado mensuravel.

### Semana 6

- Criar cliente HTTP comum com timeout/retry.
- Refatorar PubChem e ChEBI para reaproveitarem o cliente.
- Padronizar logs por batch.
- Meta: reduzir falhas transitórias e melhorar rastreabilidade.

### Semana 7

- Endurecer configuracao Docker e seguranca de porta.
- Revisar segredos e variaveis de ambiente.
- Escrever runbook de backup/restore/rollback.
- Meta: preparar operacao segura e repetivel.

### Semana 8

- Executar ciclo final de regressao.
- Validar checklist de producao.
- Consolidar metricas de baseline x otimizado.
- Meta: liberar versao apta a producao inicial.

---

## 8. Como usar o quadro no dia a dia

1. Mover cada tarefa de `Todo` para `Doing` quando iniciada.
2. Atualizar para `Review` ao abrir PR.
3. Marcar `Done` apenas com criterio de aceite validado.
4. Registrar bloqueios na coluna de observacoes.
5. Recalcular a soma de pontos concluidos por sprint ao fim da semana.

Se quiser acompanhar em planilha, copie os itens das sessoes 5 a 7 e use `Sprint`, `ID`, `Arquivo`, `Pontos`, `Status`, `Dono` e `Dependencias` como colunas.
