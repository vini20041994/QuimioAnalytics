import sys

import pytest

from scripts.run import run_etl


@pytest.mark.integration
def test_run_etl_main_smoke(monkeypatch):
    calls = []

    def fake_run_step(script_path, step_name, extra_args=None):
        calls.append((step_name, list(extra_args or [])))
        return "ok"

    monkeypatch.setattr(run_etl, "run_step", fake_run_step)
    monkeypatch.setattr(sys, "argv", ["run_etl.py"])

    run_etl.main()

    assert [name for name, _ in calls] == ["EXTRACT", "TRANSFORM", "LOAD"]


@pytest.mark.integration
def test_run_etl_main_smoke_with_minimal_inputs(monkeypatch):
    calls = []

    def fake_run_step(script_path, step_name, extra_args=None):
        calls.append((step_name, list(extra_args or [])))
        return "ok"

    monkeypatch.setattr(run_etl, "run_step", fake_run_step)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_etl.py",
            "--identificacao",
            "ident.xlsx",
            "--abundancia",
            "abund.xlsx",
            "--compostos",
            "compostos.xlsx",
        ],
    )

    run_etl.main()

    extract_args = calls[0][1]
    assert "--identificacao" in extract_args
    assert "ident.xlsx" in extract_args
    assert "--abundancia" in extract_args
    assert "abund.xlsx" in extract_args
    assert "--compostos" in extract_args
    assert "compostos.xlsx" in extract_args
