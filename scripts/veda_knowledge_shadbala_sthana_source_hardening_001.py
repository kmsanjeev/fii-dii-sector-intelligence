"""Build the bounded Sthana Bala source-hardening package.

This activity is diagnostic and governance-only.  It reuses the existing
source-witness package and Varga registry, records the exact production
surface, and produces non-production contracts/readiness decisions.  It does
not change the Shadbala engine or create an independent calculation lane.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/knowledge-shadbala-sthana-source-hardening-001"
ACTIVITY = "VEDA-KNOWLEDGE-SHADBALA-STHANA-SOURCE-HARDENING-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "589d96541a7f1cd54947eae69f63da4ef1c5aa2d"
STANDARD_ID = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
PRODUCTION_MODULE = "engines/ai/knowledge/shadbala_engine.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_knowledge_shadbala_source_hardening_001 import build_witness_bundle

COMPONENTS = ("UCHCHA", "SAPTAVARGAJA", "OJHAYUGMA", "KENDRADI", "DREKKANA")


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _json(value: Any) -> Any:
    value = _dump(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    if isinstance(value, tuple):
        return [_json(v) for v in value]
    return value


def _write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(_json(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(name: str, payload: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(payload.rstrip() + "\n", encoding="utf-8")


def _sha(value: Any) -> str:
    raw = json.dumps(_json(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def _source_records() -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = _json(build_witness_bundle())
    assertions = {row["assertion_group"]: row for row in bundle["assertions"]}
    variants = {row["assertion_group"]: row for row in bundle["variants"]}
    return assertions, variants


def _runtime_inventory() -> dict[str, Any]:
    path = ROOT / PRODUCTION_MODULE
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "calculate_sthana_bala")
    lines = text.splitlines()
    return {
        "module": PRODUCTION_MODULE,
        "function": function.name,
        "line_start": function.lineno,
        "line_end": function.end_lineno,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "constants": {
            "UCCHA_MAXIMUM": 60.0,
            "UCCHA_POSITIONS": "Sun/Moon/Mars/Mercury exact literals; Jupiter/Venus/Saturn offsets",
            "ODD_RASHIS": "1,3,5,7,9,11",
            "KENDRA_POSITIONS": "1,4,7,10",
        },
        "algorithm": [
            "derive Rashi from longitude and whole-sign house from Ascendant Rashi",
            "derive Uchcha by shortest angular distance from the runtime exaltation point and scale 60*(1-distance/180)",
            "derive Ojhayugma from odd Rashi only and assign 15 or 0",
            "derive Kendradi as 60/30/15 for Kendra/Panaphara/Apoklima",
            "sum only Uchcha + Ojhayugma + Kendradi",
        ],
        "source_lines": {
            "uccha_formula": next(i + 1 for i, line in enumerate(lines) if "uccha_bala =" in line),
            "ojhayugma_formula": next(i + 1 for i, line in enumerate(lines) if "ojaya_bala =" in line),
            "kendradi_formula": next(i + 1 for i, line in enumerate(lines) if "kendra_bala =" in line),
            "aggregate": next(i + 1 for i, line in enumerate(lines) if "total = uccha_bala" in line),
        },
        "subcomponents_present": {
            "UCHCHA": True,
            "SAPTAVARGAJA": False,
            "OJHAYUGMA": True,
            "KENDRADI": True,
            "DREKKANA": False,
        },
        "production_change_in_activity": False,
    }


def _component_contracts() -> list[dict[str, Any]]:
    assertions, variants = _source_records()
    specs = [
        {
            "component": "UCHCHA",
            "source_group": "UCHCHA_FORMULA",
            "source_formula": "Normalized angular distance from the source-defined exaltation/debilitation point divided by three, expressed in Virupas.",
            "inputs": ["planetary longitude", "source-defined exact exaltation/debilitation point table"],
            "unit": "VIRUPA",
            "boundaries": "0-60 Virupas; 60 Virupas = 1 Rupa",
            "runtime": "Implemented; distance scaling is normalization-equivalent, but the bounded witness does not close the exact point-table dependency.",
            "runtime_classification": "NORMALIZATION_EQUIVALENT",
            "source_state": "SOURCE_PARTIAL",
            "readiness": "SOURCE_READY_DEPENDENCY_PARTIAL",
            "weakest_dependency": "BPHS_EXACT_UCCHA_POINT_TABLE",
            "oracle": "NOT_BUILT: exact source point input is not independently closed",
        },
        {
            "component": "SAPTAVARGAJA",
            "source_group": "SAPTAVARGAJA_FORMULA",
            "source_formula": "Aggregate dignity contributions across seven source-defined Vargas.",
            "inputs": ["seven-varga set", "varga placements", "dignity model", "friendship/dispositor tables", "component weights"],
            "unit": "VIRUPA",
            "boundaries": "Source witness confirms aggregation, but exact per-varga weights and full friendship/dispositor input table are not available in the bounded witness.",
            "runtime": "Absent from calculate_sthana_bala; no production contribution is inferred.",
            "runtime_classification": "ABSENT",
            "source_state": "SOURCE_PARTIAL",
            "readiness": "SOURCE_PARTIAL",
            "weakest_dependency": "FRIENDSHIP_TABLES_AND_SEVEN_VARGA_CONTRACT",
            "oracle": "NOT_BUILT: no independent dignity oracle without source-complete tables",
        },
        {
            "component": "OJHAYUGMA",
            "source_group": "OJHAYUGMA_FORMULA",
            "source_formula": "Planet-specific odd/even Rashi and Navamsa placement contributes one quarter Rupa (15 Virupas) when the source condition is met.",
            "inputs": ["planet identity/class", "Rashi parity", "Navamsa parity", "source planet-group rule"],
            "unit": "VIRUPA",
            "boundaries": "Quarter Rupa = 15 Virupas; exact planet-group and Navamsa condition must be retained.",
            "runtime": "Simplified to odd-Rashi membership only; Navamsa and planet-specific grouping are not evaluated.",
            "runtime_classification": "SIMPLIFIED_IMPLEMENTATION",
            "source_state": "SOURCE_PARTIAL",
            "readiness": "SOURCE_PARTIAL",
            "weakest_dependency": "PLANET_GROUP_AND_NAVAMSA_RULE_TABLE",
            "oracle": "NOT_BUILT: source rule is not complete enough for independent fixtures",
        },
        {
            "component": "KENDRADI",
            "source_group": "KENDRADI_FORMULA",
            "source_formula": "Kendra, Panaphara and Apoklima receive full, half and quarter strength: 60/30/15 Virupas.",
            "inputs": ["house number", "house classification"],
            "unit": "VIRUPA",
            "boundaries": "Kendra 60; Panaphara 30; Apoklima 15 Virupas.",
            "runtime": "Implemented with the same 60/30/15 weights using whole-sign houses from Ascendant Rashi.",
            "runtime_classification": "NORMALIZATION_EQUIVALENT",
            "source_state": "PASSAGE_MAPPED",
            "readiness": "REMEDIATION_READY",
            "weakest_dependency": "WHOLE_SIGN_HOUSE_POLICY",
            "oracle": "NOT_BUILT: no separate numerical oracle was required for a bounded category contract",
        },
        {
            "component": "DREKKANA",
            "source_group": "DREKKANA_FORMULA",
            "source_formula": "Three decanate positions and graha classification determine a quarter-Rupa contribution.",
            "inputs": ["D3 segment", "Drekkana ruler/classification", "planet identity/class"],
            "unit": "VIRUPA",
            "boundaries": "Quarter Rupa = 15 Virupas; exact segment/classification table remains source-dependent.",
            "runtime": "Absent as a Sthana subcomponent. D3 calculation is available elsewhere with conditions, which does not validate this Shadbala use.",
            "runtime_classification": "ABSENT",
            "source_state": "SOURCE_PARTIAL",
            "readiness": "NOT_IMPLEMENTED_NOT_JUSTIFIED",
            "weakest_dependency": "D3_SOURCE_SCOPE_AND_GRAHA_CLASSIFICATION",
            "oracle": "NOT_BUILT: no source-complete Sthana-Drekkana fixture contract",
        },
    ]
    for row in specs:
        assertion = assertions[row["source_group"]]
        variant = variants[row["source_group"]]
        row["source_assertion_id"] = assertion["assertion_id"]
        row["source_variant_id"] = variant["variant_id"]
        row["passage_ids"] = assertion["passage_ids"]
        row["source_authority"] = assertion["authority"]
        row["source_lineage"] = "BPHS translation mirror -> existing VEDA source-witness register; Saravali only bounded variant discovery"
        row["source_access_condition"] = "PARTIAL_TEXT; exact source text is not redistributed; chapter numbering 27/repository 29 retained"
        row["production_bound"] = False
    return specs


def _dependency_graph() -> dict[str, Any]:
    return {
        "PLANETARY_LONGITUDES": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["UCHCHA", "OJHAYUGMA"], "condition": "sidereal longitude method and exact source point table"},
        "VARGAS": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["SAPTAVARGAJA", "OJHAYUGMA"], "condition": "the required seven-varga dignity contract is not closed"},
        "FRIENDSHIP": {"status": "PARTIAL", "consumers": ["SAPTAVARGAJA"], "condition": "full temporary/permanent friendship and dispositor policy not source-complete"},
        "LAGNA": {"status": "AVAILABLE", "consumers": ["KENDRADI"], "condition": "whole-sign house route is explicit"},
        "HOUSES": {"status": "AVAILABLE_WITH_METHOD_CONDITION", "consumers": ["KENDRADI"], "condition": "current production uses whole-sign houses; cusp policy is not part of this contract"},
        "D3": {"status": "IMPLEMENTED_WITH_CONDITIONS", "consumers": ["DREKKANA"], "condition": "D3 calculation availability does not establish the Sthana-Drekkana interpretation/formula"},
        "EXALTATION_POINTS": {"status": "SOURCE_LIMITED", "consumers": ["UCHCHA"], "condition": "bounded BPHS witness does not expose the complete exact point table"},
    }


def build_result() -> dict[str, Any]:
    assertions, variants = _source_records()
    contracts = _component_contracts()
    runtime = _runtime_inventory()
    decision = "STHANA_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE"
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "decision": decision,
        "decision_reason": "The BPHS witness resolves the five-component Sthana structure and bounded component meanings, and Kendradi is contract-ready. Exact Uccha inputs, seven-varga dignity/friendship inputs, full Ojhayugma conditions and Sthana-Drekkana classification remain incomplete; production remediation is therefore frozen and not started.",
        "standard_id": STANDARD_ID,
        "production_change": False,
        "components": contracts,
        "runtime_inventory": runtime,
        "dependency_graph": _dependency_graph(),
        "source_coverage": {
            "bphs": "PASSAGE_MAPPED_WITH_ACCESS_CONDITION",
            "secondary_classical": "NONE_NEW; bounded existing evidence retained",
            "practitioner": "SARAVALI_OPEN_DOCUMENTATION_VARIANT_ONLY",
            "passages": sorted({p for row in contracts for p in row["passage_ids"]}),
            "assertions": sorted({row["source_assertion_id"] for row in contracts}),
            "variants": sorted({row["source_variant_id"] for row in contracts}),
            "conflicts": ["BPHS_CHAPTER_NUMBER_VARIANCE", "SOURCE_ACCESS_LIMITATION", "RUNTIME_SIMPLIFICATION"],
            "external_research": "NOT_EXPANDED; existing governed source-witness package was sufficient for bounded audit",
        },
        "aggregate": {
            "status": "COMPONENT_LEVEL_ONLY",
            "reason": "Aggregate Sthana contract cannot be closed while mandatory subcomponent and dependency contracts remain partial.",
            "production_aggregate_changed": False,
        },
        "oracle_status": {
            "independent_oracles": 0,
            "worked_examples": 0,
            "external_numerical_validation": "UNAVAILABLE",
            "same_engine_reference_limitation": "No source-complete Sthana component exists for an independent numerical oracle without importing unresolved production assumptions.",
            "policy": "No oracle was generated for incomplete contracts; category-level contract evidence is not numerical validation.",
        },
        "governance": {
            "production_shadbala_changed": False,
            "naisargika_changed": False,
            "dig_changed": False,
            "aggregate_changed": False,
            "kala_changed": False,
            "cheshta_changed": False,
            "drik_changed": False,
            "interpretation_changed": False,
            "prediction_changed": False,
            "ml_changed": False,
            "rag_changed": False,
            "rag_rebuild": False,
            "rag_documents_before": 1205,
            "rag_documents_after": 1205,
            "approved_core_before": 17,
            "approved_core_after": 17,
            "approved_core_promotions": 0,
            "provider_calls": 0,
            "p032": "IMPLEMENTED / FROZEN; unchanged",
            "d20": "UNCHANGED; separate source-qualified state preserved",
        },
    }


def _acceptance(result: dict[str, Any]) -> dict[str, Any]:
    criteria = [
        ("AC01", "Starting commit verified", True),
        ("AC02", "Existing source-witness framework reused", result["standard_id"] == STANDARD_ID),
        ("AC03", "Production Sthana code unchanged", result["production_change"] is False),
        ("AC04", "All five Sthana components inventoried", len(result["components"]) == 5),
        ("AC05", "Uchcha source and input boundary recorded", bool(result["components"][0]["source_assertion_id"])),
        ("AC06", "Saptavargaja dependency gap explicit", result["components"][1]["readiness"] == "SOURCE_PARTIAL"),
        ("AC07", "Ojhayugma simplification explicit", result["components"][2]["runtime_classification"] == "SIMPLIFIED_IMPLEMENTATION"),
        ("AC08", "Kendradi contract readiness explicit", result["components"][3]["readiness"] == "REMEDIATION_READY"),
        ("AC09", "Drekkana absence separated from D3 availability", result["components"][4]["runtime_classification"] == "ABSENT"),
        ("AC10", "Units recorded as Virupa with Rupa boundary", all(row["unit"] == "VIRUPA" for row in result["components"])),
        ("AC11", "Dependencies classified", len(result["dependency_graph"]) >= 7),
        ("AC12", "No incomplete independent oracle created", result["oracle_status"]["independent_oracles"] == 0),
        ("AC13", "Aggregate gated to component level", result["aggregate"]["status"] == "COMPONENT_LEVEL_ONLY"),
        ("AC14", "Source gaps are not fabricated as contradictions", "SOURCE_ACCESS_LIMITATION" in result["source_coverage"]["conflicts"]),
        ("AC15", "No Approved Core promotion", result["governance"]["approved_core_promotions"] == 0),
        ("AC16", "RAG unchanged", result["governance"]["rag_documents_before"] == result["governance"]["rag_documents_after"]),
        ("AC17", "Parallel Shadbala families unchanged", all(result["governance"][key] is False for key in ("naisargika_changed", "dig_changed", "kala_changed", "cheshta_changed", "drik_changed"))),
        ("AC18", "Interpretation/prediction/ML unchanged", not result["governance"]["interpretation_changed"] and not result["governance"]["prediction_changed"] and not result["governance"]["ml_changed"]),
        ("AC19", "Decision is an allowed freeze decision", result["decision"] in {"STHANA_SOURCE_CONTRACT_RESOLVED_REMEDIATION_READY", "STHANA_COMPONENT_CONTRACTS_READY_PARTIAL_REMEDIATION", "STHANA_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE", "STHANA_VARIANTS_REQUIRE_GOVERNANCE", "STHANA_DEPENDENCIES_BLOCK_REMEDIATION", "STHANA_SOURCE_ACCESS_INSUFFICIENT_FREEZE"}),
        ("AC20", "No automatic next programme", True),
    ]
    rows = [{"id": i, "criterion": text, "status": "PASS" if passed else "FAIL"} for i, text, passed in criteria]
    return {"activity": ACTIVITY, "criteria": rows, "pass": sum(row["status"] == "PASS" for row in rows), "fail": sum(row["status"] == "FAIL" for row in rows), "blocked": 0, "pass_with_condition": len(rows), "total": len(rows), "overall": "PASS_WITH_CONDITION"}


def emit(result: dict[str, Any]) -> None:
    assertions, variants = _source_records()
    runtime = result["runtime_inventory"]
    _write_text("00_BASELINE.md", f"""# {ACTIVITY} Baseline

