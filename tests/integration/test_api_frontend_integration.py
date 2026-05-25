import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.integration
def test_dashboard_and_ranking_endpoints_use_staging_data(tmp_path, monkeypatch):
    candidates_path = tmp_path / "biological_ranking_candidates.parquet"
    enrichment_path = tmp_path / "external_enrichment_snapshot.parquet"

    candidates = pd.DataFrame(
        [
            {
                "feature_group": "cmp1||[M+H]+",
                "Compound": "cmp1",
                "original_id": "ID-1",
                "Adducts": "[M+H]+",
                "score": 92.0,
                "fragment_score": 81.0,
                "mass_error_ppm": 1.2,
                "formula": "C6H12O6",
                "rank_group": 1,
                "is_tied": False,
                "mz": 180.063,
                "rt": 1.25,
                "media_abundancia": 1000.0,
                "ingestion_timestamp_utc": "2026-05-25T10:00:00+00:00",
                "pipeline_version": "IST-v2-S9",
                "source_identificacao_file": "ident.xlsx",
                "source_abundancia_file": "abund.xlsx",
            },
            {
                "feature_group": "cmp1||[M+H]+",
                "Compound": "cmp1",
                "original_id": "ID-2",
                "Adducts": "[M+H]+",
                "score": 85.0,
                "fragment_score": 70.0,
                "mass_error_ppm": 2.3,
                "formula": "C6H12O6",
                "rank_group": 2,
                "is_tied": False,
                "mz": 180.063,
                "rt": 1.25,
                "media_abundancia": 900.0,
                "ingestion_timestamp_utc": "2026-05-25T10:00:00+00:00",
                "pipeline_version": "IST-v2-S9",
                "source_identificacao_file": "ident.xlsx",
                "source_abundancia_file": "abund.xlsx",
            },
        ]
    )
    candidates.to_parquet(candidates_path, index=False)

    enrichment = pd.DataFrame(
        [
            {
                "standardized_name": "cmp1",
                "description": "Composto de teste",
                "chemical_class": "Classe A",
                "chemical_subclass": "Subclasse A1",
                "enrichment_source": "PubChem",
                "enrichment_queried_at": "2026-05-25T11:00:00+00:00",
            }
        ]
    )
    enrichment.to_parquet(enrichment_path, index=False)

    monkeypatch.setenv("QUIMIO_STAGING_DIR", str(tmp_path))

    client = TestClient(app)

    dashboard_response = client.get("/api/v1/dashboard")
    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["stats"]["totalFeatures"] == 1
    assert dashboard_payload["stats"]["totalCandidates"] == 2

    ranking_response = client.get("/api/v1/ranking/features")
    assert ranking_response.status_code == 200
    ranking_payload = ranking_response.json()
    assert len(ranking_payload["items"]) == 1
    assert ranking_payload["items"][0]["candidates"][0]["rank"] == 1

    compounds_response = client.get("/api/v1/compounds")
    assert compounds_response.status_code == 200
    compounds_payload = compounds_response.json()
    assert len(compounds_payload["items"]) == 1
    assert compounds_payload["items"][0]["name"] == "cmp1"

    export_response = client.get("/api/v1/export/candidates.csv")
    assert export_response.status_code == 200
    assert "Composto,Composto ID" in export_response.text


@pytest.mark.integration
def test_upload_rejects_invalid_file_extension():
    client = TestClient(app)

    files = {
        "identification": ("ident.txt", b"invalid", "text/plain"),
        "abundance": ("abund.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400
    assert "Formato invalido" in response.json()["detail"]
