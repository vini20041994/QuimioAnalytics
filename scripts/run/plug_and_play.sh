#!/usr/bin/env bash

set -euo pipefail

ensure_docker() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    return
  fi

  if [[ "$(uname -s)" == "Linux" ]]; then
    echo "[plug-and-play] Docker nÃ£o encontrado. Instalando Docker e Docker Compose..."
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"
    echo "[plug-and-play] Docker instalado. Reinicie o terminal para ativar o grupo docker e rode novamente este script."
    exit 0
  else
    echo "[plug-and-play] Docker nÃ£o encontrado. Instale manualmente o Docker Desktop e o WSL no Windows."
    exit 1
  fi
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'EOF'
Uso:
  scripts/run/plug_and_play.sh up
  scripts/run/plug_and_play.sh down
  scripts/run/plug_and_play.sh logs [servico]

Comandos:
  up      Sobe PostgreSQL, backend e frontend com build.
  down    Derruba a stack criada pelo docker compose.
  logs    Exibe logs da stack (ou de um servico especifico).
EOF
}

resolve_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1 && flatpak-spawn --host docker compose version >/dev/null 2>&1; then
    echo "flatpak-spawn --host docker compose"
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1 && flatpak-spawn --host docker-compose --version >/dev/null 2>&1; then
    echo "flatpak-spawn --host docker-compose"
    return
  fi

  echo "[ERRO] Docker Compose nao encontrado no ambiente atual." >&2
  exit 1
}

#!/usr/bin/env bash

set -euo pipefail

ensure_docker() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    return
  fi

  if [[ "$(uname -s)" == "Linux" ]]; then
    echo "[plug-and-play] Docker nÃ£o encontrado. Instalando Docker e Docker Compose..."
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"
    echo "[plug-and-play] Docker instalado. Reinicie o terminal para ativar o grupo docker e rode novamente este script."
    exit 0
  else
    echo "[plug-and-play] Docker nÃ£o encontrado. Instale manualmente o Docker Desktop e o WSL no Windows."
    exit 1
  fi
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'EOF'
Uso:
  scripts/run/plug_and_play.sh up
  scripts/run/plug_and_play.sh down
  scripts/run/plug_and_play.sh logs [servico]

Comandos:
  up      Sobe PostgreSQL, backend e frontend com build.
  down    Derruba a stack criada pelo docker compose.
  logs    Exibe logs da stack (ou de um servico especifico).
EOF
}

resolve_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1 && flatpak-spawn --host docker compose version >/dev/null 2>&1; then
    echo "flatpak-spawn --host docker compose"
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1 && flatpak-spawn --host docker-compose --version >/dev/null 2>&1; then
    echo "flatpak-spawn --host docker-compose"
    return
  fi

  echo "[ERRO] Docker Compose nao encontrado no ambiente atual." >&2
  exit 1
}

ensure_env_file() {
  if [[ -f .env ]]; then
    return
  fi

  if [[ ! -f .env.example ]]; then
    echo "[ERRO] Arquivo .env.example nao encontrado." >&2
    exit 1
  fi

  cp .env.example .env
  echo "[plug-and-play] .env criado a partir de .env.example"
}

ensure_db_pass() {
  local db_pass
  db_pass="$(grep -E '^DB_PASS=' .env | head -n1 | cut -d'=' -f2- || true)"
  if [[ -z "${db_pass// }" ]]; then
    echo "[ERRO] DB_PASS vazio no arquivo .env. Ajuste o valor e rode novamente." >&2
    exit 1
  fi
}

is_port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$port )" 2>/dev/null | grep -q LISTEN
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1; then
    flatpak-spawn --host sh -lc "ss -ltn '( sport = :$port )' 2>/dev/null | grep -q LISTEN"
    return
  fi

  return 1
}

resolve_backend_port() {
  local configured_port
  configured_port="$(grep -E '^BACKEND_PORT=' .env | head -n1 | cut -d'=' -f2- || true)"
  configured_port="${configured_port:-8000}"

  if ! is_port_in_use "$configured_port"; then
    echo "$configured_port"
    return
  fi

  local candidate
  for candidate in 8001 8002 8003 8004 8005 8010; do
    if ! is_port_in_use "$candidate"; then
      echo "$candidate"
      return
    fi
  done

  echo "[ERRO] Nenhuma porta disponivel para o backend (8000-8010)." >&2
  exit 1
}

create_runtime_env_file() {
  local backend_port="$1"
  local runtime_env
  runtime_env="$ROOT_DIR/.env.runtime.generated"

  cat .env > "$runtime_env"
  {
    echo "BACKEND_PORT=$backend_port"
    echo "BACKEND_DB_HOST=postgres"
    echo "VITE_API_BASE_URL=http://localhost:$backend_port"
  } >> "$runtime_env"

  echo "$runtime_env"
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  ensure_docker

  local action="$1"
  local service="${2:-}"
  local compose_cmd
  local backend_port
  local runtime_env

  compose_cmd="$(resolve_compose_cmd)"

  case "$action" in
    up)
      ensure_env_file
      ensure_db_pass
      backend_port="$(resolve_backend_port)"
      runtime_env="$(create_runtime_env_file "$backend_port")"
      if [[ "$backend_port" != "${BACKEND_PORT:-8000}" ]]; then
        echo "[plug-and-play] Porta 8000 ocupada; usando BACKEND_PORT=$backend_port para esta execucao."
      fi
      echo "[plug-and-play] Subindo stack com: $compose_cmd up -d --build"
      eval "$compose_cmd --env-file $runtime_env up -d --build"
      echo
      eval "$compose_cmd --env-file $runtime_env ps"
      rm -f "$runtime_env"
      echo
      echo "[plug-and-play] Aplicacao pronta:"
      echo "  - API: http://localhost:${backend_port}/api/v1/health"
      echo "  - Frontend: http://localhost:${FRONTEND_PORT:-5173}"
      ;;
    down)
      echo "[plug-and-play] Derrubando stack..."
      eval "$compose_cmd down"
      ;;
    logs)
      if [[ -n "$service" ]]; then
        eval "$compose_cmd logs --tail=200 $service"
      else
        eval "$compose_cmd logs --tail=200"
      fi
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
