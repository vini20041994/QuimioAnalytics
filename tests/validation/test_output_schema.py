import pandas as pd
import pytest

from scripts.features.analytics import run_biological_candidate_ranking


@pytest.mark.validation
def test_output_schema_contains_required_columns_and_rank_group_is_valid(tmp_path):
    ident_path = tmp_path / "IDENTIFICACAO.xlsx"
    abund_path = tmp_path / "ABUND.xlsx"
    output_path = tmp_path / "biological_ranking_candidates.parquet"

    df_ident = pd.DataFrame(
        {
            "Compound": ["cmp1", "cmp2"],
            "Adducts": ["[M+H]+", "[M+H]+"],
            "Score": [90.0, 85.0],
            "Fragmentation Score": [80.0, 70.0],
            "Isotope Similarity": [88.0, 82.0],
            "Mass Error (ppm)": [1.2, 1.8],
            "Formula": ["C6H12O6", "C5H10O5"],
            "Compound ID": ["ID-1", "ID-2"],
            "m/z": [180.063, 150.052],
            "Retention time (min)": [1.25, 1.75],
        }
    )
    df_abund = pd.DataFrame(
        {
            "Compound": ["cmp1", "cmp2"],
            "m/z": [180.063, 150.052],
            "Retention time (min)": [1.25, 1.75],
            "1.1": [1000, 900],
            "1.2": [980, 870],
        }
    )

    df_ident.to_excel(ident_path, index=False)
    df_abund.to_excel(abund_path, index=False)

    ranked = run_biological_candidate_ranking(
        identificacao_xlsx=ident_path,
        abund_xlsx=abund_path,
        output_path=output_path,
        load_core=False,
    )

    required_cols = {
        "feature_group",
        "rank_group",
        "rank",
        "is_tied",
        "original_id",
        "fragment_score",
        "isotope_similarity",
        "mass_error_ppm",
    }

    assert required_cols.issubset(set(ranked.columns))
    assert (ranked["rank_group"] >= 1).all()
    assert output_path.exists()
