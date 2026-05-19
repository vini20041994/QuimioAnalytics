#!/usr/bin/env python3
"""
Runner interativo para ETL principal.
Permite ao usuario informar os arquivos de Identificacao e Abundancia,
copiando-os automaticamente para a pasta data/raw_inputs/.
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_INPUTS_DIR = PROJECT_ROOT / "data" / "raw_inputs"
RUN_ETL_SCRIPT = PROJECT_ROOT / "scripts" / "run" / "run_etl.py"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"

DESTINO_IDENTIFICACAO = RAW_INPUTS_DIR / "IDENTIFICACAO.xlsx"
DESTINO_ABUNDANCIA = RAW_INPUTS_DIR / "ABUND.xlsx"
COMPOSTOS_PATH = RAW_INPUTS_DIR / "Compostos_final.xlsx"


def prompt_existing_file(label: str) -> Path:
    while True:
        user_input = input(f"{label}: ").strip()
        if not user_input:
            print("Caminho nao pode ser vazio. Tente novamente.")
            continue
        chosen = Path(user_input).expanduser()
        if chosen.exists() and chosen.is_file():
            return chosen.resolve()
        print(f"Arquivo nao encontrado: {chosen}. Informe um caminho valido.")


def copy_to_raw_inputs(origem: Path, destino: Path) -> None:
    RAW_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        resposta = input(
            f"'{destino.name}' ja existe em data/raw_inputs/. Substituir? [s/N]: "
        ).strip().lower()
        if resposta != "s":
            print(f"Mantendo arquivo existente: {destino}")
            return
    shutil.copy2(origem, destino)
    print(f"Copiado: {origem.name} -> data/raw_inputs/{destino.name}")


def main():
    print("\n=== ETL Principal (Identificacao + Abundancia) ===")
    print("Informe os caminhos das planilhas para adicioná-las ao projeto.\n")

    identificacao_origem = prompt_existing_file(
        "Caminho da planilha de Identificacao (.xlsx)"
    )
    abundancia_origem = prompt_existing_file(
        "Caminho da planilha de Abundancia (.xlsx)"
    )

    print()
    copy_to_raw_inputs(identificacao_origem, DESTINO_IDENTIFICACAO)
    copy_to_raw_inputs(abundancia_origem, DESTINO_ABUNDANCIA)

    python_exec = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)

    cmd = [
        str(python_exec),
        str(RUN_ETL_SCRIPT),
        "--identificacao",
        str(DESTINO_IDENTIFICACAO),
        "--abundancia",
        str(DESTINO_ABUNDANCIA),
        "--compostos",
        str(COMPOSTOS_PATH),
    ]

    print("\nIniciando pipeline...\n")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
