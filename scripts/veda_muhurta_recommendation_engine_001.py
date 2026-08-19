"""Fail-closed conformance gate for VEDA-MUHURTA-RECOMMENDATION-ENGINE-001.

The accepted activity contracts are immutable.  This module deliberately does
not interpret their prose conditions.  It verifies whether each rule carries
an explicit machine evaluator binding; if not, the recommendation engine is
blocked rather than inventing a source-derived mapping.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

try:  # Direct CLI execution puts ``scripts`` on sys.path; pytest uses repo root.
    from scripts.veda_muhurta_activity_rule_contracts_001 import digest
except ModuleNotFoundError:  # pragma: no cover - exercised by the CLI smoke.
    from veda_muhurta_activity_rule_contracts_001 import digest


PROGRAMME = "VEDA-MUHURTA-RECOMMENDATION-ENGINE-001"
ENGINE_VERSION = "MUHURTA_GENERAL_RECOMMENDATION_V1_NOT_ACTIVATED"
DECISION = "MUHURTA_ACTIVITY_CONTRACT_IMPLEMENTATION_BLOCKED"
CONTRACT_ROOT = Path("docs/current-state/muhurta-activity-rule-contracts-001")
CONTRACTS = {
    "BUSINESS_OPENING_INAUGURATION": {
        "file": "03_BUSINESS_OPENING_RULE_CONTRACT.json",
        "contract_hash": "941E9ECB9960652C",
    },
    "EDUCATION_COMMENCEMENT": {
        "file": "04_EDUCATION_COMMENCEMENT_RULE_CONTRACT.json",
        "contract_hash": "FFE718B6AAA8D6C9",
    },
    "RELIGIOUS_SPIRITUAL_CEREMONY": {
        "file": "05_RELIGIOUS_CEREMONY_RULE_CONTRACT.json",
        "contract_hash": "A700789D07BD477D",
    },
}

# These are intentionally an allow-list of possible normalized bindings.  The
# current contracts contain none of them.  A prose ``condition`` is never an
# evaluator and is never parsed here.
MACHINE_BINDING_FIELDS = (
    "evaluator_id",
    "predicate_id",
    "predicate",
    "machine_condition",
    "allowed_values",
    "factor_values",
    "operands",
)
SUPPORTED_ACTIVITIES = {
    "BUSINESS_OPENING_INAUGURATION",
    "EDUCATION_COMMENCEMENT",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"contract must be an object: {path}")
    return value


def _contract_hash(contract: Mapping[str, Any]) -> str:
    payload = dict(contract)
    payload.pop("contract_hash", None)
    return digest(payload)


def load_contract(activity_id: str, root: Path = CONTRACT_ROOT) -> dict[str, Any]:
    binding = CONTRACTS[activity_id]
    contract = _read_json(root / binding["file"])
    claimed = contract.get("contract_hash")
    computed = _contract_hash(contract)
    if claimed != binding["contract_hash"] or computed != claimed:
        raise ValueError(
            f"contract hash mismatch for {activity_id}: claimed={claimed!r}, computed={computed!r}"
        )
    if contract.get("activity_id") != activity_id:
        raise ValueError(f"activity id mismatch for {activity_id}")
    return contract


def _machine_fields(rule: Mapping[str, Any]) -> list[str]:
    return [field for field in MACHINE_BINDING_FIELDS if field in rule]


def audit_contract(activity_id: str, root: Path = CONTRACT_ROOT) -> dict[str, Any]:
    contract = load_contract(activity_id, root)
    rules = contract.get("rules", [])
    diagnostics = []
    for rule in rules:
        bindings = _machine_fields(rule)
        # Source prose, source IDs, factor_type, and validation_state are
        # provenance/metadata, not executable rule predicates.
        if not bindings:
            diagnostics.append(
                {
                    "rule_id": rule.get("rule_id"),
                    "factor_type": rule.get("factor_type"),
                    "rule_class": rule.get("rule_class"),
                    "recommendation_effect": rule.get("recommendation_effect"),
                    "machine_binding_fields": [],
                    "condition_field_is_prose_only": isinstance(rule.get("condition"), str),
                    "status": "NOT_MACHINE_EXECUTABLE",
                    "reason": "NO_ACCEPTED_MACHINE_EVALUATOR_BINDING",
                }
            )
    return {
        "activity_id": activity_id,
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "recommendation_engine_state": contract.get("recommendation_engine_state"),
        "contract_hash_verified": True,
        "rule_count": len(rules),
        "rules_without_machine_binding": diagnostics,
        "machine_executable": not diagnostics,
        "activity_state": "BLOCKED" if diagnostics else "READY_FOR_EVALUATION",
    }


def activity_guard(activity_id: str) -> dict[str, Any]:
    """Return a categorical guard result without selecting or scoring a time."""
    if activity_id not in SUPPORTED_ACTIVITIES:
        return {
            "activity_id": activity_id,
            "recommendation_state": "ABSTAIN",
            "abstention_reason": "UNSUPPORTED_ACTIVITY",
        }
    return {
        "activity_id": activity_id,
        "recommendation_state": "ABSTAIN",
        "abstention_reason": DECISION,
    }


def build_report(root: Path = CONTRACT_ROOT) -> dict[str, Any]:
    audits = [audit_contract(activity_id, root) for activity_id in CONTRACTS]
    return {
        "programme": PROGRAMME,
        "engine_version": ENGINE_VERSION,
        "decision": DECISION,
        "recommendation_runtime": "NOT_ACTIVATED",
        "production_activation": False,
        "contracts_immutable": True,
        "prose_conditions_interpreted": False,
        "numeric_scoring": False,
        "contracts": audits,
        "supported_activity_guards": [activity_guard(item) for item in sorted(SUPPORTED_ACTIVITIES)],
        "unsupported_activity_guard": activity_guard("MARRIAGE"),
        "blocker": {
            "code": "NO_MACHINE_EVALUATOR_BINDINGS_IN_ACCEPTED_CONTRACTS",
            "impact": "Business and education source-backed rules cannot be evaluated without inventing factor mappings.",
            "required_remediation": "Amend or replace the activity contracts through a separately authorized contract-remediation activity; do not patch them here.",
        },
        "preserved": [
            "P032 calculation-only facts and inactive recommendation gates",
            "activity contract hashes and source lineage",
            "religious source-hardening gate",
            "personal Bala, ranking, scoring and high-risk activity exclusions",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["decision"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
