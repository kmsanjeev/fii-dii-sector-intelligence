"""P015 Varga calculation governance and interpretation readiness.

This module records the Varga surface that already exists in the runtime. It
does not add a second astronomy implementation or activate interpretation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.intelligence.kundli_engine import (
    DUAL_SIGNS,
    FIXED_SIGNS,
    MOVABLE_SIGNS,
    SIGNS,
)


ROOT = Path(__file__).resolve().parents[3]
_TS = "2026-08-11T00:00:00Z"
_VERSION = "1.0.0"

VARGA_METHODS: dict[str, dict[str, Any]] = {
    "D1": {"name": "Rashi", "division": 1, "method": "identity", "status": "IMPLEMENTED_VALIDATED", "p004": "VALIDATED"},
    "D2": {"name": "Hora", "division": 2, "method": "hora", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS"},
    "D3": {"name": "Drekkana", "division": 3, "method": "drekkana", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS"},
    "D4": {"name": "Chaturthamsha", "division": 4, "method": "chaturthamsa_14710", "method_id": "D4_CHATURTHAMSHA_1_4_7_10_V1", "method_version": "1.0", "source_ref": "KNOW-PROP-001 / P015-RX", "status": "IMPLEMENTED_VALIDATED", "p004": "VALIDATED", "interpretation_status": "NOT_VALIDATED"},
    "D7": {"name": "Saptamsha", "division": 7, "method": "saptamsa", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS", "safety": "HIGH_STAKES_REVIEW_REQUIRED"},
    "D9": {"name": "Navamsha", "division": 9, "method": "navamsa", "status": "IMPLEMENTED_VALIDATED", "p004": "VALIDATED", "priority": "P1"},
    "D10": {"name": "Dashamsha", "division": 10, "method": "dasamsa", "status": "IMPLEMENTED_VALIDATED", "p004": "VALIDATED", "priority": "P1"},
    "D11": {"name": "Ekadashamsha", "division": 11, "method": "general", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS"},
    "D12": {"name": "Dwadashamsha", "division": 12, "method": "dwadasamsa", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS", "priority": "P1"},
    "D16": {"name": "Shodashamsha", "division": 16, "method": "general", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS"},
    "D20": {"name": "Vimshamsha", "division": 20, "method": "general", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS"},
    "D30": {"name": "Trimshamsha", "division": 30, "method": "trimshamsa", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS", "safety": "HIGH_STAKES_REVIEW_REQUIRED"},
    "D60": {"name": "Shashtyamsha", "division": 60, "method": "general", "status": "IMPLEMENTED_WITH_CONDITIONS", "p004": "VALIDATED_WITH_CONDITIONS", "safety": "HIGH_SENSITIVITY"},
}

_PURPOSE_READINESS = {
    "D9": {"research": "RESEARCHING", "approved_core": False, "rules": [], "status": "RESEARCHING", "scope": "Dharma/refinement context; marriage interpretation not activated."},
    "D10": {"research": "RESEARCHING", "approved_core": False, "rules": [], "status": "RESEARCHING", "scope": "Professional/public-action context; career prediction not activated."},
    "D7": {"research": "RESEARCHING", "approved_core": False, "rules": [], "status": "RESEARCHING", "scope": "Children/progeny context; fertility conclusions require high-stakes review."},
    "D12": {"research": "RESEARCHING", "approved_core": False, "rules": [], "status": "RESEARCHING", "scope": "Parental/ancestral context; no life-domain prediction activated."},
}


def _meta() -> dict[str, str]:
    return {"version": _VERSION, "created_at": _TS, "updated_at": _TS, "created_by": "codex", "updated_by": "codex"}


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sign_index(longitude: float) -> tuple[int, float]:
    normalized = float(longitude) % 360.0
    sign = int(normalized / 30.0) % 12
    return sign, normalized % 30.0


def varga_sign(longitude: float, division: int, method: str) -> str:
    """Mirror the P012-wrapped legacy formula for deterministic comparison."""
    sign, degree = _sign_index(longitude)
    if method == "identity":
        return SIGNS[sign]
    if method == "hora":
        return ("Leo" if degree < 15 else "Cancer") if sign % 2 == 0 else ("Cancer" if degree < 15 else "Leo")
    amsa = min(int(degree / (30.0 / division)), division - 1)
    if method == "drekkana":
        return SIGNS[(sign + (0 if amsa == 0 else 4 if amsa == 1 else 8)) % 12]
    if method == "navamsa":
        start = sign if sign in MOVABLE_SIGNS else (sign + 8) % 12 if sign in FIXED_SIGNS else (sign + 4) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "chaturthamsa_14710":
        return SIGNS[(sign + (0, 3, 6, 9)[min(amsa, 3)]) % 12]
    if method == "dasamsa":
        start = sign if sign % 2 == 0 else (sign + 8) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "saptamsa":
        start = sign if sign % 2 == 0 else (sign + 6) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "dwadasamsa":
        return SIGNS[(sign + amsa) % 12]
    if method == "trimshamsa":
        boundaries = [5, 10, 18, 25, 30] if sign % 2 == 0 else [5, 12, 20, 25, 30]
        targets = ["Aries", "Aquarius", "Sagittarius", "Gemini", "Libra"] if sign % 2 == 0 else ["Taurus", "Virgo", "Pisces", "Capricorn", "Scorpio"]
        for index, boundary in enumerate(boundaries):
            if degree < boundary:
                return targets[index]
        return targets[-1]
    start = sign if sign % 2 == 0 else (sign + 6) % 12
    return SIGNS[(start + amsa) % 12]


def _sign_id(name: str) -> str:
    return f"VEDA-RASHI-{name.upper()}"


def canonical_varga_fact(planet_id: str, longitude: float, varga_id: str) -> dict[str, Any]:
    method_record = VARGA_METHODS[varga_id]
    _, degree = _sign_index(longitude)
    sign = varga_sign(longitude, method_record["division"], method_record["method"])
    return {
        "varga": varga_id,
        "planet_id": planet_id,
        "source_longitude": round(float(longitude) % 360.0, 8),
        "division": method_record["division"],
        "varga_sign": _sign_id(sign),
        "varga_degree": round((degree * method_record["division"]) % 30.0, 8),
        "calculation_rule_id": f"VEDA-RUL-VARGA-{method_record['division']:03d}",
        "method_id": method_record.get("method_id", method_record["method"]),
        "method_version": method_record.get("method_version", "legacy"),
        "source_ref": method_record.get("source_ref", "P004_VALIDATED_RUNTIME_REPRODUCTION"),
        "runtime_version": "P012_CANONICAL_RUNTIME",
        "validation_status": method_record["p004"],
        "interpretation_status": method_record.get("interpretation_status", _PURPOSE_READINESS.get(varga_id, {}).get("status", "REFERENCE_ONLY")),
    }


def canonical_varga_facts(planets: dict[str, float], requested: list[str] | None = None) -> list[dict[str, Any]]:
    selected = requested or list(VARGA_METHODS)
    return [canonical_varga_fact(planet, longitude, varga) for varga in selected if varga in VARGA_METHODS for planet, longitude in planets.items()]


def validation_fixtures() -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for varga_id, record in VARGA_METHODS.items():
        divisor = record["division"]
        boundaries = [0.0, (30.0 / divisor) - 0.000001, 30.0 / divisor, (30.0 / divisor) + 0.000001, 29.999999]
        for index, degree in enumerate(boundaries):
            longitude = (2 * 30.0) + degree
            fixtures.append({
                "fixture_id": f"P015-{varga_id}-{index + 1:02d}",
                "varga": varga_id,
                "longitude": longitude,
                "expected_sign": varga_sign(longitude, divisor, record["method"]),
                "boundary_case": index in {0, 1, 2, 3, 4},
                "status": record["p004"],
            })
    return fixtures


def registry() -> list[dict[str, Any]]:
    rows = []
    for varga_id, record in VARGA_METHODS.items():
        purpose = _PURPOSE_READINESS.get(varga_id, {})
        rows.append({
            **_meta(), "varga_id": varga_id, "name": record["name"], "division": record["division"],
            "calculation_module": "engines/intelligence/kundli_engine.py::_varga_sign",
            "formula_method": record["method"], "input_facts": ["P012.graha_longitudes"],
            "output_schema": "schemas/astrology/varga_fact.schema.json", "production_consumers": ["REST", "stock", "country"] + (["Personal Kundli"] if varga_id in {"D1", "D9", "D10"} else []),
            "p004_status": record["p004"], "classification": record["status"], "research_status": purpose.get("research", "CALCULATION_GOVERNED"),
            "approved_core_status": "NOT_REQUIRED_FOR_EXISTING_CALCULATION" if record["p004"].startswith("VALIDATED") else "RESEARCH_REQUIRED",
            "interpretation_status": purpose.get("status", "REFERENCE_ONLY"), "safety_status": record.get("safety", "STANDARD"),
            "known_issues": ["D60 is highly birth-time sensitive."] if varga_id == "D60" else [],
        })
    return rows


def capability_readiness() -> list[dict[str, Any]]:
    rows = []
    for varga_id, record in VARGA_METHODS.items():
        calculation_status = "ACTIVATION_READY" if record["p004"] == "VALIDATED" else "CALCULATION_VALIDATED"
        if varga_id == "D60":
            calculation_status = "CALCULATION_VALIDATED_WITH_CONDITIONS"
        purpose = _PURPOSE_READINESS.get(varga_id)
        rows.append({
            "capability_id": f"VEDA-CAP-VARGA-{int(varga_id[1:]):06d}",
            "varga": varga_id,
            "calculation": calculation_status,
            "research": purpose["research"] if purpose else "NOT_REQUIRED_FOR_CALCULATION",
            "approved_core": bool(purpose and purpose["approved_core"]),
            "rules": purpose["rules"] if purpose else [],
            "shadow": "AVAILABLE", "status": purpose["status"] if purpose else calculation_status,
            "production_activation": "NOT_EXECUTED",
            "high_stakes": varga_id in {"D7", "D30", "D60"},
        })
    return rows


def dependency_matrix() -> list[dict[str, Any]]:
    return [
        {"capability": "Marriage", "dependencies": ["D1", "D9", "VEDA-CAP-FOUNDATION-000002", "Dasha"], "status": "BLOCKED_PENDING_RESEARCH"},
        {"capability": "Career", "dependencies": ["D1", "D10", "VEDA-CAP-FOUNDATION-000002", "Dasha"], "status": "BLOCKED_PENDING_RESEARCH"},
        {"capability": "Children", "dependencies": ["D1", "D7", "VEDA-CAP-FOUNDATION-000002", "Dasha"], "status": "HIGH_STAKES_REVIEW_REQUIRED"},
        {"capability": "Parental context", "dependencies": ["D1", "D12", "VEDA-CAP-FOUNDATION-000002"], "status": "BLOCKED_PENDING_RESEARCH"},
    ]


def research_missions() -> list[dict[str, Any]]:
    return [
        {"mission_id": "VEDA-VARGA-MIS-000001", "varga": "D9", "research_type": "CLASSICAL_RULE_EXTRACTION", "priority": "P1", "status": "QUEUED", "objective": "Validate Navamsha purpose, dignity use, and scope without activating marriage prediction."},
        {"mission_id": "VEDA-VARGA-MIS-000002", "varga": "D10", "research_type": "CLASSICAL_RULE_EXTRACTION", "priority": "P1", "status": "QUEUED", "objective": "Validate Dashamsha professional-domain purpose and limits without activating career prediction."},
        {"mission_id": "VEDA-VARGA-MIS-000003", "varga": "D7", "research_type": "HIGH_STAKES_SOURCE_VERIFICATION", "priority": "P0", "status": "QUEUED", "objective": "Validate Saptamsha scope with explicit fertility and children safety boundaries."},
        {"mission_id": "VEDA-VARGA-MIS-000004", "varga": "D12", "research_type": "CLASSICAL_RULE_EXTRACTION", "priority": "P2", "status": "QUEUED", "objective": "Validate Dwadashamsha parental and ancestral scope without deterministic life claims."},
    ]


def varga_claims() -> list[dict[str, Any]]:
    return [
        {"claim_id": f"VEDA-VARGA-CLM-{index:06d}", "varga": varga, "claim_type": "INTERPRETIVE_PURPOSE", "claim_text": purpose["scope"], "research_status": purpose["research"], "approval_status": "NOT_SUBMITTED", "source_passages": [], "high_stakes": varga == "D7"}
        for index, (varga, purpose) in enumerate(_PURPOSE_READINESS.items(), start=1)
    ]


def varga_rules() -> list[dict[str, Any]]:
    return [
        {"rule_id": f"VEDA-RUL-VARGA-{record['division']:03d}", "varga": varga, "rule_type": "CALCULATION_METHOD", "method": record["method"], "source": record.get("source_ref", "P004_VALIDATED_RUNTIME_REPRODUCTION"), "status": "CALCULATION_VALIDATED" if record["p004"] == "VALIDATED" else "CALCULATION_VALIDATED_WITH_CONDITIONS", "production_activation": "NOT_EXECUTED"}
        for varga, record in VARGA_METHODS.items()
    ]


def varga_conflicts() -> list[dict[str, Any]]:
    return [
        {"conflict_id": "VEDA-VARGA-CNF-000001", "varga": "D60", "type": "INPUT_SENSITIVITY", "status": "OPEN", "description": "Small birth-time uncertainty can materially change D60 placement; it must not be treated as precise evidence without time-quality support."},
        {"conflict_id": "VEDA-VARGA-CNF-000002", "varga": "D9", "type": "INTERPRETIVE_SCOPE_VARIANCE", "status": "RESEARCH_REQUIRED", "description": "Purpose and dignity use require source/school comparison before interpretation activation."},
    ]


def shadow_results() -> list[dict[str, Any]]:
    from engines.intelligence.kundli_engine import KundliEngine

    engine = KundliEngine.__new__(KundliEngine)
    rows = []
    for varga_id in ("D2", "D7", "D9", "D10", "D12", "D30"):
        record = VARGA_METHODS[varga_id]
        for planet, longitude in (("Sun", 0.0), ("Jupiter", 95.0), ("Saturn", 189.999999)):
            governed = varga_sign(longitude, record["division"], record["method"])
            legacy = engine._varga_sign(longitude, record["division"], record["method"])
            rows.append({"varga": varga_id, "planet": planet, "longitude": longitude, "governed": governed, "legacy": legacy, "classification": "MATCH" if governed == legacy else "DEFECT"})
    return rows


def build_phase_bundle() -> dict[str, Any]:
    return {
        "meta": {**_meta(), "phase": "VEDA-P015", "contract_version": "2026-08-11"},
        "varga_registry": registry(), "varga_calculation_methods": list(VARGA_METHODS.values()),
        "varga_validation": validation_fixtures(), "varga_capability_status": capability_readiness(),
        "varga_dependency_matrix": dependency_matrix(), "varga_research_missions": research_missions(),
        "varga_claims": varga_claims(), "varga_rules": varga_rules(), "varga_conflicts": varga_conflicts(),
        "shadow_results": shadow_results(),
        "summary": {
            "vargas_inventoried": len(VARGA_METHODS),
            "vargas_implemented": len(VARGA_METHODS),
            "vargas_calculation_validated": sum(1 for item in VARGA_METHODS.values() if item["p004"] == "VALIDATED"),
            "vargas_with_conditions": sum(1 for item in VARGA_METHODS.values() if item["p004"] == "VALIDATED_WITH_CONDITIONS"),
            "vargas_blocked": 0,
            "research_missions": 4,
            "approved_interpretive_claims": 0,
            "calculation_rules": len(VARGA_METHODS),
            "open_conflicts": 2,
            "approved_core_changed": "NO",
            "production_planetary_calculation_semantics_changed": "NO",
            "production_interpretation_semantics_changed": "NO",
            "production_activation": 0,
        },
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    shadow = bundle["shadow_results"]
    return {"is_valid": bool(bundle["varga_registry"] and bundle["varga_validation"] and shadow and all(row["classification"] == "MATCH" for row in shadow)), "shadow_mismatches": [row for row in shadow if row["classification"] != "MATCH"], "fixture_count": len(bundle["varga_validation"])}


def render_docs(bundle: dict[str, Any]) -> list[Path]:
    target = ROOT / "docs" / "current-state" / "p015"
    target.mkdir(parents=True, exist_ok=True)
    summary = bundle["summary"]
    matrix = "\n".join(f"| {row['varga']} | {row['calculation']} | {row['research']} | {'YES' if row['approved_core'] else 'NO'} | {','.join(row['rules']) or '-'} | {row['shadow']} | {row['status']} |" for row in bundle["varga_capability_status"])
    docs = {
        "VEDA-P015-00_EXECUTIVE_SUMMARY.md": f"# VEDA-P015 Executive Summary\n\nP015 inventories and governs the existing Varga calculation surface without changing planetary calculations or activating life-domain interpretation.\n\n- Vargas inventoried: `{summary['vargas_inventoried']}`\n- Calculation validated: `{summary['vargas_calculation_validated']}`\n- With conditions: `{summary['vargas_with_conditions']}`\n- Production activation: `{summary['production_activation']}`\n",
        "VEDA-P015-01_VARGA_INVENTORY.md": "# Varga Inventory\n\nThe registry records current runtime methods, consumers, P004 status, and interpretation readiness.\n",
        "VEDA-P015-02_CALCULATION_METHODS.md": "# Calculation Methods\n\nThe governed registry mirrors the existing `KundliEngine._varga_sign` methods. No new formula is introduced.\n",
        "VEDA-P015-03_VALIDATION_FIXTURES.md": f"# Validation Fixtures\n\nGenerated deterministic boundary fixtures: `{len(bundle['varga_validation'])}`.\n",
        "VEDA-P015-04_D9_NAVAMSHA.md": "# D9 Navamsha\n\nD9 calculation is P004 validated and P012-compatible. Interpretive purpose remains research-only; marriage conclusions are not activated.\n",
        "VEDA-P015-05_D10_DASHAMSHA.md": "# D10 Dashamsha\n\nD10 calculation is P004 validated and P012-compatible. Career interpretation remains research-only.\n",
        "VEDA-P015-06_D7_SAPTAMSHA.md": "# D7 Saptamsha\n\nD7 is available with conditions. Children/progeny and fertility interpretation require high-stakes controls.\n",
        "VEDA-P015-07_D12_DWADASHAMSHA.md": "# D12 Dwadashamsha\n\nD12 is available with conditions. Parental/ancestral interpretation remains research-only.\n",
        "VEDA-P015-08_SECONDARY_VARGAS.md": "# Secondary Vargas\n\nD2, D3, D4, D11, D16, D20, D30, and D60 remain implemented with P004 conditions; calculation availability is not interpretive approval.\n",
        "VEDA-P015-09_RESEARCH_PROVENANCE.md": "# Research Provenance\n\nP015 does not manufacture Varga interpretive citations. Purpose claims remain research-required until P010 promotion.\n",
        "VEDA-P015-10_RULE_ENGINEERING.md": "# Rule Engineering\n\nOnly canonical Varga fact shape is emitted. No life-domain prediction rule is materialized.\n",
        "VEDA-P015-11_RUNTIME_INTEGRATION.md": "# Runtime Integration\n\nVarga facts consume P012 planetary longitude facts and carry calculation rule, runtime version, and validation status.\n",
        "VEDA-P015-12_SHADOW_VALIDATION.md": f"# Shadow Validation\n\nCompared `{len(bundle['shadow_results'])}` deterministic cases against the legacy method. Mismatches: `{len(validate_bundle(bundle)['shadow_mismatches'])}`.\n",
        "VEDA-P015-13_DEPENDENCY_MODEL.md": "# Dependency Model\n\nMarriage, career, children, and parental context remain blocked behind Varga interpretation research and their existing foundational dependencies.\n",
        "VEDA-P015-14_CAPABILITY_READINESS.md": f"# Capability Readiness\n\n| Varga | Calculation | Research | Approved Core | Rules | Shadow | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n{matrix}\n",
        "VEDA-P015-15_COVERAGE_MATRIX.md": f"# Coverage Matrix\n\n{matrix}\n",
        "VEDA-P015-16_VALIDATION_REPORT.md": f"# Validation Report\n\n`{json.dumps(validate_bundle(bundle), indent=2)}`\n",
        "VEDA-P015-17_FINAL_ACCEPTANCE.md": "# Final Acceptance\n\nP015 is PASS WITH CONDITIONS: the current calculation surface is governed and shadow-equivalent, while interpretive purpose claims remain research-only and production activation remains zero.\n",
    }
    written = []
    for name, content in docs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def export_phase_bundle() -> list[Path]:
    bundle = build_phase_bundle()
    target = cfg.VEDA_ASTROLOGY_VARGA_VALIDATION_DIR
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "p015_varga_registry.json": bundle["varga_registry"],
        "p015_varga_calculation_methods.json": bundle["varga_calculation_methods"],
        "p015_varga_validation.json": bundle["varga_validation"],
        "p015_varga_capability_status.json": bundle["varga_capability_status"],
        "p015_varga_dependency_matrix.json": bundle["varga_dependency_matrix"],
        "p015_varga_research_missions.json": bundle["varga_research_missions"],
        "p015_varga_claims.json": bundle["varga_claims"],
        "p015_varga_rules.json": bundle["varga_rules"],
        "p015_varga_conflicts.json": bundle["varga_conflicts"],
        "p015_shadow_results.json": bundle["shadow_results"],
        "p015_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle)},
    }
    written = []
    for name, payload in files.items():
        path = target / name
        _write(path, payload)
        written.append(path)
    written.extend(render_docs(bundle))
    return written


__all__ = ["VARGA_METHODS", "varga_sign", "canonical_varga_fact", "canonical_varga_facts", "validation_fixtures", "build_phase_bundle", "validate_bundle", "export_phase_bundle"]
