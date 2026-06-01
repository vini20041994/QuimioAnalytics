import pandas as pd

from api.services import final_dataset_service as service


def test_build_final_dataset_preserves_null_values(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "cmp1||[M+H]+",
                "Compound": "cmp1",
                "original_id": "ID-1",
                "Adducts": "[M+H]+",
                "score": 92.0,
                "fragment_score": 81.0,
                "media_abundancia": 1000.0,
                "description": None,
                "chemical_class": None,
                "chemical_subclass": None,
            }
        ]
    )

    def fake_load_candidates_dataframe():
        return candidates

    def fake_load_enrichment_dataframe():
        return pd.DataFrame()

    monkeypatch.setattr(service, "load_candidates_dataframe", fake_load_candidates_dataframe)
    monkeypatch.setattr(service, "load_enrichment_dataframe", fake_load_enrichment_dataframe)

    final_df = service.build_final_dataset()

    assert len(final_df) == 1
    assert pd.isna(final_df.loc[0, "Descricao"])
    assert pd.isna(final_df.loc[0, "Classe geral"])
    assert pd.isna(final_df.loc[0, "Subclasse"])


def test_load_candidates_dataframe_normalizes_lowercase_db_aliases(monkeypatch):
    source_df = pd.DataFrame(
        [
            {
                "compound": "10.18_355.1547m/z",
                "original_id": "CSID35014152",
                "adducts": "M-H2O-H",
                "formula": "C20H20O5",
                "score": 37.1,
                "fragment_score": 1.56,
                "mass_error_ppm": 1.2,
                "isotope_similarity": 98.7,
                "link": "https://example.test/csid/35014152",
                "description": "Example compound",
                "neutral_mass_da": 354.14,
                "mz": 355.15,
                "rt": 10.18,
                "media_abundancia": 343.39,
                "cv": 0.12,
                "rank_group": 1,
                "is_tied": False,
            }
        ]
    )

    def fake_read_sql_dataframe(_query):
        return source_df.copy()

    monkeypatch.setattr(service, "_read_sql_dataframe", fake_read_sql_dataframe)

    loaded = service.load_candidates_dataframe()

    assert len(loaded) == 1
    assert loaded.loc[0, "Compound"] == "10.18_355.1547m/z"
    assert loaded.loc[0, "Adducts"] == "M-H2O-H"
    assert loaded.loc[0, "Link"] == "https://example.test/csid/35014152"
    assert loaded.loc[0, "feature_group"] == "10.18_355.1547m/z||M-H2O-H"
