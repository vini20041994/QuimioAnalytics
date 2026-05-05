#!/usr/bin/env python3
"""
ETL ChEBI: Extract → Transform → Load

Uso:
    python3 run_etl_chebi.py <arquivo_entrada>

Exemplo:
    python3 run_etl_chebi.py staging/top5_external_input.csv
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"


def _python_exec():
    return str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def run_step(cmd, step_name):
    print(f"\n{'=' * 60}\n{step_name}\n{'=' * 60}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    print(f"{step_name} concluido!")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Arquivo nao encontrado: {input_file}")
        sys.exit(1)

    py = _python_exec()
    run_step([py, str(SCRIPTS_DIR / "extract" / "extract_chebi.py"), str(input_file)],
             "EXTRACT - ChEBI API")
    run_step([py, str(SCRIPTS_DIR / "transform" / "transform_chebi.py")],
             "TRANSFORM")
    run_step([py, str(SCRIPTS_DIR / "load" / "load_chebi.py")],
             "LOAD - PostgreSQL")

    print("\nETL ChEBI concluido.")
    print("Tabelas: stg.chebi_compound_raw | ref.external_compound | ref.external_identifier")


if __name__ == "__main__":
    main()
