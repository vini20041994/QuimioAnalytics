#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="quimioanalytics"
DB_USER="quimio_user"
DB_PASS=""

RUN_EXTERNAL="false"
LOAD_CORE="true"
OVERWRITE_INPUTS="false"
SKIP_INSTALL="false"

IDENTIFICACAO=""
ABUNDANCIA=""
COMPOSTOS=""

usage() {
  cat <<'EOF'
Uso:
  scripts/run/primeira_execucao.sh --db-pass <SENHA>

Objetivo:
  Executar primeira configuracao da maquina + pipeline completo em uma chamada.

O que o script faz:
  1) Instala/verifica pre-requisitos de sistema (Python e Docker) no Linux apt
  2) Executa orquestrador full-stack (venv, banco, schema/migrations, ETL, Top 5)

Opcoes:
  --db-pass VALOR            Senha do PostgreSQL (obrigatorio)
  --db-host VALOR            Host do banco (padrao: localhost)
  --db-port VALOR            Porta do banco (padrao: 5432)
  --db-name VALOR            Nome do banco (padrao: quimioanalytics)
  --db-user VALOR            Usuario do banco (padrao: quimio_user)

  --identificacao ARQ.xlsx   Planilha IDENTIFICACAO customizada
  --abundancia ARQ.xlsx      Planilha ABUND customizada
  --compostos ARQ.xlsx       Planilha Compostos_final customizada
  --overwrite-inputs         Permite sobrescrever dados_brutos

  --with-external            Executa ETLs externos (PubChem/ChEBI/ChemSpider)
  --no-load-core             Nao persiste Top 5 no schema core
  --skip-install             Pula etapa de instalacao de pre-requisitos

  -h, --help                 Exibe esta ajuda
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-pass)
      DB_PASS="${2:-}"
      shift 2
      ;;
    --db-host)
      DB_HOST="${2:-}"
      shift 2
      ;;
    --db-port)
      DB_PORT="${2:-}"
      shift 2
      ;;
    --db-name)
      DB_NAME="${2:-}"
      shift 2
      ;;
    --db-user)
      DB_USER="${2:-}"
      shift 2
      ;;
    --identificacao)
      IDENTIFICACAO="${2:-}"
      shift 2
      ;;
    --abundancia)
      ABUNDANCIA="${2:-}"
      shift 2
      ;;
    --compostos)
      COMPOSTOS="${2:-}"
      shift 2
      ;;
    --overwrite-inputs)
      OVERWRITE_INPUTS="true"
      shift
      ;;
    --with-external)
      RUN_EXTERNAL="true"
      shift
      ;;
    --no-load-core)
      LOAD_CORE="false"
      shift
      ;;
    --skip-install)
      SKIP_INSTALL="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERRO] Opcao invalida: $1"
      echo
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$DB_PASS" ]]; then
  echo "[ERRO] Informe --db-pass <SENHA>."
  exit 1
fi

if [[ "$SKIP_INSTALL" != "true" ]]; then
  echo "[primeira-execucao] Instalando/verificando pre-requisitos..."
  bash "$ROOT_DIR/scripts/run/install_system_prereqs.sh" --yes
fi

CMD=(
  python3
  scripts/run/run_pipeline_frontend.py
  --full-stack
  --db-host "$DB_HOST"
  --db-port "$DB_PORT"
  --db-name "$DB_NAME"
  --db-user "$DB_USER"
  --db-pass "$DB_PASS"
)

if [[ "$LOAD_CORE" == "true" ]]; then
  CMD+=(--load-core)
fi

if [[ "$RUN_EXTERNAL" == "true" ]]; then
  CMD+=(--run-external)
fi

if [[ -n "$IDENTIFICACAO" ]]; then
  CMD+=(--identificacao "$IDENTIFICACAO")
fi
if [[ -n "$ABUNDANCIA" ]]; then
  CMD+=(--abundancia "$ABUNDANCIA")
fi
if [[ -n "$COMPOSTOS" ]]; then
  CMD+=(--compostos "$COMPOSTOS")
fi
if [[ "$OVERWRITE_INPUTS" == "true" ]]; then
  CMD+=(--overwrite-inputs)
fi

echo "[primeira-execucao] Executando pipeline full-stack..."
echo "[primeira-execucao] Comando: ${CMD[*]}"

export PYTHONPATH="${PYTHONPATH:-.}"
"${CMD[@]}"
