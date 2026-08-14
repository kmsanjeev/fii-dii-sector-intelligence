"""P023 education, learning, and knowledge governance bundle.

Phase P023 - Education & Learning Intelligence

This module builds a governed synthesis bundle for the education domain,
following the P020 (Career) and P022 (Wealth) governance patterns.

It distinguishes between:
  - educational capacity (learning ability, knowledge orientation)
  - educational outcomes (exam success, degree completion - prohibited)
  - educational timing (Dasha/transit support - experimental)

It reuses D24 (Chaturvimshamsha) facts and strength/transit contexts,
preserves implementation boundaries, and labels experimental predictions explicitly.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from engines.common import config as cfg

ROOT = Path(__file__).resolve().parents[3]
_TS = "2026-08-14T00:00:00Z"
_VERSION = "1.0.0"
_VALIDATION_DIR = cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR

_DOMAINS: list[dict[str, Any]] = [
    {
        "domain_id": "EDUCATION",
        "capability_id": "VEDA-CAP-DOMAIN-000005",
        "name": "Education, learning, and knowledge intelligence",
        "risk_class": "HIGH_STAKES",
        "required_fact_types": ["NATAL", "BHAVA", "LORDSHIP", "DIGNITY", "VARGA", "DASHA"],
        "required_capabilities": [
            "VEDA-CAP-FOUNDATION-000002",
            "VEDA-CAP-VARGA-000003",
            "VEDA-CAP-TIMING-000001",
        ],
        "optional_capabilities": [
            "VEDA-CAP-DIGNITY-000001",
            "VEDA-CAP-STRENGTH-000001",
        ],
        "high_stakes": True,
        "research_status": "RESEARCHING",
        "knowledge_status": "PARTIAL",
        "implementation_status": "SHADOW_ONLY",
        "validation_status": "PASS_WITH_CONDITIONS",
        "activation_status": "INACTIVE",
    },
    {
        "domain_id": "D24_CALCULATION",
        "capability_id": "VEDA-CAP-VARGA-000006",
        "name": "Chaturvimshamsha (D24) calculation",
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
]

_EVIDENCE_CLASSIFICATION = [
    {"source_layer": "NATAL", "evidence_type": "SUPPORTING", "status": "APPROVED_CORE"},
    {"source_layer": "4TH_BHAVA", "evidence_type": "PRIMARY", "status": "GOVERNED"},
    {"source_layer": "5TH_BHAVA", "evidence_type": "PRIMARY", "status": "GOVERNED"},
    {"source_layer": "9TH_BHAVA", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "LORDSHIP", "evidence_type": "CONTEXTUAL", "status": "GOVERNED"},
    {"source_layer": "EDUCATION_KARAKA", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "D24_EDUCATION", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "EDUCATION_YOGA", "evidence_type": "CONTEXTUAL", "status": "RESEARCH_ONLY"},
    {"source_layer": "DIGNITY", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "STRENGTH", "evidence_type": "CONTEXTUAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "DASHA", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "TRANSIT", "evidence_type": "CONTEXTUAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "APPROVED_CORE", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
]

_SAFETY_BOUNDARIES = [
    "No deterministic prediction of academic success, exam outcomes, or degree completion.",
    "No claim that a single placement determines educational potential.",
    "No guarantee of admission, scholarship, or academic performance.",
    "No suppression of conflicts or blocked evidence.",
    "No silent upgrade of unvalidated strength or transit components.",
    "No false precision in confidence reporting.",
    "No hidden graduation into Approved Core without admin approval.",
    "No activation of production education prediction.",
]

_DEPENDENCY_GRAPH = {
    "EDUCATION": [
        "VEDA-CAP-FOUNDATION-000002",
        "VEDA-CAP-VARGA-000003",
        "VEDA-CAP-TIMING-000001",
        "VEDA-CAP-VARGA-000006",
    ],
    "D24_CALCULATION": [
        "VEDA-CAP-FOUNDATION-000001",
        "VEDA-CAP-FOUNDATION-000002",
    ],
}


def registry() -> dict[str, Any]:
    """Return the education governance registry."""
    return {
        "timestamp": _TS,
        "version": _VERSION,
        "phase": "P023",
        "title": "Education & Learning Intelligence Governance",
        "domains": _DOMAINS,
        "evidence_classification": _EVIDENCE_CLASSIFICATION,
        "safety_boundaries": _SAFETY_BOUNDARIES,
        "dependency_graph": _DEPENDENCY_GRAPH,
    }


def validate() -> dict[str, Any]:
    """Validate education governance consistency."""
    reg = registry()
    issues = []

    # Check all domains are present
    domain_ids = {d["domain_id"] for d in reg["domains"]}
    if "EDUCATION" not in domain_ids:
        issues.append("Missing EDUCATION domain")
    if "D24_CALCULATION" not in domain_ids:
        issues.append("Missing D24_CALCULATION domain")

    # Check evidence classification covers required layers
    layers = {e["source_layer"] for e in reg["evidence_classification"]}
    required_layers = {
        "NATAL", "4TH_BHAVA", "5TH_BHAVA", "9TH_BHAVA", "LORDSHIP",
        "EDUCATION_KARAKA", "D24_EDUCATION", "APPROVED_CORE"
    }
    missing = required_layers - layers
    if missing:
        issues.append(f"Missing evidence layers: {missing}")

    # Check all safety boundaries are strings
    for boundary in reg["safety_boundaries"]:
        if not isinstance(boundary, str):
            issues.append(f"Invalid safety boundary: {boundary}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "registry": reg,
    }


if __name__ == "__main__":
    validation = validate()
    print(f"\nEducation Governance Validation: {'PASS' if validation['valid'] else 'FAIL'}")
    if validation["issues"]:
        for issue in validation["issues"]:
            print(f"  - {issue}")
