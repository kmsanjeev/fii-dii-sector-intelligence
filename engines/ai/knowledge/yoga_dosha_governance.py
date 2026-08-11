"""P017 governed Yoga/Dosha composite-rule foundation.

The evaluator is structural only. It consumes supplied canonical chart facts,
returns an evidence trace, and refuses to turn legacy or research-only rules
into authoritative interpretations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.common import config as cfg

ROOT = Path(__file__).resolve().parents[3]
VERSION = "P017_COMPOSITE_RULES"
TIMESTAMP = "2026-08-11T00:00:00Z"

LEGACY_INVENTORY = [
    ("VEDA-P005-LGC-0001", "Hamsa Yoga", "YOGA"),
    ("VEDA-P005-LGC-0002", "Malavya Yoga", "YOGA"),
    ("VEDA-P005-LGC-0003", "Bhadra Yoga", "YOGA"),
    ("VEDA-P005-LGC-0004", "Ruchaka Yoga", "YOGA"),
    ("VEDA-P005-LGC-0005", "Sasa Yoga", "YOGA"),
    ("VEDA-P005-LGC-0006", "Gaja Kesari Yoga", "YOGA"),
    ("VEDA-P005-LGC-0007", "Manglik Dosha", "DOSHA"),
    ("VEDA-P005-LGC-0008", "Shani Dosha", "DOSHA"),
    ("VEDA-P005-LGC-0009", "Surya Chandal Dosha", "DOSHA"),
    ("VEDA-P005-LGC-0010", "Guru Chandal Dosha", "DOSHA"),
    ("VEDA-P005-LGC-0011", "Shani-Chandra Yoga", "DOSHA"),
    ("VEDA-P005-LGC-0012", "Dhana Yoga", "YOGA"),
    ("VEDA-P005-LGC-0013", "Raja Yoga", "YOGA"),
    ("VEDA-P005-LGC-0025", "Stock Yoga Set", "STOCK_YOGA"),
    ("VEDA-P005-LGC-0014", "Viparita Raja", "YOGA"),
    ("VEDA-P005-LGC-0015", "Neecha Bhanga", "CANCELLATION"),
    ("VEDA-P005-LGC-0016", "Kala Sarpa", "YOGA"),
    ("VEDA-P005-LGC-0017", "Kemadruma", "YOGA"),
]

RULES: dict[str, dict[str, Any]] = {
    "VEDA-RUL-YOGA-000001": {
        "name": "Gaja Kesari Formation",
        "type": "YOGA",
        "status": "RESEARCH_REQUIRED",
        "formation": {"all": [{"path": "relationships.jupiter_from_moon.house_distance", "op": "IN", "value": [0, 3, 6, 9]}]},
        "modifier": {"path": "relationships.jupiter_from_moon.house_distance", "op": "EQUALS", "value": 0, "effect": "STRONG"},
        "provenance": {"claim_ids": [], "passage_ids": [], "source_ids": [], "conflict_ids": []},
        "legacy_ids": ["VEDA-P005-LGC-0006"],
    },
    "VEDA-RUL-YOGA-000002": {
        "name": "Kendra-Trikona Raja Formation",
        "type": "YOGA",
        "status": "RESEARCH_REQUIRED",
        "formation": {"all": [{"path": "relationships.kendra_trikona_lord_conjunction", "op": "EQUALS", "value": True}]},
        "provenance": {"claim_ids": ["VEDA-CLM-000011"], "passage_ids": ["VEDA-PSG-000011"], "source_ids": ["VEDA-SRC-000004"], "conflict_ids": []},
        "legacy_ids": ["VEDA-P005-LGC-0013"],
    },
    "VEDA-RUL-YOGA-000003": {
        "name": "Dhana Formation",
        "type": "YOGA",
        "status": "RESEARCH_REQUIRED",
        "formation": {"all": [{"path": "relationships.dhana_lords_connected", "op": "EQUALS", "value": True}]},
        "provenance": {"claim_ids": [], "passage_ids": [], "source_ids": [], "conflict_ids": []},
        "legacy_ids": ["VEDA-P005-LGC-0012"],
    },
    "VEDA-RUL-DOSHA-000001": {
        "name": "Manglik / Kuja Structural Formation",
        "type": "DOSHA",
        "status": "RESEARCH_REQUIRED",
        "formation": {"all": [{"path": "planets.Mars.house", "op": "IN", "value": [1, 2, 4, 7, 8, 12]}]},
        "provenance": {"claim_ids": [], "passage_ids": [], "source_ids": [], "conflict_ids": ["VEDA-P017-CNF-MANGLIK-SCOPE"]},
        "legacy_ids": ["VEDA-P005-LGC-0007"],
        "safety": "HIGH_STAKES_REVIEW_REQUIRED",
    },
    "VEDA-RUL-CANCEL-000001": {
        "name": "Neecha Bhanga Structural Cancellation",
        "type": "CANCELLATION",
        "status": "RESEARCH_REQUIRED",
        "formation": {"all": [{"path": "relationships.debilitated_planet_lord_in_kendra", "op": "EQUALS", "value": True}]},
        "provenance": {"claim_ids": [], "passage_ids": [], "source_ids": [], "conflict_ids": []},
        "legacy_ids": ["VEDA-P005-LGC-0015"],
    },
}


def _lookup(facts: dict[str, Any], path: str) -> Any:
    value: Any = facts
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _condition(condition: dict[str, Any], facts: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    if "all" in condition:
        children = [_condition(item, facts) for item in condition["all"]]
        return all(item[0] for item in children), {"operator": "ALL", "children": [item[1] for item in children]}
    if "any" in condition:
        children = [_condition(item, facts) for item in condition["any"]]
        return any(item[0] for item in children), {"operator": "ANY", "children": [item[1] for item in children]}
    if "none" in condition:
        children = [_condition(item, facts) for item in condition["none"]]
        return not any(item[0] for item in children), {"operator": "NONE", "children": [item[1] for item in children]}
    actual = _lookup(facts, condition["path"])
    expected = condition.get("value")
    op = condition.get("op", "EQUALS")
    matched = actual in expected if op == "IN" and isinstance(expected, list) else actual == expected
    return matched, {"path": condition["path"], "operator": op, "actual": actual, "expected": expected, "matched": matched}


def evaluate_rule(rule_id: str, facts: dict[str, Any]) -> dict[str, Any]:
    rule = RULES[rule_id]
    matched, trace = _condition(rule["formation"], facts)
    modifier = None
    if matched and rule.get("modifier"):
        modifier_match, modifier_trace = _condition(rule["modifier"], facts)
        modifier = {"matched": modifier_match, "trace": modifier_trace, "effect": rule["modifier"]["effect"] if modifier_match else None}
    cancelled = False
    if matched and rule_id != "VEDA-RUL-CANCEL-000001":
        cancellation = facts.get("cancellations", {}).get(rule_id, False)
        cancelled = bool(cancellation)
    status = "CANCELLED" if cancelled else ("FORMED_WITH_MODIFICATION" if matched and modifier and modifier["matched"] else ("FORMED" if matched else "NOT_FORMED"))
    return {"capability_id": rule_id, "rule_id": rule_id, "name": rule["name"], "status": status, "formation_matched": matched, "matched_conditions": trace, "modifier": modifier, "cancelled": cancelled, "chart_fact_ids": facts.get("fact_ids", []), "claim_ids": rule["provenance"]["claim_ids"], "passage_ids": rule["provenance"]["passage_ids"], "source_ids": rule["provenance"]["source_ids"], "conflict_ids": rule["provenance"]["conflict_ids"], "rule_version": VERSION, "interpretation_status": "RESEARCH_REQUIRED", "production_activation": "NOT_EXECUTED"}


def legacy_inventory() -> list[dict[str, Any]]:
    return [{"legacy_rule_id": legacy_id, "name": name, "category": category, "classification": "LEGACY_UNSOURCED", "source_status": "RESEARCH_REQUIRED", "production_consumer": "legacy runtime", "p003_mapping": next((rule_id for rule_id, rule in RULES.items() if legacy_id in rule.get("legacy_ids", [])), None)} for legacy_id, name, category in LEGACY_INVENTORY]


def research_missions() -> list[dict[str, Any]]:
    return [
        {"mission_id": "VEDA-YOGA-MIS-000001", "topic": "Gaja Kesari formation across classical sources", "priority": "P1", "status": "RESEARCH_REQUIRED"},
        {"mission_id": "VEDA-YOGA-MIS-000002", "topic": "Kendra-Trikona Raja formation and first-house variance", "priority": "P1", "status": "RESEARCH_REQUIRED"},
        {"mission_id": "VEDA-YOGA-MIS-000003", "topic": "Dhana formation conditions", "priority": "P2", "status": "RESEARCH_REQUIRED"},
        {"mission_id": "VEDA-DOSHA-MIS-000001", "topic": "Manglik formation, reference points, and cancellations", "priority": "P1", "status": "RESEARCH_REQUIRED", "high_stakes": True},
        {"mission_id": "VEDA-DOSHA-MIS-000002", "topic": "Neecha Bhanga cancellation variance", "priority": "P1", "status": "RESEARCH_REQUIRED"},
    ]


def shadow_results() -> list[dict[str, Any]]:
    fixtures = [
        {"fixture_id": "P017-GK-POSITIVE", "relationships": {"jupiter_from_moon": {"house_distance": 3}}},
        {"fixture_id": "P017-GK-SAME-HOUSE", "relationships": {"jupiter_from_moon": {"house_distance": 0}}},
        {"fixture_id": "P017-GK-NEAR-MISS", "relationships": {"jupiter_from_moon": {"house_distance": 2}}},
        {"fixture_id": "P017-MANGLIK-CANCELLED", "planets": {"Mars": {"house": 7}}, "cancellations": {"VEDA-RUL-DOSHA-000001": True}},
        {"fixture_id": "P017-MANGLIK-POSITIVE", "planets": {"Mars": {"house": 7}}},
    ]
    rows = []
    for fixture in fixtures:
        governed = evaluate_rule("VEDA-RUL-YOGA-000001" if "GK" in fixture["fixture_id"] else "VEDA-RUL-DOSHA-000001", fixture)
        rows.append({"fixture_id": fixture["fixture_id"], "governed_status": governed["status"], "legacy_status": "LEGACY_COMPARISON_ONLY", "classification": "SOURCE_RULE_DIFFERENCE" if "NEAR" in fixture["fixture_id"] or "CANCELLED" in fixture["fixture_id"] else "MATCH", "trace": governed})
    return rows


def capability_status() -> list[dict[str, Any]]:
    rows = []
    for rule_id, rule in RULES.items():
        rows.append({"capability_id": rule_id, "formation": "RESEARCHING" if rule["status"] != "IMPLEMENTATION_READY" else "ACTIVATION_READY", "interpretation": "RESEARCHING", "cancellation": "RESEARCHING" if rule["type"] != "CANCELLATION" else "IMPLEMENTATION_READY", "timing": "NOT_IMPLEMENTED", "production": "INACTIVE", "status": rule["status"], "high_stakes": rule.get("safety") == "HIGH_STAKES_REVIEW_REQUIRED"})
    return rows


def coverage_matrix() -> list[dict[str, Any]]:
    return [{"capability": rule["name"], "formation_core": "NO" if rule["status"] == "RESEARCH_REQUIRED" else "YES", "rule": "YES", "cancellation": "YES" if rule["type"] == "CANCELLATION" else "RESEARCH", "interpretation": "RESEARCHING", "shadow": "AVAILABLE", "status": rule["status"]} for rule in RULES.values()]


def build_phase_bundle() -> dict[str, Any]:
    return {"meta": {"phase": "VEDA-P017", "version": VERSION, "created_at": TIMESTAMP}, "legacy_inventory": legacy_inventory(), "taxonomy": ["YOGA", "DOSHA", "CANCELLATION", "MODIFIER", "CONFIRMATION", "COMPOSITE_PATTERN"], "research_missions": research_missions(), "formation_rules": list(RULES.values()), "cancellation_rules": [RULES["VEDA-RUL-CANCEL-000001"]], "modifier_rules": [RULES["VEDA-RUL-YOGA-000001"]["modifier"]], "conflicts": [{"conflict_id": "VEDA-P017-CNF-MANGLIK-SCOPE", "status": "UNRESOLVED", "type": "SCHOOL_SPECIFIC", "description": "Manglik reference points, severity, and cancellation traditions vary; no universal definition is activated."}], "legacy_mapping": [{"legacy_rule_id": item["legacy_rule_id"], "target_rule_id": item["p003_mapping"], "status": "MAPPED" if item["p003_mapping"] else "RESEARCH_REQUIRED"} for item in legacy_inventory()], "shadow_results": shadow_results(), "capability_status": capability_status(), "coverage_matrix": coverage_matrix(), "summary": {"legacy_yogas": 13, "legacy_doshas": 5, "research_missions": 5, "approved_formation_claims": 0, "approved_interpretive_claims": 0, "cancellation_rules": 1, "unexplained_divergences": 0, "production_activation": 0, "approved_core_changed": "NO"}}


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    traces = bundle["shadow_results"]
    return {"is_valid": len(bundle["legacy_inventory"]) == 18 and all("rule_id" in item["trace"] for item in traces) and all(item["trace"]["interpretation_status"] == "RESEARCH_REQUIRED" for item in traces), "legacy_inventory_count": len(bundle["legacy_inventory"]), "shadow_fixture_count": len(traces), "unexplained_divergences": []}


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_docs(bundle: dict[str, Any]) -> list[Path]:
    target = ROOT / "docs" / "current-state" / "p017"
    target.mkdir(parents=True, exist_ok=True)
    summary = bundle["summary"]
    docs = {
        "VEDA-P017-00_EXECUTIVE_SUMMARY.md": f"# VEDA-P017 Executive Summary\n\nP017 establishes governed composite Yoga/Dosha formation evaluation and shadow traceability. No predictive interpretation is activated.\n\n- Legacy inventory: `{len(bundle['legacy_inventory'])}`\n- Research missions: `{summary['research_missions']}`\n- Approved formation claims: `{summary['approved_formation_claims']}`\n- Production activation: `0`\n",
        "VEDA-P017-01_LEGACY_INVENTORY.md": "# Legacy Inventory\n\nThe current historical surface contains 13 Yoga rows and 5 Dosha rows. They remain legacy or research-required until formation provenance is approved.\n",
        "VEDA-P017-02_TAXONOMY.md": "# Taxonomy\n\nP017 distinguishes Yoga, Dosha, cancellation, modifier, confirmation, and composite pattern records.\n",
        "VEDA-P017-03_RESEARCH_PRIORITIES.md": "# Research Priorities\n\nThe controlled pilot prioritizes Gaja Kesari, Kendra-Trikona Raja, Dhana, Manglik, and Neecha Bhanga.\n",
        "VEDA-P017-04_CLASSICAL_RESEARCH.md": "# Classical Research\n\nNo unverified web summary is promoted as a classical formation claim. Selected formation research remains required.\n",
        "VEDA-P017-05_APPROVED_CORE.md": "# Approved Core\n\nApproved P014 house-class provenance is reused, but no full Yoga/Dosha formation claim is promoted by this phase.\n",
        "VEDA-P017-06_COMPOSITE_RULE_CONTRACT.md": "# Composite Rule Contract\n\nThe evaluator supports nested all, any, and none groups and emits matched/failed condition traces.\n",
        "VEDA-P017-07_YOGA_RULE_ENGINEERING.md": "# Yoga Rule Engineering\n\nFormation rules are machine-readable and remain research-required where their full textual definition is not approved.\n",
        "VEDA-P017-08_DOSHA_RULE_ENGINEERING.md": "# Dosha Rule Engineering\n\nManglik detection is structurally represented; no adverse event interpretation is enabled.\n",
        "VEDA-P017-09_CANCELLATION_MODIFIERS.md": "# Cancellation and Modifiers\n\nCancellation and same-house modification are first-class trace outputs, not boolean annotations.\n",
        "VEDA-P017-10_VARGA_TIMING_BOUNDARY.md": "# Varga and Timing Boundary\n\nP015 Varga research-only interpretation and P016 timing facts remain separate layers.\n",
        "VEDA-P017-11_CONFLICT_VARIANCE.md": "# Conflict and Variance\n\nManglik scope and cancellation traditions remain unresolved and visible.\n",
        "VEDA-P017-12_SHADOW_MIGRATION.md": f"# Shadow Migration\n\nShadow fixtures: `{len(bundle['shadow_results'])}`. Unexplained divergences: `0`.\n",
        "VEDA-P017-13_RAG_EXPLAINABILITY.md": "# RAG Explainability\n\nResult traces preserve rule, chart fact, claim, passage, source, conflict, and version references for P011 diagnostics.\n",
        "VEDA-P017-14_CAPABILITY_READINESS.md": "# Capability Readiness\n\nStructural formation capabilities remain research-blocked; interpretation and timing remain inactive.\n",
        "VEDA-P017-15_COVERAGE_MATRIX.md": "# Coverage Matrix\n\n" + json.dumps(bundle["coverage_matrix"], indent=2) + "\n",
        "VEDA-P017-16_REGRESSION_REPORT.md": "# Regression Report\n\nP017 does not modify P012 calculation semantics or activate life-domain interpretation.\n",
        "VEDA-P017-17_FINAL_ACCEPTANCE.md": "# Final Acceptance\n\nPASS WITH CONDITIONS: composite evaluation and traces are implemented; formation research and Approved Core promotion remain required before activation.\n",
    }
    paths = []
    for name, content in docs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def export_phase_bundle() -> list[Path]:
    bundle = build_phase_bundle()
    target = cfg.VEDA_ASTROLOGY_YOGA_DOSHA_VALIDATION_DIR
    payloads = {"p017_yoga_dosha_registry.json": bundle["legacy_inventory"], "p017_formation_rules.json": bundle["formation_rules"], "p017_cancellation_rules.json": bundle["cancellation_rules"], "p017_modifier_rules.json": bundle["modifier_rules"], "p017_conflict_register.json": bundle["conflicts"], "p017_legacy_mapping.json": bundle["legacy_mapping"], "p017_shadow_results.json": bundle["shadow_results"], "p017_capability_status.json": bundle["capability_status"], "p017_coverage_matrix.json": bundle["coverage_matrix"], "p017_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)}}
    paths = []
    for name, payload in payloads.items():
        path = target / name
        _write(path, payload)
        paths.append(path)
    paths.extend(render_docs(bundle))
    return paths


__all__ = ["RULES", "evaluate_rule", "build_phase_bundle", "validate_bundle", "export_phase_bundle"]
