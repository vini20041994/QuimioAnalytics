#!/usr/bin/env python3
"""
ETL ClassyFire: Extract -> Transform -> Load

Uso:
    python3 run_etl_classyfire.py <arquivo_entrada>

Exemplo:
    python3 run_etl_classyfire.py data/staging/candidates_classyfire_input.txt
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"


def _python_exec() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return str(Path(sys.executable))


def run_step(cmd: list[str], step_name: str) -> None:
    print(f"\n{'=' * 60}\n{step_name}\n{'=' * 60}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    print(f"{step_name} concluido!")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Arquivo nao encontrado: {input_file}")
        sys.exit(1)

    py = _python_exec()
    run_step(
        [py, str(SCRIPTS_DIR / "extract" / "extract_classyfire.py"), str(input_file)],
        "EXTRACT - ClassyFire API",
    )
    run_step(
        [py, str(SCRIPTS_DIR / "transform" / "transform_classyfire.py")],
        "TRANSFORM",
    )
    run_step(
        [py, str(SCRIPTS_DIR / "load" / "load_classyfire.py")],
        "LOAD - PostgreSQL",
    )

    print("\nETL ClassyFire concluido.")
    print("Tabelas: stg.classyfire_compound_raw | ref.external_compound | ref.external_identifier")


if __name__ == "__main__":
    main()