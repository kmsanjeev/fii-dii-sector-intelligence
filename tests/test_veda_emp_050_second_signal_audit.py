import json

from scripts.veda_emp_050_second_signal_audit import AUDIT


def test_second_signal_audit_keeps_partial_candidates_out_of_production():
    assert AUDIT["second_signal_found"] is True
    assert AUDIT["decision"] == "SECOND_SIGNAL_FROZEN"
    assert AUDIT["candidates"][0]["status"] == "SOURCE_GOVERNABLE"
    assert {item["status"] for item in AUDIT["candidates"][1:]} == {"SOURCE_PARTIAL"}
    assert AUDIT["production_changes"] == "NONE"
    assert AUDIT["approved_core"] == "UNCHANGED"
    assert json.loads(json.dumps(AUDIT))["decision"] == AUDIT["decision"]
