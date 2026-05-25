import pandas as pd
import pytest
import json
from pathlib import Path

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
        "score",
        "fragment_score",
        "fragmentation_score",
        "isotope_similarity",
        "mass_error_ppm",
        "mass_error",
        "formula",
        "execution_id",
        "pipeline_version",
        "ingestion_timestamp_utc",
        "source_identificacao_file",
        "source_identificacao_sha256",
        "source_identificacao_mtime_utc",
        "source_abundancia_file",
        "source_abundancia_sha256",
        "source_abundancia_mtime_utc",
        "quality_report_path",
        "tag_branco",
        "tag_abund_gt_500",
        "tag_abund_gt_1000",
        "tag_abund_gt_5000",
        "tag_abund_gt_10000",
        "tag_anova_p_le_005",
        "tag_max_fold_change_ge_2",
        "tag_not_fragmented",
    }

    assert required_cols.issubset(set(ranked.columns))
    assert (ranked["rank_group"] >= 1).all()
    assert ranked["quality_report_path"].notna().all()
    assert output_path.exists()


@pytest.mark.validation
def test_quality_report_registers_rejections_and_reasons(tmp_path):
    ident_path = tmp_path / "IDENTIFICACAO.xlsx"
    abund_path = tmp_path / "ABUND.xlsx"
    output_path = tmp_path / "biological_ranking_candidates.parquet"

    df_ident = pd.DataFrame(
        {
            "Compound": ["cmp1", "cmp2", "cmp3"],
            "Adducts": ["[M+H]+", "[M+H]+", "[M+H]+"],
            "Score": [90.0, 85.0, 70.0],
            "Fragmentation Score": [80.0, 70.0, 60.0],
            "Isotope Similarity": [88.0, 130.0, 82.0],
            "Mass Error (ppm)": [1.2, 1.8, 0.7],
            "Formula": ["C6H12O6", "C5H10O5", "C7H14O7"],
            "Compound ID": ["ID-1", "ID-2", "ID-3"],
            "m/z": [180.063, 150.052, 170.042],
            "Retention time (min)": [1.25, 1.75, 2.00],
            "Branco": [1, 0, 0],
            "Abund > 500": [1, 1, 0],
            "Not Fragmented": [0, 1, 0],
        }
    )
    df_abund = pd.DataFrame(
        {
            "Compound": ["cmp1", "cmp2", "cmp3"],
            "m/z": [180.063, 150.052, 170.042],
            "Retention time (min)": [1.25, 1.75, 2.00],
            "1.1": [1000, 900, 700],
            "1.2": [980, 870, 650],
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

    assert len(ranked) == 2
    report_path = ranked["quality_report_path"].iloc[0]
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))

    assert report["rows_received"] == 3
    assert report["rows_output"] == 2
    assert report["rows_rejected"] == 1
    assert report["loss_reasons"]["invalid_isotope_similarity_range"] == 1
