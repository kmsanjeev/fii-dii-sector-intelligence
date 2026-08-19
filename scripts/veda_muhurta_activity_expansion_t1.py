"""Non-production machine contracts for Muhurta Activity Expansion T1.

This module is a diagnostic/contract fixture only.  It deliberately does not
register activities with the production recommendation or window-search
engines.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CONTRACT_VERSION = "1.0.0"
SOURCE_STANDARD = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"

FIXED_NAKSHATRAS = (
    "Rohini",
    "Uttara Phalguni",
    "Uttara Ashadha",
    "Uttara Bhadrapada",
)
LIGHT_NAKSHATRAS = ("Ashwini", "Pushya", "Hasta")

ACTIVITIES: dict[str, dict[str, Any]] = {
    "VEHICLE_CONVEYANCE_COMMENCEMENT": {
        "source_activity_class": "SHILPA_AUSHADHA_YANA_ACTION_FAMILY",
        "normalized_name": "Vehicle or conveyance first use/acquisition commencement",
        "source_assertions": ["VEDA-SWW-ASSERTION-BS-NAK-VEHICLE-001"],
        "source_passages": ["VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-09-001"],
        "rule_ids": ["MUH-T1-VEHICLE-NAK-001"],
        "factor_ids": ["P032-CALC-NAKSHATRA-001"],
        "evaluator_ids": ["MUH-T1-EVAL-NAKSHATRA-LIGHT-001"],
        "expected_nakshatra_class": "LIGHT",
        "hard_requirements": [],
        "hard_exclusions": [],
        "nonblocking_gaps": [
            "No activity-specific Vara/Yoga contract",
            "Tithi/Karana composition is not added without a source-bound vehicle assertion",
            "Personal Bala remains diagnostic/source-partial",
        ],
        "caution_class": "MODERATE_CONSEQUENCE_PROPERTY_CONTEXT",
        "consultation_class": "PRACTICAL_FINANCIAL_AND_SAFETY_CONTEXT_REQUIRED",
    },
    "CONSECRATION_INSTALLATION_COMMENCEMENT": {
        "source_activity_class": "ABHISHEKA_SHANTI_DHRUVA_ESTABLISHMENT_ACTION_FAMILY",
        "normalized_name": "Consecration or deity/temple installation commencement",
        "source_assertions": ["VEDA-SWW-ASSERTION-BS-NAK-CONSECRATION-001"],
        "source_passages": ["VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-06-001"],
        "rule_ids": ["MUH-T1-INSTALLATION-NAK-001"],
        "factor_ids": ["P032-CALC-NAKSHATRA-001"],
        "evaluator_ids": ["MUH-T1-EVAL-NAKSHATRA-FIXED-001"],
        "expected_nakshatra_class": "FIXED",
        "hard_requirements": ["CEREMONY_SUBTYPE_EXPLICIT"],
        "hard_exclusions": [],
        "nonblocking_gaps": [
            "No activity-specific Vara/Yoga contract",
            "Lineage/ritual procedure must be supplied by the relevant tradition",
            "Personal Bala remains diagnostic/source-partial",
        ],
        "caution_class": "LOW_RISK_TRADITIONAL",
        "consultation_class": "QUALIFIED_TRADITIONAL_PRACTITIONER_WHERE_RITUAL_SPECIFIC",
    },
}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def contract_hash(activity_id: str) -> str:
    return hashlib.sha256(_canonical(contract_payload(activity_id)).encode("utf-8")).hexdigest().upper()


def contract_payload(activity_id: str) -> dict[str, Any]:
    activity = ACTIVITIES[activity_id]
    return {
        "contract_id": f"VEDA-MUH-T1-CONTRACT-{activity_id}-V1",
        "version": CONTRACT_VERSION,
        "activity_id": activity_id,
        "activity_scope": activity["normalized_name"],
        "source_tradition": ["BRIHAT_SAMHITA_SCOPED_ACTION_FAMILIES", "VEDA_P032_FACT_CONTRACT"],
        "rule_ids": activity["rule_ids"],
        "hard_exclusions": activity["hard_exclusions"],
        "hard_requirements": activity["hard_requirements"],
        "strong_negatives": [],
        "preference_negatives": [],
        "preference_positives": activity["rule_ids"],
        "strong_positives": [],
        "context_rules": ["NO_UNIVERSAL_AUSPICIOUSNESS", "NO_OUTCOME_GUARANTEE"],
        "personal_factors": ["TARA_CHANDRA_DIAGNOSTIC_ONLY"],
        "source_variants": ["BRIHAT_SAMHITA_NUMBERING_VARIANT_RETAINED"],
        "precedence": ["HARD_EXCLUSION", "HARD_REQUIREMENT", "CONTEXT", "PREFERENCE", "ABSTAIN"],
        "abstention": ["MISSING_NAKSHATRA", "ACTIVITY_SCOPE_MISMATCH", "CEREMONY_SUBTYPE_MISSING"],
        "caution_class": activity["caution_class"],
        "consultation_class": activity["consultation_class"],
        "production_bound": False,
        "readiness": "MACHINE_CONTRACT_READY_WITH_NONBLOCKING_GAPS",
        "source_standard": SOURCE_STANDARD,
    }


def evaluate_activity(activity_id: str, factors: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only the source-bound Nakshatra predicate for diagnostics."""
    activity = ACTIVITIES[activity_id]
    if activity_id == "CONSECRATION_INSTALLATION_COMMENCEMENT" and not factors.get("ceremony_subtype"):
        return {"status": "ABSTAIN", "reason": "CEREMONY_SUBTYPE_MISSING", "production": False}
    nakshatra = factors.get("nakshatra")
    if not nakshatra:
        return {"status": "ABSTAIN", "reason": "MISSING_NAKSHATRA", "production": False}
    if activity["expected_nakshatra_class"] == "LIGHT":
        matched = nakshatra in LIGHT_NAKSHATRAS
    else:
        matched = nakshatra in FIXED_NAKSHATRAS
    return {
        "status": "PREFERENCE_POSITIVE" if matched else "ABSTAIN",
        "reason": "SOURCE_BOUND_NAKSHATRA_CLASS_MATCH" if matched else "NO_SOURCE_BOUND_CLASS_MATCH",
        "matched": matched,
        "production": False,
        "contract_id": contract_payload(activity_id)["contract_id"],
    }


