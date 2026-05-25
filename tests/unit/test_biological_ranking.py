import pandas as pd
import pytest

from scripts.models.biological_ranking_engine import BiologicalRankingEngine


@pytest.mark.unit
def test_biological_ranking_orders_by_ladder_rules(ranking_input_df):
    engine = BiologicalRankingEngine()

    ranked = engine.apply_ranking(ranking_input_df, group_by="feature_group")

    top = ranked.loc[ranked["original_id"] == "cmp-1"].iloc[0]
    second = ranked.loc[ranked["original_id"] == "cmp-3"].iloc[0]
    third = ranked.loc[ranked["original_id"] == "cmp-2"].iloc[0]

    assert int(top["rank_group"]) == 1
    assert int(second["rank_group"]) == 1
    assert int(third["rank_group"]) == 2


@pytest.mark.unit
def test_biological_ranking_marks_ties(ranking_input_df):
    engine = BiologicalRankingEngine()

    ranked = engine.apply_ranking(ranking_input_df, group_by="feature_group")
    tied_rows = ranked[ranked["rank_group"] == 1]

    assert len(tied_rows) == 2
    assert tied_rows["is_tied"].all()


@pytest.mark.unit
def test_biological_ranking_uses_score_as_second_criterion():
    engine = BiologicalRankingEngine()
    df = pd.DataFrame(
        [
            {
                "feature_group": "S||[M+H]+",
                "original_id": "high-score",
                "fragment_score": 90.0,
                "score": 99.0,
                "isotope_similarity": 70.0,
                "mass_error_ppm": 2.0,
                "formula": "C6H12O6",
            },
            {
                "feature_group": "S||[M+H]+",
                "original_id": "low-score",
                "fragment_score": 90.0,
                "score": 80.0,
                "isotope_similarity": 95.0,
                "mass_error_ppm": 0.1,
                "formula": "C6H12O6",
            },
        ]
    )

    ranked = engine.apply_ranking(df, group_by="feature_group")
    top = ranked.sort_values(["rank_group", "original_id"]).iloc[0]

    assert top["original_id"] == "high-score"
    assert int(top["rank_group"]) == 1


@pytest.mark.unit
def test_biological_ranking_uses_raw_values_without_normalization():
    engine = BiologicalRankingEngine()
    df = pd.DataFrame(
        [
            {
                "feature_group": "B||[M+Na]+",
                "fragment_score": "100",
                "score": "95",
                "isotope_similarity": "10",
                "mass_error_ppm": "2",
                "formula": "C10H20",
            }
        ]
    )

    ranked = engine.apply_ranking(df, group_by="feature_group")

    assert float(ranked.iloc[0]["fragment_score"]) == 100.0
    assert float(ranked.iloc[0]["score"]) == 95.0
    assert float(ranked.iloc[0]["isotope_similarity"]) == 10.0
    assert float(ranked.iloc[0]["mass_error_ppm"]) == 2.0


@pytest.mark.unit
def test_biological_ranking_preserves_original_ids(ranking_input_df):
    engine = BiologicalRankingEngine()

    ranked = engine.apply_ranking(ranking_input_df, group_by="feature_group")

    assert set(ranked["original_id"]) == {"cmp-1", "cmp-2", "cmp-3"}
    assert len(ranked) == len(ranking_input_df)
