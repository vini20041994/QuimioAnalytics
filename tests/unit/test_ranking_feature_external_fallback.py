from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app



def test_ranking_feature_external_uses_local_payload_without_triggering_etl(monkeypatch):
    def fake_build_feature_external_payload(feature_id: str, source: str):
        assert feature_id == "cmp1||[M+H]+"
        assert source == "pubchem"
        return [{"compound_id": "ID-1"}]

    def fail_if_called(_source: str, feature_id: str | None = None):
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

    def fake_run_external(source: str, feature_id: str | None = None):
        assert source == "pubchem"
        assert feature_id == "cmp2||[M+H]+"
        return {"triggered": True, "source": source, "feature_id": feature_id, "status": {"ok": True}}

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


def test_run_external_enrichment_scopes_candidates_by_feature(monkeypatch):
    captured = {}

    def fake_subprocess_run(cmd, **_kwargs):
        captured["kwargs"] = _kwargs
        captured["cmd"] = cmd
        input_idx = cmd.index("--candidates-input") + 1
        scoped_input_path = Path(cmd[input_idx])
        scoped_df = pd.read_csv(scoped_input_path)
        captured["scoped_rows"] = len(scoped_df)
        captured["feature_groups"] = set(scoped_df["feature_group"].astype(str).tolist())
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("api.main._is_pipeline_running", lambda: False)
    monkeypatch.setattr("api.main._acquire_upload_lock", lambda: True)
    monkeypatch.setattr("api.main._release_upload_lock", lambda: None)
    monkeypatch.setattr("api.main._resolve_pipeline_python", lambda: "python3")
    monkeypatch.setattr("api.main._build_pipeline_env", lambda: {})
    monkeypatch.setattr("api.main.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("api.main.load_enrichment_report", lambda: {"source_status": []})
    monkeypatch.setattr(
        "api.main.load_candidates_dataframe",
        lambda: pd.DataFrame(
            [
                {
                    "feature_group": "feature-a||M-H",
                    "Compound": "feature-a",
                    "Adducts": "M-H",
                    "original_id": "ID-A1",
                    "formula": "C6H12O6",
                },
                {
                    "feature_group": "feature-a||M-H",
                    "Compound": "feature-a",
                    "Adducts": "M-H",
                    "original_id": "ID-A2",
                    "formula": "C7H14O7",
                },
                {
                    "feature_group": "feature-b||M+H",
                    "Compound": "feature-b",
                    "Adducts": "M+H",
                    "original_id": "ID-B1",
                    "formula": "C8H16O8",
                },
            ]
        ),
    )

    from api.main import _run_external_enrichment_for_source

    result = _run_external_enrichment_for_source("pubchem", feature_id="feature-a||M-H")

    assert "--candidates-input" in captured["cmd"]
    assert captured["scoped_rows"] == 2
    assert captured["feature_groups"] == {"feature-a||M-H"}
    assert result["triggered"] is True
    assert result["feature_id"] == "feature-a||M-H"
    assert result["scoped_candidates"] == 2


def test_ranking_feature_external_job_status_reports_completed_query(monkeypatch):
    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, **_unused):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    def fake_run_feature_external_query(feature_id: str, source: str, status_callback=None):
        assert feature_id == "cmp3||[M+Na]+"
        assert source == "chebi"
        if status_callback:
            status_callback("checking_local_cache", 10)
            status_callback("executing_external_etl", 60)
            status_callback("completed", 100)
        return {
            "items": [{"compound_id": "ID-3", "source": "ChEBI"}],
            "fallback": {"triggered": True, "source": "chebi"},
        }

    monkeypatch.setattr("api.main.threading.Thread", ImmediateThread)
    monkeypatch.setattr("api.main._run_feature_external_query", fake_run_feature_external_query)

    client = TestClient(app)
    start_response = client.post(
        "/api/v1/ranking/feature-external/jobs",
        params={"feature_id": "cmp3||[M+Na]+", "source": "chebi"},
    )

    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload["state"] == "completed"
    assert start_payload["progress"] == 100

    status_response = client.get(f"/api/v1/ranking/feature-external/jobs/{start_payload['job_id']}")

    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["state"] == "completed"
    assert payload["step"] == "completed"
    assert payload["progress"] == 100
    assert payload["items"] == [{"compound_id": "ID-3", "source": "ChEBI"}]
    assert payload["fallback"] == {"triggered": True, "source": "chebi"}
