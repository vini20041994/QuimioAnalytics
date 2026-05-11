import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .database_top_5 import load_top5_to_core
from .io import load_and_merge_planilhas
from .scoring import (
    normalize_score_software,
    score_fragmentation,
    score_isotope,
    score_mass,
    softmax_per_feature,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "staging" / "top5_candidates.parquet"
DEFAULT_BATCH_NAME = "TOP5_RANKING"

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


def run_probabilistic_ranking(
    identificacao_xlsx=PROJECT_ROOT / "dados_brutos" / "IDENTIFICACAO.xlsx",
    abund_xlsx=PROJECT_ROOT / "dados_brutos" / "ABUND.xlsx",
    output_path=DEFAULT_OUTPUT_PATH,
    load_core=False,
    batch_name=DEFAULT_BATCH_NAME,
):
    output_path = Path(output_path)
    df = load_and_merge_planilhas(
        identificacao_xlsx=identificacao_xlsx,
        abund_xlsx=abund_xlsx,
        rename_map=RENAME_MAP,
        required_cols=REQUIRED_COLS,
    )

    _compute_abundance_metrics(df)

    numeric_score_cols = ["score_original", "fragment_score", "isotope_similarity", "mass_error_ppm"]
    for col in numeric_score_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["s_mass"] = df["mass_error_ppm"].abs().apply(score_mass)
    df["s_fragmentation"] = df["fragment_score"].apply(score_fragmentation)
    df["s_isotope"] = df["isotope_similarity"].apply(score_isotope)

    df["score_base"] = (df["s_mass"] + df["s_fragmentation"] + df["s_isotope"]) / 3.0

    score_min = df["score_original"].min()
    score_max = df["score_original"].max()
    df["score_software"] = df["score_original"].apply(
        lambda value: normalize_score_software(value, score_min, score_max)
    )

    abundance_factor = np.log1p(df["media_abundancia"]) * (1.0 / (1.0 + df["cv"]))
    df["score_final"] = (
        df["score_base"] * (0.5 + 0.5 * df["score_software"]) * abundance_factor
    ).fillna(0)

    df["feature_group"] = (
        df["Compound"].astype(str).str.strip()
        + "||"
        + df["Adducts"].astype(str).str.strip()
    )
    df["probabilidade"] = softmax_per_feature(df, feature_col="feature_group", score_col="score_final")

    df = df.sort_values(["feature_group", "probabilidade"], ascending=[True, False])
    df["rank"] = df.groupby("feature_group").cumcount() + 1
    df_top5 = df[df["rank"] <= 5].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_top5.to_parquet(output_path, index=False)

    print(f"Sucesso: {len(df_top5)} candidatos exportados para {output_path}")
    print("\nTop 5 candidatos mais prováveis:")
    cols_exibir = [
        "rank",
        "Compound",
        "s_mass",
        "s_fragmentation",
        "s_isotope",
        "score_software",
        "score_final",
        "probabilidade",
    ]
    cols_exibir = [c for c in cols_exibir if c in df_top5.columns]
    print(df_top5[cols_exibir].to_string(index=False))

    if load_core:
        load_top5_to_core(df_top5, batch_name=batch_name)

    return df_top5


def main():
    parser = argparse.ArgumentParser(description="Ranking probabilistico e carga opcional no schema core")
    parser.add_argument("--identificacao", default=str(PROJECT_ROOT / "dados_brutos" / "IDENTIFICACAO.xlsx"), help="Caminho da planilha de identificação (xlsx)")
    parser.add_argument("--abundancia", default=str(PROJECT_ROOT / "dados_brutos" / "ABUND.xlsx"), help="Caminho da planilha de abundância (xlsx)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Caminho do parquet de saida")
    parser.add_argument("--load-core", action="store_true", help="Persiste o Top 5 no schema core")
    parser.add_argument("--batch-name", default=DEFAULT_BATCH_NAME, help="Nome do batch em core.ingestion_batch")
    args = parser.parse_args()

    run_probabilistic_ranking(
        identificacao_xlsx=args.identificacao,
        abund_xlsx=args.abundancia,
        output_path=args.output,
        load_core=args.load_core,
        batch_name=args.batch_name,
    )


if __name__ == "__main__":
    main()
