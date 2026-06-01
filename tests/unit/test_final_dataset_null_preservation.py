import pandas as pd

from api.services.final_dataset_service import build_final_dataset


def test_build_final_dataset_preserves_null_values(tmp_path, monkeypatch):
    candidates_path = tmp_path / "biological_ranking_candidates.parquet"

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
    candidates.to_parquet(candidates_path, index=False)

    monkeypatch.setenv("QUIMIO_STAGING_DIR", str(tmp_path))

    final_df = build_final_dataset()

    assert len(final_df) == 1
    assert pd.isna(final_df.loc[0, "Descricao"])
    assert pd.isna(final_df.loc[0, "Classe geral"])
    assert pd.isna(final_df.loc[0, "Subclasse"])
