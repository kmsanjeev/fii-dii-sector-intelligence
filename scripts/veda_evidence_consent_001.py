"""Synthetic-only consented longitudinal corpus foundation.

No production database, registration endpoint, personal-data store, or external
contact is used. The module provides deterministic research contracts and a
synthetic fixture builder for governance testing only.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-consent-001"
RECRUITMENT_STATUS = "NOT_READY_EXTERNAL_REVIEW_REQUIRED"
REAL_PARTICIPANT_COUNT = 0
REAL_PERSONAL_DATA_PRESENT = False
CONSENT_SCOPES = ("CORE_RESEARCH", "BIRTH_DOCUMENT_VERIFICATION", "LONGITUDINAL_FOLLOWUP", "EVENT_DOCUMENT_UPLOAD", "AGGREGATED_PUBLICATION", "DEIDENTIFIED_RESEARCH_SHARING", "FUTURE_RECONTACT")
PARTICIPANT_STATES = ("INVITED", "CONSENT_PENDING", "CONSENTED", "BIRTH_EVIDENCE_PENDING", "BIRTH_EVIDENCE_VERIFIED", "ACTIVE_FOLLOWUP", "PAUSED", "WITHDRAWAL_REQUESTED", "WITHDRAWN", "CLOSED")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def transition(current: str, target: str) -> str:
    allowed = {"INVITED": {"CONSENT_PENDING"}, "CONSENT_PENDING": {"CONSENTED", "CLOSED"}, "CONSENTED": {"BIRTH_EVIDENCE_PENDING", "WITHDRAWAL_REQUESTED"}, "BIRTH_EVIDENCE_PENDING": {"BIRTH_EVIDENCE_VERIFIED", "WITHDRAWAL_REQUESTED"}, "BIRTH_EVIDENCE_VERIFIED": {"ACTIVE_FOLLOWUP", "PAUSED", "WITHDRAWAL_REQUESTED"}, "ACTIVE_FOLLOWUP": {"PAUSED", "WITHDRAWAL_REQUESTED", "CLOSED"}, "PAUSED": {"ACTIVE_FOLLOWUP", "WITHDRAWAL_REQUESTED", "CLOSED"}, "WITHDRAWAL_REQUESTED": {"WITHDRAWN"}, "WITHDRAWN": set(), "CLOSED": set()}
    if target not in allowed.get(current, set()):
        raise ValueError(f"INVALID_PARTICIPANT_TRANSITION:{current}->{target}")
    return target


def synthetic_participant(index: int) -> dict[str, Any]:
    tier = "A" if index <= 8 else "B" if index <= 16 else "C"
    country = "IN" if index % 5 == 0 else "US" if index % 2 else "GB"
    status = "WITHDRAWN" if index == 25 else "ACTIVE_FOLLOWUP" if index <= 20 else "BIRTH_EVIDENCE_PENDING"
    scopes = ["CORE_RESEARCH", "BIRTH_DOCUMENT_VERIFICATION"] + (["LONGITUDINAL_FOLLOWUP", "AGGREGATED_PUBLICATION"] if index <= 20 else [])
    return {
        "participant_id": f"SYNTH-P-{index:04d}", "synthetic": True, "status": status,
        "consent": {"version": "SYNTH-CONSENT-1.0", "date": "2026-01-15", "scopes": scopes, "language": "en" if country != "IN" else "en-IN", "withdrawal_terms": "versioned_policy", "retention_scope": "research_metadata_only"},
        "jurisdiction": country, "birth": {"date": f"19{index % 80 + 20:02d}-01-{index:02d}", "time": f"{index % 24:02d}:{(index * 2) % 60:02d}", "precision": "EXACT_MINUTE" if index % 4 else "ROUNDED_5_MIN", "place": "SYNTHETIC_CITY", "country": country, "timezone": "Asia/Kolkata" if country == "IN" else "UTC", "document_type": "BIRTH_CERTIFICATE" if tier == "A" else "HOSPITAL_RECORD" if tier == "B" else "SELF_REPORTED_WITH_DOCUMENT", "verification_status": "VERIFIED" if tier in {"A", "B"} else "PARTIALLY_VERIFIED", "evidence_tier": tier, "time_qualifier": "DOCUMENTED" if tier in {"A", "B"} else "UNRESOLVED", "conflict_state": "MATERIAL_CONFLICT" if index in {23, 24} else "CONSISTENT", "source_hash": digest(f"synthetic-birth-{index}")},
        "followup": {"cycle": "QUARTERLY", "last_followup": "2026-04-01", "next_followup": "2026-07-01", "state": "STOPPED" if status == "WITHDRAWN" else "PLANNED", "response_status": "WITHDRAWN" if status == "WITHDRAWN" else "SYNTHETIC"},
        "privacy_class": "SENSITIVE", "identity_vault_ref": None,
    }


def synthetic_events(index: int) -> list[dict[str, Any]]:
    precision = "DAY" if index % 3 == 1 else "MONTH" if index % 3 == 2 else "YEAR"
    return [{"event_id": f"SYNTH-E-{index:04d}-01", "participant_id": f"SYNTH-P-{index:04d}", "family": "EDUCATION", "date_start": f"2020-01-{index:02d}" if precision == "DAY" else "2020-01" if precision == "MONTH" else "2020", "date_end": f"2020-01-{index:02d}" if precision == "DAY" else "2020-03" if precision == "MONTH" else "2020", "precision": precision, "original_description": "synthetic education completion", "source_status": "DOCUMENT_SUPPORTED", "provenance": "SYNTHETIC_DOCUMENT", "classification": "RESEARCH_INTERNAL", "temporal_mode": "RETROSPECTIVE_DOCUMENTED"}, {"event_id": f"SYNTH-E-{index:04d}-02", "participant_id": f"SYNTH-P-{index:04d}", "family": "EMPLOYMENT", "date_start": "2022-06-01" if precision == "DAY" else "2022-06" if precision == "MONTH" else "2022", "date_end": "2022-06-01" if precision == "DAY" else "2022-08" if precision == "MONTH" else "2022", "precision": precision, "original_description": "synthetic employment start", "source_status": "OFFICIAL_RECORD" if index <= 16 else "SELF_REPORTED", "provenance": "SYNTHETIC_RECORD", "classification": "RESEARCH_INTERNAL", "temporal_mode": "PROSPECTIVE_OBSERVED" if index <= 20 else "RETROSPECTIVE_REPORTED"}]


def eligible(participant: dict[str, Any], events: list[dict[str, Any]], *, required_birth_tier: set[str] = {"A", "B"}, required_event_precision: set[str] = {"DAY"}) -> bool:
    return participant["status"] in {"ACTIVE_FOLLOWUP", "BIRTH_EVIDENCE_VERIFIED"} and participant["birth"]["evidence_tier"] in required_birth_tier and "CORE_RESEARCH" in participant["consent"]["scopes"] and any(event["precision"] in required_event_precision and event["participant_id"] == participant["participant_id"] for event in events)


def deidentified_export(participants: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    exported = []
    for participant in participants:
        exported.append({"research_id": digest(participant["participant_id"])[:16], "jurisdiction": participant["jurisdiction"], "birth_tier": participant["birth"]["evidence_tier"], "birth_precision": participant["birth"]["precision"], "status": participant["status"]})
    return {"export_id": "SYNTH-EXPORT-001", "dataset_version": "SYNTH-DATA-1.0", "consent_scope": "DEIDENTIFIED_RESEARCH_SHARING", "deidentification_method": "PSEUDONYMOUS_HASH_NO_IDENTITY_VAULT_FIELDS", "participants": exported, "event_count": len(events)}


def build() -> dict[str, Any]:
    participants = [synthetic_participant(i) for i in range(1, 26)]
    events = [event for i in range(1, 26) for event in synthetic_events(i)]
    eligible_ids = [p["participant_id"] for p in participants if eligible(p, events)]
    snapshot = {"snapshot_id": "SYNTH-SNAPSHOT-001", "subject_hash": digest(participants), "event_hash": digest(events), "consent_policy_hash": digest({"version": "SYNTH-CONSENT-1.0", "scopes": CONSENT_SCOPES}), "eligibility_policy_hash": digest({"birth_tiers": ["A", "B"], "event_precision": ["DAY"], "consent": "CORE_RESEARCH"}), "source_manifest_hash": digest("SYNTHETIC_SOURCE_MANIFEST-1")}
    return {"programme": "VEDA-EVIDENCE-CONSENT-001", "status": "PASS_WITH_CONDITION", "synthetic_only": True, "recruitment": "NOT_AUTHORIZED", "real_participants": REAL_PARTICIPANT_COUNT, "real_personal_data": REAL_PERSONAL_DATA_PRESENT, "participants": participants, "events": events, "eligible_ids": eligible_ids, "snapshot": snapshot, "deidentified_export": deidentified_export(participants, events), "recruitment_gate": RECRUITMENT_STATUS, "formal_access": {"astro_databank": "FORMAL_PERMISSION_REQUIRED", "human_action_artifact": "READY", "submission_performed": False}, "security": {"roles": ["PARTICIPANT", "RESEARCH_REVIEWER", "EVIDENCE_ADJUDICATOR", "RESEARCH_ADMIN", "SYSTEM_ADMIN"], "identity_vault_separate": True, "encryption": ["IN_TRANSIT", "AT_REST", "DOCUMENTS", "BACKUPS"], "threat_review": "CONDITIONAL_EXTERNAL_REVIEW_REQUIRED", "open_risks": ["legal_review", "privacy_review", "ethics_review", "incident_response", "key_management"]}, "governance": {"astrology_inspected": False, "predictions_executed": False, "production_changed": False, "approved_core_changed": False, "rag_changed": False, "ml": False, "provider_calls_added": 0}, "manifest_hash": digest({"snapshot": snapshot, "participant_count": 25, "event_count": len(events), "synthetic_only": True})}


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    artifacts = [("01_SYNTHETIC_CORPUS.json", result), ("02_RESEARCH_SNAPSHOT.json", result["snapshot"]), ("03_DEIDENTIFIED_EXPORT.json", result["deidentified_export"]), ("04_SECURITY_MODEL.json", result["security"]), ("05_FINAL_MANIFEST.json", {key: result[key] for key in ("programme", "status", "synthetic_only", "recruitment", "real_participants", "real_personal_data", "eligible_ids", "snapshot", "recruitment_gate", "formal_access", "security", "governance", "manifest_hash")})]
    for name, value in artifacts:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    write()
