import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts.run import run_etl_candidates_external as external_runner


@pytest.mark.unit
def test_build_enriched_snapshot_writes_source_timestamp_and_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(external_runner, "STAGING_DIR", tmp_path)

    pubchem_df = pd.DataFrame(
        [
            {
                "IUPACName": "glucose",
                "pubchem_description": "example description",
                "original_identifier": "cmp-1",
            }
        ]
    )
    pubchem_df.to_parquet(tmp_path / "pubchem_raw.parquet", index=False)

    statuses = [
        {"step": "ETL PubChem", "ok": True, "exit_code": 0, "stderr": ""},
        {"step": "ETL ChEBI", "ok": False, "exit_code": 1, "stderr": "timeout"},
    ]

    snapshot_path = external_runner._build_enriched_snapshot(
        statuses=statuses,
        queried_at="2026-05-25T12:00:00+00:00",
    )

    assert snapshot_path.exists()

    snapshot_df = pd.read_parquet(snapshot_path)
    assert "enrichment_source" in snapshot_df.columns
    assert "enrichment_queried_at" in snapshot_df.columns
    assert set(snapshot_df["enrichment_source"]) == {"PubChem"}

    pending_path = tmp_path / "external_enrichment_pending_retry.json"
    assert pending_path.exists()
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    assert len(pending["pending_retry"]) == 1
    assert pending["pending_retry"][0]["step"] == "ETL ChEBI"


@pytest.mark.unit
def test_main_continues_even_with_source_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(external_runner, "STAGING_DIR", tmp_path)

    def fake_load_candidates_dataframe(_):
        return pd.DataFrame({"compound_name": ["glucose"]})

    def fake_write_inputs(_):
        api = tmp_path / "candidates_external_input.csv"
        chem = tmp_path / "candidates_chemspider_input.txt"
        classy = tmp_path / "candidates_classyfire_input.txt"
        api.write_text("compound_name\nglucose\n", encoding="utf-8")
        chem.write_text("glucose\n", encoding="utf-8")
        classy.write_text("\n", encoding="utf-8")
        return api, chem, classy

    def fake_python_exec():
        return "python"

    def fake_run(_cmd, step_name):
        if step_name == "ETL ChEBI":
            return {"step": step_name, "ok": False, "exit_code": 1, "stderr": "timeout"}
        return {"step": step_name, "ok": True, "exit_code": 0, "stderr": ""}

    captured = {}

    def fake_build_snapshot(statuses, queried_at):
        captured["statuses"] = statuses
        captured["queried_at"] = queried_at
        output = tmp_path / "external_enrichment_snapshot.parquet"
        pd.DataFrame(columns=[
            "standardized_name",
            "description",
            "chemical_class",
            "chemical_subclass",
            "enrichment_source",
            "enrichment_queried_at",
        ]).to_parquet(output, index=False)
        return output

    monkeypatch.setattr(external_runner, "_load_candidates_dataframe", fake_load_candidates_dataframe)
    monkeypatch.setattr(external_runner, "_write_inputs", fake_write_inputs)
    monkeypatch.setattr(external_runner, "_python_exec", fake_python_exec)
    monkeypatch.setattr(external_runner, "_run", fake_run)
    monkeypatch.setattr(external_runner, "_build_enriched_snapshot", fake_build_snapshot)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_etl_candidates_external.py",
            "--sources",
            "pubchem",
            "chebi",
            "classyfire",
        ],
    )

    external_runner.main()

    assert len(captured["statuses"]) == 3
    assert any((not status["ok"]) and status["step"] == "ETL ChEBI" for status in captured["statuses"])
