from api.main import _resolve_next_action, _resolve_overall_outcome


def test_outcome_success_total_when_all_steps_ok():
    details = {
        "etl_ok": True,
        "ranking_ok": True,
        "external_status": "success_total",
    }
    assert _resolve_overall_outcome(details) == "success_total"


def test_outcome_success_partial_when_external_partial():
    details = {
        "etl_ok": True,
        "ranking_ok": True,
        "external_status": "success_partial",
    }
    assert _resolve_overall_outcome(details) == "success_partial"


def test_outcome_failed_when_ranking_fails():
    details = {
        "etl_ok": True,
        "ranking_ok": False,
        "external_status": "success_total",
    }
    assert _resolve_overall_outcome(details) == "failed"


def test_next_action_for_partial_contains_reexecution_hint():
    details = {"outcome": "success_partial"}
    message = _resolve_next_action(details)
    assert "reexecute" in message.casefold() or "reexecute" in message.casefold().replace("ê", "e")


def test_next_action_for_failed_contains_retry_hint():
    details = {"outcome": "failed"}
    message = _resolve_next_action(details)
    assert "tente novamente" in message.casefold()
