#!/usr/bin/env python3
"""
ETL ChemSpider: Extract → Transform → Load

Uso:
    python3 run_etl_chemspider.py --file <arquivo_entrada>
    python3 run_etl_chemspider.py --description Caffeine Aspirin
    python3 run_etl_chemspider.py --compound_id 2424 171
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

    py = _python_exec()
    run_step([py, str(SCRIPTS_DIR / "extract" / "extract_chemspider.py"), *sys.argv[1:]],
             "EXTRACT - ChemSpider")
    run_step([py, str(SCRIPTS_DIR / "transform" / "transform_chemspider.py")],
             "TRANSFORM")
    run_step([py, str(SCRIPTS_DIR / "load" / "load_chemspider.py")],
             "LOAD - PostgreSQL")

    print("\nETL ChemSpider concluido.")
    print("Tabelas: stg.chemspider_compound_raw | ref.external_compound | ref.compound_cross_reference")


if __name__ == "__main__":
    main()