def build_handoff() -> dict[str, Any]:
    activities = []
    for activity_id in ACTIVITIES:
        activity = ACTIVITIES[activity_id]
        activities.append(
            {
                "activity_id": activity_id,
                "contract_id": contract_payload(activity_id)["contract_id"],
                "contract_hash": contract_hash(activity_id),
                "source_tradition": contract_payload(activity_id)["source_tradition"],
                "required_factors": activity["factor_ids"],
                "optional_factors": ["P032-CALC-TITHI-001", "P032-CALC-KARANA-001"],
                "rule_ids": activity["rule_ids"],
                "evaluator_ids": activity["evaluator_ids"],
                "nonblocking_gaps": activity["nonblocking_gaps"],
                "blocking_gaps": [],
                "precedence": contract_payload(activity_id)["precedence"],
                "abstention": contract_payload(activity_id)["abstention"],
                "caution": activity["caution_class"],
                "consultation": activity["consultation_class"],
                "source_lineage": {
                    "assertions": activity["source_assertions"],
                    "passages": activity["source_passages"],
                    "standard": SOURCE_STANDARD,
                },
                "runtime_state": "INACTIVE",
            }
        )
    return {"programme": "VEDA-MUHURTA-ACTIVITY-EXPANSION-T1-001", "production_activation": False, "activities": activities}


__all__ = [
    "ACTIVITIES",
    "CONTRACT_VERSION",
    "FIXED_NAKSHATRAS",
    "LIGHT_NAKSHATRAS",
    "build_handoff",
    "contract_hash",
    "contract_payload",
    "evaluate_activity",
]
