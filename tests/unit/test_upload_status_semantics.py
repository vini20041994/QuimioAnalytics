from api.main import _normalize_external_sources, _resolve_external_status


def test_resolve_external_status_success_total_when_all_sources_ok():
    sources = [
        {"source": "PubChem", "ok": True},
        {"source": "ChEBI", "ok": True},
    ]

    status, external_ok = _resolve_external_status(sources, external_step_ok=True)

    assert status == "success_total"
    assert external_ok is True


def test_resolve_external_status_partial_when_some_sources_fail():
    sources = [
        {"source": "PubChem", "ok": True},
        {"source": "ChEBI", "ok": False},
    ]

    status, external_ok = _resolve_external_status(sources, external_step_ok=True)

    assert status == "success_partial"
    assert external_ok is False


def test_resolve_external_status_failed_when_all_sources_fail():
    sources = [
        {"source": "PubChem", "ok": False},
        {"source": "ChEBI", "ok": False},
    ]

    status, external_ok = _resolve_external_status(sources, external_step_ok=True)

    assert status == "failed"
    assert external_ok is False


def test_normalize_external_sources_extracts_source_and_error_excerpt():
    raw = [
        {
            "step": "ETL PubChem",
            "ok": False,
            "exit_code": 1,
            "stderr": "Falha de conexao com endpoint remoto",
        }
    ]

    normalized = _normalize_external_sources(raw)

    assert len(normalized) == 1
    assert normalized[0]["source"] == "PubChem"
    assert normalized[0]["ok"] is False
    assert normalized[0]["exit_code"] == 1
    assert "Falha de conexao" in normalized[0]["error"]
