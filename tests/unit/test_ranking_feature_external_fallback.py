from fastapi.testclient import TestClient

from api.main import app



def test_ranking_feature_external_uses_local_payload_without_triggering_etl(monkeypatch):
    def fake_build_feature_external_payload(feature_id: str, source: str):
        assert feature_id == "cmp1||[M+H]+"
        assert source == "pubchem"
        return [{"compound_id": "ID-1"}]

    def fail_if_called(_source: str):
        raise AssertionError("ETL sob demanda nao deveria ser executado quando ha dados locais")

    monkeypatch.setattr("api.main.build_feature_external_payload", fake_build_feature_external_payload)
    monkeypatch.setattr("api.main._run_external_enrichment_for_source", fail_if_called)

    client = TestClient(app)
    response = client.get(
        "/api/v1/ranking/feature-external",
        params={"feature_id": "cmp1||[M+H]+", "source": "pubchem"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == [{"compound_id": "ID-1"}]
    assert "fallback" not in payload



def test_ranking_feature_external_triggers_on_demand_etl_when_local_is_empty(monkeypatch):
    build_calls = []

    def fake_build_feature_external_payload(feature_id: str, source: str):
        build_calls.append((feature_id, source))
        if len(build_calls) == 1:
            return []
        return [{"compound_id": "ID-2", "source": "PubChem"}]

    def fake_run_external(source: str):
        assert source == "pubchem"
        return {"triggered": True, "source": source, "status": {"ok": True}}

    monkeypatch.setattr("api.main.build_feature_external_payload", fake_build_feature_external_payload)
    monkeypatch.setattr("api.main._run_external_enrichment_for_source", fake_run_external)

    client = TestClient(app)
    response = client.get(
        "/api/v1/ranking/feature-external",
        params={"feature_id": "cmp2||[M+H]+", "source": "pubchem"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == [{"compound_id": "ID-2", "source": "PubChem"}]
    assert payload["fallback"]["triggered"] is True
    assert build_calls == [
        ("cmp2||[M+H]+", "pubchem"),
        ("cmp2||[M+H]+", "pubchem"),
    ]
