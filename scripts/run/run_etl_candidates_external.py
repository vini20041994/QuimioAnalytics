#!/usr/bin/env python3
"""
Orquestra consultas em bases externas a partir do arquivo de candidatos ranqueados.

Fluxo:
1. Le o arquivo de candidatos (parquet/csv/xlsx/txt).
2. Prepara artefatos de entrada para cada base externa.
3. Executa ETL PubChem, ChEBI e/ou ChemSpider.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
RUN_DIR = PROJECT_ROOT / "scripts" / "run"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"

DEFAULT_CANDIDATES_FILE = STAGING_DIR / "biological_ranking_candidates.parquet"
DEFAULT_SOURCES = ["pubchem", "chebi", "chemspider"]


def _python_exec() -> str:
    return str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def _resolve_candidates_input(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value)
    return DEFAULT_CANDIDATES_FILE


def _load_candidates_dataframe(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de candidatos nao encontrado: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    if suffix == ".txt":
        rows = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return pd.DataFrame({"compound_name": rows})

    raise ValueError(f"Formato nao suportado para candidatos: {suffix}")


def _normalize_candidates_for_api(df: pd.DataFrame) -> pd.DataFrame:
    source = df.copy()

    def first_present(columns, default=None):
        for col in columns:
            if col in source.columns:
                return source[col]
        return pd.Series([default] * len(source))

    prepared = pd.DataFrame(
        {
            "compound_name": first_present(["Description", "Compound", "compound_name", "name"]),
            "formula": first_present(["formula", "Formula", "molecular_formula"]),
            "molecular_formula": first_present(["formula", "Formula", "molecular_formula"]),
            "source_compound_id": first_present(["original_id", "Compound ID", "compound_id", "source_compound_id"]),
            "description": first_present(["Description", "description"]),
            "rank_group": first_present(["rank_group", "rank"]),
            "is_tied": first_present(["is_tied"], default=False),
        }
    )

    for col in ["compound_name", "formula", "molecular_formula", "source_compound_id", "description"]:
        prepared[col] = prepared[col].astype("string").str.strip()
        prepared[col] = prepared[col].replace({"": pd.NA})

    prepared = prepared.dropna(how="all", subset=["compound_name", "formula", "molecular_formula", "source_compound_id"])
    prepared = prepared.drop_duplicates(subset=["compound_name", "formula", "source_compound_id"], keep="first")
    return prepared.reset_index(drop=True)


def _write_inputs(df_candidates: pd.DataFrame) -> tuple[Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    api_input = STAGING_DIR / "candidates_external_input.csv"
    chemspider_input = STAGING_DIR / "candidates_chemspider_input.txt"

    df_api = _normalize_candidates_for_api(df_candidates)
    df_api.to_csv(api_input, index=False)

    preferred_names = (
        df_api["compound_name"]
        .fillna(df_api["formula"])
        .fillna(df_api["molecular_formula"])
        .dropna()
        .astype(str)
        .str.strip()
    )
    unique_names = sorted({name for name in preferred_names if name})
    chemspider_input.write_text("\n".join(unique_names), encoding="utf-8")

    return api_input, chemspider_input


def _run(cmd: list[str], step_name: str) -> None:
    print(f"\n{'=' * 70}")
    print(step_name)
    print(f"{'=' * 70}")
    print("Executando:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"Falha em {step_name} (exit={result.returncode})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Integra ETLs externos usando arquivo de candidatos ranqueados como entrada."
    )
    parser.add_argument(
        "--candidates-input",
        default=None,
        help="Arquivo de candidatos ranqueados (parquet/csv/xlsx/txt).",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["pubchem", "chebi", "chemspider"],
        default=DEFAULT_SOURCES,
        help="Quais fontes externas consultar.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates_path = _resolve_candidates_input(args.candidates_input)

    print("\n=== Integracao de Bases Externas via Candidatos ===")
    print(f"Arquivo de candidatos: {candidates_path}")
    print(f"Fontes selecionadas: {', '.join(args.sources)}")

    df_candidates = _load_candidates_dataframe(candidates_path)
    if df_candidates.empty:
        raise ValueError("Arquivo de candidatos esta vazio.")

    api_input, chemspider_input = _write_inputs(df_candidates)
    print(f"Entrada normalizada (PubChem/ChEBI): {api_input}")
    print(f"Entrada ChemSpider (TXT): {chemspider_input}")

    py = _python_exec()

    if "pubchem" in args.sources:
        _run(
            [py, str(RUN_DIR / "run_etl_pubchem.py"), str(api_input)],
            "ETL PubChem",
        )

    if "chebi" in args.sources:
        _run(
            [py, str(RUN_DIR / "run_etl_chebi.py"), str(api_input)],
            "ETL ChEBI",
        )

    if "chemspider" in args.sources:
        _run(
            [py, str(RUN_DIR / "run_etl_chemspider.py"), "--file", str(chemspider_input)],
            "ETL ChemSpider",
        )

    print("\nIntegracao concluida com sucesso.")
    print("Arquivos gerados em data/staging:")
    print("- candidates_external_input.csv")
    print("- candidates_chemspider_input.txt")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"\nErro: {exc}")
        sys.exit(1)
