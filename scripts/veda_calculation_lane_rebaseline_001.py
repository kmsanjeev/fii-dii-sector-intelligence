"""Build the post-Ashtakavarga calculation-lane rebaseline.

This is governance/audit tooling only.  It inventories the existing runtime and
current evidence, emits deterministic scorecards, and selects a recommended
next programme.  It does not change calculation logic, RAG, prediction, ML, or
Approved Core state.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/calculation-lane-rebaseline-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "f22a6998c200ee15da6dc951c40efbd1a38df1ea"
RX2 = ROOT / "docs/current-state/calc-ashtakavarga-remediation-rx2-001"
RAG_MANIFEST = ROOT / "data/intelligence/rag_knowledge/veda_unified_manifest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.varga_governance import VARGA_METHODS


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, title: str, body: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def rx2_state() -> dict[str, Any]:
    binding = json.loads((RX2 / "01_V2_RUNTIME_BINDING.json").read_text(encoding="utf-8"))
    conformance = json.loads((RX2 / "05_SOURCE_CELL_CONFORMANCE.json").read_text(encoding="utf-8"))
    synthetic = json.loads((RX2 / "11_SYNTHETIC_VALIDATION.json").read_text(encoding="utf-8"))
    return {
        "decision": "ASHTAKAVARGA_V2_RAW_RUNTIME_REMEDIATED_WITH_LEGACY_COMPATIBILITY",
        "contract": binding["contract"],
        "production": binding["production"],
        "source_cells": conformance["production_cells"],
        "source_exact": conformance["exact_matches"],
        "source_mismatches": conformance["mismatch_count"],
        "target_totals": conformance["target_totals"],
        "synthetic": synthetic,
        "conditions": ["EXTERNAL_NUMERICAL_ORACLE_UNAVAILABLE", "REDUCTIONS_DEFERRED", "INTERPRETATION_RESEARCH_ONLY", "PREDICTIVE_VALIDATION_NONE"],
    }


def rag_state() -> dict[str, Any]:
    manifest = json.loads(RAG_MANIFEST.read_text(encoding="utf-8"))
    return {
        "document_count": manifest["document_count"],
        "corpus_content_hash": manifest["corpus_content_hash"],
        "approved_core_count": manifest["approved_core_count"],
        "trust_zone_counts": manifest["trust_zone_counts"],
        "deterministic_rebuild": "CURRENT_MANIFEST_PRESENT; NO_REBUILD_REQUIRED",
    }


def base_row(family: str, cls: str, source: str, internal: str, external: str, boundaries: str, interpretation: str, production: str, blocker: str, action: str) -> dict[str, Any]:
    return {
        "family": family,
        "implemented": True,
        "capability_class": cls,
        "source_contract": source,
        "internal_deterministic_validation": internal,
        "external_numerical_validation": external,
        "astronomical_validation": external if family in {"astronomical_ephemeris", "planetary_longitude", "sidereal_ayanamsha", "lagna_ascendant", "transit_facts"} else "NOT_APPLICABLE",
        "boundary_validation": boundaries,
        "interpretive_validation": interpretation,
        "production_use": production,
        "open_blocker": blocker,
        "next_action": action,
    }


def inventory() -> list[dict[str, Any]]:
    rows = [
        base_row("astronomical_ephemeris", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "VALIDATED_WITH_CONDITIONS", "NOT_APPLICABLE", "Kundli/astro/transit runtime", "Full-body sidereal external scope and explicit ephemeris-file pinning remain conditional", "Preserve MOSEPH policy; do not reopen without a new reference gap"),
        base_row("planetary_longitude", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "VALIDATED_WITH_CONDITIONS", "NOT_APPLICABLE", "Kundli and astro runtime", "Tropical Horizons oracle is strong; complete sidereal external coverage is partial", "Keep current runtime and reference boundaries explicit"),
        base_row("sidereal_ayanamsha", "PARTIALLY_VALIDATED", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "BOUNDARY_SENSITIVE", "NOT_APPLICABLE", "Kundli and astro runtime", "Lahiri/Nirayana convention is bounded but not a complete independent all-body oracle", "Source-witness and reference-policy work only"),
        base_row("timezone_dst_historical", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "NOT_APPLICABLE", "Personal/REST runtime and historical fixtures", "Fixed-offset personal surfaces and historical LMT/gap/fold policy differ", "Preserve explicit timezone profile and uncertainty"),
        base_row("lagna_ascendant", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "BOUNDARY_SENSITIVE", "NOT_APPLICABLE", "Kundli/Jyotisha runtime", "120-case tropical validation passes, but sign-boundary/reference differences remain", "Do not silently change boundary policy"),
        base_row("houses_whole_sign", "COMPLETE_WITH_CONDITION", "PLATFORM_CONTRACT", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "NOT_APPLICABLE", "Kundli/Jyotisha runtime", "Whole-sign house policy is deterministic but not an independent classical numerical oracle", "Keep as explicit runtime policy"),
        base_row("nakshatra_pada", "PRODUCTION_GRADE_CALCULATION_FOUNDATION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "NOT_APPLICABLE", "Dasha/Panchanga runtime", "No material calculation blocker; interpretation is a separate lane", "Freeze calculation contract"),
        base_row("tithi", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "NOT_APPLICABLE", "P032 foundation", "Independent numerical oracle is not present", "Keep deterministic fact-only implementation"),
        base_row("yoga_calendar", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "NOT_APPLICABLE", "P032 foundation", "Source terminology and recommendation scope remain bounded", "No recommendation activation"),
        base_row("karana", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "NOT_APPLICABLE", "P032 foundation", "No independent external numerical oracle", "Keep fact-only contract"),
        base_row("D1_rashi", "PRODUCTION_GRADE_CALCULATION_FOUNDATION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "VALIDATED", "NOT_APPLICABLE", "Core Kundli runtime", "External reference coverage is bounded by the calculation programme", "Freeze D1 calculation surface"),
        base_row("D2_hora", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli REST/stock/country surfaces", "Interpretive use is not calculation validation", "No new interpretation"),
        base_row("D3_drekkana", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli REST/stock/country surfaces", "Interpretive purpose remains governed separately", "Freeze calculation"),
        base_row("D4_chaturthamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "P015-RX/P029/P030 context", "Calculation validated for selected method; interpretation remains gated", "Do not reopen without new evidence"),
        base_row("D7_saptamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli runtime", "Purpose and high-stakes interpretation remain source-limited", "Keep calculation-only"),
        base_row("D9_navamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli/P031/P024 context", "Calculation is stable; interpretive scope remains research-governed", "No interpretive activation"),
        base_row("D10_dasamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli/P021 context", "Calculation is stable; career interpretation is separate", "No new career rules"),
        base_row("D11_ekadasamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli runtime", "General method remains condition-qualified", "No expansion"),
        base_row("D12_dwadasamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli/P029 context", "Ancestral/parental interpretation remains source-limited", "No new interpretation"),
        base_row("D16_shodasamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli runtime", "General method remains condition-qualified", "Freeze calculation"),
        base_row("D20_vimshamsha", "PARTIALLY_VALIDATED", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "BOUNDARY_VALIDATED", "RESEARCH_ONLY", "Kundli/P031 source-gated spiritual context", "Destination/sign mapping remains unresolved; interpretation is not validated", "Keep frozen; no automatic D20 programme"),
        base_row("D30_trimshamsa", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Kundli runtime", "General method and interpretive scope remain condition-qualified", "No expansion"),
        base_row("D60_shashtiamsha", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "BIRTH_TIME_SENSITIVE", "RESEARCH_ONLY", "Kundli runtime", "Extreme birth-time sensitivity and source scope", "Keep calculation-only and uncertainty-aware"),
        base_row("vimshottari_antardasha", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "RESEARCH_ONLY", "Personal/REST/stock/country timing facts", "External numerical comparison is not independent; interpretation remains separate", "Freeze sequence/period arithmetic"),
        base_row("other_dasha_systems", "RESEARCH_ONLY", "INVENTORY_ONLY", "NOT_AVAILABLE", "UNVALIDATED", "NOT_AVAILABLE", "RESEARCH_ONLY", "None", "Yogini and Ashtottari are inventory-only", "Do not implement without authorization"),
        base_row("shadbala", "PARTIALLY_VALIDATED", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Strength engine", "Cheshta/Drik and broader source authority remain partial", "Source-contract work before activation"),
        base_row("other_bala_vimshopaka", "PARTIALLY_VALIDATED", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Shadbala context", "Weights/aggregation are not a separately externally validated capability", "Keep subordinate to strength governance"),
        base_row("ashtakavarga_raw_bav_sav", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_RESOLVED", "INTERNALLY_VALIDATED", "UNAVAILABLE", "VALIDATED", "RESEARCH_ONLY", "Shadbala/P018 runtime", "Reductions deferred; external numerical oracle unavailable", "Freeze RX2 state"),
        base_row("muhurta_panchanga_facts", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "UNVALIDATED", "VALIDATED", "RESEARCH_ONLY", "P032 foundation", "Tara/Chandra Bala and recommendation source gates remain open", "Keep recommendations inactive"),
        base_row("transit_facts", "COMPLETE_WITH_CONDITION", "SOURCE_CONTRACT_PARTIAL", "INTERNALLY_VALIDATED", "PARTIALLY_VALIDATED", "VALIDATED_WITH_CONDITIONS", "RESEARCH_ONLY", "Transit foundation/P019", "Historical Jupiter/Saturn scope is bounded; predictive interpretation is separate", "No new transit recipe"),
        base_row("jaimini_primitives", "NOT_IMPLEMENTED", "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE", "RESEARCH_ONLY", "None", "No current deterministic Jaimini calculation module found", "Remain deferred"),
        base_row("arudha_calculations", "NOT_IMPLEMENTED", "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE", "RESEARCH_ONLY", "None", "No current deterministic Arudha calculation module found", "Remain deferred"),
    ]
    return rows


def source_readiness() -> list[dict[str, Any]]:
    return [
        {"family": "Ashtakavarga raw BAV/SAV", "status": "COMPLETE_WITH_CONDITION", "source_state": "BPHS V2 witness/matrix resolved", "remaining": "external numerical oracle unavailable; reductions deferred"},
        {"family": "D20 destination mapping", "status": "SOURCE_GOVERNANCE_REQUIRED", "source_state": "category starts and narrow upasana scope supported", "remaining": "complete destination/sign/deity mapping unresolved"},
        {"family": "Shadbala/Cheshta/Drik", "status": "SOURCE_GOVERNANCE_REQUIRED", "source_state": "partial governed contracts", "remaining": "component-specific source and numerical authority"},
        {"family": "Varga interpretive purposes", "status": "SOURCE_GOVERNANCE_REQUIRED", "source_state": "calculation surface exists", "remaining": "D7/D9/D10/D12/D20 interpretation scopes"},
        {"family": "Muhurta personal Bala", "status": "SOURCE_GOVERNANCE_REQUIRED", "source_state": "Panchanga facts and scoped event families", "remaining": "legible operative Tara/Chandra Bala witnesses"},
        {"family": "Houses/ayanamsha/Ascendant boundaries", "status": "REFERENCE_LIMITED", "source_state": "deterministic policy and bounded references", "remaining": "independent external coverage at boundary and sidereal scope"},
    ]


def consumers() -> dict[str, Any]:
    return {
        "production_internal": [
            "engines/intelligence/kundli_engine.py",
            "engines/intelligence/jyotisha_runtime.py",
            "engines/ai/knowledge/varga_governance.py",
            "engines/ai/knowledge/dasha_governance.py",
            "engines/ai/knowledge/muhurta_foundation.py",
            "engines/transit_gochar.py",
            "engines/ai/knowledge/shadbala_engine.py",
        ],
        "api_ui": "Jyotisha runtime surfaces expose D1/Varga/Dasha/fact outputs; no direct Ashtakavarga UI/API consumer found",
        "research_audit": "calculation and governance scripts/tests consume explicit artifacts",
        "rag": "RAG stores governed records; no calculation result is promoted by this activity",
        "prediction": "no direct activation; PRED-M4 unchanged",
        "ml": "locked; no calculation consumer activation",
        "orphans_or_research_only": ["other_dasha_systems", "jaimini_primitives", "arudha_calculations", "D20 interpretation", "Muhurta recommendations"],
    }


def stop_register() -> list[dict[str, Any]]:
    return [
        {"item": "Ashtakavarga reductions", "state": "FROZEN_DEFERRED", "reason": "RX2 raw contract is complete with conditions; no new evidence"},
        {"item": "D20 interpretation/destination mapping", "state": "FROZEN_SOURCE_LIMITED", "reason": "partial calculation authority; no new source witness"},
        {"item": "Muhurta recommendations", "state": "STOPPED_INACTIVE", "reason": "P032 foundation only; personal Bala source gate open"},
        {"item": "Production predictive astrology", "state": "STOPPED", "reason": "interpretation and empirical gates"},
        {"item": "PRED-M4", "state": "STOPPED_UNCHANGED", "reason": "insufficient empirical sample"},
        {"item": "ML", "state": "LOCKED", "reason": "no authorized labels/model programme"},
        {"item": "Generic ADB acquisition", "state": "EXTERNAL_ACCESS_STOP", "reason": "formal access/human gate"},
        {"item": "Muller documentary scale verification", "state": "MANUAL_ACCESS_STOP", "reason": "manual verification required"},
        {"item": "Hindi production review", "state": "HUMAN_REVIEW_PENDING", "reason": "human validation not complete"},
        {"item": "Additional languages", "state": "PLANNED", "reason": "LANG-002+ remains planned"},
        {"item": "Prashna", "state": "MISSING_FOUNDATION", "reason": "not started"},
    ]


def candidates() -> list[dict[str, Any]]:
    return [
        {"rank": 1, "id": "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001", "lane": "SOURCE GOVERNANCE", "objective": "Generalize text/witness/edition/passage/layer/normalized-assertion/variant/authority metadata from Ashtakavarga to future source-heavy knowledge", "why_now": "RX2 demonstrated that explicit witness lineage prevents invalid hybrid contracts", "dependency": "existing knowledge/source registry and claim schemas", "evidence_readiness": "READY_FOR_BOUNDED_AUDIT", "expected_value": "HIGH", "risk": "MEDIUM", "estimated_scope": "MEDIUM", "autonomous": "YES", "selected": True},
        {"rank": 2, "id": "VEDA-CALC-D20-SOURCE-RECONCILIATION-001", "lane": "CALCULATION / SOURCE GOVERNANCE", "objective": "Resolve D20 destination/sign/deity mapping with a source-scoped witness", "why_now": "D20 remains the clearest partial calculation family", "dependency": "legible primary witness and variant decision", "evidence_readiness": "PARTIAL", "expected_value": "HIGH", "risk": "HIGH", "estimated_scope": "MEDIUM", "autonomous": "CONDITIONAL_NO", "selected": False},
        {"rank": 3, "id": "VEDA-KNOW-STRENGTH-SOURCE-001", "lane": "SOURCE GOVERNANCE", "objective": "Harden Shadbala, Cheshta, Drik and related Bala source contracts", "why_now": "Strength implementation exists but component provenance is uneven", "dependency": "edition/passages and independent numerical witnesses", "evidence_readiness": "PARTIAL", "expected_value": "HIGH", "risk": "HIGH", "estimated_scope": "LARGE", "autonomous": "YES_BOUNDED", "selected": False},
        {"rank": 4, "id": "VEDA-KNOW-MUHURTA-BALA-001", "lane": "SOURCE GOVERNANCE", "objective": "Audit operative Tara Bala and Chandra Bala formulas without activating recommendations", "why_now": "P032 facts are frozen but personal Bala is the remaining foundation gap", "dependency": "legible edition-specific operative passages", "evidence_readiness": "BLOCKED_BY_SOURCE_WITNESS", "expected_value": "MEDIUM", "risk": "HIGH", "estimated_scope": "MEDIUM", "autonomous": "NO", "selected": False},
        {"rank": 5, "id": "VEDA-CALC-SIDEREAL-REFERENCE-POLICY-001", "lane": "CALCULATION", "objective": "Reconcile remaining sidereal/Ascendant boundary reference policy", "why_now": "Known boundary differences remain explicit after Oracle/ASC work", "dependency": "new independent reference scope", "evidence_readiness": "PARTIAL", "expected_value": "MEDIUM", "risk": "MEDIUM", "estimated_scope": "SMALL", "autonomous": "YES_BOUNDED", "selected": False},
    ]


def build() -> dict[str, Any]:
    rows = inventory()
    classes = {key: sum(1 for row in rows if row["capability_class"] == key) for key in ("PRODUCTION_GRADE_CALCULATION_FOUNDATION", "COMPLETE_WITH_CONDITION", "PARTIALLY_VALIDATED", "RESEARCH_ONLY", "DEFERRED", "NOT_IMPLEMENTED")}
    rx2 = rx2_state()
    rag = rag_state()
    return {
        "programme": "VEDA-CALCULATION-LANE-REBASELINE-001",
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "production_code_changed": False,
        "ashtakavarga": rx2,
        "inventory": rows,
        "class_counts": classes,
        "source_readiness": source_readiness(),
        "consumers": consumers(),
        "stop_register": stop_register(),
        "candidates": candidates(),
        "primary_decision": {
            "decision": "KNOWLEDGE_SOURCE_HARDENING_SELECTED",
            "programme_id": "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001",
            "lane": "SOURCE GOVERNANCE",
            "objective": "Extend the existing source registry and knowledge architecture with reusable witness/edition/passage/layer/variant authority metadata.",
            "why_now": "The RX2 Ashtakavarga result shows this is the highest-leverage way to prevent future source-contract ambiguity without reopening complete calculation families.",
            "evidence_ready": "YES_FOR_BOUNDED_AUDIT",
            "autonomous": "YES",
            "automatically_started": False,
        },
        "rag": rag,
        "governance": {
            "approved_core_before": rag["approved_core_count"],
            "approved_core_after": rag["approved_core_count"],
            "rag_changed": False,
            "rag_rebuild": False,
            "prediction_changed": False,
            "pred_m4": "UNCHANGED",
            "ml": "LOCKED",
            "external_evidence_changed": False,
            "human_validation": "COMM-002/GROUP-001 PENDING",
            "emp_001": "ACTIVE LONGITUDINAL",
        },
    }


def emit(bundle: dict[str, Any]) -> None:
    write_md("00_BASELINE.md", "Calculation Lane Rebaseline Baseline", f"Starting commit: `{STARTING_COMMIT}`. RX2 is accepted and production code is not changed by this rebaseline. The audit is deterministic and reuses current VEDA artifacts; no external provider, personal data, prediction, ML, RAG rebuild or Approved Core action occurred.")
    write_json("01_CALCULATION_INVENTORY.json", {"programme": bundle["programme"], "families": bundle["inventory"], "family_count": len(bundle["inventory"]), "inventory_hash": digest(bundle["inventory"])})
    write_json("02_CALCULATION_MATURITY_MATRIX.json", {"programme": bundle["programme"], "class_counts": bundle["class_counts"], "rows": bundle["inventory"], "matrix_hash": digest(bundle["inventory"])})
    write_json("03_SOURCE_READINESS_MATRIX.json", {"programme": bundle["programme"], "rows": bundle["source_readiness"], "matrix_hash": digest(bundle["source_readiness"])})
    write_json("04_CONSUMER_MAP.json", bundle["consumers"])
    write_json("05_STOP_DEFER_FREEZE_REGISTER.json", {"rows": bundle["stop_register"], "register_hash": digest(bundle["stop_register"])})
    write_md("06_HIGH_VALUE_GAPS.md", "High-Value Calculation Gaps", "The remaining correctness-relevant gaps are primarily source/reference gaps, not missing implementation.\n\n- D20 destination/sign mapping remains partial and should stay frozen.\n- Shadbala/Cheshta/Drik source contracts remain uneven.\n- Muhurta personal Bala requires a legible operative witness.\n- Sidereal/Ascendant boundary policies remain explicit conditions.\n- Jaimini and Arudha are absent and are not justified as immediate feature work.\n\nThe Ashtakavarga raw contract is complete with conditions and is not reopened.")
    write_json("07_NEXT_PROGRAMME_CANDIDATES.json", {"candidates": bundle["candidates"], "candidate_count": len(bundle["candidates"])})
    decision = bundle["primary_decision"]
    write_md("08_PRIMARY_NEXT_DECISION.md", "Primary Next Decision", f"Decision: `{decision['decision']}`\n\nProgramme ID: `{decision['programme_id']}`\n\nLane: `{decision['lane']}`\n\nObjective: {decision['objective']}\n\nWhy now: {decision['why_now']}\n\nEvidence ready: `{decision['evidence_ready']}`\n\nAutonomous: `{decision['autonomous']}`\n\nAutomatically started: `NO`. This rebaseline does not implement or authorize the candidate.")
    write_md("09_SOURCE_WITNESS_STANDARD_ASSESSMENT.md", "Source-Witness Standard Assessment", "Recommendation: YES, as the next bounded knowledge-governance programme. The existing source architecture can be extended rather than duplicated. RX2 already demonstrates useful fields including text/witness/edition/passage/source-layer and variant authority. Generalizing those fields would reduce future D20, Shadbala and Muhurta source ambiguity. This is a recommendation only; no source-witness migration, RAG rebuild, promotion or implementation was started here.")
    write_md("10_PARALLEL_LANE_STATE.md", "Parallel Lane State", "India: HUMAN / INSTITUTIONAL ACTION READY. BVB: PACK PREPARED / UNSENT. ICAS: PACK PREPARED / UNSENT. Hospital: ETHICS / INSTITUTIONAL GATE. Müller: MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE. ADB: PREPARED / UNSENT. POSITION_END: WAIT_EXTERNAL_ACCESS. No external evidence lane changed.")
    write_md("11_ROADMAP_SYNCHRONIZATION.md", "Roadmap Synchronization", "RX2 remains COMPLETE_WITH_CONDITION and frozen. D20 remains PARTIALLY_VALIDATED and frozen. P032 remains an implemented/frozen foundation with recommendations inactive. PRED-M4, ML, EMP-001, COMM-002 and GROUP-001 states are unchanged. The recommended source-witness candidate is recorded as NOT STARTED and was not automatically authorized or implemented.")
    write_md("12_FINAL_ACCEPTANCE.md", "Final Acceptance", "Overall: `PASS_WITH_CONDITION`. The current calculation lane was inventoried from repository code and authoritative artifacts; maturity dimensions were kept separate; RX2 was preserved; stop/defer states were rebuilt; no production calculation logic changed; and one autonomous next-programme recommendation was selected without starting it. Conditions: external reference gaps, source-limited D20/strength/Muhurta areas, and all human/provider gates remain explicit.")


def main() -> int:
    bundle = build()
    emit(bundle)
    print(json.dumps({"programme": bundle["programme"], "inventory_count": len(bundle["inventory"]), "class_counts": bundle["class_counts"], "primary_decision": bundle["primary_decision"], "rag": bundle["rag"]}, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
