import argparse
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from scripts.config import RAW_INPUTS_DIR, STAGING_DIR
from scripts.models.biological_ranking_engine import BiologicalRankingEngine
from .database_candidates import load_candidates_to_core
from .io import INPUT_CONTRACT, load_and_merge_planilhas


LOGGER = logging.getLogger(__name__)
DEFAULT_OUTPUT_PATH = STAGING_DIR / "biological_ranking_candidates.parquet"
DEFAULT_BATCH_NAME = "BIOLOGICAL_RANKING"
PIPELINE_VERSION = "IST-v2-S5"

RENAME_MAP = {
    "Neutral mass (Da)": "neutral_mass",
    "m/z": "mz",
    "Formula": "formula",
    "Score": "score_original",
    "Fragmentation Score": "fragment_score",
    "Isotope Similarity": "isotope_similarity",
    "Mass Error (ppm)": "mass_error_ppm",
    "Retention time (min)": "rt",
}

REQUIRED_COLS = ["Compound", "Adducts", "score_original", "fragment_score", "isotope_similarity", "mass_error_ppm"]


def _sha256_file(file_path):
    hash_obj = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def _iso_utc_from_ts(timestamp_value):
    return datetime.fromtimestamp(timestamp_value, tz=timezone.utc).isoformat()


def _build_lineage_metadata(identificacao_xlsx, abund_xlsx, execution_id):
    identificacao_path = Path(identificacao_xlsx)
    abundancia_path = Path(abund_xlsx)

    ident_stat = identificacao_path.stat()
    abund_stat = abundancia_path.stat()

    return {
        "execution_id": execution_id,
        "pipeline_version": PIPELINE_VERSION,
        "ingestion_timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "source_identificacao_file": str(identificacao_path.resolve()),
        "source_identificacao_sha256": _sha256_file(identificacao_path),
        "source_identificacao_mtime_utc": _iso_utc_from_ts(ident_stat.st_mtime),
        "source_abundancia_file": str(abundancia_path.resolve()),
        "source_abundancia_sha256": _sha256_file(abundancia_path),
        "source_abundancia_mtime_utc": _iso_utc_from_ts(abund_stat.st_mtime),
    }


def _find_replicate_columns(df):
    return [
        col
        for col in df.columns
        if isinstance(col, str)
        and "." in col
        and all(part.isdigit() for part in col.split(".", 1))
    ]


def _compute_abundance_metrics(df):
    cols_replicatas = _find_replicate_columns(df)
    if not cols_replicatas:
        df["media_abundancia"] = 0.0
        df["cv"] = 0.0
        return

    df[cols_replicatas] = df[cols_replicatas].apply(pd.to_numeric, errors="coerce")
    df["media_abundancia"] = df[cols_replicatas].mean(axis=1)
    df["cv"] = df[cols_replicatas].std(axis=1) / (df["media_abundancia"] + 1e-9)


def run_biological_candidate_ranking(
    identificacao_xlsx=RAW_INPUTS_DIR / "IDENTIFICACAO.xlsx",
    abund_xlsx=RAW_INPUTS_DIR / "ABUND.xlsx",
    output_path=DEFAULT_OUTPUT_PATH,
    load_core=False,
    batch_name=DEFAULT_BATCH_NAME,
):
    execution_id = uuid.uuid4().hex
    output_path = Path(output_path)

    LOGGER.info(
        "ranking_execution_started",
        extra={
            "execution_id": execution_id,
            "pipeline_version": PIPELINE_VERSION,
            "identificacao_xlsx": str(identificacao_xlsx),
            "abund_xlsx": str(abund_xlsx),
            "output_path": str(output_path),
        },
    )

    df = load_and_merge_planilhas(
        identificacao_xlsx=identificacao_xlsx,
        abund_xlsx=abund_xlsx,
        rename_map=RENAME_MAP,
        required_cols=REQUIRED_COLS,
        input_contract=INPUT_CONTRACT,
    )

    lineage_metadata = _build_lineage_metadata(
        identificacao_xlsx=identificacao_xlsx,
        abund_xlsx=abund_xlsx,
        execution_id=execution_id,
    )
    for column_name, column_value in lineage_metadata.items():
        df[column_name] = column_value

    _compute_abundance_metrics(df)

    numeric_score_cols = ["score_original", "fragment_score", "isotope_similarity", "mass_error_ppm"]
    for col in numeric_score_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Canonical column used by the ranking engine and validation contract.
    df["score"] = df["score_original"]

    if "Compound ID" in df.columns:
        df["original_id"] = df["Compound ID"]
    else:
        df["original_id"] = df["Compound"]

    df["feature_group"] = (
        df["Compound"].astype(str).str.strip()
        + "||"
        + df["Adducts"].astype(str).str.strip()
    )

    ranking_engine = BiologicalRankingEngine()
    df = ranking_engine.apply_ranking(df, group_by="feature_group")
    df["rank"] = df["rank_group"].astype(int)
    df["abs_mass_error_ppm"] = df["mass_error_ppm"].abs()

    # Contract aliases kept for downstream compatibility with IST-v2 docs.
    df["fragmentation_score"] = df["fragment_score"]
    df["mass_error"] = df["mass_error_ppm"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    LOGGER.info(
        "ranking_execution_completed",
        extra={
            "execution_id": execution_id,
            "pipeline_version": PIPELINE_VERSION,
            "output_path": str(output_path),
            "row_count": int(len(df)),
            "feature_groups": int(df["feature_group"].nunique()),
        },
    )

    print(f"Sucesso: {len(df)} candidatos exportados para {output_path} (todos os candidatos)")
    print("\nCandidatos rankeados:")
    cols_exibir = [
        "rank_group",
        "is_tied",
        "rank",
        "original_id",
        "Compound",
        "fragment_score",
        "abs_mass_error_ppm",
        "isotope_similarity",
    ]
    cols_exibir = [c for c in cols_exibir if c in df.columns]
    print(df[cols_exibir].to_string(index=False))

    if load_core:
        load_candidates_to_core(df, batch_name=batch_name)

    return df


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    parser = argparse.ArgumentParser(description="Ranking biologico e carga opcional no schema core")
    parser.add_argument("--identificacao", default=str(RAW_INPUTS_DIR / "IDENTIFICACAO.xlsx"), help="Caminho da planilha de identificação (xlsx)")
    parser.add_argument("--abundancia", default=str(RAW_INPUTS_DIR / "ABUND.xlsx"), help="Caminho da planilha de abundância (xlsx)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Caminho do parquet de saida")
    parser.add_argument("--load-core", action="store_true", help="Persiste candidatos no schema core")
    parser.add_argument("--batch-name", default=DEFAULT_BATCH_NAME, help="Nome do batch em core.ingestion_batch")
    args = parser.parse_args()

    run_biological_candidate_ranking(
        identificacao_xlsx=args.identificacao,
        abund_xlsx=args.abundancia,
        output_path=args.output,
        load_core=args.load_core,
        batch_name=args.batch_name,
    )


if __name__ == "__main__":
    main()
