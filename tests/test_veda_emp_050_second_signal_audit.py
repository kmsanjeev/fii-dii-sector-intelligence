import json

from scripts.veda_emp_050_second_signal_audit import AUDIT


def test_second_signal_audit_keeps_partial_candidates_out_of_production():
    assert AUDIT["second_signal_found"] is False
    assert AUDIT["decision"] == "NO_SECOND_SOURCE_GOVERNABLE_SIGNAL"
    assert {item["status"] for item in AUDIT["candidates"]} == {"SOURCE_PARTIAL"}
    assert AUDIT["production_changes"] == "NONE"
    assert AUDIT["approved_core"] == "UNCHANGED"
    assert json.loads(json.dumps(AUDIT))["decision"] == AUDIT["decision"]
