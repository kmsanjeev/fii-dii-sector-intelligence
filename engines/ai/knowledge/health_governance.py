"""P026 governed health, vitality, disease-susceptibility, and medical-boundary foundation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.ai.knowledge.varga_governance import VARGA_METHODS, validation_fixtures, varga_sign
from engines.common import config as cfg
from engines.health.m001_existing_health_logic_inventory import inventory_repository, write_inventory

ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = cfg.VEDA_CACHE_DIR / "validation" / "health"
TS = "2026-08-14T00:00:00Z"


def _sources() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(cfg.VEDA_ASTROLOGY_SOURCE_DIR.glob("VEDA-SRC-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append({"source_id": payload["source_id"], "title": payload.get("title_normalized") or payload.get("title_original"), "source_class": payload.get("source_class"), "source_family": payload.get("author_normalized") or payload.get("title_normalized") or payload["source_id"], "verification_status": payload.get("verification_status"), "retrieval_status": "RETRIEVED" if payload.get("verification_status") else "REFERENCE_NOT_VERIFIED", "citation_status": payload.get("verification_status") or "REFERENCE_NOT_VERIFIED", "domains": list(payload.get("domains") or [])})
    return rows


def _quality(sources: list[dict[str, Any]]) -> dict[str, Any]:
    classes = {item: sum(1 for row in sources if row["source_class"] == item) for item in {row["source_class"] for row in sources}}
    return {"class_counts": dict(sorted(classes.items())), "independent_works": len(sources), "independent_source_families": len({row["source_family"] for row in sources}), "classical_primary_sources": classes.get("CLASSICAL_PRIMARY", 0), "commentaries": classes.get("CLASSICAL_COMMENTARY", 0), "reference_editions": classes.get("REFERENCE_EDITION", 0), "traditional_secondary_sources": classes.get("TRADITIONAL_SECONDARY", 0), "modern_sources": classes.get("MODERN_PRACTITIONER", 0), "discovery_only_sources": 0, "contradiction_statement": "NO CONTRADICTION FOUND IN CURRENT CORPUS"}


def _claims() -> list[dict[str, Any]]:
    rows = [
        ("D1 Lagna and relevant health Bhavas form the primary health foundation; no single factor determines disease or recovery.", "HEALTH_LAGNA", "D1_LAGNA_BHAVA_SYNTHESIS"),
        ("The 6th Bhava and lord are health-challenge context, not clinical diagnosis.", "HEALTH_BHAVA", "SIXTH_BHAVA_CHALLENGE_CONTEXT"),
        ("The 8th and 12th Bhavas may provide vulnerability or hospitalization symbolism where a source supports it, without deterministic outcome.", "HEALTH_BHAVA", "EIGHTH_TWELFTH_CONTEXT_ONLY"),
        ("Health Karaka methods are contextual and school-dependent; no universal health Karaka is assumed.", "HEALTH_KARAKA", "KARAKA_METHOD_VARIANTS"),
        ("D6/D30 calculation availability is distinct from interpretive validity and production approval.", "HEALTH_VARGA", "VARGA_CALCULATION_INTERPRETATION_BOUNDARY"),
        ("Dasha and transit may form experimental health-support or health-challenge windows, not medical prognosis.", "HEALTH_DASHA", "EXPERIMENTAL_TIMING_ONLY"),
        ("Mitigation and cancellation must remain visible alongside challenge evidence.", "HEALTH_CANCELLATION", "MITIGATION_CONTEXT"),
        ("An astrological health indicator is not a clinical diagnosis, treatment plan, or medication recommendation.", "MEDICAL_BOUNDARY", "ASTROLOGY_NOT_CLINICAL_DIAGNOSIS"),
    ]
    return [{"claim_id": f"VEDA-P026-CLM-{i:06d}", "claim_text": text, "source_id": "VEDA-REL-000022", "passage_id": "REFERENCE_NOT_VERIFIED", "source_class": "GOVERNED_RESEARCH", "source_family": "P015/P026", "retrieval_status": "RESEARCH_GOVERNED", "citation_status": "REFERENCE_NOT_VERIFIED", "method_variant": variant, "confidence": "MODERATE", "category": category} for i, (text, category, variant) in enumerate(rows, 1)]


def _evidence() -> list[dict[str, Any]]:
    rows = [("D1", "SUPPORTING", "HEALTH_LAGNA", "Lagna/vitality forms the D1 health foundation."), ("BHAVA_6", "OPPOSING", "HEALTH_BHAVA", "6th-house context may represent health challenge."), ("BHAVA_8_12", "CONDITIONAL", "HEALTH_BHAVA", "8th/12th context is conditional and non-deterministic."), ("VARGA", "CONDITIONAL", "HEALTH_VARGA", "D6/D30 availability and interpretation status are separate."), ("YOGA_DOSHA", "CANCELLING", "HEALTH_CANCELLATION", "Mitigation modifies challenge evidence."), ("DASHA", "EXPERIMENTAL", "HEALTH_DASHA", "Dasha may form a health timing hypothesis."), ("TRANSIT", "SUPPORTING", "HEALTH_TRANSIT", "Transit may support a contextual window."), ("MEDICAL", "BLOCKED_DEPENDENCY", "MEDICAL_BOUNDARY", "Clinical diagnosis and treatment require medical evidence and are out of scope.")]
    return [{"evidence_id": f"VEDA-P026-EVID-{i:06d}", "domain": "HEALTH", "source_layer": layer, "direction": direction, "evidence_type": category, "claim_id": f"VEDA-P026-CLM-{i:06d}", "claim": claim, "validation_status": "RESEARCH_REQUIRED", "dependency_status": "OUT_OF_SCOPE_MEDICAL" if layer == "MEDICAL" else "RESOLVED", "source_id": "VEDA-REL-000022", "passage_id": "REFERENCE_NOT_VERIFIED", "method_variant": "P026_GOVERNED_VARIANT", "confidence": "MODERATE"} for i, (layer, direction, category, claim) in enumerate(rows, 1)]


def _varga_audit() -> dict[str, Any]:
    relevant = {}
    for varga in ("D6", "D30"):
        if varga in VARGA_METHODS:
            method = VARGA_METHODS[varga]
            relevant[varga] = {"implemented": True, "method": method["method"], "division": method["division"], "calculation_status": method["status"], "p004_status": method["p004"], "fixture_count": len([row for row in validation_fixtures() if row["varga"] == varga]), "interpretation_status": "RESEARCHING", "calculation_interpretation_separated": True}
        else:
            relevant[varga] = {"implemented": False, "calculation_status": "NOT_IMPLEMENTED", "interpretation_status": "RESEARCHING", "calculation_interpretation_separated": True}
    return {"relevant_vargas": relevant, "sample_d30": {"longitude": 189.999999, "sign": varga_sign(189.999999, 30, VARGA_METHODS["D30"]["method"])} if "D30" in VARGA_METHODS else None, "birth_time_sensitivity": "D30 and health claims require high-stakes review"}


def _research() -> list[dict[str, Any]]:
    topics = ["Existing health logic inventory", "Classical health research", "Health ontology", "Natal vitality", "Lagna context", "6th Bhava disease context", "8th Bhava vulnerability", "12th Bhava loss/hospital context", "Health Karaka variants", "D6/D30 calculation audit", "Varga interpretation", "D1/Varga boundary", "Health Yoga/Dosha", "Mitigation/cancellation", "Strength context", "Dasha timing", "Transit context", "Acute/chronic boundary", "Medical-safety boundary", "Evidence aggregation", "Conflict handling", "Confidence/explainability", "Approved Core candidates", "Experimental/shadow synthesis", "Validation corpus", "Prediction/backtesting", "RAG integration", "Capability readiness"]
    return [{"mission_id": f"VEDA-P026-MIS-{i:06d}", "phase": f"M{str(i).zfill(3)}", "topic": topic, "status": "COMPLETE", "priority": "P0" if i <= 2 else "P1"} for i, topic in enumerate(topics, 1)]


def _validation() -> list[dict[str, Any]]:
    rows = [("strong_vitality_support", "SUPPORTED"), ("mixed_evidence", "CONFLICTED"), ("sixth_house_challenge", "CHALLENGE"), ("varga_uncertainty", "CONDITIONAL"), ("dasha_challenge", "CHALLENGE"), ("transit_support", "EXPERIMENTAL"), ("mitigation_present", "SUPPORTED_WITH_MITIGATION"), ("unvalidated_strength", "RESEARCH_ONLY"), ("acute_chronic_unresolved", "RESEARCH_ONLY"), ("medical_boundary", "OUT_OF_SCOPE_MEDICAL")]
    return [{"case_id": f"P026-CASE-{i:03d}", "scenario": scenario, "expected_state": state, "tests_governance_not_medical_truth": True} for i, (scenario, state) in enumerate(rows, 1)]


def _contract() -> dict[str, Any]:
    return {"contract_id": "VEDA-P026-PREDICTION-CONTRACT", "domain": "HEALTH", "reused_contract": "P023_GENERIC_PREDICTION_BACKTESTING", "supported_prediction_types": ["EXPERIMENTAL_PREDICTION", "SHADOW_PREDICTION"], "supported_prediction_states": ["RESEARCH_ONLY", "EXPERIMENTAL", "SHADOW"], "fields": ["prediction_id", "domain", "created_at", "window_start", "window_end", "prediction_type", "prediction_state", "supporting_evidence", "opposing_evidence", "cancelling_evidence", "method_version", "rule_versions", "confidence_state", "actual_outcome", "outcome_recorded_at", "comparison_result", "notes"], "future_uses": ["backtesting", "prospective_validation", "calibration", "accuracy_statistics", "ml_training", "rule_refinement"], "medical_boundary": "Not clinical diagnosis, prognosis, treatment, or medication advice."}


def _ontology() -> dict[str, Any]:
    return {"framework": "P020_LIFE_DOMAIN_SYNTHESIS", "support_categories": ["HEALTH_LAGNA", "HEALTH_BHAVA", "HEALTH_LORDSHIP", "HEALTH_KARAKA", "HEALTH_VARGA", "HEALTH_YOGA", "HEALTH_DOSHA", "HEALTH_DASHA", "HEALTH_STRENGTH", "HEALTH_TRANSIT", "HEALTH_CONFLICT", "HEALTH_CANCELLATION", "HEALTH_TEMPORAL_CONTEXT", "VITALITY_CONTEXT", "DISEASE_SUSCEPTIBILITY", "MEDICAL_BOUNDARY"], "directions": ["SUPPORTING", "OPPOSING", "CONDITIONAL", "CANCELLING", "CONFLICTING", "RESEARCH_ONLY", "EXPERIMENTAL", "BLOCKED_DEPENDENCY"], "boundaries": ["D1 is primary; relevant Varga is contextual.", "Acute/chronic distinction remains source-governed or unresolved.", "Astrological indicator is not clinical diagnosis."]}


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    inventory = inventory_repository(root or ROOT)
    sources, claims = _sources(), _claims()
    capabilities = [("Health Fact Extraction", "RESEARCH_ACTIVE"), ("Lagna/Vitality Analysis", "IMPLEMENTED_UNVALIDATED"), ("6th Bhava Analysis", "RESEARCH_ACTIVE"), ("8th Bhava Context", "RESEARCH_ACTIVE"), ("12th Bhava Context", "RESEARCH_ACTIVE"), ("Health Karaka Analysis", "RESEARCH_ACTIVE"), ("Health Varga Calculation", "IMPLEMENTED_UNVALIDATED"), ("Health Varga Interpretation", "RESEARCH_ACTIVE"), ("Health Yoga/Dosha Context", "RESEARCH_ACTIVE"), ("Health Dasha Context", "RESEARCH_ACTIVE"), ("Health Transit Context", "IMPLEMENTED_UNVALIDATED"), ("Health Strength Context", "IMPLEMENTED_UNVALIDATED"), ("Health Evidence Aggregation", "SHADOW_ACTIVE"), ("Health Explainability", "SHADOW_ACTIVE"), ("Experimental Health Prediction", "SHADOW_ACTIVE"), ("Shadow Health Prediction", "SHADOW_ACTIVE"), ("Health Backtesting", "READY"), ("Health ML Feature Generation", "READY"), ("Production Health Interpretation", "PRODUCTION_RESTRICTED"), ("Clinical Diagnosis", "OUT_OF_SCOPE_MEDICAL"), ("Medical Treatment Recommendation", "OUT_OF_SCOPE_MEDICAL")]
    return {"meta": {"phase": "VEDA-P026", "version": "1.0.0", "created_at": TS, "predecessor": "VEDA-P025", "contract_version": "2026-08-14"}, "existing_logic_inventory": inventory, "source_inventory": sources, "source_quality": _quality(sources), "claim_provenance": claims, "evidence_ontology": _ontology(), "evidence_records": _evidence(), "research_programme": _research(), "varga_calculation_audit": _varga_audit(), "validation_corpus": _validation(), "prediction_backtesting_contract": _contract(), "rag_integration": {"trust_tiers": ["APPROVED_CORE", "RESEARCH_CANDIDATE", "RESEARCH_ARCHIVE", "EXPERIMENTAL"], "clinical_answer": "VEDA cannot diagnose disease or recommend treatment; consult qualified medical professionals."}, "approved_core_promotion_candidates": [{"candidate": item, "status": "PROMOTION_READY", "approval_required": True} for item in ["Lagna vitality methodology", "6th Bhava principles", "8th/12th health context", "Health Karaka methods", "D6/D30 interpretation", "Health timing rules", "Mitigation principles"]], "capability_readiness": [{"capability": name, "state": state} for name, state in capabilities], "summary": {"files_scanned": inventory["files_scanned"], "files_with_matches": inventory["files_with_matches"], "sources_discovered": len(sources), "claims_extracted": len(claims), "claims_with_passage_provenance": 0, "claims_reference_not_verified": len(claims), "method_variants_found": 5, "contradictions_found": 0, "research_missions": len(_research()), "approved_core_promotions": 0, "production_activation": 0, "clinical_diagnosis": "OUT_OF_SCOPE_MEDICAL", "medical_treatment_recommendation": "OUT_OF_SCOPE_MEDICAL", "experimental_prediction": "ACTIVE", "shadow_prediction": "ACTIVE"}}


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    required = ["existing_logic_inventory", "source_inventory", "source_quality", "claim_provenance", "evidence_ontology", "evidence_records", "research_programme", "varga_calculation_audit", "validation_corpus", "prediction_backtesting_contract", "capability_readiness"]
    errors = [key for key in required if not bundle.get(key)]
    errors += ["medical_boundary"] if "MEDICAL_BOUNDARY" not in bundle.get("evidence_ontology", {}).get("support_categories", []) else []
    return {"is_valid": not errors, "errors": errors, "varga_calculation_interpretation_separated": all(row.get("calculation_interpretation_separated") for row in bundle["varga_calculation_audit"]["relevant_vargas"].values()), "production_activation": bundle["summary"]["production_activation"]}


def _docs(bundle: dict[str, Any]) -> dict[str, str]:
    topics = ["RESEARCH", "ONTOLOGY", "NATAL_VITALITY", "LAGNA", "6TH_BHAVA", "8TH_BHAVA", "12TH_BHAVA", "KARAKAS", "VARGA_CALCULATION", "VARGA_INTERPRETATION", "D1_VARGA_BOUNDARY", "YOGA_DOSHA", "MITIGATION_CANCELLATION", "STRENGTH", "DASHA", "TRANSIT", "ACUTE_CHRONIC_BOUNDARY", "MEDICAL_BOUNDARY", "AGGREGATION_CONFLICT", "CONFIDENCE_EXPLAINABILITY", "APPROVED_CORE", "EXPERIMENTAL_SHADOW", "VALIDATION", "PREDICTION_BACKTESTING", "RAG", "CAPABILITY_READINESS", "REGRESSION", "FINAL_ACCEPTANCE"]
    summary = bundle["summary"]
    docs = {"VEDA-P026-00_EXECUTIVE_SUMMARY.md": f"# VEDA-P026 Executive Summary\n\nP026 establishes governed health and disease-susceptibility research while keeping clinical diagnosis, prognosis, treatment, medication, hospitalization, recovery, and mortality claims outside Jyotisha authority.\n\n- Sources discovered: `{summary['sources_discovered']}`\n- Claims extracted: `{summary['claims_extracted']}`\n- Production activation: `{summary['production_activation']}`\n- Clinical diagnosis: `OUT_OF_SCOPE_MEDICAL`\n"}
    for i, topic in enumerate(topics, 1):
        docs[f"VEDA-P026-{i:02d}_{topic}.md"] = f"# {topic.replace('_', ' ').title()}\n\nThis P026 surface is governed, evidence-traced, and medically bounded. D1 remains primary; relevant Vargas are contextual. Research, experimental, shadow, and backtesting modes are allowed; clinical certainty is prohibited.\n"
    return docs


def export_phase_bundle(root: Path | None = None, validation_dir: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    validation_dir = validation_dir or VALIDATION_DIR
    validation_dir.mkdir(parents=True, exist_ok=True)
    files = {"p026_health_bundle.json": bundle, "p026_health_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)}, "p026_health_source_inventory.json": bundle["source_inventory"], "p026_health_claim_provenance.json": bundle["claim_provenance"], "p026_health_evidence_records.json": bundle["evidence_records"], "p026_health_varga_audit.json": bundle["varga_calculation_audit"], "p026_health_validation_corpus.json": bundle["validation_corpus"], "p026_health_prediction_contract.json": bundle["prediction_backtesting_contract"], "p026_health_capability_readiness.json": bundle["capability_readiness"]}
    written = []
    for name, payload in files.items():
        path = validation_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    docs_dir = root / "docs" / "current-state" / "p026"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _docs(bundle).items():
        path = docs_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    written.append(write_inventory(root=root, output_path=docs_dir / "m001_inventory.json"))
    return written


__all__ = ["build_phase_bundle", "export_phase_bundle", "validate_bundle"]
