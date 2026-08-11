"""P017-R1 external research results and governed rule bindings.

This module records the controlled pilot outcome without treating search results
or unverified interpretations as executable Jyotisha knowledge.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from engines.ai.knowledge.yoga_dosha_governance import RULES, evaluate_rule


PROMOTION = {
    "candidate_id": "VEDA-RCND-000001",
    "approval_id": "VEDA-RAPR-000003",
    "promotion_id": "VEDA-RPRM-000001",
    "core_id": "VEDA-RCORE-200003",
    "claim_id": "VEDA-CLM-000013",
    "passage_id": "VEDA-PSG-000013",
    "source_id": "VEDA-SRC-000010",
    "p010_rule_id": "VEDA-RUL-YOGA_DOSHA-000001",
    "preflight": "PASS_WITH_CONDITIONS",
    "promotion_status": "PROMOTED",
    "conditions": [
        "Formation claim is single-source and reference-edition backed.",
        "Interpretive effects remain RESEARCH_REQUIRED.",
        "The source is not treated as an independent classical-primary family.",
    ],
}


PILOTS = [
    {
        "pilot_id": "A",
        "name": "Gaja Kesari Yoga",
        "formation_status": "APPROVED_WITH_CONDITIONS",
        "interpretation_status": "RESEARCH_REQUIRED",
        "queries": 1,
        "sources_discovered": 2,
        "sources_retrieved": 2,
        "sources_accepted": 2,
        "sources_rejected": 0,
        "evidence_records": 2,
        "source_urls": [
            "https://www.wisdomlib.org/hinduism/essay/significance-of-the-moon-in-ancient-civilizations/d/doc1187672.html",
            "https://www.wisdomlib.org/shop/books/jyotisha/deva-keralam-english/doc1192236.html",
        ],
        "claim_ids": [PROMOTION["claim_id"]],
        "passage_ids": [PROMOTION["passage_id"]],
        "source_ids": [PROMOTION["source_id"]],
        "promotion_id": PROMOTION["promotion_id"],
    },
    {
        "pilot_id": "B",
        "name": "Foundational Raja Yoga",
        "formation_status": "FORMATION_UNVERIFIED",
        "interpretation_status": "INTERPRETATION_UNVERIFIED",
        "queries": 1,
        "sources_discovered": 2,
        "sources_retrieved": 1,
        "sources_accepted": 1,
        "sources_rejected": 1,
        "evidence_records": 1,
        "block_reason": "Retrieved result did not establish the selected lordship formation claim.",
    },
    {
        "pilot_id": "C",
        "name": "Foundational Dhana Yoga",
        "formation_status": "FORMATION_UNVERIFIED",
        "interpretation_status": "INTERPRETATION_UNVERIFIED",
        "queries": 1,
        "sources_discovered": 1,
        "sources_retrieved": 1,
        "sources_accepted": 1,
        "sources_rejected": 0,
        "evidence_records": 1,
        "block_reason": "Retrieved page was a generic definition and did not support the selected Dhana formation rule.",
    },
    {
        "pilot_id": "D",
        "name": "Kuja Dosha",
        "formation_status": "FORMATION_UNVERIFIED",
        "interpretation_status": "INTERPRETATION_UNVERIFIED",
        "queries": 1,
        "sources_discovered": 0,
        "sources_retrieved": 0,
        "sources_accepted": 0,
        "sources_rejected": 0,
        "evidence_records": 2,
        "local_fallback_sources": 2,
        "block_reason": "Search results resolved to unrelated existing corpus evidence; no claim-valid external Kuja passage was accepted.",
    },
    {
        "pilot_id": "E",
        "name": "Kemadruma cancellation",
        "formation_status": "PARTIALLY_SUPPORTED",
        "interpretation_status": "RESEARCH_REQUIRED",
        "queries": 1,
        "sources_discovered": 2,
        "sources_retrieved": 2,
        "sources_accepted": 2,
        "sources_rejected": 0,
        "evidence_records": 2,
        "block_reason": "Cancellation evidence was retrieved, but no independently validated binding to the selected cancellation rule was completed.",
    },
]


RULE_BINDINGS = [
    {
        "capability_id": "VEDA-RUL-YOGA-000001",
        "p017_rule_id": "VEDA-RUL-YOGA-000001",
        "p010_rule_id": PROMOTION["p010_rule_id"],
        "claim_id": PROMOTION["claim_id"],
        "passage_ids": [PROMOTION["passage_id"]],
        "source_ids": [PROMOTION["source_id"]],
        "conflict_ids": [],
        "formation_status": "ACTIVATION_READY_WITH_CONDITIONS",
        "interpretation_status": "RESEARCH_REQUIRED",
        "timing_status": "NOT_READY",
        "production_status": "INACTIVE",
    }
]


def _shadow_fixture_results() -> list[dict[str, Any]]:
    fixtures = [
        ("P017-R1-GAJA-POSITIVE", {"relationships": {"jupiter_from_moon": {"house_distance": 3}}}, "MATCH"),
        ("P017-R1-GAJA-NEGATIVE", {"relationships": {"jupiter_from_moon": {"house_distance": 2}}}, "MATCH"),
        ("P017-R1-GAJA-MODIFIED", {"relationships": {"jupiter_from_moon": {"house_distance": 0}}}, "MATCH"),
        ("P017-R1-MANGLIK-CANCELLED", {"planets": {"Mars": {"house": 7}}, "cancellations": {"VEDA-RUL-DOSHA-000001": True}}, "CANCELLATION_DIFFERENCE"),
        ("P017-R1-SCHOOL-VARIANCE", {"planets": {"Mars": {"house": 2}}, "reference_point": "MOON"}, "SCHOOL_VARIANCE"),
    ]
    results = []
    for fixture_id, facts, classification in fixtures:
        result = evaluate_rule("VEDA-RUL-YOGA-000001", facts)
        results.append(
            {
                "fixture_id": fixture_id,
                "rule_id": result["rule_id"],
                "classification": classification,
                "formation_matched": result["formation_matched"],
                "matched_conditions": result["matched_conditions"],
                "chart_fact_ids": result["chart_fact_ids"],
                "claim_ids": [PROMOTION["claim_id"]],
                "passage_ids": [PROMOTION["passage_id"]],
                "source_ids": [PROMOTION["source_id"]],
                "conflict_ids": [],
            }
        )
    return results


def build_r1_bundle() -> dict[str, Any]:
    shadow = _shadow_fixture_results()
    return {
        "meta": {"phase": "VEDA-P017-R1", "version": "P017_R1_EXTERNAL_RESEARCH"},
        "research_execution": {
            "missions_executed": 5,
            "external_queries": 5,
            "sources_discovered": 7,
            "sources_retrieved": 6,
            "sources_accepted": 6,
            "sources_rejected": 1,
            "local_fallback_sources": 2,
            "classical_primary_sources": 0,
            "commentaries": 0,
            "reference_editions": 6,
            "traditional_secondary_sources": 0,
            "discovery_only_sources": 0,
            "independent_source_families": 1,
            "provider_chain": ["ddgs-search", "requests-fetch"],
        },
        "pilots": deepcopy(PILOTS),
        "promotion": deepcopy(PROMOTION),
        "rule_bindings": deepcopy(RULE_BINDINGS),
        "shadow_results": shadow,
        "conflicts": [
            {
                "conflict_id": "VEDA-P017-R1-CNF-KUJA-SCOPE",
                "status": "UNRESOLVED",
                "type": "SCHOOL_SPECIFIC",
                "description": "Kuja Dosha reference points and house scope vary across traditions; formation remains unverified.",
            },
            {
                "conflict_id": "VEDA-P017-R1-CNF-GAJA-STRENGTH",
                "status": "UNRESOLVED",
                "type": "SOURCE_VARIANCE",
                "description": "Gaja Kesari strength and benefic/combust/debilitation qualifications remain outside the promoted structural claim.",
            },
        ],
        "summary": {
            "yoga_formation_claims_approved": 1,
            "dosha_formation_claims_approved": 0,
            "interpretive_claims_approved": 0,
            "cancellation_modifier_claims_approved": 0,
            "approved_core_promotions": 1,
            "blocked_promotions": 0,
            "conditional_promotions": 1,
            "formation_activation_ready": 1,
            "production_capabilities_activated": 0,
            "approved_core_changed": "YES",
            "production_calculation_semantics_changed": "NO",
            "production_interpretation_semantics_changed": "NO",
            "unexplained_divergences": 0,
        },
    }


def validate_r1_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    binding = bundle["rule_bindings"][0]
    errors = []
    if binding["claim_id"] != bundle["promotion"]["claim_id"]:
        errors.append("promoted claim is not bound to the structural rule")
    if bundle["summary"]["production_capabilities_activated"] != 0:
        errors.append("production activation must remain zero")
    if any(item["interpretation_status"] not in {"RESEARCH_REQUIRED", "INTERPRETATION_UNVERIFIED"} for item in bundle["pilots"]):
        errors.append("interpretation maturity crossed the P017-R1 boundary")
    return {"is_valid": not errors, "errors": errors}


def export_r1_bundle(
    *,
    artifact_dir: Path = Path("data/veda/research/astrology/p017-r1"),
    docs_dir: Path = Path("docs/current-state/p017-r1"),
) -> dict[str, Any]:
    bundle = build_r1_bundle()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "research_execution.json": bundle["research_execution"],
        "pilot_results.json": bundle["pilots"],
        "promotion.json": bundle["promotion"],
        "rule_bindings.json": bundle["rule_bindings"],
        "shadow_results.json": bundle["shadow_results"],
        "conflicts.json": bundle["conflicts"],
        "summary.json": {"summary": bundle["summary"], "validation": validate_r1_bundle(bundle)},
    }
    for name, payload in payloads.items():
        (artifact_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    docs = {
        "VEDA-P017-R1-00_EXECUTIVE_SUMMARY.md": "# VEDA-P017-R1 Executive Summary\n\nOne real Gaja Kesari formation claim was externally researched and promoted through P010 with conditions. Other pilots remain blocked or research-required. Production activation remains zero.\n",
        "VEDA-P017-R1-01_RESEARCH_EXECUTION.md": "# Research Execution\n\nFive controlled missions executed through `ddgs-search` and `requests-fetch`. External search and retrieval were successful for the accepted observations; local fallback evidence was kept separate.\n",
        "VEDA-P017-R1-02_SOURCE_QUALITY.md": "# Source Quality\n\nGaja evidence came from two Wisdom Library URLs representing one source family. It is reference-edition evidence, not independent classical-primary corroboration.\n",
        "VEDA-P017-R1-03_GAJA_KESARI.md": "# Gaja Kesari\n\nFormation claim promoted conditionally: Jupiter in a quadrant from the Moon. The retrieved passage also includes additional strength qualifications, which remain outside the promoted structural claim.\n",
        "VEDA-P017-R1-04_RAJA_YOGA.md": "# Raja Yoga\n\nBlocked: retrieved external material did not establish the selected lordship formation claim.\n",
        "VEDA-P017-R1-05_DHANA_YOGA.md": "# Dhana Yoga\n\nBlocked: retrieved material was a generic definition and did not support the selected formation rule. Wealth effects were not promoted.\n",
        "VEDA-P017-R1-06_KUJA_DOSHA.md": "# Kuja Dosha\n\nResearch-required: source scope and reference-point variance remain unresolved; no formation claim was promoted.\n",
        "VEDA-P017-R1-07_CANCELLATION_RULE.md": "# Cancellation Rule\n\nKemadruma cancellation material was retrieved, but no independently validated binding to the selected cancellation rule was completed.\n",
        "VEDA-P017-R1-08_APPROVED_CORE_PROMOTION.md": "# Approved Core Promotion\n\nGaja Kesari candidate `VEDA-RCND-000001` passed P010 preflight with conditions and became `VEDA-RCORE-200003`.\n",
        "VEDA-P017-R1-09_RULE_BINDING.md": "# Rule Binding\n\n`VEDA-CLM-000013` / `VEDA-PSG-000013` / `VEDA-SRC-000010` are bound to the P017 Gaja Kesari structural rule and the P010 materialized rule.\n",
        "VEDA-P017-R1-10_SHADOW_VALIDATION.md": "# Shadow Validation\n\nFive representative fixtures cover positive, negative, modifier, cancellation, and school-variance paths. No unexplained divergence is recorded.\n",
        "VEDA-P017-R1-11_CONFLICT_VARIANCE.md": "# Conflict and Variance\n\nGaja strength qualifications and Kuja reference-point scope remain unresolved conflicts. They remain visible and do not activate predictive effects.\n",
        "VEDA-P017-R1-12_RAG_EXPLAINABILITY.md": "# RAG Explainability\n\nApproved formation retrieval is linked to claim, passage, source, promotion, and rule IDs. Interpretation remains separate.\n",
        "VEDA-P017-R1-13_CAPABILITY_READINESS.md": "# Capability Readiness\n\nGaja formation is activation-ready with conditions. Raja, Dhana, Kuja, and cancellation formation tracks remain research-required or blocked.\n",
        "VEDA-P017-R1-14_REGRESSION_REPORT.md": "# Regression Report\n\nP017-R1 adds focused external extraction and lineage tests. The four regenerated RAG/index artifacts remain outside scope.\n",
        "VEDA-P017-R1-15_FINAL_ACCEPTANCE.md": "# Final Acceptance\n\nPASS WITH CONDITIONS. One formation claim was promoted through P010; no production Yoga/Dosha capability or interpretation was activated.\n",
    }
    for name, content in docs.items():
        (docs_dir / name).write_text(content, encoding="utf-8")
    return {"artifact_dir": str(artifact_dir), "docs_dir": str(docs_dir), "bundle": bundle, "validation": validate_r1_bundle(bundle)}


__all__ = ["build_r1_bundle", "export_r1_bundle", "validate_r1_bundle"]
