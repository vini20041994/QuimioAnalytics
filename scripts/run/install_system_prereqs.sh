#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

AUTO_YES="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      AUTO_YES="true"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Uso: scripts/run/install_system_prereqs.sh [--yes]

Instala pre-requisitos de sistema para Linux (Debian/Ubuntu via apt):
- python3, python3-venv, python3-pip
- docker.io, docker-compose-plugin

Opcoes:
  -y, --yes    Nao pede confirmacao antes de instalar
  -h, --help   Exibe esta ajuda
EOF
      exit 0
      ;;
    *)
      echo "[ERRO] Opcao invalida: $1"
      exit 1
      ;;
  esac
done

log() {
  echo "[setup] $*"
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

require_sudo() {
  if ! has_cmd sudo; then
    echo "[ERRO] sudo nao encontrado. Instale sudo ou execute como root."
    exit 1
  fi
}

detect_linux_id() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    echo "${ID:-linux}"
    return
  fi
  echo "linux"
}

prompt_confirm() {
  if [[ "$AUTO_YES" == "true" ]]; then
    return 0
  fi

  read -r -p "Instalar/atualizar pre-requisitos agora? [s/N] " answer
  case "$answer" in
    s|S|sim|SIM|y|Y|yes|YES) return 0 ;;
    *)
      log "Instalacao cancelada pelo usuario."
      exit 0
      ;;
  esac
}

install_apt_packages() {
  local -a pkgs=(
    python3
    python3-venv
    python3-pip
    docker.io
    docker-compose-plugin
  )

  local -a missing=()
  for pkg in "${pkgs[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    log "Pacotes principais ja estao instalados."
  else
    log "Pacotes ausentes detectados: ${missing[*]}"
    prompt_confirm
    require_sudo
    sudo apt-get update
    sudo apt-get install -y "${missing[@]}"
  fi
}

ensure_docker_running() {
  if ! has_cmd docker; then
    echo "[ERRO] docker nao esta disponivel no PATH apos instalacao."
    exit 1
  fi

  if has_cmd systemctl; then
    require_sudo
    sudo systemctl enable --now docker >/dev/null 2>&1 || true
  fi

  if docker info >/dev/null 2>&1; then
    log "Docker acessivel para o usuario atual."
    return
  fi

  log "Sem permissao de acesso ao Docker para o usuario atual."
  if id -nG "$USER" | grep -qw docker; then
    echo "[ERRO] Usuario no grupo docker, mas sessao atual nao refletiu permissao."
    echo "      Saia e entre novamente na sessao e rode o comando de execucao completa."
    exit 1
  fi

  require_sudo
  sudo usermod -aG docker "$USER"
  echo "[ERRO] Usuario adicionado ao grupo docker."
  echo "      Faca logout/login (ou reinicie a sessao) e execute novamente."
  exit 1
}

ensure_compose() {
  if docker compose version >/dev/null 2>&1; then
    log "Docker Compose plugin disponivel (docker compose)."
    return
  fi

  if has_cmd docker-compose; then
    log "docker-compose classico disponivel."
    return
  fi

  echo "[ERRO] Docker Compose nao encontrado (nem plugin, nem binario classico)."
  exit 1
}

main() {
  local linux_id
  linux_id="$(detect_linux_id)"
  log "Sistema detectado: $linux_id"

  case "$linux_id" in
    ubuntu|debian|linuxmint|pop)
      install_apt_packages
      ;;
    *)
      echo "[ERRO] Distribuicao nao suportada automaticamente por este script: $linux_id"
      echo "      Suporte automatico atual: Debian/Ubuntu (apt)."
      echo "      Consulte o manual em docs/SETUP_PRIMEIRA_EXECUCAO.md."
      exit 1
      ;;
  esac

  ensure_docker_running
  ensure_compose

  log "Pre-requisitos de sistema verificados/instalados com sucesso."
}

main "$@"
