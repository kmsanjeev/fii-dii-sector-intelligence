"""P022 wealth, income, and financial capacity governance bundle.

Phase P022 - Wealth & Financial Capacity Intelligence

This module builds a shadow-only governance bundle for the wealth-domain
synthesis layer. It distinguishes between:
  - financial capacity (resources, income support, stability)
  - investment returns (prohibited)
  - stock selection (prohibited)
  - trading action (prohibited)

It reuses canonical D2 (Hora) and relevant strength/transit contexts,
preserves implementation boundaries, and does not activate deterministic
wealth prediction or financial advice.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from engines.common import config as cfg

try:
    from engines.intelligence.kundli_engine import KundliEngine
except Exception:
    KundliEngine = None


ROOT = Path(__file__).resolve().parents[3]
_TS = "2026-08-14T00:00:00Z"
_VERSION = "1.0.0"
_VALIDATION_DIR = cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR

_DOMAINS: list[dict[str, Any]] = [
    {
        "domain_id": "WEALTH",
        "capability_id": "VEDA-CAP-DOMAIN-000004",
        "name": "Wealth, income, and financial capacity intelligence",
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
        "domain_id": "D2_CALCULATION",
        "capability_id": "VEDA-CAP-VARGA-000005",
        "name": "Hora (D2) calculation",
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
    {"source_layer": "2ND_BHAVA", "evidence_type": "PRIMARY", "status": "GOVERNED"},
    {"source_layer": "11TH_BHAVA", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "LORDSHIP", "evidence_type": "CONTEXTUAL", "status": "GOVERNED"},
    {"source_layer": "WEALTH_KARAKA", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "D2_WEALTH", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
    {"source_layer": "DHANA_YOGA", "evidence_type": "CONTEXTUAL", "status": "RESEARCH_ONLY"},
    {"source_layer": "DIGNITY", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "STRENGTH", "evidence_type": "CONTEXTUAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "DASHA", "evidence_type": "CONDITIONAL", "status": "GOVERNED"},
    {"source_layer": "TRANSIT", "evidence_type": "CONTEXTUAL", "status": "IMPLEMENTED_UNVALIDATED"},
    {"source_layer": "APPROVED_CORE", "evidence_type": "SUPPORTING", "status": "GOVERNED"},
]

_SAFETY_BOUNDARIES = [
    "No deterministic prediction of wealth, income, or financial capacity.",
    "No financial advice, investment recommendations, or trading signals.",
    "No suppression of conflicts or blocked evidence.",
    "No silent upgrade of unvalidated strength or transit components.",
    "No false precision in confidence reporting.",
    "No claim of guaranteed cash flows or returns.",
    "Dhana Yoga must be presented as contextual, not deterministic.",
]

_DEPENDENCY_GRAPH = [
    {
        "domain_id": "WEALTH",
        "required": ["NATAL", "2ND_BHAVA", "11TH_BHAVA", "LORDSHIP", "DIGNITY", "DASHA"],
        "optional": ["WEALTH_KARAKA", "D2_WEALTH", "STRENGTH", "TRANSIT"],
        "blocked": ["DETERMINISTIC_OUTCOME", "INVESTMENT_ADVICE", "STOCK_SELECTION", "TRADING_ACTION"],
        "research_only": ["DHANA_YOGA", "ML_EVIDENCE"],
    },
]


def _meta() -> dict[str, str]:
    return {
        "version": _VERSION,
        "created_at": _TS,
        "updated_at": _TS,
        "created_by": "codex",
        "updated_by": "codex",
    }


def registry() -> list[dict[str, Any]]:
    return [
        {
            **_meta(),
            "contract_version": _VERSION,
            "domains": [{**_meta(), **row} for row in _DOMAINS],
            "evidence_classification": _EVIDENCE_CLASSIFICATION,
            "dependency_graph": _DEPENDENCY_GRAPH,
            "safety_boundaries": _SAFETY_BOUNDARIES,
        }
    ]


if __name__ == "__main__":
    import json as jsonlib
    reg = registry()
    print(jsonlib.dumps(reg, ensure_ascii=False, indent=2))
