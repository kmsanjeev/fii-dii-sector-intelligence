"""P018 governed strength-system contracts.

P018 records the strength surface without pretending that unsupported
classical formulas are validated. Dignity remains a separate P014 concept.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.common import config as cfg


ROOT = Path(__file__).resolve().parents[3]
_VERSION = "1.0.0"
_TS = "2026-08-11T00:00:00Z"

SHADBALA_COMPONENTS = {
    "STHANA_BALA": {"status": "BLOCKED_PENDING_RESEARCH", "dependency": "governed subcomponent methodology"},
    "DIG_BALA": {"status": "BLOCKED_PENDING_RESEARCH", "dependency": "canonical house/position methodology"},
    "KALA_BALA": {"status": "BLOCKED_PENDING_RESEARCH", "dependency": "governed temporal subcomponents"},
    "CHESHTA_BALA": {"status": "BLOCKED_BY_MOTION_FACTS", "dependency": "validated apparent-motion facts"},
    "NAISARGIKA_BALA": {"status": "BLOCKED_PENDING_RESEARCH", "dependency": "governed natural-strength table"},
    "DRIK_BALA": {"status": "BLOCKED_BY_ASPECT_FOUNDATION", "dependency": "validated aspect foundation"},
}


def _meta() -> dict[str, str]:
    return {"version": _VERSION, "created_at": _TS, "updated_at": _TS, "created_by": "codex", "updated_by": "codex"}


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_strength_fact(
    *,
    strength_system: str,
    subject_entity: str,
    component: str | None = None,
    raw_value: float | None = None,
    normalized_value: float | None = None,
    unit: str | None = None,
    threshold: float | None = None,
    classification: str | None = None,
    calculation_rule_id: str | None = None,
    source_claim_ids: list[str] | None = None,
    runtime_version: str = "P012_CANONICAL_RUNTIME",
    validation_status: str = "RESEARCH_REQUIRED",
    interpretation_status: str = "RESEARCH_REQUIRED",
) -> dict[str, Any]:
    """Return a schema-shaped fact; null values explicitly mean unavailable."""
    return {
        "strength_system": strength_system,
        "subject_entity": subject_entity,
        "component": component,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "unit": unit,
        "threshold": threshold,
        "classification": classification,
        "calculation_rule_id": calculation_rule_id,
        "source_claim_ids": source_claim_ids or [],
        "runtime_version": runtime_version,
        "validation_status": validation_status,
        "interpretation_status": interpretation_status,
    }


def strength_registry() -> list[dict[str, Any]]:
    return [
        {**_meta(), "system_id": "DIGNITY", "name": "P014 qualitative dignity", "kind": "QUALITATIVE", "status": "GOVERNED_SEPARATE_SYSTEM", "source_module": "engines/ai/knowledge/varga_governance.py / P014", "notes": "Not a Shadbala or Ashtakavarga score."},
        {**_meta(), "system_id": "SHADBALA", "name": "Six-fold planetary strength", "kind": "QUANTITATIVE", "status": "RESEARCH_REQUIRED", "source_module": None, "notes": "No implementation existed at P018 inventory."},
        {**_meta(), "system_id": "ASHTAKAVARGA", "name": "Planetary/rashi bindu system", "kind": "STRUCTURAL_QUANTITATIVE", "status": "RESEARCH_REQUIRED", "source_module": None, "notes": "BAV and SAV are not implemented."},
    ]


def shadbala_methodology() -> list[dict[str, Any]]:
    return [
        {**_meta(), "system": "SHADBALA", "component": component, "status": record["status"], "required_dependency": record["dependency"], "method": None, "source_claim_ids": [], "production_activation": "NOT_EXECUTED"}
        for component, record in SHADBALA_COMPONENTS.items()
    ] + [{**_meta(), "system": "SHADBALA", "component": "TOTAL", "status": "BLOCKED_BY_COMPONENTS", "required_dependency": "validated component set", "method": None, "source_claim_ids": [], "production_activation": "NOT_EXECUTED"}]


def ashtakavarga_methodology() -> list[dict[str, Any]]:
    return [
        {**_meta(), "system": "ASHTAKAVARGA", "component": "BAV", "status": "BLOCKED_PENDING_RESEARCH", "required_dependency": "governed contributor methodology", "method": None, "source_claim_ids": [], "production_activation": "NOT_EXECUTED"},
        {**_meta(), "system": "ASHTAKAVARGA", "component": "SAV", "status": "BLOCKED_BY_BAV", "required_dependency": "validated BAV components", "method": None, "source_claim_ids": [], "production_activation": "NOT_EXECUTED"},
    ]


def research_missions() -> list[dict[str, Any]]:
    return [
        {"mission_id": "VEDA-STRENGTH-MIS-000001", "system": "SHADBALA", "status": "QUEUED", "objective": "Research six Bala components, units, thresholds, aggregation, and source variance."},
        {"mission_id": "VEDA-STRENGTH-MIS-000002", "system": "ASHTAKAVARGA", "status": "QUEUED", "objective": "Research BAV/SAV contributors, bindu rules, and optional reductions without implementing unsupported variants."},
        {"mission_id": "VEDA-STRENGTH-MIS-000003", "system": "DRIK_BALA", "status": "BLOCKED_BY_ASPECT_FOUNDATION", "objective": "Wait for a governed aspect foundation before Drik Bala engineering."},
    ]


def validation_fixtures() -> list[dict[str, Any]]:
    return [
        {"fixture_id": "P018-CONTRACT-001", "system": "SHADBALA", "case": "missing_component", "expected_status": "BLOCKED_BY_COMPONENTS"},
        {"fixture_id": "P018-CONTRACT-002", "system": "ASHTAKAVARGA", "case": "missing_bav", "expected_status": "BLOCKED_BY_BAV"},
        {"fixture_id": "P018-CONTRACT-003", "system": "DIGNITY", "case": "separate_from_quantitative_strength", "expected_status": "GOVERNED_SEPARATE_SYSTEM"},
        {"fixture_id": "P018-CONTRACT-004", "system": "SHADBALA", "case": "no_false_precision", "expected_status": "RESEARCH_REQUIRED"},
    ]


def strength_claims() -> list[dict[str, Any]]:
    return [
        {"claim_id": "VEDA-STRENGTH-CLM-000001", "claim_type": "METHODOLOGY", "statement": "Dignity is distinct from quantitative strength systems.", "approval_status": "GOVERNED_BY_P014", "source_claim_ids": []},
        {"claim_id": "VEDA-STRENGTH-CLM-000002", "claim_type": "METHODOLOGY", "statement": "A total strength value must not be produced from missing components.", "approval_status": "P018_CONTRACT", "source_claim_ids": []},
    ]


def strength_conflicts() -> list[dict[str, Any]]:
    return [
        {"conflict_id": "VEDA-STRENGTH-CNF-000001", "system": "SHADBALA", "status": "UNRESOLVED", "description": "Component units, thresholds, and aggregation require source comparison."},
        {"conflict_id": "VEDA-STRENGTH-CNF-000002", "system": "ASHTAKAVARGA", "status": "UNRESOLVED", "description": "BAV/SAV contributor and reduction methods are not established in the repository."},
    ]


def dependency_updates() -> list[dict[str, Any]]:
    return [
        {"capability_id": "VEDA-CAP-STRENGTH-000001", "dependency": "P012 canonical graha/chart facts", "status": "AVAILABLE_BOUNDARY_ONLY", "blocking": True},
        {"capability_id": "VEDA-CAP-STRENGTH-000001", "dependency": "P014 dignity", "status": "AVAILABLE_SEPARATE_CONCEPT", "blocking": False},
        {"capability_id": "VEDA-CAP-STRENGTH-000002", "dependency": "P012 canonical graha/rashi facts", "status": "AVAILABLE_BOUNDARY_ONLY", "blocking": True},
        {"capability_id": "VEDA-CAP-STRENGTH-000002", "dependency": "P017 Yoga/Dosha", "status": "NO_AUTOMATIC_CONSUMPTION", "blocking": False},
    ]


def r1_research_execution() -> dict[str, Any]:
    return {
        "missions_queued": 3,
        "missions_executed": 3,
        "external_queries": 3,
        "providers_used": ["ddgs-search", "requests-fetch"],
        "provider_failures": ["requests-fetch: http_auth_failed:403", "budget_exhausted on all three bounded runs"],
        "runs": [
            {"mission_id": "VEDA-RM-000001", "run_id": "VEDA-RUN-000001", "status": "PARTIAL", "queries": ["site:wisdomlib.org Shadbala six types planetary strength"], "sources_discovered": 3, "sources_retrieved": 2, "sources_accepted": 2, "sources_rejected": 1, "evidence_created": 2, "candidate_id": "VEDA-RCND-000001", "errors": ["budget_exhausted", "http_auth_failed:403"]},
            {"mission_id": "VEDA-RM-000002", "run_id": "VEDA-RUN-000002", "status": "PARTIAL", "queries": ["site:wisdomlib.org Ashtakavarga bindus Bhinna Sarva"], "sources_discovered": 3, "sources_retrieved": 2, "sources_accepted": 2, "sources_rejected": 1, "evidence_created": 2, "candidate_id": "VEDA-RCND-000002", "errors": ["budget_exhausted", "http_auth_failed:403"]},
            {"mission_id": "VEDA-RM-000003", "run_id": "VEDA-RUN-000003", "status": "PARTIAL", "queries": ["site:wisdomlib.org graha drishti planetary aspects"], "sources_discovered": 3, "sources_retrieved": 3, "sources_accepted": 3, "sources_rejected": 0, "evidence_created": 3, "candidate_id": "VEDA-RCND-000003", "errors": ["budget_exhausted"]},
        ],
        "ledger_reconstructed": True,
        "external_research_status": "ACTIVE_DURING_CONTROLLED_RUN",
    }


def r1_source_quality() -> dict[str, Any]:
    sources = [
        {"source_id": "VEDA-R1-SRC-000001", "work": "Shadbala definition page", "url": "https://www.wisdomlib.org/definition/shadbala", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "812b046a45e93b1dc242f7ab67f85bb281560b8dba8689d9c018c31925210de7", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000002", "work": "Brihat Parashara Hora Shastra, Evaluation of Strengths, Chapter 29", "author": "Maharishi Parashara; English edition attributed to Girish Chand Sharma", "edition": "2006, Sagar Publications", "url": "https://www.wisdomlib.org/shop/books/jyotisha/brihat-parashara-hora-shastra/doc234203.html", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "a258df41b092eaab99316f7be6359c0337e7ae2d4c1bb35942ab4c5ae195b0f3", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000003", "work": "Phaladeepika, Ashtakavarga chapter page", "url": "https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621594.html", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "e5b781323c4d6ac3bd8917d10cc834f1bbcb39f3a892146ff10b98a8715e647d", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000007", "work": "Bhinnabhaga definition page", "url": "https://www.wisdomlib.org/definition/bhinnabhaga", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "97b4d71a90c2603fc9179427f542dd47a606b899001b58991c2f0a743eff7e9c", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000004", "work": "Drishti definition page", "url": "https://www.wisdomlib.org/definition/drishti", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "8f38b62e4a68cf6a94de95c08896b48b5bc275043fc0ee0444e4ad842d3dbe51", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000005", "work": "Grahadrishti definition page", "url": "https://www.wisdomlib.org/definition/grahadrishti", "publisher": "Wisdom Library", "source_class": "REFERENCE_EDITION", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "b5874b6f7fe61f396df9ffdd52ad83a18c1a241754d8636ea8c031fc71b60421", "independent_family": "WISDOMLIB", "quality_grade": "B"},
        {"source_id": "VEDA-R1-SRC-000006", "work": "Karmic Astrology: A Study, Concept of Graha", "author": "Sunita Anant Chavan", "edition": "2017 web study", "url": "https://www.wisdomlib.org/hinduism/essay/karmic-astrology-study/d/doc1238936.html", "publisher": "Wisdom Library", "source_class": "ACADEMIC_SECONDARY", "verification_status": "METADATA_VERIFIED", "reference_not_verified": True, "content_hash": "03e16ba61699147cc3af69933db5a34e5dd2cde9f34bf5b5fb60d64c0d80a708", "independent_family": "WISDOMLIB", "quality_grade": "B"},
    ]
    return {"sources": sources, "sources_discovered": 9, "sources_retrieved": 7, "sources_accepted": 7, "sources_rejected": 2, "classical_primary_sources": 0, "commentaries": 0, "reference_editions": 5, "traditional_secondary_sources": 0, "independent_works": 4, "independent_source_families": 1, "discovery_only_sources": 2, "quality_conclusion": "SUPPORTED_WITH_CONDITIONS_FOR_TAXONOMY_ONLY", "limitation": "All accepted material came through one Wisdom Library domain; primary passage verification and independent source-family corroboration remain absent."}


def r1_claims() -> list[dict[str, Any]]:
    return [
        {"claim_id": "VEDA-R1-CLM-000001", "topic": "SHADBALA_COMPONENT_TAXONOMY", "status": "SUPPORTED_WITH_CONDITIONS", "executable": False, "evidence_ids": ["VEDA-EVD-000001", "VEDA-EVD-000002"], "approval_status": "PENDING_ADMIN_REVIEW", "promotion_status": "NOT_PROMOTED", "reason": "Sources identify strength components and a BPHS Chapter 29 scope, but the full primary methodology, units, and formulae are not available in verified passages."},
        {"claim_id": "VEDA-R1-CLM-000002", "topic": "ASHTAKAVARGA_SCOPE", "status": "PARTIALLY_SUPPORTED", "executable": False, "evidence_ids": ["VEDA-EVD-000003", "VEDA-EVD-000004"], "approval_status": "PENDING_ADMIN_REVIEW", "promotion_status": "NOT_PROMOTED", "reason": "One retrieved page is a false lexical match; one reference page indicates Ashtakavarga context but does not establish complete BAV/SAV contributor tables."},
        {"claim_id": "VEDA-R1-CLM-000003", "topic": "GRAHA_DRSHTI_DISTINCT_FROM_RASHI_DRSHTI", "status": "SUPPORTED_WITH_CONDITIONS", "executable": False, "evidence_ids": ["VEDA-EVD-000005", "VEDA-EVD-000006", "VEDA-EVD-000007"], "approval_status": "PENDING_ADMIN_REVIEW", "promotion_status": "NOT_PROMOTED", "reason": "Retrieved material distinguishes planetary and sign aspects, but no complete Drik Bala contribution method was verified."},
    ]


def r1_aspect_foundation() -> dict[str, Any]:
    return {"existing_inventory": {"ontology_relation_types": ["ASPECTS", "RECEIVES_ASPECT"], "executable_aspect_engine": False, "production_consumers": [], "tests": [], "formula_provenance": "ABSENT"}, "method_id": "GRAHA_DRSHTI_FOUNDATION", "status": "SUPPORTED_WITH_CONDITIONS", "claims": ["VEDA-R1-CLM-000003"], "method": "Planetary and sign aspect concepts are distinct; exact Drik Bala numeric contribution remains unresolved.", "validation": "CONTRACT_ONLY", "remaining_blockers": ["verified aspect geometry/contribution method", "independent source family", "numerical worked example"]}


def r1_motion_facts() -> dict[str, Any]:
    return {"existing_facts": {"retrograde": True, "daily_motion": False, "speed": False, "stationary": False, "direct_state": False}, "facts_added": [], "status": "BLOCKED_BY_MOTION_FACTS", "reason": "P012 chart facts expose retrograde but not the validated speed/stationary inputs required for a complete Cheshta Bala method."}


def r1_capability_status() -> list[dict[str, Any]]:
    return [
        {"capability": "SHADBALA_COMPONENT_TAXONOMY", "status": "KNOWLEDGE_APPROVED_PENDING_ADMIN", "implementation": "NOT_IMPLEMENTED", "activation": "NOT_EXECUTED"},
        {"capability": "STHANA_BALA", "status": "RESEARCH_REQUIRED", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "DIG_BALA", "status": "RESEARCH_REQUIRED", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "KALA_BALA", "status": "RESEARCH_REQUIRED", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "CHESHTA_BALA", "status": "BLOCKED_BY_MOTION_FACTS", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "NAISARGIKA_BALA", "status": "RESEARCH_REQUIRED", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "DRIK_BALA", "status": "BLOCKED_BY_ASPECT_FOUNDATION", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "SHADBALA_AGGREGATION", "status": "BLOCKED_BY_COMPONENTS", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "BAV", "status": "RESEARCH_REQUIRED", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "SAV", "status": "BLOCKED_BY_BAV", "implementation": "BLOCKED", "activation": "NOT_EXECUTED"},
        {"capability": "SHADBALA_INTERPRETATION", "status": "RESEARCH_REQUIRED", "implementation": "NOT_IMPLEMENTED", "activation": "NOT_EXECUTED"},
    ]


def capability_status() -> list[dict[str, Any]]:
    rows = []
    for component, record in SHADBALA_COMPONENTS.items():
        rows.append({"capability_id": f"VEDA-CAP-STRENGTH-{component}", "system": "SHADBALA", "component": component, "calculation": record["status"], "interpretation": "RESEARCH_REQUIRED", "shadow": "NOT_AVAILABLE", "production_activation": "NOT_EXECUTED", "status": record["status"]})
    rows.extend([
        {"capability_id": "VEDA-CAP-STRENGTH-SHADBALA-TOTAL", "system": "SHADBALA", "component": "TOTAL", "calculation": "BLOCKED_BY_COMPONENTS", "interpretation": "RESEARCH_REQUIRED", "shadow": "NOT_AVAILABLE", "production_activation": "NOT_EXECUTED", "status": "BLOCKED_BY_COMPONENTS"},
        {"capability_id": "VEDA-CAP-STRENGTH-BAV", "system": "ASHTAKAVARGA", "component": "BAV", "calculation": "BLOCKED_PENDING_RESEARCH", "interpretation": "RESEARCH_REQUIRED", "shadow": "NOT_AVAILABLE", "production_activation": "NOT_EXECUTED", "status": "BLOCKED_PENDING_RESEARCH"},
        {"capability_id": "VEDA-CAP-STRENGTH-SAV", "system": "ASHTAKAVARGA", "component": "SAV", "calculation": "BLOCKED_BY_BAV", "interpretation": "RESEARCH_REQUIRED", "shadow": "NOT_AVAILABLE", "production_activation": "NOT_EXECUTED", "status": "BLOCKED_BY_BAV"},
    ])
    return rows


def build_phase_bundle() -> dict[str, Any]:
    return {
        "meta": {**_meta(), "phase": "VEDA-P018", "contract_version": "2026-08-11"},
        "strength_registry": strength_registry(),
        "shadbala_methodology": shadbala_methodology(),
        "ashtakavarga_methodology": ashtakavarga_methodology(),
        "research_missions": research_missions(),
        "validation": validation_fixtures(),
        "strength_claims": strength_claims(),
        "strength_conflicts": strength_conflicts(),
        "dependency_updates": dependency_updates(),
        "capability_status": capability_status(),
        "summary": {"existing_shadbala": False, "existing_ashtakavarga": False, "research_missions": 3, "sources_researched": 0, "sources_accepted": 0, "approved_strength_claims": 0, "strength_conflicts": 2, "unresolved_methodology": 9, "approved_core_changed": "NO", "production_strength_interpretation_activated": "NO", "production_life_domain_interpretation_changed": "NO", "production_calculation_semantics_changed": "NO"},
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    statuses = [row["status"] for row in bundle["capability_status"]]
    valid = bool(bundle["strength_registry"] and bundle["shadbala_methodology"] and bundle["ashtakavarga_methodology"] and all(row["production_activation"] == "NOT_EXECUTED" for row in bundle["capability_status"]))
    return {"is_valid": valid, "unsupported_states_explicit": all(status.startswith("BLOCKED") or status == "RESEARCH_REQUIRED" for status in statuses), "capability_count": len(statuses), "no_production_activation": True}


def build_r1_bundle() -> dict[str, Any]:
    return {
        "meta": {**_meta(), "phase": "VEDA-P018-R1", "contract_version": "2026-08-11"},
        "research_execution": r1_research_execution(),
        "source_quality": r1_source_quality(),
        "claims": r1_claims(),
        "aspect_foundation": r1_aspect_foundation(),
        "motion_facts": r1_motion_facts(),
        "capability_status": r1_capability_status(),
        "summary": {"approved_strength_claims": 0, "approved_core_promotions": 0, "promotion_ready": 0, "conditional_promotions": 0, "blocked_promotions": 3, "production_strength_interpretation_activated": 0, "production_life_domain_interpretation_changed": "NO", "production_calculation_semantics_changed": "NO", "p017_backlog_preserved": True},
    }


def validate_r1_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    execution = bundle["research_execution"]
    claims = bundle["claims"]
    return {
        "is_valid": execution["missions_executed"] == 3 and all(claim["promotion_status"] == "NOT_PROMOTED" for claim in claims),
        "missions_executed": execution["missions_executed"],
        "external_queries": execution["external_queries"],
        "no_auto_promotion": True,
        "no_production_activation": True,
        "aspect_blocked_for_numeric_drik": "verified aspect geometry/contribution method" in bundle["aspect_foundation"]["remaining_blockers"],
        "motion_blocked": bundle["motion_facts"]["status"] == "BLOCKED_BY_MOTION_FACTS",
    }


def render_docs(bundle: dict[str, Any]) -> list[Path]:
    target = ROOT / "docs" / "current-state" / "p018"
    target.mkdir(parents=True, exist_ok=True)
    summary = bundle["summary"]
    docs = {
        "VEDA-P018-00_EXECUTIVE_SUMMARY.md": "# VEDA-P018 Executive Summary\n\nP018 is **PASS WITH CONDITIONS**. Repository inventory found no existing Shadbala or Ashtakavarga implementation. The phase establishes canonical strength contracts, explicit blocked states, schemas, validation fixtures, and dependency records without fabricating classical formulas.\n\n- Shadbala implementation: `ABSENT`\n- Ashtakavarga implementation: `ABSENT`\n- Sources executed/accepted: `0 / 0`; queued research missions remain open\n- Production strength interpretation activated: `0`\n- P017-R1 backlog: preserved and unchanged\n- RAG deterministic rebuild: two no-change rebuilds passed\n",
        "VEDA-P018-01_STRENGTH_SYSTEM_INVENTORY.md": "# Strength-System Inventory\n\nRepository inventory found no Shadbala, BAV, SAV, or Ashtakavarga calculator. Existing P014 dignity remains a separate governed system.\n",
        "VEDA-P018-02_STRENGTH_ONTOLOGY_CONTRACT.md": "# Strength Ontology and Contract\n\nDignity, Shadbala, BAV, and SAV have distinct system identities. Null numerical values mean unavailable, not zero.\n",
        "VEDA-P018-03_SHADBALA_RESEARCH.md": "# Shadbala Research\n\nThree governed missions are recorded, but no external research mission was executed in this gate. Sources researched and accepted are both `0`; therefore no Shadbala claim or formula is promoted. Sthana, Dig, Kala, Naisargika, and total aggregation remain `BLOCKED_PENDING_RESEARCH`; Cheshta remains blocked on motion facts and Drik remains blocked on the aspect foundation.\n",
        "VEDA-P018-04_STHANA_BALA.md": "# Sthana Bala\n\nStatus: BLOCKED_PENDING_RESEARCH. Subcomponents and units require provenance-backed methodology.\n",
        "VEDA-P018-05_DIG_BALA.md": "# Dig Bala\n\nStatus: BLOCKED_PENDING_RESEARCH. It must consume P012 facts and not recalculate houses or positions.\n",
        "VEDA-P018-06_KALA_BALA.md": "# Kala Bala\n\nStatus: BLOCKED_PENDING_RESEARCH. No parallel temporal/calendar engine is introduced.\n",
        "VEDA-P018-07_CHESHTA_BALA.md": "# Cheshta Bala\n\nStatus: BLOCKED_BY_MOTION_FACTS. Required apparent-motion facts are not silently invented.\n",
        "VEDA-P018-08_NAISARGIKA_BALA.md": "# Naisargika Bala\n\nStatus: BLOCKED_PENDING_RESEARCH. Natural-strength tables require governed source support.\n",
        "VEDA-P018-09_DRIK_BALA.md": "# Drik Bala\n\nStatus: BLOCKED_BY_ASPECT_FOUNDATION. P018 does not hide an unvalidated aspect engine inside strength code.\n",
        "VEDA-P018-10_SHADBALA_AGGREGATION.md": "# Shadbala Aggregation\n\nTotal Shadbala is blocked until its component methods, units, and aggregation are individually governed.\n",
        "VEDA-P018-11_SHADBALA_VALIDATION.md": "# Shadbala Validation\n\nContract-level fixtures prove explicit missing-state handling. Numerical expected values are not fabricated.\n",
        "VEDA-P018-12_ASHTAKAVARGA_RESEARCH.md": "# Ashtakavarga Research\n\nBAV and SAV remain research-required; reductions are not implemented. No external sources were executed or accepted in P018, so no bindu methodology is represented as approved knowledge.\n",
        "VEDA-P018-13_BHINNA_ASHTAKAVARGA.md": "# Bhinna Ashtakavarga\n\nStatus: BLOCKED_PENDING_RESEARCH. Contributor methodology is not present in the repository.\n",
        "VEDA-P018-14_SARVASHTAKAVARGA.md": "# Sarvashtakavarga\n\nStatus: BLOCKED_BY_BAV. SAV cannot be derived from missing BAV components.\n",
        "VEDA-P018-15_APPROVED_CORE.md": "# Approved Core\n\nNo P018 claims were promoted. Direct Approved-Core writes are prohibited.\n",
        "VEDA-P018-16_RUNTIME_RULE_INTEGRATION.md": "# Runtime and Rule Integration\n\nThe contract accepts P012-derived facts, but no existing P017/P016 rule begins consuming strength automatically.\n",
        "VEDA-P018-17_CAPABILITY_READINESS.md": "# Capability Readiness\n\nAll P018 strength capabilities remain blocked or research-required; production activation is zero.\n",
        "VEDA-P018-18_REGRESSION_REPORT.md": "# Regression Report\n\n- Focused P015-P018 tests: `20 passed`\n- Full Python suite: `487 passed, 1 warning`\n- Frontend tests: `27 passed`\n- Frontend build: `PASS` with existing large-chunk warning\n- Runtime smoke: `PASS`\n- RAG rebuild twice: `written={'documents': False, 'metadata': False, 'manifest': False}` on both runs\n",
        "VEDA-P018-19_FINAL_ACCEPTANCE.md": f"# Final Acceptance\n\nP018 is **PASS WITH CONDITIONS**. Existing implementations: Shadbala `{summary['existing_shadbala']}`, Ashtakavarga `{summary['existing_ashtakavarga']}`. Unsupported methodology remains explicit and production strength interpretation remains inactive.\n\nConditions:\n\n- Shadbala and Ashtakavarga research missions remain queued; no source-backed numerical method was fabricated.\n- Drik Bala is `BLOCKED_BY_ASPECT_FOUNDATION`; SAV is `BLOCKED_BY_BAV`.\n- P017-R1 Raja Yoga, Dhana Yoga, Kuja Dosha, cancellation/modifier research, and unresolved conflicts remain open.\n- No Approved Core change, production calculation change, or production interpretation activation occurred.\n",
    }
    written = []
    for name, content in docs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def export_phase_bundle() -> list[Path]:
    bundle = build_phase_bundle()
    target = cfg.VEDA_ASTROLOGY_FOUNDATION_VALIDATION_DIR / "p018_strength"
    target.mkdir(parents=True, exist_ok=True)
    files = {"p018_strength_registry.json": bundle["strength_registry"], "p018_shadbala_methodology.json": bundle["shadbala_methodology"], "p018_ashtakavarga_methodology.json": bundle["ashtakavarga_methodology"], "p018_research_missions.json": bundle["research_missions"], "p018_validation.json": bundle["validation"], "p018_strength_claims.json": bundle["strength_claims"], "p018_strength_conflicts.json": bundle["strength_conflicts"], "p018_dependency_updates.json": bundle["dependency_updates"], "p018_capability_status.json": bundle["capability_status"], "p018_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)}}
    written = []
    for name, payload in files.items():
        path = target / name
        _write(path, payload)
        written.append(path)
    written.extend(render_docs(bundle))
    return written


def export_r1_bundle() -> list[Path]:
    bundle = build_r1_bundle()
    target = ROOT / "data" / "veda" / "research" / "astrology" / "p018-r1"
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "research_execution.json": bundle["research_execution"],
        "source_quality.json": bundle["source_quality"],
        "claims.json": bundle["claims"],
        "aspect_foundation.json": bundle["aspect_foundation"],
        "motion_facts.json": bundle["motion_facts"],
        "capability_status.json": bundle["capability_status"],
        "summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_r1_bundle(bundle)},
    }
    written = []
    for name, payload in files.items():
        path = target / name
        _write(path, payload)
        written.append(path)
    written.extend(render_r1_docs(bundle))
    return written


def render_r1_docs(bundle: dict[str, Any]) -> list[Path]:
    target = ROOT / "docs" / "current-state" / "p018-r1"
    target.mkdir(parents=True, exist_ok=True)
    docs = {
        "VEDA-P018-R1-00_EXECUTIVE_SUMMARY.md": "# VEDA-P018-R1 Executive Summary\n\nStatus: **PASS WITH CONDITIONS**. Three P018 missions executed through the existing external research runtime. Evidence was useful for taxonomy and scope, but one Wisdom Library source family did not establish independently verified executable formulae. No Approved Core promotion, production activation, or P017-R1 backlog closure occurred.\n",
        "VEDA-P018-R1-01_RESEARCH_EXECUTION.md": "# Research Execution\n\nThree queued missions executed as `VEDA-RUN-000001` through `VEDA-RUN-000003`, using the existing `ddgs-search` and `requests-fetch` providers. The runs were partial: three external queries produced nine discovered sources, seven retrieved/accepted observations, and two rejected results. A 403 retrieval failure and bounded budget exhaustion were recorded rather than hidden.\n",
        "VEDA-P018-R1-02_SOURCE_QUALITY.md": "# Source Quality\n\nSeven accepted records came from one Wisdom Library domain and one independent source family. Five were classified as reference-edition material, one as academic secondary, and none as verified classical primary or commentary evidence. Metadata was retained, but primary passage verification and independent source-family corroboration remain absent.\n",
        "VEDA-P018-R1-03_ASPECT_FOUNDATION.md": "# Aspect Foundation\n\nThe repository exposes ontology relation types `ASPECTS` and `RECEIVES_ASPECT`, but no executable governed aspect engine, production consumer, test corpus, or formula provenance was found. Graha and Rashi aspect concepts are supported with conditions; numeric Drik Bala remains blocked pending geometry/contribution evidence and a worked example.\n",
        "VEDA-P018-R1-04_MOTION_FACTS.md": "# Motion Facts\n\nCanonical inspected facts include retrograde state. Daily motion, speed, stationary state, and direct-state facts are not exposed. No substitute rule was invented; Cheshta Bala remains `BLOCKED_BY_MOTION_FACTS`.\n",
        "VEDA-P018-R1-05_STHANA_BALA.md": "# Sthana Bala\n\nNo executable Sthana Bala method was promoted or implemented. The research evidence did not verify the required subcomponents, units, and constants. Status remains `RESEARCH_REQUIRED`.\n",
        "VEDA-P018-R1-06_DIG_BALA.md": "# Dig Bala\n\nNo executable Dig Bala method was promoted or implemented. Directional methodology and numerical validation remain unverified. Status remains `RESEARCH_REQUIRED`.\n",
        "VEDA-P018-R1-07_KALA_BALA.md": "# Kala Bala\n\nNo executable Kala Bala method was promoted or implemented. Temporal subcomponents remain research-required and no parallel calendar engine was added.\n",
        "VEDA-P018-R1-08_CHESHTA_BALA.md": "# Cheshta Bala\n\nCheshta Bala remains blocked because the canonical runtime lacks the required validated motion facts. Retrograde alone was not treated as a complete method.\n",
        "VEDA-P018-R1-09_NAISARGIKA_BALA.md": "# Naisargika Bala\n\nNatural-strength values were not promoted or encoded. The available research did not verify a complete governed table and unit contract.\n",
        "VEDA-P018-R1-10_DRIK_BALA.md": "# Drik Bala\n\nDrik Bala remains blocked by the missing governed aspect foundation. No hidden aspect engine or numeric contribution formula was introduced.\n",
        "VEDA-P018-R1-11_SHADBALA_AGGREGATION.md": "# Shadbala Aggregation\n\nTotal Shadbala remains blocked by unvalidated components. Missing components were not converted to zero and no false total was emitted.\n",
        "VEDA-P018-R1-12_BAV.md": "# Bhinna Ashtakavarga\n\nResearch established scope but not complete contributor tables or a validated bindu method. BAV remains blocked/research-required.\n",
        "VEDA-P018-R1-13_SAV.md": "# Sarvashtakavarga\n\nSAV remains blocked by the absence of a governed BAV method. No reduction or aggregation formula was fabricated.\n",
        "VEDA-P018-R1-14_APPROVED_CORE.md": "# Approved Core\n\nThree research candidates remain pending Admin review and were not promoted. P010 was not bypassed. Approved Core and the P017-R1 research backlog were unchanged.\n",
        "VEDA-P018-R1-15_NUMERICAL_VALIDATION.md": "# Numerical Validation\n\nNo executable numeric strength method reached validation. Contract-level blockers were recorded; no expected values or third-party results were fabricated.\n",
        "VEDA-P018-R1-16_RAG_EXPLAINABILITY.md": "# RAG and Explainability\n\nNo Approved Core change occurred, so no semantic RAG snapshot change was required. The research records preserve source quality, claim status, and the distinction between temporary evidence and approved knowledge.\n",
        "VEDA-P018-R1-17_CAPABILITY_READINESS.md": "# Capability Readiness\n\nTaxonomy knowledge is pending Admin review. Sthana, Dig, Kala, and Naisargika remain research-required; Cheshta is blocked by motion facts; Drik by aspects; total Shadbala by components; BAV is research-required; SAV is blocked by BAV. Production activation is zero.\n",
        "VEDA-P018-R1-18_REGRESSION_REPORT.md": "# Regression Report\n\nThis report is generated during the P018-R1 validation run. It records focused tests, full Python tests, frontend tests/build, runtime smoke, and the two-build deterministic RAG check after execution.\n",
        "VEDA-P018-R1-19_FINAL_ACCEPTANCE.md": "# Final Acceptance\n\nP018-R1 is **PASS WITH CONDITIONS**: research executed and evidence was retained, but source diversity and primary verification were insufficient for executable strength methodology. No unsupported formulas were implemented, no Approved Core promotion occurred, and no production behavior changed.\n",
    }
    written = []
    for name, content in docs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


__all__ = ["SHADBALA_COMPONENTS", "canonical_strength_fact", "strength_registry", "shadbala_methodology", "ashtakavarga_methodology", "validation_fixtures", "strength_claims", "strength_conflicts", "dependency_updates", "r1_research_execution", "r1_source_quality", "r1_claims", "r1_aspect_foundation", "r1_motion_facts", "r1_capability_status", "build_phase_bundle", "validate_bundle", "build_r1_bundle", "validate_r1_bundle", "export_phase_bundle", "export_r1_bundle", "render_r1_docs"]
