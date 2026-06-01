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


def test_build_ranking_payload_returns_all_candidates_by_default(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "feature-1||M-H",
                "Compound": "feature-1",
                "original_id": f"ID-{index}",
                "Adducts": "M-H",
                "formula": f"C{index}H{index}",
                "score": 100 - index,
                "fragment_score": 50 - index,
                "mass_error_ppm": float(index),
                "isotope_similarity": 90 - index,
                "Link": "",
                "Description": f"Candidate {index}",
                "mz": 100.0,
                "rt": 1.0,
                "rank_group": index + 1,
            }
            for index in range(7)
        ]
    )

    def fake_load_candidates_dataframe():
        return candidates

    def fake_load_enrichment_dataframe():
        return pd.DataFrame()

    def fake_load_identificacao_trusted_dataframe():
        return pd.DataFrame()

    monkeypatch.setattr(service, "load_candidates_dataframe", fake_load_candidates_dataframe)
    monkeypatch.setattr(service, "load_enrichment_dataframe", fake_load_enrichment_dataframe)
    monkeypatch.setattr(service, "load_identificacao_trusted_dataframe", fake_load_identificacao_trusted_dataframe)

    payload = service.build_ranking_payload()

    assert len(payload) == 1
    assert len(payload[0]["candidates"]) == 7
    assert [item["compound_id"] for item in payload[0]["candidates"]] == [
        "ID-0",
        "ID-1",
        "ID-2",
        "ID-3",
        "ID-4",
        "ID-5",
        "ID-6",
    ]


def test_build_ranking_payload_applies_candidate_limit_when_requested(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "feature-1||M-H",
                "Compound": "feature-1",
                "original_id": f"ID-{index}",
                "Adducts": "M-H",
                "formula": f"C{index}H{index}",
                "score": 100 - index,
                "fragment_score": 50 - index,
                "mass_error_ppm": float(index),
                "isotope_similarity": 90 - index,
                "Link": "",
                "Description": f"Candidate {index}",
                "mz": 100.0,
                "rt": 1.0,
                "rank_group": index + 1,
            }
            for index in range(7)
        ]
    )

    def fake_load_candidates_dataframe():
        return candidates

    def fake_load_enrichment_dataframe():
        return pd.DataFrame()

    def fake_load_identificacao_trusted_dataframe():
        return pd.DataFrame()

    monkeypatch.setattr(service, "load_candidates_dataframe", fake_load_candidates_dataframe)
    monkeypatch.setattr(service, "load_enrichment_dataframe", fake_load_enrichment_dataframe)
    monkeypatch.setattr(service, "load_identificacao_trusted_dataframe", fake_load_identificacao_trusted_dataframe)

    payload = service.build_ranking_payload(candidate_limit=5)

    assert len(payload) == 1
    assert len(payload[0]["candidates"]) == 5
    assert [item["compound_id"] for item in payload[0]["candidates"]] == [
        "ID-0",
        "ID-1",
        "ID-2",
        "ID-3",
        "ID-4",
    ]


def test_build_dashboard_payload_uses_raw_abundance_measurements(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "feature-1||M-H",
                "Compound": "feature-1",
                "original_id": "ID-1",
                "media_abundancia": 10.0,
            }
        ]
    )
    abundance_df = pd.DataFrame(
        [
            {"sample": "1.1", "abundance": 100.0},
            {"sample": "1.2", "abundance": 80.0},
        ]
    )

    def fake_load_candidates_dataframe():
        return candidates

    def fake_read_sql_dataframe(query, _params=None):
        if "FROM core.abundance_measurement" in query:
            return abundance_df
        return pd.DataFrame()

    monkeypatch.setattr(service, "load_candidates_dataframe", fake_load_candidates_dataframe)
    monkeypatch.setattr(service, "_read_sql_dataframe", fake_read_sql_dataframe)

    payload = service.build_dashboard_payload()

    assert payload["abundanceData"] == [
        {"sample": "1.1", "abundance": 100.0},
        {"sample": "1.2", "abundance": 80.0},
    ]


def test_build_ranking_summary_payload_returns_feature_metadata(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "feature-1||M-H",
                "Compound": "cmp-a",
                "original_id": "ID-1",
                "mz": 100.1234,
                "rt": 1.23,
                "rank_group": 1,
                "score": 90.0,
            },
            {
                "feature_group": "feature-1||M-H",
                "Compound": "cmp-b",
                "original_id": "ID-2",
                "mz": 100.1234,
                "rt": 1.23,
                "rank_group": 2,
                "score": 85.0,
            },
        ]
    )

    monkeypatch.setattr(service, "load_candidates_dataframe", lambda: candidates)

    payload = service.build_ranking_summary_payload()

    assert len(payload) == 1
    assert payload[0]["feature_id"] == "feature-1||M-H"
    assert payload[0]["candidate_count"] == 2
    assert payload[0]["top_candidate_name"] == "cmp-a"


def test_build_feature_candidates_payload_returns_only_requested_feature(monkeypatch):
    candidates = pd.DataFrame(
        [
            {
                "feature_group": "feature-1||M-H",
                "Compound": "cmp-a",
                "original_id": "ID-1",
                "Adducts": "M-H",
                "formula": "C6H12O6",
                "score": 90.0,
                "fragment_score": 70.0,
                "mass_error_ppm": 1.2,
                "isotope_similarity": 98.0,
                "Description": "A",
                "mz": 100.0,
                "rt": 1.0,
                "rank_group": 1,
            },
            {
                "feature_group": "feature-2||M+H",
                "Compound": "cmp-b",
                "original_id": "ID-2",
                "Adducts": "M+H",
                "formula": "C7H14O7",
                "score": 85.0,
                "fragment_score": 65.0,
                "mass_error_ppm": 1.8,
                "isotope_similarity": 97.0,
                "Description": "B",
                "mz": 200.0,
                "rt": 2.0,
                "rank_group": 1,
            },
        ]
    )

    monkeypatch.setattr(service, "load_candidates_dataframe", lambda: candidates)
    monkeypatch.setattr(service, "load_enrichment_dataframe", lambda: pd.DataFrame())
    monkeypatch.setattr(service, "load_identificacao_trusted_dataframe", lambda: pd.DataFrame())

    payload = service.build_feature_candidates_payload("feature-1||M-H")

    assert len(payload) == 1
    assert payload[0]["compound_id"] == "ID-1"
    assert payload[0]["name"] == "cmp-a"
