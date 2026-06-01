import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.integration
def test_dashboard_and_ranking_endpoints_use_staging_data(tmp_path, monkeypatch):

    # Popular banco de dados de teste (apenas identificação)
    import psycopg2
    from scripts.config import get_db_params
    db_params = get_db_params()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            # Limpar tabelas filhas antes da tabela pai para respeitar constraints
            cur.execute("DELETE FROM core.abundance_measurement")
            cur.execute("DELETE FROM core.candidate_identification")
            cur.execute("DELETE FROM core.replicate")
            cur.execute("DELETE FROM core.sample_group")
            cur.execute("DELETE FROM stg.abundance_row")
            cur.execute("DELETE FROM stg.identification_row")
            cur.execute("DELETE FROM stg.curated_catalog_row")
            cur.execute("DELETE FROM core.feature")
            cur.execute("DELETE FROM core.ingestion_batch")
            # Criar batch
            cur.execute("""
                INSERT INTO core.ingestion_batch (batch_name, solvent, ionization_mode, source_notes)
                VALUES ('batch_test', NULL, NULL, 'Teste integração') RETURNING batch_id
            """)
            batch_id = cur.fetchone()[0]
            # Inserir identificação
            # Normalização para compatibilidade com backend
            compound_code = 'cmp1'.casefold().strip()
            adducts = '[M+H]+'.casefold().strip()
            # Inserir identificação 1
            cur.execute("""
                INSERT INTO stg.identification_row (
                    batch_id, source_sheet, source_row_number, compound_code, source_compound_id, adducts,
                    molecular_formula, score, fragmentation_score, mass_error_ppm, isotope_similarity, link_url,
                    description, neutral_mass_da, mz, retention_time_min, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id, 'sheet1', 2, compound_code, 'ID-1', adducts, 'C6H12O6', 92.0, 81.0, 1.2, 0.98, 'http://link1',
                'Descrição 1', 180.063, 180.063, 1.25, '{}'
            ))
            # Inserir feature correspondente
            cur.execute("""
                INSERT INTO core.feature (
                    batch_id, feature_code, neutral_mass_da, mz, retention_time_min, source_identification_count, present_in_identification, present_in_abundance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (batch_id, feature_code) DO NOTHING
            """,
            (
                batch_id, compound_code, 180.063, 180.063, 1.25, 1, True, True
            ))
            # Inserir identificação 2
            cur.execute("""
                INSERT INTO stg.identification_row (
                    batch_id, source_sheet, source_row_number, compound_code, source_compound_id, adducts,
                    molecular_formula, score, fragmentation_score, mass_error_ppm, isotope_similarity, link_url,
                    description, neutral_mass_da, mz, retention_time_min, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id, 'sheet1', 3, compound_code, 'ID-2', adducts, 'C6H12O6', 85.0, 70.0, 2.3, 0.95, 'http://link2',
                'Descrição 2', 180.063, 180.063, 1.25, '{}'
            ))
            conn.commit()
            # Depuração: conferir se os dados estão no banco
            cur.execute("SELECT compound_code, adducts FROM stg.identification_row")
            print('identification_row:', cur.fetchall())

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

    ranking_external_response = client.get(
        "/api/v1/ranking/feature-external",
        params={"feature_id": "cmp1||[M+H]+", "source": "pubchem"},
    )
    assert ranking_external_response.status_code == 200
    ranking_external_payload = ranking_external_response.json()
    assert len(ranking_external_payload["items"]) >= 1
    first_external = ranking_external_payload["items"][0]
    assert first_external["compound_id"] == "ID-1"
    assert first_external["formula"] == "C6H12O6"
    assert first_external["link"] == "https://pubchem.ncbi.nlm.nih.gov/compound/1234"
    assert first_external["description"] == "Composto de teste"

    compounds_response = client.get("/api/v1/compounds")
    assert compounds_response.status_code == 200
    compounds_payload = compounds_response.json()
    assert len(compounds_payload["items"]) == 1
    assert compounds_payload["items"][0]["name"] == "cmp1"

    export_response = client.get("/api/v1/export/candidates.csv")
    assert export_response.status_code == 200
    assert "ID,Metabólito/Composto" in export_response.text


@pytest.mark.integration
def test_upload_rejects_invalid_file_extension():
    client = TestClient(app)

    files = {
        "identification": ("ident.txt", b"invalid", "text/plain"),
        "abundance": ("abund.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "compounds": ("compounds.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400
    assert "Formato invalido" in response.json()["detail"]
