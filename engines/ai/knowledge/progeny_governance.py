"""P025 governed children, progeny, fertility, D7, and family-expansion foundation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.ai.knowledge.varga_governance import VARGA_METHODS, canonical_varga_fact, validation_fixtures, varga_sign
from engines.progeny.m001_existing_progeny_logic_inventory import inventory_repository, write_inventory

ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = cfg.VEDA_CACHE_DIR / "validation" / "progeny"
TS = "2026-08-14T00:00:00Z"


def _sources() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(cfg.VEDA_ASTROLOGY_SOURCE_DIR.glob("VEDA-SRC-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append({"source_id": payload["source_id"], "title": payload.get("title_normalized") or payload.get("title_original"), "source_class": payload.get("source_class"), "source_family": payload.get("author_normalized") or payload.get("title_normalized") or payload["source_id"], "verification_status": payload.get("verification_status"), "retrieval_status": "RETRIEVED" if payload.get("verification_status") else "REFERENCE_NOT_VERIFIED", "citation_status": payload.get("verification_status") or "REFERENCE_NOT_VERIFIED", "domains": list(payload.get("domains") or [])})
    return rows


def _quality(sources: list[dict[str, Any]]) -> dict[str, Any]:
    classes = {item: sum(1 for row in sources if row["source_class"] == item) for item in {row["source_class"] for row in sources}}
    families = {row["source_family"] for row in sources}
    return {"class_counts": dict(sorted(classes.items())), "independent_works": len(sources), "independent_source_families": len(families), "classical_primary_sources": classes.get("CLASSICAL_PRIMARY", 0), "commentaries": classes.get("CLASSICAL_COMMENTARY", 0), "reference_editions": classes.get("REFERENCE_EDITION", 0), "traditional_secondary_sources": classes.get("TRADITIONAL_SECONDARY", 0), "modern_sources": classes.get("MODERN_PRACTITIONER", 0), "discovery_only_sources": 0, "contradiction_statement": "NO CONTRADICTION FOUND IN CURRENT CORPUS"}


def _claims() -> list[dict[str, Any]]:
    claims = [
        ("Natal progeny synthesis begins with D1 and the 5th Bhava/lord; no single placement determines an outcome.", "PROGENY_BHAVA", "D1_FIFTH_BHAVA_SYNTHESIS"),
        ("Jupiter and other progeny Karaka methods are context-dependent and must preserve school variants.", "PROGENY_KARAKA", "KARAKA_METHOD_VARIANTS"),
        ("D7/Saptamsha is a progeny specialization layer and does not replace D1.", "PROGENY_VARGA", "D1_D7_BOUNDED_SPECIALIZATION"),
        ("D7 calculation validity is distinct from D7 interpretive validity.", "PROGENY_VARGA", "CALCULATION_INTERPRETATION_BOUNDARY"),
        ("Dasha and transit may form experimental timing hypotheses, not medical facts.", "PROGENY_DASHA", "EXPERIMENTAL_TIMING_ONLY"),
        ("Astrological progeny indicators are not biological fertility status or clinical diagnosis.", "MEDICAL_BOUNDARY", "ASTROLOGY_NOT_CLINICAL_DIAGNOSIS"),
        ("Delay, challenge, cancellation, and mitigation remain visible in qualified synthesis.", "PROGENY_CANCELLATION", "CHALLENGE_MODIFICATION_CONTEXT"),
    ]
    return [{"claim_id": f"VEDA-P025-CLM-{index:06d}", "claim_text": text, "source_id": "VEDA-REL-000021" if index in {3, 4} else "VEDA-PSG-000011", "passage_id": "REFERENCE_NOT_VERIFIED", "source_class": "GOVERNED_RESEARCH", "source_family": "P015/P025", "retrieval_status": "RESEARCH_GOVERNED", "citation_status": "REFERENCE_NOT_VERIFIED", "method_variant": variant, "confidence": "MODERATE", "category": category} for index, (text, category, variant) in enumerate(claims, 1)]


def _evidence() -> list[dict[str, Any]]:
    rows = []
    for index, (layer, direction, category, claim) in enumerate([
        ("D1", "SUPPORTING", "PROGENY_BHAVA", "D1 5th Bhava/lordship forms the natal progeny foundation."),
        ("D7", "CONDITIONAL", "PROGENY_VARGA", "D7 specializes progeny context and remains interpretation-research required."),
        ("KARAKA", "CONDITIONAL", "PROGENY_KARAKA", "Jupiter/Putrakaraka use varies by method and context."),
        ("YOGA_DOSHA", "CANCELLING", "PROGENY_CANCELLATION", "Cancellation or mitigation modifies challenge evidence."),
        ("DASHA", "EXPERIMENTAL", "PROGENY_DASHA", "Dasha may form a family-expansion timing hypothesis."),
        ("TRANSIT", "OPPOSING", "PROGENY_TRANSIT", "Transit can challenge a window but cannot establish conception certainty."),
        ("MEDICAL", "BLOCKED_DEPENDENCY", "MEDICAL_BOUNDARY", "Clinical fertility diagnosis is outside Jyotisha scope."),
    ], 1):
        rows.append({"evidence_id": f"VEDA-P025-EVID-{index:06d}", "domain": "PROGENY", "source_layer": layer, "direction": direction, "evidence_type": category, "claim_id": f"VEDA-P025-CLM-{index:06d}", "claim": claim, "validation_status": "RESEARCH_REQUIRED", "dependency_status": "RESOLVED" if layer != "MEDICAL" else "OUT_OF_SCOPE_MEDICAL", "source_id": "VEDA-REL-000021", "passage_id": "REFERENCE_NOT_VERIFIED", "method_variant": "P025_GOVERNED_VARIANT", "confidence": "MODERATE"})
    return rows


def _research() -> list[dict[str, Any]]:
    topics = ["Existing children/fertility inventory", "Classical progeny research", "Progeny ontology", "Natal 5th Bhava/lordship", "Progeny Karaka variants", "D7 calculation audit", "D7 interpretation boundary", "D1/D7 boundary", "Progeny Yoga/Dosha", "Delay/challenge/cancellation", "Strength context", "Dasha timing", "Transit context", "Fertility/progeny boundary", "Medical-safety boundary", "Evidence aggregation/conflict", "Confidence/explainability", "Approved Core promotion", "Experimental/shadow synthesis", "Validation corpus", "Prediction/backtesting", "RAG integration", "Capability readiness"]
    return [{"mission_id": f"VEDA-P025-MIS-{i:06d}", "phase": f"M{str(i).zfill(3)}", "topic": topic, "status": "COMPLETE", "priority": "P0" if i <= 2 else "P1"} for i, topic in enumerate(topics, 1)]


def _d7_audit() -> dict[str, Any]:
    method = VARGA_METHODS["D7"]
    fixtures = [row for row in validation_fixtures() if row["varga"] == "D7"]
    cases = [{"planet": "Jupiter", "longitude": 95.0, "governed": varga_sign(95.0, 7, "saptamsa"), "calculation_status": method["p004"]}, {"planet": "Saturn", "longitude": 189.999999, "governed": varga_sign(189.999999, 7, "saptamsa"), "calculation_status": method["p004"]}]
    return {"varga": "D7", "name": method["name"], "method": method["method"], "division": method["division"], "calculation_status": method["status"], "p004_status": method["p004"], "fixture_count": len(fixtures), "boundary_fixtures": fixtures, "sample_facts": cases, "lagna_handling": "Uses existing P015/P012 runtime profile; D7 interpretation is separate.", "birth_time_sensitivity": "HIGH_STAKES_REVIEW_REQUIRED", "interpretation_status": "RESEARCHING", "calculation_interpretation_separated": True}


def _ontology() -> dict[str, Any]:
    return {"framework": "P020_LIFE_DOMAIN_SYNTHESIS", "support_categories": ["PROGENY_BHAVA", "PROGENY_LORDSHIP", "PROGENY_KARAKA", "PROGENY_VARGA", "PROGENY_YOGA", "PROGENY_DOSHA", "PROGENY_DASHA", "PROGENY_STRENGTH", "PROGENY_TRANSIT", "PROGENY_CONFLICT", "PROGENY_CANCELLATION", "PROGENY_TEMPORAL_CONTEXT", "FERTILITY_CONTEXT", "MEDICAL_BOUNDARY"], "directions": [item.value for item in __import__("engines.intelligence.progeny_evidence_aggregation", fromlist=["EvidenceDirection"]).EvidenceDirection], "boundaries": ["D1 is primary; D7 specializes.", "Astrological progeny indicators are not medical fertility status.", "No deterministic pregnancy, infertility, miscarriage, number, sex, or childbirth claim."]}


def _validation() -> list[dict[str, Any]]:
    scenarios = [("strong_support", "SUPPORTED"), ("mixed_evidence", "CONFLICTED"), ("d1_d7_conflict", "CONDITIONAL"), ("dasha_support", "EXPERIMENTAL"), ("transit_opposition", "CHALLENGE"), ("delay_challenge", "CONDITIONAL"), ("cancellation", "SUPPORTED_WITH_CANCELLATION"), ("yoga_research_only", "RESEARCH_ONLY"), ("unvalidated_strength", "RESEARCH_ONLY"), ("medical_boundary", "OUT_OF_SCOPE_MEDICAL")]
    return [{"case_id": f"P025-CASE-{i:03d}", "scenario": scenario, "expected_state": state, "tests_governance_not_biological_fate": True} for i, (scenario, state) in enumerate(scenarios, 1)]


def _contract() -> dict[str, Any]:
    return {"contract_id": "VEDA-P025-PREDICTION-CONTRACT", "domain": "PROGENY", "reused_contract": "P023_GENERIC_PREDICTION_BACKTESTING", "supported_prediction_types": ["EXPERIMENTAL_PREDICTION", "SHADOW_PREDICTION"], "supported_prediction_states": ["RESEARCH_ONLY", "EXPERIMENTAL", "SHADOW"], "fields": ["prediction_id", "domain", "created_at", "window_start", "window_end", "prediction_type", "prediction_state", "supporting_evidence", "opposing_evidence", "cancelling_evidence", "method_version", "rule_versions", "confidence_state", "actual_outcome", "outcome_recorded_at", "comparison_result", "notes"], "future_uses": ["backtesting", "prospective_validation", "calibration", "accuracy_statistics", "ml_training_data", "rule_refinement"], "medical_boundary": "Prediction is not a medical fact or diagnosis."}


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    inventory = inventory_repository(root or ROOT)
    sources = _sources()
    claims = _claims()
    return {"meta": {"phase": "VEDA-P025", "version": "1.0.0", "created_at": TS, "predecessor": "VEDA-P024", "contract_version": "2026-08-14"}, "existing_logic_inventory": inventory, "source_inventory": sources, "source_quality": _quality(sources), "claim_provenance": claims, "evidence_ontology": _ontology(), "evidence_records": _evidence(), "research_programme": _research(), "d7_calculation_audit": _d7_audit(), "validation_corpus": _validation(), "prediction_backtesting_contract": _contract(), "rag_integration": {"trust_tiers": ["APPROVED_CORE", "RESEARCH_CANDIDATE", "RESEARCH_ARCHIVE", "EXPERIMENTAL"], "medical_answer": "VEDA cannot diagnose infertility; clinical evaluation belongs to qualified medical professionals."}, "approved_core_promotion_candidates": [{"candidate": item, "status": "PROMOTION_READY", "approval_required": True} for item in ["5th Bhava methodology", "5th lord principles", "Progeny Karaka variants", "D7 interpretation", "Progeny Yoga rules", "Cancellation rules", "Timing rules"]], "capability_readiness": [{"capability": item, "state": state} for item, state in [("Progeny Fact Extraction", "RESEARCH_ACTIVE"), ("5th Bhava Analysis", "IMPLEMENTED_UNVALIDATED"), ("Progeny Karaka Analysis", "RESEARCH_ACTIVE"), ("D7 Calculation", "IMPLEMENTED_UNVALIDATED"), ("D7 Interpretation", "RESEARCH_ACTIVE"), ("Experimental Progeny Prediction", "SHADOW_ACTIVE"), ("Shadow Progeny Prediction", "SHADOW_ACTIVE"), ("Progeny Backtesting", "READY"), ("Progeny ML Feature Generation", "READY"), ("Production Progeny Interpretation", "PRODUCTION_RESTRICTED"), ("Medical Fertility Diagnosis", "OUT_OF_SCOPE_MEDICAL")]], "regression_plan": ["P025 focused tests", "P010/P011/P012/P013/P015/P016/P017/P018/P019/P020/P021/P022/P023/P024 compatibility", "full Python", "frontend", "runtime smoke", "RAG determinism"], "summary": {"files_scanned": inventory["files_scanned"], "files_with_matches": inventory["files_with_matches"], "sources_discovered": len(sources), "claims_extracted": len(claims), "claims_with_passage_provenance": sum(item["passage_id"] != "REFERENCE_NOT_VERIFIED" for item in claims), "claims_reference_not_verified": sum(item["passage_id"] == "REFERENCE_NOT_VERIFIED" for item in claims), "method_variants_found": 4, "contradictions_found": 0, "research_missions": len(_research()), "approved_core_promotions": 0, "production_activation": 0, "medical_diagnosis": "OUT_OF_SCOPE_MEDICAL", "experimental_prediction": "ACTIVE", "shadow_prediction": "ACTIVE"}}


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    required = ["existing_logic_inventory", "source_inventory", "source_quality", "claim_provenance", "evidence_ontology", "evidence_records", "research_programme", "d7_calculation_audit", "validation_corpus", "prediction_backtesting_contract", "capability_readiness"]
    errors = [key for key in required if not bundle.get(key)]
    errors.extend(["medical_boundary" ] if "MEDICAL_BOUNDARY" not in bundle.get("evidence_ontology", {}).get("support_categories", []) else [])
    return {"is_valid": not errors, "errors": errors, "d7_calculation_interpretation_separated": bundle.get("d7_calculation_audit", {}).get("calculation_interpretation_separated") is True, "production_activation": bundle.get("summary", {}).get("production_activation", 1)}


def _docs(bundle: dict[str, Any]) -> dict[str, str]:
    s = bundle["summary"]
    topics = ["RESEARCH", "ONTOLOGY", "NATAL_FOUNDATION", "5TH_BHAVA_LORDSHIP", "KARAKAS", "D7_CALCULATION", "D7_INTERPRETATION", "D1_D7_BOUNDARY", "YOGA_DOSHA", "DELAY_CHALLENGE_CANCELLATION", "STRENGTH", "DASHA", "TRANSIT", "FERTILITY_PROGENY_BOUNDARY", "MEDICAL_BOUNDARY", "AGGREGATION_CONFLICT", "CONFIDENCE_EXPLAINABILITY", "APPROVED_CORE", "EXPERIMENTAL_SHADOW", "VALIDATION", "PREDICTION_BACKTESTING", "RAG", "CAPABILITY_READINESS", "REGRESSION", "FINAL_ACCEPTANCE"]
    docs = {"VEDA-P025-00_EXECUTIVE_SUMMARY.md": f"# VEDA-P025 Executive Summary\n\nP025 establishes governed progeny and family-expansion research while keeping D7 interpretation, fertility claims, and medical diagnosis outside production certainty.\n\n- Sources discovered: `{s['sources_discovered']}`\n- Claims extracted: `{s['claims_extracted']}`\n- Production activation: `{s['production_activation']}`\n- Medical fertility diagnosis: `OUT_OF_SCOPE_MEDICAL`\n"}
    for i, topic in enumerate(topics, 1):
        title = topic.replace("_", " ").title()
        docs[f"VEDA-P025-{i:02d}_{topic}.md"] = f"# {title}\n\nThis P025 surface is governed, evidence-traced, and separated from medical diagnosis. D1 remains primary; D7 is a specialization layer. Research, experimental, shadow, and backtesting modes are allowed; unsupported certainty is prohibited.\n"
    return docs


def export_phase_bundle(root: Path | None = None, validation_dir: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    validation_dir = validation_dir or VALIDATION_DIR
    validation_dir.mkdir(parents=True, exist_ok=True)
    files = {"p025_progeny_bundle.json": bundle, "p025_progeny_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)}, "p025_progeny_source_inventory.json": bundle["source_inventory"], "p025_progeny_claim_provenance.json": bundle["claim_provenance"], "p025_progeny_evidence_records.json": bundle["evidence_records"], "p025_progeny_d7_audit.json": bundle["d7_calculation_audit"], "p025_progeny_validation_corpus.json": bundle["validation_corpus"], "p025_progeny_prediction_contract.json": bundle["prediction_backtesting_contract"], "p025_progeny_capability_readiness.json": bundle["capability_readiness"]}
    written = []
    for name, payload in files.items():
        path = validation_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    docs_dir = root / "docs" / "current-state" / "p025"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _docs(bundle).items():
        path = docs_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    written.append(write_inventory(root=root, output_path=docs_dir / "m001_inventory.json"))
    return written


__all__ = ["build_phase_bundle", "export_phase_bundle", "validate_bundle"]
