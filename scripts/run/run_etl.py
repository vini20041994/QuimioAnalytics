#!/usr/bin/env python3
"""
Pipeline ETL principal: Extract → Transform → Load

Uso:
    python3 scripts/run/run_etl.py
    python3 scripts/run/run_etl.py --identificacao path/ident.xlsx --abundancia path/abund.xlsx

Variaveis de ambiente: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
"""
import sys
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"

EXTRACT_SCRIPT   = PROJECT_ROOT / "scripts" / "extract" / "extract_stg_xlsx.py"
TRANSFORM_SCRIPT = PROJECT_ROOT / "scripts" / "transform" / "transform_stg_xlsx.py"
LOAD_SCRIPT      = PROJECT_ROOT / "scripts" / "load" / "load_stg_transformed.py"


def _python_exec():
    return str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def run_step(script_path, step_name, extra_args=None):
    print(f"\n{'=' * 60}\n{step_name}\n{'=' * 60}")
    cmd = [_python_exec(), str(script_path)] + (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    print(f"{step_name} concluido!")
    return result.stdout


def parse_args():
    parser = argparse.ArgumentParser(description="ETL principal (Extract -> Transform -> Load).")
    parser.add_argument("--identificacao", help="Planilha de identificacao.")
    parser.add_argument("--abundancia",    help="Planilha de abundancia.")
    parser.add_argument("--compostos",     help="Planilha de compostos curados.")
    return parser.parse_args()


def main():
    args = parse_args()

    extra_args = []
    if args.identificacao:
        extra_args += ["--identificacao", args.identificacao]
    if args.abundancia:
        extra_args += ["--abundancia", args.abundancia]
    if args.compostos:
        extra_args += ["--compostos", args.compostos]

    run_step(EXTRACT_SCRIPT,   "EXTRACT", extra_args)
    run_step(TRANSFORM_SCRIPT, "TRANSFORM")
    output = run_step(LOAD_SCRIPT, "LOAD")

    print("\nPipeline ETL concluido.")
    if output:
        print(output)


if __name__ == "__main__":
    main()

