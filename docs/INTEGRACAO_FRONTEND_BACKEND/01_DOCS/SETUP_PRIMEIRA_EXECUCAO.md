# Setup de Primeira Execucao (Linux)

Este guia permite preparar a maquina do zero e rodar o pipeline completo com um unico comando.

## 1. O que foi criado

- Script de pre-requisitos do sistema: scripts/run/install_system_prereqs.sh
- Script de primeira execucao integrada: scripts/run/primeira_execucao.sh

## 2. O que esse fluxo automatiza

1. Verifica/instala Python 3, venv e pip.
2. Verifica/instala Docker e Docker Compose.
3. Executa o orquestrador full-stack:
   - cria/usa venv,
   - sobe banco,
   - aplica schema e migrations,
   - roda ETL interno,
   - gera Top 5,
   - opcionalmente integra bases externas.

## 3. Passo a passo rapido

No diretorio raiz do projeto:

```bash
cd /home/vinicius_joacir/QuimioAnalytics
chmod +x scripts/run/install_system_prereqs.sh scripts/run/primeira_execucao.sh
./scripts/run/primeira_execucao.sh --db-pass "SUA_SENHA"
```

## 4. Execucao recomendada (com integracao externa)

```bash
./scripts/run/primeira_execucao.sh --db-pass "SUA_SENHA" --with-external
```

## 5. Opcoes uteis

- Pular instalacao de pre-requisitos (maquina ja preparada):

```bash
./scripts/run/primeira_execucao.sh --db-pass "SUA_SENHA" --skip-install
```

- Usar planilhas customizadas:

```bash
./scripts/run/primeira_execucao.sh \
  --db-pass "SUA_SENHA" \
  --identificacao /caminho/IDENTIFICACAO.xlsx \
  --abundancia /caminho/ABUND.xlsx \
  --compostos /caminho/Compostos_final.xlsx \
  --overwrite-inputs
```

- Nao carregar Top 5 no core:

```bash
./scripts/run/primeira_execucao.sh --db-pass "SUA_SENHA" --no-load-core
```

## 6. Mensagens comuns

- "Usuario adicionado ao grupo docker"
  - Faça logout/login e execute novamente.

- "Distribuicao nao suportada automaticamente"
  - O instalador automatico atual cobre Debian/Ubuntu (apt).
  - Em outras distros, instale Python 3 + venv + Docker + Compose manualmente e rode com --skip-install.

## 7. Fluxo alternativo (dois comandos)

Se quiser separar instalacao e execucao:

```bash
./scripts/run/install_system_prereqs.sh --yes
python3 scripts/run/run_pipeline_frontend.py --full-stack --db-pass "SUA_SENHA" --load-core
```
