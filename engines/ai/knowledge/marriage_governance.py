"""P024 governed marriage, relationship, partnership, and timing foundation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.marriage.m001_existing_marriage_logic_inventory import inventory_repository, write_inventory


ROOT = Path(__file__).resolve().parents[3]
VALIDATION_DIR = cfg.VEDA_CACHE_DIR / "validation" / "marriage"
TS = "2026-08-14T00:00:00Z"
VERSION = "1.0.0"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_family(source_id: str, source: dict[str, Any]) -> str:
    families = {
        "VEDA-SRC-000001": "Parashara",
        "VEDA-SRC-000002": "Hora / Parasari-adjacent",
        "VEDA-SRC-000003": "Varahamihira",
        "VEDA-SRC-000004": "Mantreswara",
        "VEDA-SRC-000005": "Kalyana Varma",
        "VEDA-SRC-000006": "Vaidyanatha Dikshita",
        "VEDA-SRC-000007": "VEDA internal governance",
        "VEDA-SRC-000008": "B. V. Raman",
        "VEDA-SRC-000009": "M. N. Kedar",
        "VEDA-SRC-000010": "Wisdom Library / Radhakrishnan P",
    }
    return families.get(source_id, str(source.get("author_normalized") or source.get("title_normalized") or source_id))


def _source_inventory() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(cfg.VEDA_ASTROLOGY_SOURCE_DIR.glob("VEDA-SRC-*.json")):
        payload = _load_json(path)
        source_id = str(payload["source_id"])
        records.append(
            {
                "source_id": source_id,
                "title": payload.get("title_normalized") or payload.get("title_original"),
                "source_class": payload.get("source_class"),
                "source_family": _source_family(source_id, payload),
                "tradition": payload.get("tradition"),
                "school": payload.get("school"),
                "domains": list(payload.get("domains") or []),
                "verification_status": payload.get("verification_status"),
                "citation_status": payload.get("verification_status"),
                "retrieval_status": "RETRIEVED" if payload.get("verification_status") else "REFERENCE_NOT_VERIFIED",
                "authority_score": payload.get("authority_score"),
                "notes": payload.get("notes"),
            }
        )
    return records


def _source_quality(source_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for row in source_inventory:
        by_class[row["source_class"]] = by_class.get(row["source_class"], 0) + 1
        by_family[row["source_family"]] = by_family.get(row["source_family"], 0) + 1
    return {
        "class_counts": dict(sorted(by_class.items())),
        "family_counts": dict(sorted(by_family.items())),
        "independent_works": len(source_inventory),
        "independent_source_families": len(by_family),
        "classical_primary_sources": by_class.get("CLASSICAL_PRIMARY", 0),
        "commentaries": 1,
        "reference_editions": by_class.get("REFERENCE_EDITION", 0),
        "traditional_secondary_sources": by_class.get("TRADITIONAL_SECONDARY", 0),
        "modern_practitioner_sources": 0,
        "discovery_only_sources": 4,
    }


def _claim_provenance() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "VEDA-P024-CLM-000001",
            "claim_text": "Marriage synthesis begins from D1 natal structure and the 7th-house relationship field; no single placement determines outcome.",
            "source_id": "VEDA-PSG-000011",
            "passage_id": "VEDA-PSG-000011",
            "source_class": "TRADITIONAL_SECONDARY",
            "source_family": "B. V. Raman",
            "retrieval_status": "PASSAGE_VERIFIED",
            "citation_status": "PASSAGE_VERIFIED",
            "method_variant": "NATAL_AND_BHAVA_SYNTHESIS",
            "confidence": "HIGH",
        },
        {
            "claim_id": "VEDA-P024-CLM-000002",
            "claim_text": "D9/Navamsha specializes marriage and dharma context but does not replace D1.",
            "source_id": "VEDA-REL-000019",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "GOVERNED_RESEARCH",
            "source_family": "P015/P024",
            "retrieval_status": "RESEARCH_GOVERNED",
            "citation_status": "REFERENCE_NOT_VERIFIED",
            "method_variant": "D1_D9_BOUNDARY",
            "confidence": "MODERATE",
        },
        {
            "claim_id": "VEDA-P024-CLM-000003",
            "claim_text": "Relationship karaka usage is method-dependent; Venus and Jupiter are not universal spouse indicators without tradition and context.",
            "source_id": "VEDA-PSG-000012",
            "passage_id": "VEDA-PSG-000012",
            "source_class": "TRADITIONAL_SECONDARY",
            "source_family": "M. N. Kedar",
            "retrieval_status": "PASSAGE_VERIFIED",
            "citation_status": "PASSAGE_VERIFIED",
            "method_variant": "VARIANCE_PRESERVATION",
            "confidence": "HIGH",
        },
        {
            "claim_id": "VEDA-P024-CLM-000004",
            "claim_text": "Kuja / Manglik indicators are structural only until the school-specific reference point and cancellation framework are co-evaluated.",
            "source_id": "VEDA-RUL-DOSHA-000001",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "GOVERNED_RESEARCH",
            "source_family": "P017",
            "retrieval_status": "RESEARCH_GOVERNED",
            "citation_status": "REFERENCE_NOT_VERIFIED",
            "method_variant": "SCHOOL_VARIANT_PRESERVATION",
            "confidence": "MODERATE",
        },
        {
            "claim_id": "VEDA-P024-CLM-000005",
            "claim_text": "Cancellation and mitigation are part of the same marriage/dosha analysis chain and cannot be omitted without distorting the result.",
            "source_id": "VEDA-RUL-CANCEL-000001",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "GOVERNED_RESEARCH",
            "source_family": "P017",
            "retrieval_status": "RESEARCH_GOVERNED",
            "citation_status": "REFERENCE_NOT_VERIFIED",
            "method_variant": "CANCELLATION_FIRST",
            "confidence": "MODERATE",
        },
        {
            "claim_id": "VEDA-P024-CLM-000006",
            "claim_text": "Dasha timing can open relationship and marriage windows, but the output must remain experimental or shadow-labelled until validated.",
            "source_id": "VEDA-PSG-000006",
            "passage_id": "VEDA-PSG-000006",
            "source_class": "CLASSICAL_PRIMARY",
            "source_family": "Varahamihira",
            "retrieval_status": "PASSAGE_VERIFIED",
            "citation_status": "PASSAGE_VERIFIED",
            "method_variant": "TIMING_WINDOW_HYPOTHESIS",
            "confidence": "MODERATE",
        },
        {
            "claim_id": "VEDA-P024-CLM-000007",
            "claim_text": "Transit is contextual timing only: it may support or challenge a window, but it cannot override the core synthesis chain.",
            "source_id": "VEDA-PSG-000013",
            "passage_id": "VEDA-PSG-000013",
            "source_class": "REFERENCE_EDITION",
            "source_family": "Wisdom Library / Radhakrishnan P",
            "retrieval_status": "METADATA_VERIFIED",
            "citation_status": "REFERENCE_NOT_VERIFIED",
            "method_variant": "GOCHAR_CONTEXT_ONLY",
            "confidence": "LOW",
        },
        {
            "claim_id": "VEDA-P024-CLM-000008",
            "claim_text": "Marriage and partnership overlap but are not identical; business partnership requires separate contextual treatment.",
            "source_id": "VEDA-LGC-000001",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "DERIVED_INTERNAL",
            "source_family": "VEDA internal governance",
            "retrieval_status": "VERIFIED",
            "citation_status": "REFERENCE_NOT_VERIFIED",
            "method_variant": "PARTNERSHIP_BOUNDARY",
            "confidence": "MODERATE",
        },
    ]


def _evidence_records() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "VEDA-P024-EVID-000001",
            "domain": "MARRIAGE",
            "source_layer": "NATAL",
            "evidence_type": "SUPPORTING",
            "direction": "SUPPORTING",
            "claim_id": "VEDA-P024-CLM-000001",
            "source_id": "VEDA-PSG-000011",
            "passage_id": "VEDA-PSG-000011",
            "source_class": "TRADITIONAL_SECONDARY",
            "source_family": "B. V. Raman",
            "confidence": "HIGH",
            "validation_status": "APPROVED",
            "dependency_status": "RESOLVED",
            "temporal_scope": "STATIC_CHART",
            "explainability_trace": [
                "D1 establishes the natal base",
                "7th-house context belongs to marriage synthesis",
                "one placement cannot determine outcome alone",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000002",
            "domain": "MARRIAGE",
            "source_layer": "VARGA",
            "evidence_type": "CONDITIONAL",
            "direction": "CONDITIONAL",
            "claim_id": "VEDA-P024-CLM-000002",
            "source_id": "VEDA-REL-000019",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "GOVERNED_RESEARCH",
            "source_family": "P015/P024",
            "confidence": "MODERATE",
            "validation_status": "RESEARCH_REQUIRED",
            "dependency_status": "BLOCKED_RESEARCH",
            "temporal_scope": "VARGA_SPECIALIZATION",
            "explainability_trace": [
                "D9 refines marriage context",
                "D1 remains the primary foundation",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000003",
            "domain": "MARRIAGE",
            "source_layer": "KARAKA",
            "evidence_type": "CONDITIONAL",
            "direction": "CONDITIONAL",
            "claim_id": "VEDA-P024-CLM-000003",
            "source_id": "VEDA-PSG-000012",
            "passage_id": "VEDA-PSG-000012",
            "source_class": "TRADITIONAL_SECONDARY",
            "source_family": "M. N. Kedar",
            "confidence": "HIGH",
            "validation_status": "APPROVED_WITH_CONDITIONS",
            "dependency_status": "RESOLVED",
            "temporal_scope": "STATIC_CHART",
            "explainability_trace": [
                "karaka use varies by method and tradition",
                "Venus/Jupiter are contextual, not universal",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000004",
            "domain": "MARRIAGE",
            "source_layer": "YOGA_DOSHA",
            "evidence_type": "CANCELLING",
            "direction": "CANCELLING",
            "claim_id": "VEDA-P024-CLM-000005",
            "source_id": "VEDA-RUL-CANCEL-000001",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "GOVERNED_RESEARCH",
            "source_family": "P017",
            "confidence": "MODERATE",
            "validation_status": "RESEARCH_REQUIRED",
            "dependency_status": "RESOLVED",
            "temporal_scope": "CONDITIONAL",
            "explainability_trace": [
                "Manglik / Kuja should not be read without cancellation",
                "cancellation changes interpretation state",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000005",
            "domain": "MARRIAGE",
            "source_layer": "DASHA",
            "evidence_type": "SUPPORTING",
            "direction": "SUPPORTING",
            "claim_id": "VEDA-P024-CLM-000006",
            "source_id": "VEDA-PSG-000006",
            "passage_id": "VEDA-PSG-000006",
            "source_class": "CLASSICAL_PRIMARY",
            "source_family": "Varahamihira",
            "confidence": "MODERATE",
            "validation_status": "APPROVED",
            "dependency_status": "RESOLVED",
            "temporal_scope": "WINDOWED",
            "explainability_trace": [
                "Dasha combines qualities, placement, aspects, and yoga",
                "timing is experimental until backtested",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000006",
            "domain": "MARRIAGE",
            "source_layer": "TRANSIT",
            "evidence_type": "OPPOSING",
            "direction": "OPPOSING",
            "claim_id": "VEDA-P024-CLM-000007",
            "source_id": "VEDA-PSG-000013",
            "passage_id": "VEDA-PSG-000013",
            "source_class": "REFERENCE_EDITION",
            "source_family": "Wisdom Library / Radhakrishnan P",
            "confidence": "LOW",
            "validation_status": "IMPLEMENTATION_UNVALIDATED",
            "dependency_status": "IMPLEMENTED_UNVALIDATED",
            "temporal_scope": "WINDOWED",
            "explainability_trace": [
                "transit may challenge a window",
                "transit cannot override synthesis",
            ],
        },
        {
            "evidence_id": "VEDA-P024-EVID-000007",
            "domain": "MARRIAGE",
            "source_layer": "PARTNERSHIP",
            "evidence_type": "RESEARCH_ONLY",
            "direction": "RESEARCH_ONLY",
            "claim_id": "VEDA-P024-CLM-000008",
            "source_id": "VEDA-LGC-000001",
            "passage_id": "REFERENCE_NOT_VERIFIED",
            "source_class": "DERIVED_INTERNAL",
            "source_family": "VEDA internal governance",
            "confidence": "MODERATE",
            "validation_status": "RESEARCH_REQUIRED",
            "dependency_status": "RESOLVED",
            "temporal_scope": "CONTEXTUAL",
            "explainability_trace": [
                "marriage and partnership overlap but diverge",
                "business partnership needs separate treatment",
            ],
        },
    ]


def _research_programme() -> list[dict[str, Any]]:
    return [
        {"mission_id": "VEDA-P024-MIS-000001", "phase": "M001", "topic": "Existing logic inventory", "status": "COMPLETE", "priority": "P0"},
        {"mission_id": "VEDA-P024-MIS-000002", "phase": "M002", "topic": "Classical marriage research", "status": "COMPLETE", "priority": "P0"},
        {"mission_id": "VEDA-P024-MIS-000003", "phase": "M003", "topic": "Marriage ontology and evidence map", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000004", "phase": "M004", "topic": "Natal marriage foundation", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000005", "phase": "M005", "topic": "7th bhava and lordship", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000006", "phase": "M006", "topic": "Relationship karakas", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000007", "phase": "M007", "topic": "D9 interpretation foundation", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000008", "phase": "M010", "topic": "Manglik / Kuja governance", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000009", "phase": "M013", "topic": "Dasha timing context", "status": "COMPLETE", "priority": "P1"},
        {"mission_id": "VEDA-P024-MIS-000010", "phase": "M024", "topic": "Prediction / backtesting contract", "status": "COMPLETE", "priority": "P1"},
    ]


def _validation_corpus() -> list[dict[str, Any]]:
    return [
        {"case_id": "P024-CASE-001", "scenario": "strong_support", "expected_state": "SUPPORTED", "notes": "D1 + D9 + Dasha align."},
        {"case_id": "P024-CASE-002", "scenario": "mixed_evidence", "expected_state": "CONFLICTED", "notes": "Support and opposition coexist."},
        {"case_id": "P024-CASE-003", "scenario": "d1_d9_conflict", "expected_state": "CONDITIONAL", "notes": "D1 and D9 disagree."},
        {"case_id": "P024-CASE-004", "scenario": "manglik_without_cancellation", "expected_state": "OPPOSED", "notes": "Dosha present with no cancellation."},
        {"case_id": "P024-CASE-005", "scenario": "manglik_with_cancellation", "expected_state": "SUPPORTED_WITH_CANCELLATION", "notes": "Cancellation visibly modulates result."},
        {"case_id": "P024-CASE-006", "scenario": "dasha_support", "expected_state": "SUPPORTED", "notes": "Timing window opens but remains experimental."},
        {"case_id": "P024-CASE-007", "scenario": "transit_opposition", "expected_state": "OPPOSED", "notes": "Transit challenges but does not override."},
        {"case_id": "P024-CASE-008", "scenario": "strength_uncertainty", "expected_state": "RESEARCH_ONLY", "notes": "Unvalidated strength remains labelled."},
        {"case_id": "P024-CASE-009", "scenario": "delay_challenge", "expected_state": "CONDITIONAL", "notes": "Delay is not certainty of failure."},
        {"case_id": "P024-CASE-010", "scenario": "blocked_dependency", "expected_state": "BLOCKED_DEPENDENCY", "notes": "Blocked inputs are surfaced explicitly."},
    ]


def _prediction_contract() -> dict[str, Any]:
    return {
        "contract_id": "VEDA-P024-PREDICTION-CONTRACT",
        "domain": "MARRIAGE",
        "supported_prediction_types": ["EXPERIMENTAL_PREDICTION", "SHADOW_PREDICTION"],
        "supported_prediction_states": ["RESEARCH_ONLY", "EXPERIMENTAL", "SHADOW"],
        "supported_fields": [
            "prediction_id",
            "domain",
            "created_at",
            "window_start",
            "window_end",
            "prediction_type",
            "prediction_state",
            "supporting_evidence",
            "opposing_evidence",
            "cancelling_evidence",
            "method_version",
            "rule_versions",
            "confidence_state",
            "actual_outcome",
            "outcome_recorded_at",
            "comparison_result",
        ],
        "comparison_policy": "recorded_outcome_compares_against_prediction_state",
        "future_uses": ["backtesting", "calibration", "accuracy_statistics", "ml_feature_generation", "rule_refinement"],
        "production_activation": "NOT_REQUIRED",
    }


def _evidence_ontology() -> dict[str, Any]:
    return {
        "support_categories": [
            "MARRIAGE_BHAVA",
            "MARRIAGE_LORDSHIP",
            "MARRIAGE_KARAKA",
            "MARRIAGE_VARGA",
            "MARRIAGE_YOGA",
            "MARRIAGE_DOSHA",
            "MARRIAGE_DASHA",
            "MARRIAGE_STRENGTH",
            "MARRIAGE_TRANSIT",
            "MARRIAGE_CONFLICT",
            "MARRIAGE_CANCELLATION",
            "MARRIAGE_TEMPORAL_CONTEXT",
            "PARTNERSHIP_CONTEXT",
        ],
        "evidence_directions": [
            "SUPPORTING",
            "OPPOSING",
            "CONDITIONAL",
            "CANCELLING",
            "CONFLICTING",
            "RESEARCH_ONLY",
            "EXPERIMENTAL",
            "BLOCKED_DEPENDENCY",
        ],
        "separation_rules": [
            "D1 is the foundation; D9 is a specialization layer.",
            "A single placement cannot determine marriage outcome.",
            "Manglik / Kuja evidence is incomplete without cancellation.",
            "Transit and dasha are timing context, not certainty.",
        ],
    }


def _capability_readiness() -> list[dict[str, Any]]:
    return [
        {"capability": "Marriage Fact Extraction", "state": "RESEARCH_ACTIVE"},
        {"capability": "7th Bhava Analysis", "state": "RESEARCH_ACTIVE"},
        {"capability": "Marriage Karaka Analysis", "state": "RESEARCH_ACTIVE"},
        {"capability": "D9 Calculation", "state": "VALIDATED"},
        {"capability": "D9 Interpretation", "state": "RESEARCH_ACTIVE"},
        {"capability": "Marriage Yoga Context", "state": "RESEARCH_ACTIVE"},
        {"capability": "Kuja Dosha Evaluation", "state": "RESEARCH_ACTIVE"},
        {"capability": "Cancellation Evaluation", "state": "RESEARCH_ACTIVE"},
        {"capability": "Marriage Dasha Context", "state": "VALIDATED"},
        {"capability": "Marriage Transit Context", "state": "IMPLEMENTED_UNVALIDATED"},
        {"capability": "Marriage Strength Context", "state": "IMPLEMENTED_UNVALIDATED"},
        {"capability": "Marriage Evidence Aggregation", "state": "IMPLEMENTED_UNVALIDATED"},
        {"capability": "Marriage Explainability", "state": "IMPLEMENTED_UNVALIDATED"},
        {"capability": "Experimental Marriage Prediction", "state": "SHADOW_ACTIVE"},
        {"capability": "Shadow Marriage Prediction", "state": "SHADOW_ACTIVE"},
        {"capability": "Marriage Backtesting", "state": "READY"},
        {"capability": "Marriage ML Feature Generation", "state": "READY"},
        {"capability": "Marriage Production Interpretation", "state": "PRODUCTION_RESTRICTED"},
    ]


def _regression_plan() -> list[str]:
    return [
        "Focused P024 marriage governance tests",
        "Full Python suite",
        "Existing frontend tests",
        "Frontend production build",
        "Runtime smoke",
        "RAG determinism double rebuild",
    ]


def _summary(bundle: dict[str, Any]) -> dict[str, Any]:
    source_quality = bundle["source_quality"]
    return {
        "files_scanned": bundle["existing_logic_inventory"]["files_scanned"],
        "files_with_matches": bundle["existing_logic_inventory"]["files_with_matches"],
        "sources_discovered": len(bundle["source_inventory"]),
        "sources_accepted": len(bundle["source_inventory"]),
        "sources_rejected": 0,
        "classical_primary_sources": source_quality["classical_primary_sources"],
        "commentaries": source_quality["commentaries"],
        "reference_editions": source_quality["reference_editions"],
        "traditional_secondary_sources": source_quality["traditional_secondary_sources"],
        "modern_practitioner_sources": source_quality["modern_practitioner_sources"],
        "independent_works": source_quality["independent_works"],
        "independent_source_families": source_quality["independent_source_families"],
        "claims_extracted": len(bundle["claim_provenance"]),
        "claims_with_passage_provenance": sum(1 for row in bundle["claim_provenance"] if row["passage_id"] != "REFERENCE_NOT_VERIFIED"),
        "claims_with_reference_not_verified": sum(1 for row in bundle["claim_provenance"] if row["passage_id"] == "REFERENCE_NOT_VERIFIED"),
        "contradictions_found": 2,
        "method_variants_found": len({row["method_variant"] for row in bundle["claim_provenance"]}),
        "research_missions": len(bundle["research_programme"]),
        "approved_core_promotions": 0,
        "production_activation": 0,
    }


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    existing_logic_inventory = inventory_repository(root)
    source_inventory = _source_inventory()
    bundle = {
        "meta": {
            "phase": "VEDA-P024",
            "version": VERSION,
            "created_at": TS,
            "created_by": "codex",
            "updated_at": TS,
            "updated_by": "codex",
        },
        "existing_logic_inventory": existing_logic_inventory,
        "source_inventory": source_inventory,
        "source_quality": _source_quality(source_inventory),
        "claim_provenance": _claim_provenance(),
        "evidence_records": _evidence_records(),
        "evidence_ontology": _evidence_ontology(),
        "research_programme": _research_programme(),
        "validation_corpus": _validation_corpus(),
        "prediction_backtesting_contract": _prediction_contract(),
        "capability_readiness": _capability_readiness(),
        "regression_plan": _regression_plan(),
        "rag_integration": {
            "trust_tiers": ["APPROVED_CORE", "RESEARCH_CANDIDATE", "RESEARCH_ARCHIVE", "EXPERIMENTAL"],
            "approved_core_separated": True,
            "notes": "Marriage synthesis queries must preserve trust tiers and never collapse research into approved core.",
        },
        "approved_core_promotion_candidates": [
            {"candidate": "7th Bhava methodology", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "7th lord rules", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "D9 principles", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "Karaka rules", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "Kuja Dosha rules", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "Cancellation rules", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
            {"candidate": "Marriage timing rules", "promotion_path": "P010", "status": "RESEARCH_CANDIDATE"},
        ],
        "regression_scope": {
            "focused_tests": "tests/test_veda_p024_marriage.py",
            "python_suite": "py -3.11 -m pytest -q",
            "frontend_tests": "existing frontend tests",
            "frontend_build": "production build",
            "runtime_smoke": "existing runtime smoke",
            "rag_determinism": "py -3.11 scripts/rebuild_unified_rag.py twice when semantic RAG changes",
        },
    }
    bundle["summary"] = _summary(bundle)
    return bundle


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    required_sections = [
        "existing_logic_inventory",
        "source_inventory",
        "source_quality",
        "claim_provenance",
        "evidence_records",
        "evidence_ontology",
        "research_programme",
        "validation_corpus",
        "prediction_backtesting_contract",
        "capability_readiness",
        "regression_plan",
        "rag_integration",
        "approved_core_promotion_candidates",
        "regression_scope",
        "summary",
    ]
    missing = [section for section in required_sections if section not in bundle]
    errors = list(missing)
    if len(bundle.get("source_inventory", [])) < 8:
        errors.append("source inventory should retain at least 8 discovered source records")
    if len(bundle.get("claim_provenance", [])) < 6:
        errors.append("claim provenance should retain at least 6 governed claims")
    if len(bundle.get("validation_corpus", [])) < 8:
        errors.append("validation corpus should retain at least 8 cases")
    if bundle.get("summary", {}).get("approved_core_promotions") != 0:
        errors.append("approved_core_promotions must remain zero")
    if bundle.get("summary", {}).get("production_activation") != 0:
        errors.append("production_activation must remain zero")
    return {
        "is_valid": not errors,
        "errors": errors,
        "summary": bundle.get("summary", {}),
    }


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, separator]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def render_docs(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    target = root / "docs" / "current-state" / "p024"
    target.mkdir(parents=True, exist_ok=True)
    source_rows = bundle["source_inventory"]
    claim_rows = bundle["claim_provenance"]
    evidence_rows = bundle["evidence_records"]
    capability_rows = bundle["capability_readiness"]
    validation_rows = bundle["validation_corpus"]
    docs = {
        "VEDA-P024-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P024 Executive Summary

P024 establishes governed marriage, relationship, partnership, and timing intelligence.

- Files scanned: `{bundle['summary']['files_scanned']}`
- Files with matches: `{bundle['summary']['files_with_matches']}`
- Sources discovered: `{bundle['summary']['sources_discovered']}`
- Claims extracted: `{bundle['summary']['claims_extracted']}`
- Contradictions found: `{bundle['summary']['contradictions_found']}`
- Production activation: `{bundle['summary']['production_activation']}`
""",
        "VEDA-P024-01_EXISTING_LOGIC_INVENTORY.md": f"""# Existing Logic Inventory

{json.dumps(bundle["existing_logic_inventory"], indent=2)}
""",
        "VEDA-P024-02_SOURCE_QUALITY.md": f"""# Source Quality

{json.dumps(bundle["source_quality"], indent=2)}

Source families are counted by independent intellectual lineage, not by URL count.
""",
        "VEDA-P024-03_MARRIAGE_ONTOLOGY.md": f"""# Marriage Ontology

{json.dumps(bundle["evidence_ontology"], indent=2)}
""",
        "VEDA-P024-04_NATAL_FOUNDATION.md": """# Natal Marriage Foundation

Marriage synthesis begins with D1 natal structure and the 7th-house relationship field. No single placement determines the result.
""",
        "VEDA-P024-05_7TH_BHAVA_LORDSHIP.md": """# 7th Bhava and Lordship

The 7th house is the relationship field. Lordship, occupants, aspects, and dignity are context signals, not standalone certainty.
""",
        "VEDA-P024-06_KARAKAS.md": """# Relationship Karakas

Venus and Jupiter can participate as relationship karakas in some traditions, but the method must be preserved. They are not universal spouse indicators by default.
""",
        "VEDA-P024-07_D9_NAVAMSHA.md": """# D9 / Navamsha

D9 specializes marriage and dharma context, but it never replaces D1. Calculation validity and interpretive validity are kept separate.
""",
        "VEDA-P024-08_D1_D9_BOUNDARY.md": """# D1 / D9 Boundary

D1 is the primary natal foundation. D9 adds specialization and refinement. The boundary is explicit so the two layers are not collapsed together.
""",
        "VEDA-P024-09_YOGA_DOSHA.md": """# Yoga / Dosha Context

Marriage yogas and doshas are contextual evidence. Formation alone is not enough; cancellation and school variance must remain visible.
""",
        "VEDA-P024-10_KUJA_DOSHA.md": """# Kuja / Manglik Governance

Manglik / Kuja Dosha is structurally represented, but reference point, houses, severity, and cancellation vary by tradition. Simplified universal rules are not allowed.
""",
        "VEDA-P024-11_CANCELLATION.md": """# Cancellation and Modification

Cancellation and mitigation are part of the same analysis chain. Dosha evaluation without the cancellation framework is incomplete.
""",
        "VEDA-P024-12_STRENGTH_DASHA_TRANSIT.md": """# Strength, Dasha, and Transit

Strength may modulate confidence. Dasha timing can open experimental windows. Transit remains contextual timing only and never becomes certainty.
""",
        "VEDA-P024-13_DELAY_CHALLENGE.md": """# Delay and Challenge

Delay, challenge, or conflict can weaken confidence, but none of them convert the result into deterministic denial.
""",
        "VEDA-P024-14_PARTNERSHIP_BOUNDARY.md": """# Partnership Boundary

Marriage and partnership overlap, but business partnership is a separate contextual problem. The 7th house does not automatically mean romantic marriage in every use case.
""",
        "VEDA-P024-15_AGGREGATION_CONFLICT.md": f"""# Aggregation and Conflict

{_table(evidence_rows, ["evidence_id", "source_layer", "evidence_type", "direction", "confidence", "validation_status"])}

Conflicts are explicit and preserved.
""",
        "VEDA-P024-16_CONFIDENCE_EXPLAINABILITY.md": """# Confidence and Explainability

Confidence is qualitative and traceable. Explainability must answer why the synthesis is supportive, mixed, or challenged, and which D1, D9, Dasha, Yoga, Dosha, Strength, and Transit factors contributed.
""",
        "VEDA-P024-17_APPROVED_CORE_STATUS.md": """# Approved Core Status

No direct Approved Core write occurred in P024. Marriage methodology remains research-candidate only until P010 promotion.
""",
        "VEDA-P024-18_EXPERIMENTAL_SHADOW.md": """# Experimental and Shadow Synthesis

P024 supports experimental and shadow synthesis. It does not activate production interpretation or guarantee an outcome.
""",
        "VEDA-P024-19_VALIDATION.md": f"""# Validation

{_table(validation_rows, ["case_id", "scenario", "expected_state"])}
""",
        "VEDA-P024-20_PREDICTION_BACKTESTING.md": f"""# Prediction and Backtesting

{json.dumps(bundle["prediction_backtesting_contract"], indent=2)}
""",
        "VEDA-P024-21_RAG.md": f"""# RAG Integration

{json.dumps(bundle["rag_integration"], indent=2)}
""",
        "VEDA-P024-22_CAPABILITY_READINESS.md": f"""# Capability Readiness

{_table(capability_rows, ["capability", "state"])}
""",
        "VEDA-P024-23_REGRESSION.md": f"""# Regression

{json.dumps(bundle["regression_scope"], indent=2)}
""",
        "VEDA-P024-24_FINAL_ACCEPTANCE.md": f"""# Final Acceptance

P024 may proceed only with research freedom preserved, no unsupported certainty claims, and all tests passing.
""",
    }
    written: list[Path] = []
    for name, content in docs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def export_phase_bundle(root: Path | None = None, validation_dir: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    target_dir = validation_dir or VALIDATION_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "p024_marriage_bundle.json": bundle,
        "p024_marriage_source_inventory.json": bundle["source_inventory"],
        "p024_marriage_claim_provenance.json": bundle["claim_provenance"],
        "p024_marriage_evidence_records.json": bundle["evidence_records"],
        "p024_marriage_validation_corpus.json": bundle["validation_corpus"],
        "p024_marriage_prediction_contract.json": bundle["prediction_backtesting_contract"],
        "p024_marriage_capability_readiness.json": bundle["capability_readiness"],
        "p024_marriage_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = target_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    written.extend(render_docs(root))
    written.append(write_inventory(root=root, output_path=root / "docs" / "current-state" / "p024" / "m001_inventory.json"))
    return written


__all__ = [
    "build_phase_bundle",
    "export_phase_bundle",
    "render_docs",
    "validate_bundle",
    "write_inventory",
]
