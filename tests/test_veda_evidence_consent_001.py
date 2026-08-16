"""Synthetic-only consent corpus foundation tests."""

import json

import pytest

from scripts.veda_evidence_consent_001 import build, deidentified_export, transition


def test_synthetic_only_and_india_support():
    result = build()
    assert result["synthetic_only"] is True
    assert result["real_participants"] == 0
    assert result["real_personal_data"] is False
    assert sum(p["jurisdiction"] == "IN" for p in result["participants"]) == 5


def test_granular_versioned_consent_and_pseudonymous_identity():
    result = build()
    assert all(p["participant_id"].startswith("SYNTH-P-") for p in result["participants"])
    assert all(p["consent"]["version"] for p in result["participants"])
    assert all("CORE_RESEARCH" in p["consent"]["scopes"] for p in result["participants"])
    assert all(p["identity_vault_ref"] is None for p in result["participants"])


def test_withdrawal_and_state_transitions():
    assert transition("INVITED", "CONSENT_PENDING") == "CONSENT_PENDING"
    assert transition("WITHDRAWAL_REQUESTED", "WITHDRAWN") == "WITHDRAWN"
    with pytest.raises(ValueError):
        transition("WITHDRAWN", "ACTIVE_FOLLOWUP")
    assert any(p["status"] == "WITHDRAWN" for p in build()["participants"])


def test_multievent_precision_and_source_separation():
    result = build()
    assert len(result["events"]) == 50
    assert {e["precision"] for e in result["events"]} == {"DAY", "MONTH", "YEAR"}
    assert all("source_status" in e and "family" in e for e in result["events"])
    assert all("birth" in p and p["birth"]["evidence_tier"] in {"A", "B", "C"} for p in result["participants"])


def test_snapshot_export_and_determinism():
    first = build(); second = build()
    assert first["snapshot"] == second["snapshot"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    exported = deidentified_export(first["participants"], first["events"])
    assert all("birth_date" not in row and "birth_time" not in row for row in exported["participants"])


def test_recruitment_and_prediction_gates():
    result = build()
    assert result["recruitment_gate"] == "NOT_READY_EXTERNAL_REVIEW_REQUIRED"
    assert result["governance"]["predictions_executed"] is False
    assert result["governance"]["astrology_inspected"] is False
    assert result["formal_access"]["submission_performed"] is False
