import pandas as pd
import pytest

from scripts.gerar_relatorio_entrega3 import _compute_quality_metrics


@pytest.mark.unit
def test_quality_metrics_reports_rows_lost():
    df_raw = pd.DataFrame(
        {
            "Compound": ["a", "b", "c", "d", "e"],
            "Compound ID": [1, 2, 3, 4, 5],
            "Adducts": ["x", "x", "x", "x", "x"],
            "Score": [10, 20, 30, 40, 50],
            "Fragmentation Score": [1, 2, 3, 4, 5],
            "Mass Error (ppm)": [0.1, 0.2, 0.3, 0.4, 0.5],
            "Isotope Similarity": [90, 91, 92, 93, 94],
        }
    )
    df_candidates = pd.DataFrame({"feature_group": ["g1", "g2", "g3"]})

    metrics = _compute_quality_metrics(df_raw, df_candidates)

    assert metrics["rows_lost"] == 2
    assert metrics["rows_lost_pct"] == pytest.approx(40.0)


@pytest.mark.unit
def test_quality_metrics_handles_missing_candidate_df():
    df_raw = pd.DataFrame({"Compound": ["a", "b"], "Mass Error (ppm)": [0.1, 0.2]})

    metrics = _compute_quality_metrics(df_raw, None)

    assert metrics["rows_lost"] == 2
    assert metrics["rows_lost_pct"] == pytest.approx(100.0)
