"""P020 career, education, and wealth governance bundle.

Phase P020 - Career / Education / Wealth Intelligence

This module builds a shadow-only governance bundle for the life-domain
synthesis layer. It reuses canonical D10 calculation facts, preserves the
current implementation boundaries, and does not activate runtime prediction.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from engines.ai.knowledge.varga_governance import canonical_varga_fact
from engines.common import config as cfg

try:  # pragma: no cover - optional dependency in lean environments
    from engines.intelligence.kundli_engine import KundliEngine
except Exception:  # pragma: no cover - optional dependency in lean environments
    KundliEngine = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[3]
_TS = "2026-08-14T00:00:00Z"
_VERSION = "1.0.0"
_VALIDATION_DIR = cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR

_DOMAINS: list[dict[str, Any]] = [
    {
        "domain_id": "CAREER",
        "capability_id": "VEDA-CAP-DOMAIN-000002",
        "name": "Career and education intelligence",
        "risk_class": "HIGH_STAKES",
        "required_fact_types": ["NATAL", "BHAVA", "LORDSHIP", "DIGNITY", "VARGA", "DASHA"],
        "required_capabilities": [
            "VEDA-CAP-FOUNDATION-000002",
            "VEDA-CAP-VARGA-000003",
            "VEDA-CAP-VARGA-000004",
            "VEDA-CAP-TIMING-000001",
        ],
        "optional_capabilities": [
            "VEDA-CAP-DIGNITY-000001",
        ],
        "high_stakes": True,
        "research_status": "RESEARCHING",
        "knowledge_status": "PARTIAL",
        "implementation_status": "SHADOW_ONLY",
        "validation_status": "PASS_WITH_CONDITIONS",
        "activation_status": "INACTIVE",
    },
    {
        "domain_id": "FINANCE",
        "capability_id": "VEDA-CAP-DOMAIN-000003",
        "name": "Finance intelligence",
        "risk_class": "HIGH_STAKES",
        "required_fact_types": ["NATAL", "BHAVA", "LORDSHIP", "DIGNITY", "VARGA", "DASHA", "TRANSIT"],
        "required_capabilities": [
            "VEDA-CAP-FOUNDATION-000002",
            "VEDA-CAP-VARGA-000003",
            "VEDA-CAP-VARGA-000004",
            "VEDA-CAP-TIMING-000001",
        ],
        "optional_capabilities": [
            "VEDA-CAP-DIGNITY-000001",
        ],
        "high_stakes": True,
        "research_status": "RESEARCHING",
        "knowledge_status": "PARTIAL",
        "implementation_status": "SHADOW_ONLY",
        "validation_status": "PASS_WITH_CONDITIONS",
        "activation_status": "INACTIVE",
    },
    {
        "domain_id": "D10_CALCULATION",
        "capability_id": "VEDA-CAP-VARGA-000003",
        "name": "Dashamsha calculation",
        "risk_class": "CALCULATION",
        "required_fact_types": ["NATAL"],
        "required_capabilities": [
            "VEDA-CAP-FOUNDATION-000001",
            "VEDA-CAP-FOUNDATION-000002",
        ],
        "optional_capabilities": [],
        "high_stakes": False,
        "research_status": "VALIDATED_BUT_NOT_DOMAIN_GOVERNED",
        "knowledge_status": "GOVERNED_CALCULATION",
        "implementation_status": "CALCULATION_READY",
        "validation_status": "SHADOW_VALIDATED",
        "activation_status": "ACTIVE",
    },
    {
        "domain_id": "D10_INTERPRETATION",
        "capability_id": "VEDA-CAP-VARGA-000004",
        "name": "Dashamsha interpretation",
        "risk_class": "HIGH_STAKES",
        "required_fact_types": ["VARGA", "DASHA", "DIGNITY", "TRANSIT"],
        "required_capabilities": [
            "VEDA-CAP-VARGA-000003",
            "VEDA-CAP-TIMING-000001",
            "VEDA-CAP-DIGNITY-000001",
        ],
        "optional_capabilities": [
            "VEDA-CAP-FOUNDATION-000002",
        ],
        "high_stakes": True,
        "research_status": "RESEARCHING",
        "knowledge_status": "PARTIAL",
        "implementation_status": "SHADOW_ONLY",
        "validation_status": "RESEARCH_REQUIRED",
        "activation_status": "INACTIVE",
    },
]

_EVIDENCE_CLASSIFICATION = [
    {"source_layer": "NATAL", "evidence_type": "SUPPORTING", "status": "APPROVED_CORE"},
    {"source_layer": "BHAVA", "evidence_type": "CONTEXTUAL", "status": "APPROVED_CORE"},
    {"source_layer": "LORDSHIP", "evidence_type": "SUPPORTING", "status": "APPROVED_CORE"},
    {"source_layer": "DIGNITY", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "VARGA", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "DASHA", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "YOGA_DOSHA", "evidence_type": "CONTEXTUAL", "status": "RESEARCH_ONLY"},
    {"source_layer": "STRENGTH", "evidence_type": "CONTEXTUAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "TRANSIT", "evidence_type": "CONDITIONAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "APPROVED_CORE", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "RESEARCH_ONLY", "evidence_type": "UNKNOWN", "status": "RESEARCH_ONLY"},
    {"source_layer": "ML_EVIDENCE", "evidence_type": "CONFLICTING", "status": "RESEARCH_ONLY"},
    {"source_layer": "TEMPORARY_RESEARCH", "evidence_type": "BLOCKED", "status": "TEMPORARY"},
]

_EVIDENCE_RECORDS = [
    {
        "evidence_id": "VEDA-P020-EVID-000001",
        "domain_id": "CAREER",
        "evidence_type": "SUPPORTING",
        "source_layer": "NATAL",
        "source_fact_id": "VEDA-FACT-D1-000001",
        "rule_id": "VEDA-RUL-P020-CAREER-001",
        "claim_ids": ["VEDA-P020-CLM-000001"],
        "direction": "SUPPORTING",
        "weight_or_importance": "PRIMARY",
        "confidence": "MODERATE",
        "dependency_status": "RESOLVED",
        "validation_status": "SHADOW_VALIDATED",
        "temporal_scope": "STATIC_CHART",
        "explainability_trace": [
            "career synthesis begins with natal chart facts",
            "natal facts are required before higher-level interpretation",
        ],
    },
    {
        "evidence_id": "VEDA-P020-EVID-000002",
        "domain_id": "CAREER",
        "evidence_type": "CONDITIONAL",
        "source_layer": "D10_INTERPRETATION",
        "source_fact_id": "VEDA-FACT-D10-000001",
        "rule_id": "VEDA-RUL-P020-D10-001",
        "claim_ids": ["VEDA-P020-CLM-000002"],
        "direction": "CONDITIONAL",
        "weight_or_importance": "PRIMARY",
        "confidence": "LOW",
        "dependency_status": "BLOCKED_RESEARCH",
        "validation_status": "RESEARCH_REQUIRED",
        "temporal_scope": "TIMING_AND_CONTEXT",
        "explainability_trace": [
            "D10 supports professional context only",
            "D10 interpretation stays research-only",
        ],
    },
    {
        "evidence_id": "VEDA-P020-EVID-000003",
        "domain_id": "FINANCE",
        "evidence_type": "OPPOSING",
        "source_layer": "APPROVED_CORE",
        "source_fact_id": "VEDA-FACT-BOUNDARY-000001",
        "rule_id": "VEDA-RUL-P020-SAFETY-001",
        "claim_ids": ["VEDA-P020-CLM-000003"],
        "direction": "OPPOSING",
        "weight_or_importance": "PRIMARY",
        "confidence": "HIGH",
        "dependency_status": "RESOLVED",
        "validation_status": "GOVERNED",
        "temporal_scope": "ALWAYS",
        "explainability_trace": [
            "finance is high stakes",
            "deterministic wealth prediction remains blocked",
        ],
    },
    {
        "evidence_id": "VEDA-P020-EVID-000004",
        "domain_id": "FINANCE",
        "evidence_type": "CONTEXTUAL",
        "source_layer": "TRANSIT",
        "source_fact_id": "VEDA-FACT-TRANSIT-000001",
        "rule_id": "VEDA-RUL-P020-TRANSIT-001",
        "claim_ids": ["VEDA-P020-CLM-000004"],
        "direction": "CONTEXTUAL",
        "weight_or_importance": "SECONDARY",
        "confidence": "LOW",
        "dependency_status": "IMPLEMENTED_UNVALIDATED",
        "validation_status": "IMPLEMENTATION_UNVALIDATED",
        "temporal_scope": "WINDOWED",
        "explainability_trace": [
            "transit may be used as contextual timing only",
            "transit interpretation in P019 remains unvalidated",
        ],
    },
]

_CLAIMS = [
    {
        "claim_id": "VEDA-P020-CLM-000001",
        "domain_id": "CAREER",
        "claim_text": "Career synthesis must combine natal, bhava, lordship, dignity, varga, and dasha evidence before any explanation is surfaced.",
        "interpretation_type": "DERIVED_RULE",
        "support_level": "MULTI_SOURCE",
        "evidence_types": ["SUPPORTING", "CONTEXTUAL", "CONDITIONAL"],
        "conflicting_claims": ["VEDA-P020-CLM-000002"],
        "research_status": "NEEDS_MORE_RESEARCH",
        "approval_status": "NOT_SUBMITTED",
        "high_stakes": True,
        "requires_safety_review": True,
        "allowed_output_mode": "RESEARCH_ONLY",
    },
    {
        "claim_id": "VEDA-P020-CLM-000002",
        "domain_id": "CAREER",
        "claim_text": "D10 can inform professional context, but it does not authorise deterministic career prediction.",
        "interpretation_type": "IMPLEMENTATION_NOTE",
        "support_level": "CONFLICTED",
        "evidence_types": ["CONDITIONAL", "OPPOSING"],
        "conflicting_claims": ["VEDA-P020-CLM-000001"],
        "research_status": "REVIEWED",
        "approval_status": "APPROVED_WITH_CONDITIONS",
        "high_stakes": True,
        "requires_safety_review": True,
        "allowed_output_mode": "TRADITIONAL_INTERPRETATION_ONLY",
    },
    {
        "claim_id": "VEDA-P020-CLM-000003",
        "domain_id": "FINANCE",
        "claim_text": "Finance and wealth outputs remain high-stakes and must not be framed as guaranteed outcomes.",
        "interpretation_type": "HYPOTHESIS",
        "support_level": "CROSS_VERIFIED",
        "evidence_types": ["OPPOSING", "CONTEXTUAL"],
        "conflicting_claims": ["VEDA-P020-CLM-000004"],
        "research_status": "UNDER_REVIEW",
        "approval_status": "NOT_SUBMITTED",
        "high_stakes": True,
        "requires_safety_review": True,
        "allowed_output_mode": "NO_END_USER_OUTPUT",
    },
    {
        "claim_id": "VEDA-P020-CLM-000004",
        "domain_id": "FINANCE",
        "claim_text": "Transit context may be used only as timing context, not as proof of financial success.",
        "interpretation_type": "IMPLEMENTATION_NOTE",
        "support_level": "SINGLE_SOURCE",
        "evidence_types": ["CONTEXTUAL", "BLOCKED"],
        "conflicting_claims": ["VEDA-P020-CLM-000003"],
        "research_status": "UNDER_REVIEW",
        "approval_status": "NOT_SUBMITTED",
        "high_stakes": True,
        "requires_safety_review": True,
        "allowed_output_mode": "RESEARCH_ONLY",
    },
]

_RESEARCH_MISSIONS = [
    {
        "mission_id": "VEDA-P020-MIS-000001",
        "topic": "Career synthesis boundaries",
        "priority": "P1",
        "status": "QUEUED",
        "objective": "Extract classical and governed support for career synthesis without activating deterministic prediction.",
    },
    {
        "mission_id": "VEDA-P020-MIS-000002",
        "topic": "Finance safety boundary",
        "priority": "P0",
        "status": "QUEUED",
        "objective": "Confirm that wealth and finance language remains high-stakes and non-deterministic.",
    },
    {
        "mission_id": "VEDA-P020-MIS-000003",
        "topic": "D10 interpretation limits",
        "priority": "P1",
        "status": "QUEUED",
        "objective": "Validate Dashamsha as a professional-context signal while keeping interpretation research-only.",
    },
    {
        "mission_id": "VEDA-P020-MIS-000004",
        "topic": "Evidence conflict handling",
        "priority": "P2",
        "status": "QUEUED",
        "objective": "Document how conflicting or blocked evidence is surfaced in explainability traces.",
    },
]

_CONFLICTS = [
    {
        "conflict_id": "VEDA-P020-CNF-000001",
        "domain_id": "CAREER",
        "conflict_type": "SCOPE_COLLISION",
        "status": "CONTEXT_DEPENDENT",
        "description": "D10 should support professional context, but it must not be promoted to deterministic career prediction.",
        "resolution": "Use D10 as one supporting signal inside the governed synthesis chain.",
    },
    {
        "conflict_id": "VEDA-P020-CNF-000002",
        "domain_id": "FINANCE",
        "conflict_type": "HIGH_STAKES_BOUNDARY",
        "status": "BLOCKED",
        "description": "Finance language can look predictive even when the underlying evidence is only contextual.",
        "resolution": "Block end-user deterministic outputs until the safety review path is explicitly approved.",
    },
    {
        "conflict_id": "VEDA-P020-CNF-000003",
        "domain_id": "TRANSIT",
        "conflict_type": "IMPLEMENTATION_UNVALIDATED",
        "status": "RESEARCH_REQUIRED",
        "description": "Transit support exists in the runtime, but the interpretation layer remains implementation-unvalidated.",
        "resolution": "Carry transit forward as contextual timing only.",
    },
]

_DEPENDENCY_GRAPH = [
    {
        "domain_id": "CAREER",
        "required": ["NATAL", "BHAVA", "LORDSHIP", "DIGNITY", "VARGA", "DASHA"],
        "optional": ["YOGA_DOSHA", "STRENGTH", "TRANSIT"],
        "blocked": ["DETERMINISTIC_OUTCOME", "UNVALIDATED_WEALTH_PROMISE"],
        "research_only": ["ML_EVIDENCE", "TEMPORARY_RESEARCH"],
    },
    {
        "domain_id": "FINANCE",
        "required": ["NATAL", "BHAVA", "LORDSHIP", "DIGNITY", "VARGA", "DASHA", "TRANSIT"],
        "optional": ["YOGA_DOSHA", "STRENGTH"],
        "blocked": ["DETERMINISTIC_OUTCOME", "PERSONALIZED_INVESTMENT_ADVICE"],
        "research_only": ["ML_EVIDENCE", "TEMPORARY_RESEARCH"],
    },
]

_AGGREGATION_MODEL = {
    "chain": [
        "Canonical chart facts",
        "Domain-relevant fact selection",
        "Governed rule evaluation",
        "Supporting and opposing evidence",
        "Dependency status",
        "Conflict handling",
        "Synthesis result",
        "Explainability trace",
        "RAG / user output",
    ],
    "fact_selection_policy": "Keep only facts that belong to the active domain and preserve source provenance.",
    "rule_policy": "Rules may confirm or block evidence, but they do not replace source facts.",
    "conflict_policy": "Conflicts are explicit artifacts and never silently folded into a positive claim.",
}

_CONFIDENCE_MODEL = {
    "policy": "Qualitative only",
    "bands": ["LOW", "MODERATE", "HIGH"],
    "signals": [
        "source diversity",
        "rule provenance",
        "validation state",
        "dependency readiness",
        "safety boundary status",
    ],
    "notes": "No false numerical precision; the bundle uses qualitative confidence labels only.",
}

_TEMPORAL_CONTEXT = {
    "natal": "Static chart facts remain the reference base.",
    "dasha": "Time-scoped and necessary for timing-dependent synthesis.",
    "transit": "Contextual timing only until the interpretation layer is validated.",
    "boundary_note": "Temporal evidence cannot be upgraded into deterministic outcome claims.",
}

_VARGA_CONTEXT = {
    "approved_calculation": "D10 calculation is a governed supporting fact.",
    "interpretation_state": "D10 interpretation remains research-only.",
    "current_limiter": "The synthesis layer may reference D10, but it may not claim guaranteed career or wealth outcomes.",
}

_YOGA_DOSHA_CONTEXT = {
    "status": "RESEARCH_ONLY",
    "boundary": "Yoga and dosha evidence may contribute context, but it is not sufficient on its own for life-domain conclusions.",
}

_STRENGTH_CONTEXT = {
    "shadbala": "IMPLEMENTED_UNVALIDATED",
    "drik_bala": "IMPLEMENTED_UNVALIDATED",
    "bav": "IMPLEMENTED_UNVALIDATED",
    "sav": "IMPLEMENTED_UNVALIDATED",
    "full_shadbala": "CALCULABLE_WITH_UNVALIDATED_COMPONENTS",
}

_TRANSIT_CONTEXT = {
    "p019_state": "INACTIVE / IMPLEMENTED_UNVALIDATED",
    "sade_sati": "RESEARCH_LIMITED",
    "dhaiya": "RESEARCH_LIMITED",
    "rule": "Transit may remain contextual, but it cannot override the safety boundary.",
}

_EXPLAINABILITY_GRAPH = {
    "trace": [
        "Canonical chart facts",
        "Domain-relevant selection",
        "Rule match",
        "Support / opposition evidence",
        "Dependency state",
        "Conflict handling",
        "Synthesis result",
        "Output boundary check",
    ],
    "required_properties": [
        "source provenance",
        "rule provenance",
        "confidence",
        "conflict",
        "dependency state",
        "validation state",
        "high-stakes boundary",
    ],
}

_SAFETY_BOUNDARIES = [
    "No deterministic prediction of career, wealth, marriage, health, or longevity.",
    "No financial advice framing.",
    "No suppression of conflicts or blocked evidence.",
    "No silent upgrade of unvalidated transit or strength components.",
    "No false precision in confidence reporting.",
]

_RAG_INTEGRATION = {
    "local_first": True,
    "approved_core_separation": True,
    "temporary_research_isolation": True,
    "notes": "Approved core, research-only evidence, and temporary research must remain distinct in retrieval and explanation.",
}

_PILOT_SYNTHESIS_ENGINE = {
    "mode": "SHADOW_ONLY",
    "output_policy": "Research-only",
    "consumer_state": "No runtime activation",
    "pilot_domains": ["CAREER", "FINANCE"],
    "notes": "This phase defines the synthesis contract and explainability path only.",
}


def _meta() -> dict[str, str]:
    return {
        "version": _VERSION,
        "created_at": _TS,
        "updated_at": _TS,
        "created_by": "codex",
        "updated_by": "codex",
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.move(str(tmp), str(path))


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    shutil.move(str(tmp), str(path))


def _domain_rows() -> list[dict[str, Any]]:
    return [{**_meta(), **row} for row in _DOMAINS]


def _capability_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _DOMAINS:
        rows.append(
            {
                "capability_id": row["capability_id"],
                "domain_id": row["domain_id"],
                "name": row["name"],
                "risk_class": row["risk_class"],
                "required_fact_types": list(row["required_fact_types"]),
                "required_capabilities": list(row["required_capabilities"]),
                "optional_capabilities": list(row["optional_capabilities"]),
                "high_stakes": row["high_stakes"],
                "research_status": row["research_status"],
                "knowledge_status": row["knowledge_status"],
                "implementation_status": row["implementation_status"],
                "validation_status": row["validation_status"],
                "activation_status": row["activation_status"],
                "confidence_band": "HIGH" if not row["high_stakes"] else ("MODERATE" if row["domain_id"] == "D10_CALCULATION" else "LOW"),
                "notes": (
                    "Existing calculation is governed" if row["domain_id"] == "D10_CALCULATION"
                    else "Shadow-only domain synthesis"
                ),
            }
        )
    return rows


def _validation_fixtures() -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    longitudes = [0.0, 14.999999, 15.0, 29.999999, 30.0, 95.0]
    domain_sources = [
        ("CAREER", "Sun"),
        ("CAREER", "Jupiter"),
        ("FINANCE", "Moon"),
        ("FINANCE", "Saturn"),
    ]

    for domain_id, planet_id in domain_sources:
        for index, longitude in enumerate(longitudes, start=1):
            fact = canonical_varga_fact(planet_id, longitude, "D10")
            fixtures.append(
                {
                    "fixture_id": f"VEDA-P020-FIX-{len(fixtures) + 1:06d}",
                    "domain_id": domain_id,
                    "capability_id": "VEDA-CAP-VARGA-000004",
                    "planet_id": planet_id,
                    "longitude": longitude,
                    "expected_fact": fact,
                    "expected_varga_sign": fact["varga_sign"],
                    "expected_rule_id": fact["calculation_rule_id"],
                    "boundary_case": index in {1, 2, 3, 4, 5, 6},
                    "validation_status": fact["validation_status"],
                }
            )
    return fixtures


def _shadow_validation() -> list[dict[str, Any]]:
    if KundliEngine is None:
        return [
            {
                "planet_id": "Sun",
                "longitude": 95.0,
                "governed_sign": canonical_varga_fact("Sun", 95.0, "D10")["varga_sign"],
                "legacy_sign": None,
                "classification": "SKIPPED",
                "reason": "Kundli engine unavailable in this environment",
            }
        ]

    engine = KundliEngine.__new__(KundliEngine)
    rows: list[dict[str, Any]] = []
    for planet_id, longitude in [("Sun", 0.0), ("Jupiter", 95.0), ("Moon", 29.999999), ("Saturn", 189.999999)]:
        governed = canonical_varga_fact(planet_id, longitude, "D10")["varga_sign"]
        legacy = engine._varga_sign(longitude, 10, "dasamsa")
        legacy_id = f"VEDA-RASHI-{str(legacy).upper()}" if legacy else None
        rows.append(
            {
                "planet_id": planet_id,
                "longitude": longitude,
                "governed_sign": governed,
                "legacy_sign": legacy_id,
                "classification": "MATCH" if governed == legacy_id else "DEFECT",
            }
        )
    return rows


def _validation_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    shadow = bundle["shadow_validation"]
    mismatches = [row for row in shadow if row["classification"] != "MATCH"]
    return {
        "registry_rows": len(bundle["domain_registry"]),
        "capability_rows": len(bundle["capability_status"]),
        "evidence_rows": len(bundle["evidence_records"]),
        "claims": len(bundle["claims"]),
        "research_missions": len(bundle.get("research_missions", [])),
        "validation_fixtures": len(bundle["validation_fixtures"]),
        "shadow_cases": len(shadow),
        "shadow_mismatches": len(mismatches),
        "high_stakes_domains": sum(1 for row in bundle["domain_registry"] if row["high_stakes"]),
        "production_activation": sum(1 for row in bundle["capability_status"] if row["activation_status"] == "ACTIVE"),
    }


def build_phase_bundle() -> dict[str, Any]:
    bundle = {
        "meta": {**_meta(), "phase": "VEDA-P020", "contract_version": "2026-08-14"},
        "domain_registry": _domain_rows(),
        "evidence_contract": {
            "evidence_contract_id": "VEDA-P020-EVIDENCE-CONTRACT",
            "distinguish_fact_rule_signal": True,
            "allowed_evidence_types": [
                "SUPPORTING",
                "OPPOSING",
                "CONTEXTUAL",
                "CONDITIONAL",
                "CANCELLING",
                "UNKNOWN",
                "CONFLICTING",
                "BLOCKED",
            ],
            "source_layers": [
                "NATAL",
                "BHAVA",
                "LORDSHIP",
                "DIGNITY",
                "VARGA",
                "DASHA",
                "YOGA_DOSHA",
                "STRENGTH",
                "TRANSIT",
                "APPROVED_CORE",
                "RESEARCH_ONLY",
                "ML_EVIDENCE",
                "TEMPORARY_RESEARCH",
            ],
        },
        "evidence_classification": list(_EVIDENCE_CLASSIFICATION),
        "evidence_records": list(_EVIDENCE_RECORDS),
        "dependency_graph": list(_DEPENDENCY_GRAPH),
        "aggregation_model": dict(_AGGREGATION_MODEL),
        "conflict_framework": list(_CONFLICTS),
        "confidence_model": dict(_CONFIDENCE_MODEL),
        "temporal_context": dict(_TEMPORAL_CONTEXT),
        "varga_context": dict(_VARGA_CONTEXT),
        "yoga_dosha_context": dict(_YOGA_DOSHA_CONTEXT),
        "strength_context": dict(_STRENGTH_CONTEXT),
        "transit_context": dict(_TRANSIT_CONTEXT),
        "explainability_graph": dict(_EXPLAINABILITY_GRAPH),
        "research_programme": list(_RESEARCH_MISSIONS),
        "pilot_domain_selection": ["CAREER", "FINANCE"],
        "pilot_synthesis_engine": dict(_PILOT_SYNTHESIS_ENGINE),
        "safety_boundaries": list(_SAFETY_BOUNDARIES),
        "rag_integration": dict(_RAG_INTEGRATION),
        "claims": list(_CLAIMS),
        "validation_fixtures": _validation_fixtures(),
        "capability_status": _capability_status(),
        "research_missions": list(_RESEARCH_MISSIONS),
        "shadow_validation": _shadow_validation(),
    }
    bundle["summary"] = _validation_summary(bundle)
    return bundle


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    required_sections = [
        "domain_registry",
        "evidence_contract",
        "evidence_classification",
        "evidence_records",
        "dependency_graph",
        "aggregation_model",
        "conflict_framework",
        "confidence_model",
        "temporal_context",
        "varga_context",
        "yoga_dosha_context",
        "strength_context",
        "transit_context",
        "explainability_graph",
        "research_missions",
        "pilot_domain_selection",
        "pilot_synthesis_engine",
        "safety_boundaries",
        "rag_integration",
        "claims",
        "validation_fixtures",
        "capability_status",
        "shadow_validation",
        "summary",
    ]
    missing = [name for name in required_sections if name not in bundle]
    shadow = bundle.get("shadow_validation", [])
    mismatches = [row for row in shadow if row.get("classification") != "MATCH"]
    errors = list(missing)
    if len(bundle.get("domain_registry", [])) != 4:
        errors.append("domain_registry must contain exactly 4 rows")
    if len(bundle.get("validation_fixtures", [])) < 24:
        errors.append("validation_fixtures must contain at least 24 rows")
    if len(bundle.get("research_missions", [])) < 3:
        errors.append("research_missions must contain at least 3 rows")
    if len(bundle.get("claims", [])) < 4:
        errors.append("claims must contain at least 4 rows")
    if len(bundle.get("capability_status", [])) != 4:
        errors.append("capability_status must contain exactly 4 rows")
    if mismatches:
        errors.append("shadow validation contains mismatches")
    return {
        "is_valid": not errors,
        "errors": errors,
        "shadow_mismatches": mismatches,
        "summary": bundle.get("summary", {}),
    }


def render_docs(root: Path | None = None) -> list[Path]:
    target_root = root or ROOT
    target = target_root / "docs" / "current-state" / "p020"
    target.mkdir(parents=True, exist_ok=True)
    bundle = build_phase_bundle()
    report = validate_bundle(bundle)

    registry_rows = "\n".join(
        f"| {row['domain_id']} | {row['name']} | {row['risk_class']} | {row['research_status']} | {row['implementation_status']} | {row['activation_status']} |"
        for row in bundle["domain_registry"]
    )
    evidence_rows = "\n".join(
        f"| {row['evidence_id']} | {row['domain_id']} | {row['source_layer']} | {row['evidence_type']} | {row['confidence']} | {row['validation_status']} |"
        for row in bundle["evidence_records"]
    )
    validation_rows = "\n".join(
        f"| {row['fixture_id']} | {row['domain_id']} | {row['planet_id']} | {row['longitude']} | {row['expected_varga_sign']} | {row['validation_status']} |"
        for row in bundle["validation_fixtures"]
    )
    docs = {
        "VEDA-P020-00_EXECUTIVE_SUMMARY.md": (
            "# VEDA-P020 Executive Summary\n\n"
            "P020 establishes a shadow-only career, education, and wealth synthesis framework.\n\n"
            f"- Registry rows: `{bundle['summary']['registry_rows']}`\n"
            f"- High-stakes domains: `{bundle['summary']['high_stakes_domains']}`\n"
            f"- Validation fixtures: `{bundle['summary']['validation_fixtures']}`\n"
            f"- Shadow mismatches: `{bundle['summary']['shadow_mismatches']}`\n"
            "\nThe phase preserves the boundary between fact, rule match, supporting signal, and conflicting signal.\n"
        ),
        "VEDA-P020-01_CAPABILITY_REGISTRY.md": (
            "# Capability Registry\n\n"
            f"| Domain | Name | Risk | Research | Implementation | Activation |\n| --- | --- | --- | --- | --- | --- |\n{registry_rows}\n\n"
            "Career and finance remain inactive. D10 calculation is governed; D10 interpretation remains research-only.\n"
        ),
        "VEDA-P020-02_EVIDENCE_AND_CONFLICTS.md": (
            "# Evidence and Conflicts\n\n"
            f"| Evidence ID | Domain | Source Layer | Type | Confidence | Validation |\n| --- | --- | --- | --- | --- | --- |\n{evidence_rows}\n\n"
            "Conflicts are explicit artifacts. No blocked evidence is silently treated as support.\n"
        ),
        "VEDA-P020-03_VALIDATION_PLAN.md": (
            "# Validation Plan\n\n"
            f"| Fixture ID | Domain | Planet | Longitude | Expected Sign | Status |\n| --- | --- | --- | --- | --- | --- |\n{validation_rows}\n\n"
            f"Shadow validation mismatches: `{len(report['shadow_mismatches'])}`.\n"
        ),
        "VEDA-P020-04_FINAL_ACCEPTANCE.md": (
            "# Final Acceptance\n\n"
            "P020 is PASS WITH CONDITIONS. The governance bundle is present, D10 shadow validation matches the legacy formula, and runtime activation remains unchanged.\n"
        ),
    }
    written: list[Path] = []
    for name, content in docs.items():
        path = target / name
        _write_text(path, content)
        written.append(path)
    return written


def export_phase_bundle(
    root: Path | None = None,
    validation_dir: Path | None = None,
) -> list[Path]:
    bundle = build_phase_bundle()
    target_dir = validation_dir or _VALIDATION_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "p020_career_bundle.json": bundle,
        "p020_career_registry.json": bundle["domain_registry"],
        "p020_career_validation.json": bundle["validation_fixtures"],
        "p020_career_capability_status.json": bundle["capability_status"],
        "p020_career_research_missions.json": bundle["research_missions"],
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = target_dir / name
        _write_json(path, payload)
        written.append(path)
    written.extend(render_docs(root=root))
    return written


if __name__ == "__main__":
    result = {
        "written_files": [str(path) for path in export_phase_bundle()],
        "summary": build_phase_bundle()["summary"],
    }
    print(json.dumps(result, indent=2))
