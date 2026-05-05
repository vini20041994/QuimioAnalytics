#!/usr/bin/env python3
"""
Orquestra consultas em bases externas a partir do resultado Top 5.

Fluxo:
1. Lê o arquivo do Top 5 (parquet/csv/xlsx/txt).
2. Prepara artefatos de entrada para cada base externa.
3. Executa ETL PubChem, ChEBI e/ou ChemSpider.

Uso:
    python3 scripts/run/run_etl_top5_external.py
    python3 scripts/run/run_etl_top5_external.py --top5 staging/top5_candidates.parquet
    python3 scripts/run/run_etl_top5_external.py --sources pubchem chebi
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = PROJECT_ROOT / "staging"
RUN_DIR = PROJECT_ROOT / "scripts" / "run"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"

DEFAULT_TOP5 = STAGING_DIR / "top5_candidates.parquet"
DEFAULT_SOURCES = ["pubchem", "chebi", "chemspider"]


def _python_exec() -> str:
    return str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def _load_top5_dataframe(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo Top 5 não encontrado: {file_path}")

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

    raise ValueError(f"Formato não suportado para Top 5: {suffix}")


def _normalize_top5_for_api(df: pd.DataFrame) -> pd.DataFrame:
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
            "source_compound_id": first_present(["Compound ID", "compound_id", "source_compound_id"]),
            "description": first_present(["Description", "description"]),
            "rank": first_present(["rank"]),
            "probabilidade": first_present(["probabilidade", "global_probability"]),
        }
    )

    for col in ["compound_name", "formula", "molecular_formula", "source_compound_id", "description"]:
        prepared[col] = prepared[col].astype("string").str.strip()
        prepared[col] = prepared[col].replace({"": pd.NA})

    prepared = prepared.dropna(how="all", subset=["compound_name", "formula", "molecular_formula", "source_compound_id"])
    prepared = prepared.drop_duplicates(subset=["compound_name", "formula", "source_compound_id"], keep="first")
    return prepared.reset_index(drop=True)


def _write_inputs(df_top5: pd.DataFrame) -> tuple[Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    api_input = STAGING_DIR / "top5_external_input.csv"
    chemspider_input = STAGING_DIR / "top5_chemspider_input.txt"

    df_api = _normalize_top5_for_api(df_top5)
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
    print(f"{step_name}")
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
        description="Integra ETLs externos usando o resultado Top 5 como entrada."
    )
    parser.add_argument(
        "--top5",
        default=str(DEFAULT_TOP5),
        help="Arquivo Top 5 (parquet/csv/xlsx/txt).",
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
    top5_path = Path(args.top5)

    print("\n=== Integração de Bases Externas via Top 5 ===")
    print(f"Top 5 de entrada: {top5_path}")
    print(f"Fontes selecionadas: {', '.join(args.sources)}")

    df_top5 = _load_top5_dataframe(top5_path)
    if df_top5.empty:
        raise ValueError("Arquivo Top 5 está vazio.")

    api_input, chemspider_input = _write_inputs(df_top5)
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

    print("\n✅ Integração concluída com sucesso.")
    print("Arquivos gerados no staging:")
    print("- top5_external_input.csv")
    print("- top5_chemspider_input.txt")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"\n❌ Erro: {exc}")
        sys.exit(1)