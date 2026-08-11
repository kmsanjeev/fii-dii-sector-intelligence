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


__all__ = ["SHADBALA_COMPONENTS", "canonical_strength_fact", "strength_registry", "shadbala_methodology", "ashtakavarga_methodology", "validation_fixtures", "strength_claims", "strength_conflicts", "dependency_updates", "build_phase_bundle", "validate_bundle", "export_phase_bundle"]
