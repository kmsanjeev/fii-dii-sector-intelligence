"""Focused governance checks for the whole-veda autonomous rebaseline."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/autonomous-work-rebaseline-001"


def read_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_baseline_and_immutable_governance_state():
    baseline = read_json("01_AUTHORITATIVE_STATE_RECONCILIATION.json")
    state = baseline["authoritative_state"]
    assert baseline["starting_commit"] == "84092ca0e6bb2c4b38a4ee13c1d2a63f80d9881c"
    assert baseline["branch"] == "main"
    assert state["APPROVED_CORE"] == 17
    assert state["REGISTERED_SOURCES"] == 14
    assert state["ML"] == "LOCKED_DEFERRED"
    assert state["PRED_M4"] == "INSUFFICIENT_SAMPLE_STOPPED_UNCHANGED"
    assert state["RAW_PROVIDER_DATA_COMMITTED"] is False


def test_no_autonomous_candidate_passes_ready_work_gate():
    gate = read_json("12_READY_WORK_GATE.json")
    candidates = read_json("11_AUTONOMOUS_CANDIDATE_INVENTORY.json")["candidates"]
    assert gate["decision"] == "VEDA_NO_HIGH_VALUE_AUTONOMOUS_PROGRAMME_READY"
    assert gate["autonomous_ready_now"] == []
    assert gate["autonomous_ready_with_condition"] == []
    assert all(item["state"] != "AUTONOMOUS_READY" for item in candidates)
    assert all(item["state"] != "AUTONOMOUS_READY_WITH_CONDITION" for item in candidates)


def test_muhurta_rag_and_engineering_release_gates_are_preserved():
    muhurta = read_json("06_MUHURTA_STATUS.json")
    rag = read_json("08_RAG_STATUS.json")
    engineering = read_json("09_ENGINEERING_STATUS.json")
    assert muhurta["operational_count"] == 4
    assert muhurta["expansion_decision"] == "FREEZE_MUHURTA_ACTIVITY_EXPANSION_PENDING_NEW_EVIDENCE"
    assert rag["manifest"] == 1205
    assert rag["approved_core"] == 17
    assert rag["provider_calls"] == 0
    assert engineering["full_suite"]["collected"] == 1269
    assert engineering["full_suite"]["passed"] == 1269
    assert engineering["full_suite"]["failed"] == 0
    assert engineering["production_code_changed"] is False


def test_final_acceptance_and_next_selection_are_consistent():
    selection = (OUT / "16_NEXT_PROGRAMME_SELECTION.md").read_text(encoding="utf-8")
    acceptance = (OUT / "19_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8")
    register = read_json("20_ACCEPTANCE_REGISTER.json")
    assert "VEDA_NO_HIGH_VALUE_AUTONOMOUS_PROGRAMME_READY" in selection
    assert "No programme is recommended or started" in selection
    assert "PASS_WITH_CONDITION" in acceptance
    assert "No duplicate programme was proposed and no next programme was started" in acceptance.replace("\n", " ")
    assert register["decision"] == "VEDA_NO_HIGH_VALUE_AUTONOMOUS_PROGRAMME_READY"
    assert register["summary"]["fail"] == 0
    assert register["summary"]["blocked"] == 0