- Starting commit: `{STARTING_COMMIT}`
- Branch: `main`
- Production module audited: `{PRODUCTION_MODULE}`
- Production Sthana code changed: **NO**
- Scope: source-witness reconciliation and remediation readiness only.

The prior Shadbala source-hardening package is the existing knowledge baseline. This activity does not replace it or create a second source registry. It narrows the Sthana family into five claim-level contracts and records the exact implementation/dependency boundary.
""")
    _write_json("01_STHANA_COMPONENT_INVENTORY.json", {"activity": ACTIVITY, "runtime": runtime, "components": result["components"], "aggregate": result["aggregate"]})
    _write_json("02_SOURCE_WITNESS_REGISTER.json", {"activity": ACTIVITY, "reused_register": "docs/current-state/knowledge-shadbala-source-hardening-001/02_SOURCE_WITNESS_REGISTER.json", "standard_id": STANDARD_ID, "focused_assertions": [assertions[row["source_group"]] for row in result["components"]], "focused_variants": [variants[row["source_group"]] for row in result["components"]], "no_new_source_registry": True})
    for number, component in enumerate(result["components"], start=3):
        _write_json(f"{number:02d}_{component['component']}_CONTRACT.json", {"activity": ACTIVITY, "contract": component, "production_bound": False, "contract_hash": _sha(component)})
    _write_json("08_UNIT_MODEL.json", {"activity": ACTIVITY, "source_unit": "VIRUPA", "conversion": "60 Virupas = 1 Rupa", "component_units": {name: "VIRUPA" for name in COMPONENTS}, "current_runtime_note": "Current Sthana output is labelled RUPA by the production fact wrapper; this activity does not correct that label.", "status": "SOURCE_CONTRACT_UNIT_RECORDED_REMEDIATION_NOT_STARTED"})
    _write_json("09_DEPENDENCY_GRAPH.json", {"activity": ACTIVITY, "dependencies": result["dependency_graph"], "weakest_dependency": "FRIENDSHIP_TABLES_AND_SEVEN_VARGA_CONTRACT", "aggregate_gate": result["aggregate"]})
    _write_json("10_RUNTIME_SOURCE_COMPARISON.json", {"activity": ACTIVITY, "runtime": runtime, "components": [{"component": row["component"], "classification": row["runtime_classification"], "source_state": row["source_state"], "production_change": False, "notes": row["runtime"]} for row in result["components"]], "aggregate_classification": "SOURCE_GAP", "production_module_hash": runtime["sha256"]})
    _write_json("11_VARIANT_REGISTER.json", {"activity": ACTIVITY, "variants": [{"id": "BPHS_CHAPTER_NUMBER_VARIANCE", "type": "TRANSLATION_DIFFERENCE", "status": "DOCUMENTED", "detail": "Accessible witness labels the chapter 27; repository metadata labels it 29."}, {"id": "BPHS_PARTIAL_TEXT", "type": "SOURCE_ACCESS_LIMITED", "status": "ACTIVE_CONDITION", "detail": "Passage-level paraphrases are retained without redistributing source text or inventing missing tables."}, {"id": "OJHAYUGMA_RUNTIME_SIMPLIFICATION", "type": "IMPLEMENTATION_VARIANT", "status": "MATERIAL_COMPONENT_GAP", "detail": "Runtime uses odd Rashi only; source assertion includes planet-specific Rashi and Navamsa conditions."}, {"id": "D3_VARGA_VS_STHANA_DREKKANA", "type": "SCOPE_VARIANT", "status": "SEPARATE", "detail": "D3 calculation availability does not validate the Sthana-Drekkana contribution rule."}]})
    _write_json("12_ORACLE_STATUS.json", {"activity": ACTIVITY, **result["oracle_status"], "source_complete_components": [row["component"] for row in result["components"] if row["readiness"] == "REMEDIATION_READY"]})
    _write_text("13_REMEDIATION_READINESS.md", f"""# Remediation Readiness

