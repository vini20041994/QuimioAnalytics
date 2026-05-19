import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .database_top_10 import load_top10_to_core
from .io import load_and_merge_planilhas
from .scoring import (
    normalize_score_software,
    score_fragmentation,
    score_isotope,
    score_mass,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "staging" / "top10_candidates.parquet"
DEFAULT_BATCH_NAME = "TOP10_RANKING"
DEFAULT_TOP_N = 10

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
    top_n=DEFAULT_TOP_N,
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
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["abs_mass_error_ppm"] = df["mass_error_ppm"].abs()
    df["s_mass"] = df["abs_mass_error_ppm"].apply(score_mass)
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
    # Classificação condicional:
    # 1. fragment_score DESC (NaN = ausente, prioridade menor)
    # 2. score_original DESC (tiebreaker ou quando fragment_score ausente)
    # 3. abs_mass_error_ppm ASC (tiebreaker, desconsiderar sinal)
    # 4. isotope_similarity DESC (tiebreaker final)
    df = df.sort_values(
        ["feature_group", "fragment_score", "score_original", "abs_mass_error_ppm", "isotope_similarity"],
        ascending=[True, False, False, True, False],
        na_position="last",
    )
    df["rank"] = df.groupby("feature_group").cumcount() + 1
    df = df[df["rank"] <= int(top_n)].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    print(f"Sucesso: {len(df)} candidatos exportados para {output_path} (Top {int(top_n)})")
    print("\nCandidatos rankeados:")
    cols_exibir = [
        "rank",
        "Compound",
        "fragment_score",
        "score_original",
        "abs_mass_error_ppm",
        "isotope_similarity",
        "s_mass",
        "s_fragmentation",
        "s_isotope",
    ]
    cols_exibir = [c for c in cols_exibir if c in df.columns]
    print(df[cols_exibir].to_string(index=False))

    if load_core:
        load_top10_to_core(df, batch_name=batch_name)

    return df


def main():
    parser = argparse.ArgumentParser(description="Ranking probabilistico e carga opcional no schema core")
    parser.add_argument("--identificacao", default=str(PROJECT_ROOT / "dados_brutos" / "IDENTIFICACAO.xlsx"), help="Caminho da planilha de identificação (xlsx)")
    parser.add_argument("--abundancia", default=str(PROJECT_ROOT / "dados_brutos" / "ABUND.xlsx"), help="Caminho da planilha de abundância (xlsx)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Caminho do parquet de saida")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Quantidade maxima de candidatos por feature_group")
    parser.add_argument("--load-core", action="store_true", help="Persiste o Top 10 no schema core")
    parser.add_argument("--batch-name", default=DEFAULT_BATCH_NAME, help="Nome do batch em core.ingestion_batch")
    args = parser.parse_args()

    if args.top_n < 1:
        raise ValueError("--top-n deve ser maior ou igual a 1")

    run_probabilistic_ranking(
        identificacao_xlsx=args.identificacao,
        abund_xlsx=args.abundancia,
        output_path=args.output,
        top_n=args.top_n,
        load_core=args.load_core,
        batch_name=args.batch_name,
    )


if __name__ == "__main__":
    main()
