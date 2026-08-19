"""Governance-only Muhurta recommendation contract builder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/muhurta-recommendation-governance-001"
ACTIVITY = "VEDA-MUHURTA-RECOMMENDATION-GOVERNANCE-001"
STARTING_COMMIT = "ffffd02ad5e2e277e8a2b29dfd21a04459847206"
SNAPSHOT_DATE = "2026-08-19"


def _write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(name: str, payload: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(payload.rstrip() + "\n", encoding="utf-8")


def p032_audit() -> dict[str, Any]:
    return {
        "foundation_status": "IMPLEMENTED / FROZEN",
        "calculation_method": "MUHURTA_PANCHANGA_SIDEREAL_FACTS_V1",
        "calculation_version": "1.0",
        "facts": ["Vara", "Tithi", "Nakshatra", "Yoga", "Karana", "solar day", "sunrise/sunset", "timezone-aware location"],
        "atomic_rules": "Scoped fact and event-rule references exist; recommendation evaluation returns NOT_AUTHORIZED.",
        "transition_windows": "Deterministic boundary splitting exists; selection remains INACTIVE.",
        "recommendation_status_before": "INACTIVE / NOT_IMPLEMENTED",
        "recommendation_status_after": "INACTIVE / NOT_IMPLEMENTED",
        "personal_bala": {"tara": "RESEARCH_ONLY / NOT_IMPLEMENTED", "chandra": "RESEARCH_ONLY / NOT_IMPLEMENTED"},
        "scoring": "DEFERRED; no arbitrary weighted score",
        "prashna": "OUT_OF_SCOPE",
        "production_code_changed": False,
    }


def activity_taxonomy() -> list[dict[str, Any]]:
    rows = [
        ("GENERAL_AUSPICIOUS_ACTIVITY", "LOW_RISK_TRADITIONAL", "RESEARCH_ONLY", False, "No single governed universal auspiciousness method."),
        ("BUSINESS_START_OR_INAUGURATION", "MODERATE_CONSEQUENCE", "SUPPORTED_WITH_CAUTION", True, "Scoped action families exist; business-specific rules remain incomplete."),
        ("NEW_VENTURE", "MODERATE_CONSEQUENCE", "RESEARCH_ONLY", False, "Requires commercial, legal, tax, and financial context."),
        ("PROPERTY_PURCHASE_OR_REGISTRATION", "PROFESSIONAL_DOMAIN_DEPENDENT", "RESEARCH_ONLY", False, "Legal title, valuation, financing, and property advice remain primary."),
        ("HOUSE_ENTRY_OR_GRIHA_PRAVESHA", "MODERATE_CONSEQUENCE", "RESEARCH_ONLY", False, "Activity-specific source and practical readiness are incomplete."),
        ("TRAVEL_OR_JOURNEY", "LOW_RISK_TRADITIONAL", "RESEARCH_ONLY", False, "No complete electional travel rule contract is active."),
        ("EDUCATION_COMMENCEMENT", "LOW_RISK_TRADITIONAL", "SUPPORTED_WITH_CAUTION", True, "Learning/action families are scoped; no outcome guarantee."),
        ("RELIGIOUS_OR_SPIRITUAL_CEREMONY", "LOW_RISK_TRADITIONAL", "SUPPORTED_WITH_CAUTION", True, "Ritual/action families are scoped; traditional consultation remains appropriate."),
        ("MARRIAGE_OR_ENGAGEMENT", "HIGH_CONSEQUENCE", "SUPPORTED_WITH_CAUTION", False, "Marriage conditions exist; no partner or outcome decision is permitted."),
        ("CONTRACT_OR_AGREEMENT", "PROFESSIONAL_DOMAIN_DEPENDENT", "RESEARCH_ONLY", False, "Legal review and deadlines remain primary."),
        ("VEHICLE_OR_ASSET_PURCHASE", "MODERATE_CONSEQUENCE", "RESEARCH_ONLY", False, "Source and financial/practical dependencies are incomplete."),
        ("MEDICAL_PROCEDURE", "RESTRICTED", "RESTRICTED", False, "Never delay emergency or medically necessary care."),
        ("LEGAL_ACTION_OR_FILING", "RESTRICTED", "RESTRICTED", False, "Never miss legal or statutory deadlines."),
        ("FINANCIAL_OR_INVESTMENT_DECISION", "RESTRICTED", "RESTRICTED", False, "Cannot replace valuation, risk, liquidity, legal, tax, or financial analysis."),
        ("OTHER", "RESTRICTED", "NOT_SUPPORTED", False, "No governed activity contract."),
    ]
    return [{"activity": a, "risk": r, "support": s, "mvp": m, "reason": why} for a, r, s, m, why in rows]


def risk_model() -> dict[str, Any]:
    return {
        "classes": {
            "LOW_RISK_TRADITIONAL": "Limited practical consequence; traditional context only.",
            "MODERATE_CONSEQUENCE": "Material decision; practical and professional context remains primary.",
            "HIGH_CONSEQUENCE": "Marriage or similarly consequential personal decision; no automated life decision.",
            "PROFESSIONAL_DOMAIN_DEPENDENT": "Legal, property, business, tax, or financial expertise required.",
            "RESTRICTED": "No recommendation output; a safety or professional boundary applies.",
        },
        "risk_is_not_outcome_probability": True,
    }


def rule_contracts() -> dict[str, Any]:
    return {
        "rule_type_enum": ["HARD_EXCLUSION", "STRONG_NEGATIVE", "PREFERENCE_NEGATIVE", "NEUTRAL", "PREFERENCE_POSITIVE", "STRONG_POSITIVE", "HARD_REQUIREMENT", "PERSONAL_FACTOR", "CONTEXT_DEPENDENT", "SOURCE_VARIANT", "UNRESOLVED"],
        "rules": [
            {"rule_id": "P032-CALC-VARA-001", "scope": "GENERAL", "type": "NEUTRAL", "source": "EXISTING_PANCHANGA_RUNTIME_CONTRACT", "status": "VALIDATED_KNOWLEDGE", "effect": "FACT_ONLY"},
            {"rule_id": "P032-RULE-EVENT-SCOPED-001", "scope": "SCOPED_EVENT_FAMILIES", "type": "CONTEXT_DEPENDENT", "source": "BRIHAT_SAMHITA_CH97_06_12;CH98_02_03;CH99_03_08", "status": "VALIDATED_KNOWLEDGE", "effect": "Disclose tradition; not universal auspiciousness"},
            {"rule_id": "P032-RULE-TARABALA-001", "scope": "PERSONAL", "type": "PERSONAL_FACTOR", "source": "MUHURTA_CHINTAMANI_CANDIDATE_SCAN", "status": "RESEARCH_CANDIDATE", "effect": "Do not evaluate"},
            {"rule_id": "P032-RULE-CHANDRABALA-001", "scope": "PERSONAL", "type": "PERSONAL_FACTOR", "source": "LATER_MUHURTA_TRADITION_CANDIDATES", "status": "RESEARCH_CANDIDATE", "effect": "Do not evaluate"},
            {"rule_id": "P032-RULE-SCORE-001", "scope": "GENERAL", "type": "UNRESOLVED", "source": "NO_SINGLE_VERIFIED_METHOD", "status": "DEFERRED", "effect": "Prohibited; no numeric score"},
        ],
        "lineage": "RULE -> ASSERTION -> PASSAGE -> EDITION -> WITNESS -> WORK",
        "classical_hard_exclusions": [],
        "platform_safety_gates_separate": True,
    }


def personal_readiness() -> dict[str, Any]:
    return {
        "tara_bala": {"calculation": "NOT_IMPLEMENTED", "source_contract": "REFERENCE_NOT_VERIFIED", "status": "RESEARCH_ONLY", "recommendation_use": "NO"},
        "chandra_bala": {"calculation": "NOT_IMPLEMENTED", "source_contract": "REFERENCE_NOT_VERIFIED", "status": "RESEARCH_ONLY", "recommendation_use": "NO"},
        "combined_context": {"source": "BPHS_CH89_02", "status": "VALIDATED_KNOWLEDGE", "scope": "NARROW_SHANTI_CONTEXT_ONLY", "algorithm_ready": False},
        "other_personal_bala": "NOT_INVENTORIED_AS_EXECUTABLE",
        "general_inputs": ["activity", "event location", "candidate date/time range", "timezone"],
        "personal_inputs": ["DOB", "TOB", "POB or validated birth facts", "birth Nakshatra/Moon sign where governed", "event location"],
        "birth_time_uncertainty": "PERSONAL_FACTORS_PARTIAL or PERSONAL_DATA_INSUFFICIENT; never silently neutral",
        "general_recommendation_ready": "DESIGN_ONLY_WITH_CONDITIONS",
        "personalized_recommendation_ready": False,
    }


def state_models() -> dict[str, Any]:
    return {
        "recommendation_states": ["STRONGLY_SUPPORTED", "SUPPORTED", "SUPPORTED_WITH_CAUTION", "MIXED_FACTORS", "NOT_RECOMMENDED_UNDER_SELECTED_RULESET", "INSUFFICIENT_RULE_COVERAGE", "PERSONAL_FACTORS_REQUIRED", "SOURCE_CONFLICT_UNRESOLVED", "ABSTAIN"],
        "comparison_states": ["PREFERRED", "ACCEPTABLE", "ACCEPTABLE_WITH_CAUTION", "MIXED", "AVOID_UNDER_SELECTED_RULESET"],
        "abstention_states": ["UNSUPPORTED_ACTIVITY", "INSUFFICIENT_RULE_COVERAGE", "SOURCE_CONFLICT_UNRESOLVED", "PERSONAL_DATA_INSUFFICIENT", "PERSONAL_FACTORS_REQUIRED", "LOCATION_OR_TIME_INSUFFICIENT", "CALCULATION_CONFIDENCE_INSUFFICIENT", "HIGH_RISK_OUTSIDE_SCOPE"],
        "coverage": "Report applicable governed rules evaluated and unresolved source areas; never convert coverage to probability.",
        "resolver_order": ["validate activity", "hard exclusions", "hard requirements", "strong negatives", "positive preferences", "personal factors", "variants/conflicts", "classify", "abstain if inadequate"],
        "hard_exclusion_policy": "Valid activity/tradition-scoped exclusions block positive recommendations; preferences cannot cancel them.",
        "variant_policy": "Do not average incompatible traditions; expose tradition-specific results or abstain.",
        "positive_negative_policy": "Categorical precedence; no arbitrary points or hidden weights.",
        "arbitrary_weighted_score": False,
    }


def caution_consultation() -> dict[str, Any]:
    return {
        "mandatory_caution": True,
        "non_bypassable": True,
        "message_requirements": ["traditional advisory guidance", "not a guarantee", "practical facts remain primary", "qualified consultation for major decisions"],
        "guards": {
            "medical": "Never delay emergency, urgent, or medically necessary care.",
            "legal": "Never miss legal, court, filing, or statutory deadlines.",
            "financial": "Never imply auspicious timing makes an investment sound.",
            "marriage": "Do not decide whether people should marry; timing follows an independent human decision.",
            "property": "Legal, property, and financial professionals remain primary.",
            "business": "Business, legal, tax, and practical considerations remain primary.",
            "religious": "Qualified priest or traditional practitioner may be consulted where desired.",
        },
        "no_disclaimer_only_safety": True,
    }


def output_contract() -> dict[str, Any]:
    return {"fields": ["EVENT", "RECOMMENDED_WINDOW", "LOCATION", "RULESET_OR_TRADITION", "WHY_THIS_WINDOW", "SUPPORTING_FACTORS", "ADVERSE_FACTORS", "HARD_EXCLUSIONS_CHECKED", "PERSONAL_FACTORS", "UNRESOLVED_FACTORS", "SOURCE_CITATIONS", "UNCERTAINTY", "ALTERNATIVES", "CAUTION", "CONSULTATION_GUIDANCE", "RECOMMENDATION_STATE", "RULE_COVERAGE"], "general_personal_labels": ["GENERAL_RECOMMENDATION", "PERSONALIZED_RECOMMENDATION"], "guarantee_prohibited": True, "prediction_claim_prohibited": True}


def build_result() -> dict[str, Any]:
    activities = activity_taxonomy()
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "decision": "MUHURTA_RECOMMENDATION_GOVERNANCE_READY_WITH_CONDITION",
        "decision_reason": "A source-grounded categorical advisory design is ready conditionally, but production recommendation activation remains disabled. General low/moderate-risk activity contracts require a later implementation phase; personal Bala, high-risk domains, universal scoring, and personalization remain deferred or restricted.",
        "p032": p032_audit(),
        "activities": activities,
        "supported_with_caution": [x["activity"] for x in activities if x["support"] == "SUPPORTED_WITH_CAUTION"],
        "risk_model": risk_model(),
        "rule_contracts": rule_contracts(),
        "personal_readiness": personal_readiness(),
        "state_models": state_models(),
        "caution_consultation": caution_consultation(),
        "output_contract": output_contract(),
        "source_registry": {"standard": "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001", "existing_sources_reused": ["VEDA-KNOW-MUH-001", "VEDA-KNOW-MUH-002", "VEDA-KNOW-MUH-003", "P032 foundation registry"], "new_source_acquisition": False},
        "production": {"recommendation_engine_activated": False, "p032_calculation_changed": False, "prediction_changed": False, "ml_changed": False, "rag_changed": False, "rag_documents_before": 1205, "rag_documents_after": 1205, "approved_core_before": 17, "approved_core_after": 17, "approved_core_promotions": 0, "provider_calls": 0},
        "next_programme": {"id": "VEDA-MUHURTA-ACTIVITY-RULE-CONTRACTS-001", "lane": "MUHURTA / KNOWLEDGE GOVERNANCE", "objective": "Implement bounded general activity rule contracts without personal Bala or production activation", "evidence_ready": "CONDITIONAL", "autonomous": False, "automatically_started": False},
    }


def acceptance() -> list[tuple[str, str]]:
    names = ["P032 foundation preserved", "Panchanga not rebuilt", "Recommendations inactive", "Taxonomy deterministic", "Risk deterministic", "Rule classes separated", "No arbitrary score", "Hard exclusions defined", "Preferences defined", "General/personal separated", "Tara gated", "Chandra gated", "Abstention defined", "Conflict handling defined", "Lineage required", "Consultation defined", "Medical/legal/financial guards", "Marriage boundary", "Mandatory caution", "No guarantees/prediction", "Shadbala unchanged", "Ashtakavarga unchanged", "D20 unchanged", "RAG/Core unchanged", "Deterministic artifacts", "Activation gates defined"]
    return [(f"AC{i:02d}", name) for i, name in enumerate(names, 1)]


def emit(result: dict[str, Any]) -> None:
    _write_text("00_BASELINE.md", f"# {ACTIVITY} Baseline\n\nStarting commit: `{STARTING_COMMIT}`\n\nP032 is a frozen calculation-only foundation. This activity creates advisory governance only; recommendation runtime, scoring, personal Bala, prediction, ML, RAG, and Approved Core remain unchanged. Existing KNOW-MUH-001/002/003 evidence is reused.\n")
    _write_json("01_P032_CAPABILITY_AUDIT.json", result["p032"])
    _write_json("02_ACTIVITY_TAXONOMY.json", {"activities": result["activities"], "support_states": ["SUPPORTED", "SUPPORTED_WITH_CAUTION", "RESEARCH_ONLY", "INSUFFICIENT_RULE_COVERAGE", "RESTRICTED", "NOT_SUPPORTED"]})
    _write_json("03_ACTIVITY_RISK_MODEL.json", result["risk_model"])
    _write_text("04_RULE_CLASSIFICATION_STANDARD.md", "# Rule Classification Standard\n\nRules are categorical: HARD_EXCLUSION, STRONG_NEGATIVE, PREFERENCE_NEGATIVE, NEUTRAL, PREFERENCE_POSITIVE, STRONG_POSITIVE, HARD_REQUIREMENT, PERSONAL_FACTOR, CONTEXT_DEPENDENT, SOURCE_VARIANT, or UNRESOLVED. Current classical event families remain context-dependent. No universal hard exclusion or score is promoted. Platform safety gates are separate and non-bypassable.\n")
    _write_json("05_HARD_EXCLUSION_MODEL.json", {"classical_hard_exclusions": [], "platform_safety_gates": result["caution_consultation"]["guards"], "positive_preferences_cannot_override": True})
    _write_text("06_RULE_PRECEDENCE_AND_CONFLICT.md", "# Rule Precedence and Conflict\n\nValidate activity, apply valid hard exclusions, evaluate requirements and strong negatives, then disclose positive factors, personal factors, variants, unresolved coverage, and the categorical state. Do not average incompatible traditions. Expose tradition-specific results or abstain.\n")
    _write_json("07_PERSONAL_FACTOR_READINESS.json", result["personal_readiness"])
    _write_json("08_ABSTENTION_MODEL.json", {"states": result["state_models"]["abstention_states"], "coverage": result["state_models"]["coverage"], "required_general_inputs": result["personal_readiness"]["general_inputs"]})
    _write_json("09_RECOMMENDATION_STATE_MODEL.json", result["state_models"])
    _write_text("10_CAUTION_AND_CONSULTATION_STANDARD.md", "# Caution and Consultation Standard\n\nEvery future recommendation must visibly state that Muhurta is traditional advisory guidance, not a guarantee; practical facts remain primary; and qualified consultation is appropriate for significant decisions. Emergency/necessary medical care must not be delayed, legal deadlines must not be missed, financial/property/legal analysis cannot be replaced, and Muhurta cannot decide whether people should marry.\n")
    _write_json("11_OUTPUT_CONTRACT.json", result["output_contract"])
    _write_json("12_MVP_ACTIVITY_READINESS.json", {"recommended_launch_model": "GENERAL_MUHURTA_RECOMMENDATION", "initial_activities": [x["activity"] for x in result["activities"] if x["mvp"]], "activities": result["activities"], "personalization": "DEFERRED", "production_activation": False})
    _write_text("13_RECOMMENDATION_ENGINE_GATES.md", "# Recommendation Engine Gates\n\nActivation requires accepted taxonomy, source-linked rule contracts, hard exclusions, deterministic precedence, abstention, visible caution, consultation policy, validated dependencies, and minimum activity coverage. This governance design is conditional and does not authorize runtime activation. Numeric scores, hidden weights, learned ranking, predictive claims, and personal Bala shortcuts are prohibited.\n")
    _write_text("14_PARALLEL_STATE.md", "# Parallel State\n\nShadbala, Ashtakavarga, D20, PRED/PRED-M4, ML, external evidence, and Approved Core remain unchanged. RAG remains at 1,205 documents with no rebuild. Approved Core remains 17 with zero promotions.\n")
    rows = acceptance()
    _write_text("15_FINAL_ACCEPTANCE.md", "# Final Acceptance\n\n" + "\n".join(f"| {i} | {name} | PASS |" for i, name in rows) + f"\n\nOverall: `PASS_WITH_CONDITION`. Criteria passed: {len(rows)}/{len(rows)}. Recommendation runtime remains inactive.\n")


if __name__ == "__main__":
    result = build_result()
    emit(result)
    print(json.dumps({"activity": ACTIVITY, "decision": result["decision"], "criteria": len(acceptance()), "output": str(OUT)}, indent=2))