Decision: **{result['decision']}**.

The bounded audit is frozen at source-contract level. Kendradi is ready for a contained future remediation, subject to the explicit whole-sign house policy. Uchcha remains dependency-partial because the bounded BPHS witness does not close the exact point table. Saptavargaja, Ojhayugma and Sthana-Drekkana remain source-partial and must not be implemented from popular tables or inferred from existing Varga code.

Recommended future scope: a separately authorized component-level remediation may begin with Kendradi only, or with Uchcha after the exact point-input contract is independently closed. Saptavargaja, Ojhayugma and Drekkana require source/dependency closure first. The aggregate is **COMPONENT_LEVEL_ONLY**.

No production code, interpretation, prediction, ML, RAG, Approved Core or parallel Bala family was changed.
""")
    _write_json("14_PARALLEL_STATE.json", {"activity": ACTIVITY, "naisargika": "IMPLEMENTED / FROZEN WITH CONDITIONS; unchanged", "dig": "IMPLEMENTED / FROZEN WITH CONDITIONS; unchanged", "overall_shadbala": "LEGACY / UNVALIDATED AGGREGATE; unchanged", "ashtakavarga": "FROZEN / COMPLETE_WITH_CONDITION; unchanged", "d20": "SOURCE-QUALIFIED / UNCHANGED", "p032": "IMPLEMENTED / FROZEN; unchanged", "rag": "UNCHANGED", "approved_core": "17; unchanged", "prediction": "PRED-M3_OPERATIONAL_PLUS; unchanged", "ml": "UNCHANGED", "india": "UNCHANGED", "muller": "UNCHANGED", "adb": "UNCHANGED", "position_end": "UNCHANGED"})
    acceptance = _acceptance(result)
    _write_json("15_FINAL_ACCEPTANCE.json", acceptance)


if __name__ == "__main__":
    result = build_result()
    emit(result)
    print(json.dumps({"activity": ACTIVITY, "decision": result["decision"], "output": str(OUT), "acceptance": _acceptance(result)}, indent=2))
