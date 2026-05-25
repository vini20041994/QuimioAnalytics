#!/usr/bin/env python3
"""
Orquestra consultas em bases externas a partir do arquivo de candidatos ranqueados.

Fluxo:
1. Le o arquivo de candidatos (parquet/csv/xlsx/txt).
2. Prepara artefatos de entrada para cada base externa.
3. Executa ETL PubChem, ChEBI e/ou ChemSpider.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
RUN_DIR = PROJECT_ROOT / "scripts" / "run"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"

DEFAULT_CANDIDATES_FILE = STAGING_DIR / "biological_ranking_candidates.parquet"
DEFAULT_SOURCES = ["pubchem", "chebi", "classyfire"]


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
            "inchikey": first_present(["inchikey", "InChIKey"]),
            "rank_group": first_present(["rank_group", "rank"]),
            "is_tied": first_present(["is_tied"], default=False),
        }
    )

    for col in ["compound_name", "formula", "molecular_formula", "source_compound_id", "description", "inchikey"]:
        prepared[col] = prepared[col].astype("string").str.strip()
        prepared[col] = prepared[col].replace({"": pd.NA})

    prepared = prepared.dropna(how="all", subset=["compound_name", "formula", "molecular_formula", "source_compound_id"])
    prepared = prepared.drop_duplicates(subset=["compound_name", "formula", "source_compound_id"], keep="first")
    return prepared.reset_index(drop=True)


def _write_inputs(df_candidates: pd.DataFrame) -> tuple[Path, Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    api_input = STAGING_DIR / "candidates_external_input.csv"
    chemspider_input = STAGING_DIR / "candidates_chemspider_input.txt"
    classyfire_input = STAGING_DIR / "candidates_classyfire_input.txt"

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

    inchikeys = (
        df_api["inchikey"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    unique_inchikeys = sorted({value for value in inchikeys if value})
    classyfire_input.write_text("\n".join(unique_inchikeys), encoding="utf-8")

    return api_input, chemspider_input, classyfire_input


def _run(cmd: list[str], step_name: str) -> dict:
    print(f"\n{'=' * 70}")
    print(step_name)
    print(f"{'=' * 70}")
    print("Executando:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.stdout:
        print(result.stdout)

    status = {
        "step": step_name,
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "stderr": result.stderr.strip() if result.stderr else "",
    }

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        print(f"Aviso: falha em {step_name} (exit={result.returncode}). O lote seguira para as demais fontes.")

    return status


def _build_enriched_snapshot(statuses: list[dict], queried_at: str) -> Path:
    rows = []

    pubchem_path = STAGING_DIR / "pubchem_raw.parquet"
    if pubchem_path.exists():
        df_pubchem = pd.read_parquet(pubchem_path)
        for _, row in df_pubchem.iterrows():
            rows.append(
                {
                    "standardized_name": row.get("IUPACName") or row.get("Title") or row.get("original_identifier"),
                    "description": row.get("pubchem_description"),
                    "chemical_class": None,
                    "chemical_subclass": None,
                    "enrichment_source": "PubChem",
                    "enrichment_queried_at": queried_at,
                }
            )

    chebi_path = STAGING_DIR / "chebi_raw.parquet"
    if chebi_path.exists():
        df_chebi = pd.read_parquet(chebi_path)
        for _, row in df_chebi.iterrows():
            rows.append(
                {
                    "standardized_name": row.get("chebi_name") or row.get("compound_name"),
                    "description": row.get("definition"),
                    "chemical_class": row.get("chemical_role_text"),
                    "chemical_subclass": None,
                    "enrichment_source": "ChEBI",
                    "enrichment_queried_at": queried_at,
                }
            )

    classyfire_path = STAGING_DIR / "classyfire_raw.parquet"
    if classyfire_path.exists():
        df_classyfire = pd.read_parquet(classyfire_path)
        for _, row in df_classyfire.iterrows():
            rows.append(
                {
                    "standardized_name": row.get("inchikey"),
                    "description": None,
                    "chemical_class": row.get("Chemical_Class"),
                    "chemical_subclass": row.get("Chemical_Subclass"),
                    "enrichment_source": "ClassyFire",
                    "enrichment_queried_at": queried_at,
                }
            )

    snapshot = pd.DataFrame(
        rows,
        columns=[
            "standardized_name",
            "description",
            "chemical_class",
            "chemical_subclass",
            "enrichment_source",
            "enrichment_queried_at",
        ],
    )
    snapshot = snapshot.dropna(how="all", subset=["standardized_name", "description", "chemical_class", "chemical_subclass"])

    output_path = STAGING_DIR / "external_enrichment_snapshot.parquet"
    snapshot.to_parquet(output_path, index=False)

    report = {
        "queried_at": queried_at,
        "source_status": statuses,
        "snapshot_rows": int(len(snapshot)),
        "snapshot_file": str(output_path),
    }
    (STAGING_DIR / "external_enrichment_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    failed_sources = [item for item in statuses if not item.get("ok")]
    if failed_sources:
        pending = {
            "queried_at": queried_at,
            "pending_retry": failed_sources,
        }
        (STAGING_DIR / "external_enrichment_pending_retry.json").write_text(
            json.dumps(pending, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return output_path


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
        choices=["pubchem", "chebi", "chemspider", "classyfire"],
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

    api_input, chemspider_input, classyfire_input = _write_inputs(df_candidates)
    print(f"Entrada normalizada (PubChem/ChEBI): {api_input}")
    print(f"Entrada ChemSpider (TXT): {chemspider_input}")
    print(f"Entrada ClassyFire (TXT): {classyfire_input}")

    py = _python_exec()
    statuses = []

    if "pubchem" in args.sources:
        statuses.append(_run(
            [py, str(RUN_DIR / "run_etl_pubchem.py"), str(api_input)],
            "ETL PubChem",
        ))

    if "chebi" in args.sources:
        statuses.append(_run(
            [py, str(RUN_DIR / "run_etl_chebi.py"), str(api_input)],
            "ETL ChEBI",
        ))

    if "chemspider" in args.sources:
        statuses.append(_run(
            [py, str(RUN_DIR / "run_etl_chemspider.py"), "--file", str(chemspider_input)],
            "ETL ChemSpider",
        ))

    if "classyfire" in args.sources:
        statuses.append(_run(
            [py, str(PROJECT_ROOT / "scripts" / "extract" / "extract_classyfire.py"), str(classyfire_input)],
            "ETL ClassyFire",
        ))

    queried_at = datetime.now(tz=timezone.utc).isoformat()
    snapshot_file = _build_enriched_snapshot(statuses=statuses, queried_at=queried_at)

    print("\nIntegracao concluida com sucesso.")
    print("Arquivos gerados em data/staging:")
    print("- candidates_external_input.csv")
    print("- candidates_chemspider_input.txt")
    print("- candidates_classyfire_input.txt")
    print(f"- {snapshot_file.name}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"\nErro: {exc}")
        sys.exit(1)
