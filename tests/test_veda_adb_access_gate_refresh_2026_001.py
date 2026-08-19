"""Focused governance checks for the 2026 ADB access-state refresh."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OUT = ROOT / "docs" / "current-state" / "adb-access-gate-refresh-2026-001"


def _load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_official_policy_snapshot_preserves_provider_boundaries():
    policy = _load("01_OFFICIAL_PROVIDER_POLICY_SNAPSHOT.json")
    assert policy["full_export_status"] == "FORMAL_EXPORT_SUSPENDED_2026"
    assert policy["contract_status"] == "REMOVED_FOR_DURATION_OF_2026"
    assert policy["public_sample_status"]["status"] == "CURRENT_C_SAMPLE_REMAINS_AVAILABLE"
    assert policy["public_sample_status"]["download_performed_by_this_activity"] is False
    assert policy["research_tool_route"]["bulk_or_export_capability"] == "NOT_ESTABLISHED"
    assert policy["policy_page"].startswith("https://www.astro.com/")


def test_package_submission_and_provider_states_are_separate():
    state = _load("05_PROVIDER_ACCESS_STATE.json")
    assert state["decision"] == "ADB_FORMAL_EXPORT_SUSPENDED_2026_PACKAGE_PRESERVED"
    assert state["package_state"] == "PACKAGE_READY_FOR_REOPEN_NEEDS_POLICY_REFRESH"
    assert state["submission_state"] == "UNSENT"
    assert state["provider_access_state"] == "FORMAL_EXPORT_ACCESS_SUSPENDED_2026"
    assert state["evidence_state"] == "INSUFFICIENT_FOR_NEXT_POSITION_END_STAGE"
    assert state["position_end_state"] == "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED"
    assert state["temporary_or_permanent"].startswith("TEMPORARILY")


def test_sample_and_parallel_states_do_not_reopen_work():
    sample = _load("03_PUBLIC_SAMPLE_STATE.json")
    assert sample["further_generic_sample_work_justified"] is False
    assert sample["acquisition_started"] is False
    assert sample["source_diversity_result"].startswith("NO_NEW_VERIFIED")
    parallel = (OUT / "07_PARALLEL_STATE.md").read_text(encoding="utf-8")
    assert "| PRED-M4 | Insufficient sample; unchanged |" in parallel
    assert "RAG | 1,205 documents; no rebuild" in parallel
    assert "P032 | Implemented/frozen; unchanged" in parallel


def test_final_acceptance_and_reopen_trigger_preserve_safety_boundary():
    acceptance = (OUT / "08_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8")
    trigger = (OUT / "06_REOPEN_TRIGGER.md").read_text(encoding="utf-8")
    assert "ADB_FORMAL_EXPORT_SUSPENDED_2026_PACKAGE_PRESERVED" in acceptance
    assert "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED" in acceptance
    assert "No scraping" in acceptance
    assert "No assumed calendar date" in trigger
    assert "1 January 2027" in trigger


def test_existing_unsent_package_is_preserved():
    package = ROOT / "docs" / "current-state" / "evidence-adb-access-rx-2026-001"
    assert (package / "05_PROVIDER_REQUEST_DRAFT.md").exists()
    assert (package / "06_FOUNDER_ADB_ACCESS_ACTION_CARD.md").exists()
    text = (package / "06_FOUNDER_ADB_ACCESS_ACTION_CARD.md").read_text(encoding="utf-8")
    assert "Do not invent credentials" in text
    assert "no claim that VEDA has provider approval" in text
