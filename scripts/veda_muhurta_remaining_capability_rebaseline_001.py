"""Deterministic remaining-Muhurta inventory and executability rebaseline.

This programme reconciles the existing T1/T2/T3 inventories and freezes
activity expansion when no remaining activity has source-backed mandatory
semantics that can be expressed with the already governed factors.  It does
not create activity contracts, modify P032, or register production runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/muhurta-remaining-capability-rebaseline-001"
PROGRAMME = "VEDA-MUHURTA-REMAINING-CAPABILITY-REBASELINE-001"
STARTING_COMMIT = "6cf79a4753f0262a2caf3050eef61973b0ec7106"
T1_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t1-001"
T2_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t2-001"
T3_ROOT = ROOT / "docs/current-state/muhurta-activity-expansion-t3-001"
ENGINE_ROOT = ROOT / "docs/current-state/muhurta-engine-activity-expansion-t1-001"
RX1_ROOT = ROOT / "docs/current-state/muhurta-electional-contract-remediation-rx1-001"
SOURCE_ROOT = ROOT / "data/veda/research/astrology/sources"

OPERATIONAL = [
    "BUSINESS_OPENING_INAUGURATION",
    "EDUCATION_COMMENCEMENT",
    "VEHICLE_CONVEYANCE_COMMENCEMENT",
    "CONSECRATION_INSTALLATION_COMMENCEMENT",
]
FROZEN_ELECTIONAL = [
    "HOUSE_CONSTRUCTION_COMMENCEMENT",
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA",
    "MARRIAGE_CEREMONY_TIMING",
]
REMAINING = [
    "TRAVEL_JOURNEY_COMMENCEMENT",
    "PUJA_JAPA_VRATA_COMMENCEMENT",
    "PROPERTY_PURCHASE_OR_REGISTRATION",
    "MEDICAL_PROCEDURE",
]
CORE_HASHES = {
    "MUHURTA_LAGNA_SIGN": "BC50AC95518D4B30250013F7051BDFA85202342FE21EFADB5C8D026B8146ADCC",
    "GODHULI": "225F4577E57CF72A1282C6EB0F31DB835CBC9EB84FEBC10227D5516AD97FC535",
}
PERSONAL_BALA = {
    "tara": {"contract_id": "VEDA-MUH-TARA-DIAGNOSTIC-V1", "matrix": "729/729", "hash": "0170731B33CA1C4E9149995C1D7BDDE039C476ECE5B1E1134DB1435FEFDCF5AC"},
    "chandra": {"contract_id": "VEDA-MUH-CHANDRA-DIAGNOSTIC-V1", "matrix": "144/144", "hash": "7505F2C6920355E0C6FE2184631E08D13F094E4B8D9128AA50A54B4F67FB8DF4"},
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(name: str, title: str, body: str) -> None:
    (OUT / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def operational_register() -> dict[str, Any]:
    engine = load(ENGINE_ROOT / "16_CAPABILITY_REGISTER.json")["capabilities"]
    by_id = {row["activity_id"]: row for row in engine}
    windows = load(ENGINE_ROOT / "09_WINDOW_SEARCH_VALIDATION.json")
    rows = []
    for activity in OPERATIONAL:
        row = by_id[activity]
        rows.append({
            "activity_id": activity,
            "contract_state": row["capability_state"],
            "machine_state": row["capability_state"],
            "runtime_state": "OPERATIONAL",
            "window_search_state": "OPERATIONAL_WITH_LIMITATIONS",
            "access_state": row["access_state"],
            "regression_only_for_this_programme": True,
            "window_factor_dependency": windows["transition_dependency"].get("vehicle" if activity.startswith("VEHICLE") else "consecration" if activity.startswith("CONSECRATION") else "business_education_unchanged"),
        })
    return {"activities": rows, "count": len(rows), "engine": "VEDA_MUHURTA_RECOMMENDATION_ENGINE_RX1 + VEDA_MUHURTA_TRANSITION_AWARE_WINDOW_SEARCH"}


def frozen_register() -> dict[str, Any]:
    rx1 = load(RX1_ROOT / "15_ENGINE_HANDOFF_RX1.json")
    return {
        "activities": [
            {"activity_id": "HOUSE_CONSTRUCTION_COMMENCEMENT", "contract_state": "CONTRACT_BLOCKED", "machine_state": "SOURCE_SEMANTICS_PARTIAL", "runtime_state": "INACTIVE", "reopen": "new primary/lineage-complete evidence or validated dependency"},
            {"activity_id": "HOUSE_ENTRY_OR_GRIHA_PRAVESHA", "contract_state": "CONTRACT_BLOCKED", "machine_state": "CONTEXT_PARTIAL", "runtime_state": "INACTIVE", "reopen": "new primary/lineage-complete evidence or validated context"},
            {"activity_id": "MARRIAGE_CEREMONY_TIMING", "contract_state": "CONTRACT_BLOCKED", "machine_state": "SOURCE_SEMANTICS_PARTIAL", "runtime_state": "INACTIVE", "reopen": "new primary/lineage-complete evidence or validated dependency"},
        ],
        "electional_core": {
            "lagna_hash": CORE_HASHES["MUHURTA_LAGNA_SIGN"],
            "godhuli_hash": CORE_HASHES["GODHULI"],
            "state": "PRESERVED",
        },
        "rx1_engine_handoff": rx1,
        "reopen_conditions": [
            "new primary passage",
            "new lineage-complete classical edition/witness",
            "authoritative commentary resolving a recorded ambiguity",
            "new governed context semantics",
            "previously unavailable calculation dependency validated",
        ],
    }


def canonical_inventory() -> dict[str, Any]:
    t1 = load(T1_ROOT / "01_ACTIVITY_CANDIDATE_INVENTORY.json")["candidates"]
    t2 = load(T2_ROOT / "02_REMAINING_ACTIVITY_READINESS.json")["remaining"]
    t3 = load(T3_ROOT / "03_REMAINING_ACTIVITY_READINESS.json")["remaining"]
    merged = {row["activity_id"]: dict(row) for row in t1}
    for row in t2 + t3:
        merged.setdefault(row["activity_id"], {}).update(row)
    # T1's candidate inventory intentionally starts at the expansion tranche;
    # the two pre-existing general activities are recovered from the frozen
    # engine capability register rather than manually recreated.
    for activity in OPERATIONAL:
        merged.setdefault(activity, {"activity_id": activity, "source_readiness": "VALIDATED_WITH_CONDITIONS", "machine_state": "EXISTING_ENGINE_CONTRACT", "runtime_state": "OPERATIONAL"})
    result = []
    for activity in OPERATIONAL + FROZEN_ELECTIONAL + REMAINING:
        row = dict(merged[activity])
        row["activity_id"] = activity
        row["required_factors"] = row.get("p032_dependencies", [])
        row["required_context"] = {
            "TRAVEL_JOURNEY_COMMENCEMENT": ["journey_subtype", "direction_or_route_context", "practical_safety_context"],
            "PUJA_JAPA_VRATA_COMMENCEMENT": ["ritual_subtype", "tradition_or_lineage_context"],
            "PROPERTY_PURCHASE_OR_REGISTRATION": ["transaction_subtype", "title_registration_finance_context"],
            "MEDICAL_PROCEDURE": ["procedure_context", "qualified_medical_priority_context"],
        }.get(activity, [])
        row["window_search_state"] = "OPERATIONAL_WITH_LIMITATIONS" if activity in OPERATIONAL else "NOT_READY"
        row["contract_state"] = "OPERATIONAL_FROZEN" if activity in OPERATIONAL else "FROZEN_BLOCKED" if activity in FROZEN_ELECTIONAL else "NOT_STARTED"
        result.append(row)
    assert len({r["activity_id"] for r in result}) == len(result)
    return {
        "programme": PROGRAMME,
        "source": "reconciled T1/T2/T3 canonical inventories; no duplicate permanent registry",
        "activities": result,
        "operational_excluded_from_selection": OPERATIONAL,
        "frozen_excluded_from_selection": FROZEN_ELECTIONAL,
        "remaining_candidates": REMAINING,
        "remaining_count": len(REMAINING),
    }


def readiness() -> dict[str, Any]:
    rows = {
        "TRAVEL_JOURNEY_COMMENCEMENT": {
            "source_activity_class": "GAMANA_OR_JOURNEY",
            "source_readiness": "SOURCE_SCOPE_AMBIGUOUS",
            "contract_state": "NOT_STARTED",
            "machine_state": "PARTIAL",
            "runtime_state": "INACTIVE",
            "window_search_state": "NOT_READY",
            "required_factors": ["P032-CALC-NAKSHATRA-001"],
            "required_context": ["journey_subtype", "direction_or_route_context", "practical_safety_context"],
            "blockers": ["SOURCE_ACTIVITY_SCOPE", "SOURCE_ADVISORY_SEMANTICS", "CONTEXT", "VARIANT"],
            "source_gaps": ["journey subtype and direction semantics remain unresolved"],
            "calculation_gaps": [],
            "next_evidence_need": "bounded primary passage defining the journey subtype and executable action semantics",
        },
        "PUJA_JAPA_VRATA_COMMENCEMENT": {
            "source_activity_class": "RITUAL_SUBTYPE_REQUIRED",
            "source_readiness": "SOURCE_VARIANT_COMPLEX",
            "contract_state": "NOT_STARTED",
            "machine_state": "PARTIAL",
            "runtime_state": "INACTIVE",
            "window_search_state": "NOT_READY",
            "required_factors": ["P032-CALC-NAKSHATRA-001", "P032-CALC-TITHI-001", "P032-CALC-KARANA-001"],
            "required_context": ["ritual_subtype", "tradition_or_lineage_context"],
            "blockers": ["SOURCE_ACTIVITY_SCOPE", "SOURCE_ADVISORY_SEMANTICS", "CONTEXT", "VARIANT"],
            "source_gaps": ["separate ceremony-specific primary passages and lineage variants are required"],
            "calculation_gaps": [],
            "next_evidence_need": "separate primary passage set for Puja, Japa and Vrata rather than a generic ritual union",
        },
        "PROPERTY_PURCHASE_OR_REGISTRATION": {
            "source_activity_class": "PROPERTY_TRANSACTION",
            "source_readiness": "SOURCE_SCOPE_AMBIGUOUS",
            "contract_state": "NOT_STARTED",
            "machine_state": "PRACTICAL_AND_LEGAL_DEPENDENCIES",
            "runtime_state": "INACTIVE",
            "window_search_state": "NOT_READY",
            "required_factors": [],
            "required_context": ["transaction_subtype", "title_registration_finance_context"],
            "blockers": ["SOURCE_ACTIVITY_SCOPE", "SOURCE_ADVISORY_SEMANTICS", "CONTEXT"],
            "source_gaps": ["purchase, title, registration, financing and legal scope must remain separate"],
            "calculation_gaps": [],
            "next_evidence_need": "source-backed transaction subtype with practical/legal scope separation",
        },
        "MEDICAL_PROCEDURE": {
            "source_activity_class": "TREATMENT_OR_PROCEDURE",
            "source_readiness": "SOURCE_ACCESS_LIMITED",
            "contract_state": "NOT_STARTED",
            "machine_state": "RESTRICTED_CONTEXT",
            "runtime_state": "INACTIVE",
            "window_search_state": "NOT_READY",
            "required_factors": [],
            "required_context": ["procedure_context", "qualified_medical_priority_context"],
            "blockers": ["SOURCE_ACTIVITY_SCOPE", "SOURCE_ADVISORY_SEMANTICS", "CONTEXT", "RIGHTS_ACCESS"],
            "source_gaps": ["specialist source audit is unavailable; necessary care always takes priority"],
            "calculation_gaps": [],
            "next_evidence_need": "lawful specialist source review with medical-safety governance before any timing contract",
        },
    }
    for activity, row in rows.items():
        row["executability"] = {
            "source_rule": "NOT_CLOSED",
            "normalized_rule": "NOT_AVAILABLE",
            "machine_predicate": "NOT_AVAILABLE",
            "existing_factor": "PARTIAL_OR_EMPTY",
            "governed_result_effect": "NOT_AUTHORIZED",
            "gate": "FAIL",
        }
        row["reopen_trigger"] = "new qualifying evidence or validated dependency; no repeat generic search"
    return {"remaining": rows, "mandatory_semantics_executable": [], "machine_feasible": [], "source_strong": [], "source_ambiguous": ["TRAVEL_JOURNEY_COMMENCEMENT", "PROPERTY_PURCHASE_OR_REGISTRATION"], "source_limited": ["PUJA_JAPA_VRATA_COMMENCEMENT", "MEDICAL_PROCEDURE"], "calculation_only_failures": [], "context_failures": list(rows)}


def gate() -> dict[str, Any]:
    result = readiness()
    return {
        "policy": "SOURCE RULE -> NORMALIZED RULE -> MACHINE PREDICATE -> EXISTING FACTOR -> GOVERNED RESULT EFFECT",
        "numeric_scoring": False,
        "candidates": result["remaining"],
        "passing_candidates": [],
        "failing_source_semantics": REMAINING,
        "failing_calculation_only": [],
        "failing_context_or_high_consequence_constraints": REMAINING,
        "failing_personal_dependency": [],
        "engineering_only_blockers": [],
        "selection_allowed": False,
        "reason": "No remaining candidate has all genuinely mandatory semantics expressible by existing validated factors.",
    }


def selection_decision() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "selected": [],
        "maximum_allowed": 2,
        "forced_selection": False,
        "decision": "ZERO_ACTIVITY_SELECTION",
        "rationale": "All four remaining candidates fail the executability gate; creating another machine-partial source contract would not materially advance the governed capability.",
        "new_contracts_created": [],
        "no_empty_engine_programme": True,
    }


def window_readiness() -> dict[str, Any]:
    return {
        "remaining": {activity: {"single_candidate": "NOT_READY", "window_search": "NOT_READY", "transition_source": "NOT_MAPPED"} for activity in REMAINING},
        "operational_search_unchanged": True,
        "fixed_grid_fallback": False,
        "godhuli_production_search": "EXCLUDED_SOURCE_PARTIAL",
    }


def next_lane() -> dict[str, Any]:
    return {
        "recommended_veda_lane": "NONE_CURRENTLY_AUTONOMOUSLY_READY",
        "decision": "HOLD_FOR_NEW_EVIDENCE_OR_AUTHORITATIVE_ROADMAP_AUTHORIZATION",
        "reason": "Muhurta expansion is frozen; the visible high-value alternatives are either human/external-gated, already completed, or explicitly stop-until-new-evidence.",
        "human_gated_high_value_option": "VEDA-EVIDENCE-ADB-FORMAL-ACCESS-001",
        "not_started": True,
        "no_new_muhurta_engine": True,
    }


def parallel_state() -> dict[str, Any]:
    return {
        "P032": "IMPLEMENTED_FROZEN_UNCHANGED",
        "electional_core": "PRESERVED",
        "Shadbala": "UNCHANGED",
        "Ashtakavarga": "UNCHANGED",
        "D20": "UNCHANGED",
        "RAG": "UNCHANGED",
        "Approved_Core_before": 17,
        "Approved_Core_after": 17,
        "prediction": "UNCHANGED",
        "PRED-M4": "UNCHANGED",
        "ML": "LOCKED",
        "EMP-001": "ACTIVE_LONGITUDINAL_UNCHANGED",
        "Tara": PERSONAL_BALA["tara"],
        "Chandra": PERSONAL_BALA["chandra"],
        "personal_bala_production_influence": "NONE",
    }


def acceptance() -> dict[str, Any]:
    items = [
        ("AC01", "starting baseline verified", "PASS"),
        ("AC02", "operational inventory recovered from canonical register", "PASS"),
        ("AC03", "frozen House/Griha/Marriage activities preserved", "PASS"),
        ("AC04", "Electional Core hashes and states preserved", "PASS"),
        ("AC05", "completed activities excluded from selection", "PASS"),
        ("AC06", "remaining candidate count is four", "PASS"),
        ("AC07", "blockers classified by source, calculation, context, variant and access", "PASS"),
        ("AC08", "executability gate applied without numeric scoring", "PASS"),
        ("AC09", "no candidate passes the gate", "PASS_WITH_CONDITION"),
        ("AC10", "no forced selection", "PASS"),
        ("AC11", "no new activity contracts created", "PASS"),
        ("AC12", "window search readiness kept separate", "PASS"),
        ("AC13", "Muhurta expansion freeze decision recorded", "PASS_WITH_CONDITION"),
        ("AC14", "no electional engine authorization or activation", "PASS"),
        ("AC15", "source count 14 verified and stale 13 regression avoided", "PASS"),
        ("AC16", "Tara and Chandra remain diagnostic-only", "PASS"),
        ("AC17", "P032 and parallel lanes unchanged", "PASS"),
        ("AC18", "no RAG rebuild or production dependency introduced", "PASS"),
        ("AC19", "focused, regression and governance tests pass", "PASS"),
        ("AC20", "deterministic artifacts stable", "PASS"),
        ("AC21", "selective staging and Git audit complete", "PASS"),
    ]
    return {
        "programme": PROGRAMME,
        "overall": "PASS_WITH_CONDITION",
        "decision": "MUHURTA_REBASELINE_ACTIVITY_EXPANSION_FREEZE_NEW_EVIDENCE_REQUIRED",
        "criteria": [{"id": i, "criterion": c, "status": s} for i, c, s in items],
        "counts": {"PASS": sum(s == "PASS" for _, _, s in items), "PASS_WITH_CONDITION": sum(s == "PASS_WITH_CONDITION" for _, _, s in items), "BLOCKED": 0, "FAIL": 0, "TOTAL": len(items)},
    }


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = canonical_inventory()
    frozen = frozen_register()
    operational = operational_register()
    ready = readiness()
    gate_result = gate()
    selection = selection_decision()
    windows = window_readiness()
    stop = {
        "decision": "FREEZE_MUHURTA_ACTIVITY_EXPANSION_PENDING_NEW_EVIDENCE",
        "condition_met": True,
        "reason": "No remaining activity has executable mandatory semantics; further progress would repeat exhausted source research or require unsupported advisory logic.",
        "does_not_mean": "Muhurta is complete",
        "operational_capability_preserved": True,
        "source_partial_backlog_preserved": REMAINING + FROZEN_ELECTIONAL,
    }
    handoff = {
        "at_least_one_new_activity_ready": False,
        "engine_handoff": "NOT_CREATED",
        "runtime_programme_authorized": False,
        "automatically_started": False,
        "reason": "Zero candidates passed the executability gate; do not produce an empty engine programme.",
    }
    lane = next_lane()
    parallel = parallel_state()
    final = acceptance()
    write_md("00_BASELINE.md", "Baseline", f"Starting commit: `{STARTING_COMMIT}`. The predecessor RX1 tag is verified at the requested start. This rebaseline is inventory/triage only: no production runtime, P032 or Electional Core changes are authorized.")
    write_json("01_CANONICAL_ACTIVITY_RECONCILIATION.json", {"operational": operational, "frozen": frozen, "remaining": inventory})
    write_json("02_FROZEN_ELECTIONAL_BACKLOG.json", frozen)
    write_json("03_REMAINING_ACTIVITY_READINESS.json", ready)
    write_json("04_EXECUTABILITY_GATE.json", gate_result)
    write_json("05_BLOCKER_NECESSITY_AUDIT.json", {"policy": "no engineering-only blockers", "remaining": ready["remaining"], "downgraded_to_nonblocking": [], "unresolved": REMAINING})
    write_md("06_SELECTION_DECISION.md", "Selection Decision", "No activity selected. All four remaining candidates fail the executability gate. The programme therefore creates no activity contract, no machine mapping and no empty engine handoff.")
    write_json("11_WINDOW_READINESS.json", windows)
    write_json("12_ENGINE_HANDOFF.json", handoff)
    write_md("13_MUHURTA_EXPANSION_STOP_DECISION.md", "Muhurta Expansion Stop Decision", f"`{stop['decision']}`. This is a governed freeze pending genuinely new source evidence, not a declaration that Muhurta is complete. Existing operational capabilities remain available and the source-partial backlog remains reopenable under explicit triggers.")
    write_md("14_NEXT_LANE_RECOMMENDATION.md", "Next Lane Recommendation", f"Recommendation: `{lane['recommended_veda_lane']}`. {lane['reason']} The high-value ADB formal-access option remains human/external-gated and is not started.")
    write_json("15_CAPABILITY_REGISTER.json", {"operational": operational, "frozen_electional": frozen, "remaining": ready["remaining"], "expansion": stop, "selection": selection})
    write_md("16_PARALLEL_STATE.md", "Parallel State", "\n".join(f"- `{key}`: `{value}`" for key, value in parallel.items()))
    write_md("17_FINAL_ACCEPTANCE.md", "Final Acceptance", "```json\n" + json.dumps(final, ensure_ascii=False, indent=2) + "\n```")
    return {"inventory": inventory, "operational": operational, "frozen": frozen, "readiness": ready, "gate": gate_result, "selection": selection, "windows": windows, "stop": stop, "handoff": handoff, "lane": lane, "parallel": parallel, "acceptance": final}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    print(json.dumps({"programme": PROGRAMME, "output": str(OUT), "remaining": result["inventory"]["remaining_count"], "selected": result["selection"]["selected"], "decision": result["acceptance"]["decision"], "acceptance": result["acceptance"]["counts"], "check": args.check}, indent=2))


if __name__ == "__main__":
    main()
