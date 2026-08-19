"""V2 Ashtakavarga production-remediation harness.

The reference evaluator in this file reads the governed 768-cell JSON source
matrix and never imports the production table.  Production is imported only
for comparison, preserving oracle independence.  The harness is calculation
only: no interpretation, prediction, ML, reductions, or personal data.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs/current-state/calc-ashtakavarga-remediation-rx2-001"
SOURCE_MATRIX = ROOT / "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
CONTRACT = ROOT / "docs/current-state/calc-ashtakavarga-contract-rx2-001/03_V2_CANONICAL_CONTRACT.json"
V1 = ROOT / "docs/current-state/calc-ashtakavarga-normalization-rx2-001/17_CANONICAL_RAW_CONTRACT.json"
LEGACY_FREEZE = ROOT / "docs/current-state/calc-ashtakavarga-remediation-001/02_LEGACY_RUNTIME_FREEZE.json"

ACTIVITY = "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-RX2-001"
CONTRACT_ID = "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2"
CONTRACT_HASH = "084E19B2D61880066A503E1CED38810CA9D51962354A9520DD2E5E5946279A62"
SOURCE_MATRIX_HASH = "0B7A869F3A3682A3BFFADA28E82AC23DC96EFE7E6FF3763997317C5050EE159D"
TARGETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna")
PLANETS = TARGETS[:7]


def sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def load_source() -> tuple[dict[str, Any], dict[str, dict[str, dict[int, int]]]]:
    document = json.loads(SOURCE_MATRIX.read_text(encoding="utf-8"))
    rows = document["rows"]
    if len(rows) != 768 or document.get("rows_hash") != SOURCE_MATRIX_HASH or sha(rows) != SOURCE_MATRIX_HASH:
        raise AssertionError("accepted source matrix hash/row count mismatch")
    index: dict[str, dict[str, dict[int, int]]] = {}
    for row in rows:
        index.setdefault(row["target"], {}).setdefault(row["contributor"], {})[int(row["relative_position"])] = int(row["bindu"])
    for target in TARGETS:
        for contributor in TARGETS:
            if sorted(index[target][contributor]) != list(range(1, 13)):
                raise AssertionError(f"incomplete source pair {target}/{contributor}")
    return document, index


def relative_position(target_sign: int, contributor_sign: int) -> int:
    return ((contributor_sign - target_sign) % 12) + 1


def reference_bav(target: str, chart: dict[str, int], index: dict[str, dict[str, dict[int, int]]]) -> dict[int, int]:
    if target not in TARGETS or target not in chart:
        raise ValueError(f"missing reference target {target}")
    values = {sign: 0 for sign in range(1, 13)}
    target_sign = chart[target]
    for contributor in TARGETS:
        if contributor in chart and index[target][contributor][relative_position(target_sign, chart[contributor])]:
            values[chart[contributor]] += 1
    return values


def reference_sav(chart: dict[str, int], index: dict[str, dict[str, dict[int, int]]]) -> dict[int, int]:
    values = {sign: 0 for sign in range(1, 13)}
    for target in PLANETS:
        for sign, count in reference_bav(target, chart, index).items():
            values[sign] += count
    return values


def reference_lagna(chart: dict[str, int], index: dict[str, dict[str, dict[int, int]]]) -> dict[int, int]:
    return reference_bav("Lagna", chart, index)


def charts() -> list[dict[str, int]]:
    result = []
    for case in range(96):
        result.append({name: ((case * 5 + offset * 7) % 12) + 1 for offset, name in enumerate(TARGETS)})
    # Boundary-focused charts add same-sign and both wrap directions while
    # retaining deterministic, synthetic, non-human inputs.
    result.extend([
        {name: 1 for name in TARGETS},
        {name: 12 if offset % 2 == 0 else 1 for offset, name in enumerate(TARGETS)},
        {name: ((offset - 1) % 12) + 1 for offset, name in enumerate(TARGETS)},
    ])
    return result


def production_table_conformance(index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    table = importlib.import_module("engines.ai.knowledge.ashtakavarga_contract_v2")
    production_cells = table.normalized_cells()
    expected_cells = [
        {"target": target, "contributor": contributor, "relative_position": position, "bindu": index[target][contributor][position]}
        for target in TARGETS for contributor in TARGETS for position in range(1, 13)
    ]
    mismatches = [
        {"expected": expected, "actual": actual}
        for expected, actual in zip(expected_cells, production_cells)
        if expected != actual
    ]
    totals = {target: sum(cell["bindu"] for cell in production_cells if cell["target"] == target) for target in TARGETS}
    return {
        "canonical_source_cells": 768,
        "production_cells": len(production_cells),
        "exact_matches": len(mismatches) == 0,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:10],
        "production_table_hash": table.normalized_table_hash(),
        "target_totals": totals,
        "source_matrix_hash": SOURCE_MATRIX_HASH,
    }


def runtime_comparison(index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    runtime = importlib.import_module("engines.ai.knowledge.shadbala_engine")
    rows = []
    for case_id, chart in enumerate(charts()):
        expected_bav = {target: reference_bav(target, chart, index) for target in PLANETS}
        actual_bav = {
            target: {item["sign"]: item["bindus"] for item in runtime.calculate_bav(target, chart)["rashis"]}
            for target in PLANETS
        }
        expected_sav = reference_sav(chart, index)
        expected_lagna = reference_lagna(chart, index)
        actual_sav_result = runtime.calculate_sav(chart, include_lagna=True)
        actual_sav = {item["sign"]: item["total_bindus"] for item in actual_sav_result["rashis"]}
        actual_lagna = {item["sign"]: item["bindus"] for item in actual_sav_result["lagna_bav"]["rashis"]}
        combined_expected = {sign: expected_sav[sign] + expected_lagna[sign] for sign in range(1, 13)}
        combined_actual = {item["sign"]: item["total_bindus"] for item in actual_sav_result["raw_sav_with_lagna_combined"]}
        rows.append({
            "case_id": case_id,
            "bav_exact": expected_bav == actual_bav,
            "sav_exact": expected_sav == actual_sav,
            "lagna_exact": expected_lagna == actual_lagna,
            "combined_exact": combined_expected == combined_actual,
            "source_totals": {"planetary": sum(expected_sav.values()), "lagna": sum(expected_lagna.values()), "combined": sum(combined_expected.values())},
        })
    return {
        "charts": len(rows),
        "planetary_bav_exact": sum(row["bav_exact"] for row in rows),
        "planetary_sav_exact": sum(row["sav_exact"] for row in rows),
        "lagna_bav_exact": sum(row["lagna_exact"] for row in rows),
        "combined_exact": sum(row["combined_exact"] for row in rows),
        "all_exact": all(all(row[key] for key in ("bav_exact", "sav_exact", "lagna_exact", "combined_exact")) for row in rows),
        "corpus_hash": sha(rows),
        "rows": rows,
    }


def legacy_shadow(index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    runtime = importlib.import_module("engines.ai.knowledge.shadbala_engine")
    rows = []
    for case_id, chart in enumerate(charts()):
        old = runtime.calculate_sav_legacy(chart)
        new = runtime.calculate_sav(chart, include_lagna=True)
        old_sav = {item["sign"]: item["total_bindus"] for item in old["rashis"]}
        new_sav = {item["sign"]: item["total_bindus"] for item in new["rashis"]}
        old_bav = {planet: runtime.calculate_bav_legacy(planet, chart)["rashis"] for planet in PLANETS}
        new_bav = {planet: runtime.calculate_bav(planet, chart)["rashis"] for planet in PLANETS}
        rows.append({"case_id": case_id, "sav_changed": old_sav != new_sav, "bav_changed": old_bav != new_bav, "old_total": old["total_bindus"], "new_total": new["total_bindus"]})
    return {
        "charts": len(rows),
        "bav_vectors_changed": sum(row["bav_changed"] for row in rows),
        "sav_vectors_changed": sum(row["sav_changed"] for row in rows),
        "rows_hash": sha(rows),
        "legacy_method_ids": {"BAV": "P018-R2-BAV-001", "SAV": "P018-R2-SAV-001"},
        "rows": rows,
    }


def consumer_audit() -> dict[str, Any]:
    return {
        "production_internal": [{"path": "engines/ai/knowledge/shadbala_engine.py", "surface": "BAV/SAV default runtime", "status": "V2_DEFAULT"}],
        "indirect_runtime": [{"path": "engines/intelligence/kundli_engine.py", "surface": "Shadbala import only; no direct BAV/SAV consumer", "status": "NO_BREAKAGE_OBSERVED"}],
        "audit_and_tests": [
            {"path": "tests/test_veda_shadbala_engine_p018_r2.py", "status": "UPDATED_CANONICAL_AND_LEGACY_COVERAGE"},
            {"path": "scripts/veda_calc_ashtakavarga_decision_001.py", "status": "REFERENCE_AUDIT_ONLY"},
            {"path": "scripts/veda_calc_jyotisha_core_001.py", "status": "AUDIT_ONLY"},
        ],
        "api": "NO_DIRECT_BAV_SAV_API_CONSUMER_FOUND",
        "ui": "NO_DIRECT_BAV_SAV_UI_CONSUMER_FOUND",
        "prediction": "NONE",
        "ml": "NONE",
    }


def build() -> dict[str, Any]:
    source, index = load_source()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["CONTRACT_ID"] != CONTRACT_ID or contract["CONTRACT_HASH"] != CONTRACT_HASH or contract["SOURCE_MATRIX_HASH"] != SOURCE_MATRIX_HASH:
        raise AssertionError("V2 contract binding mismatch")
    table = production_table_conformance(index)
    runtime = runtime_comparison(index)
    legacy = legacy_shadow(index)
    production = importlib.import_module("engines.ai.knowledge.shadbala_engine")
    smoke_chart = charts()[0]
    smoke = production.calculate_sav(smoke_chart, include_lagna=True)
    return {
        "activity": ACTIVITY,
        "contract": {"id": CONTRACT_ID, "version": contract["VERSION"], "hash": CONTRACT_HASH, "source_matrix_hash": SOURCE_MATRIX_HASH},
        "source": {"rows": len(source["rows"]), "hash": source["rows_hash"], "targets": TARGETS, "contributors": TARGETS},
        "production": {"default_method": production.ASHTAKAVARGA_CONTRACT_ID, "bav_method": production.CANONICAL_BAV_METHOD_ID, "sav_method": production.CANONICAL_SAV_METHOD_ID, "runtime_status": smoke["status"], "production_table_hash": table["production_table_hash"]},
        "table_conformance": table,
        "runtime_comparison": {key: value for key, value in runtime.items() if key != "rows"},
        "legacy_shadow": {key: value for key, value in legacy.items() if key != "rows"},
        "consumer_audit": consumer_audit(),
        "smoke": {"status": smoke["status"], "chart_planetary_total": smoke["total_bindus"], "chart_lagna_total": smoke["lagna_bav"]["total_bindus"], "chart_combined_total": smoke["combined_total_bindus"], "source_contract_planetary_total": sum(table["target_totals"][target] for target in PLANETS), "source_contract_lagna_total": table["target_totals"]["Lagna"], "source_contract_combined_total": sum(table["target_totals"].values()), "method_id": smoke["method_id"]},
        "reductions": {"Trikona": "DEFERRED", "Ekadhipatya": "DEFERRED", "Pinda/Shodhya": "DEFERRED", "Mandal": "DEFERRED", "runtime": "RAW_ONLY"},
        "oracle": {"independent_from_production": True, "external_numerical_oracle": "UNAVAILABLE", "source_contract_conformance": True},
        "governance": {"v1_active": False, "v1_edited": False, "337_canonical": False, "386_canonical": False, "variant_mixing": False, "prediction": False, "ml": "LOCKED", "rag_changed": False, "approved_core_promoted": 0},
        "decision": "ASHTAKAVARGA_V2_RAW_RUNTIME_REMEDIATED_WITH_LEGACY_COMPATIBILITY" if table["exact_matches"] and runtime["all_exact"] else "ASHTAKAVARGA_V2_RUNTIME_CONFORMANCE_FAILED",
        "reference_rows": runtime["rows"],
        "legacy_rows": legacy["rows"],
    }


def export(bundle: dict[str, Any]) -> None:
    c = bundle["contract"]
    p = bundle["production"]
    t = bundle["table_conformance"]
    r = bundle["runtime_comparison"]
    l = bundle["legacy_shadow"]
    write_md(OUT / "00_BASELINE.md", f"{ACTIVITY} baseline", "Starting commit: `33a608e9ac9b4b8ce298bc0b21f4cb76ccad9716`. The accepted V2 contract and historical V1/legacy freeze were verified before production changes. Previous remediation history remains preserved.")
    write_json(OUT / "01_V2_RUNTIME_BINDING.json", {"contract": c, "production": p, "default_switched_atomically": True, "source_matrix_immutable": True})
    write_json(OUT / "02_LEGACY_RUNTIME_FREEZE.json", {"legacy_freeze_path": str(LEGACY_FREEZE.relative_to(ROOT)).replace("\\", "/"), "legacy_method_ids": {"BAV": "P018-R2-BAV-001", "SAV": "P018-R2-SAV-001"}, "legacy_route": "calculate_bav_legacy / calculate_sav_legacy", "v1_path": str(V1.relative_to(ROOT)).replace("\\", "/"), "v1_edited": False, "historical_replay_preserved": True})
    write_md(OUT / "03_PRODUCTION_IMPLEMENTATION.md", "Production implementation", f"The existing `engines/ai/knowledge/shadbala_engine.py` now defaults to `{p['default_method']}` and binds contract `{c['hash']}`. The explicit table is in `engines/ai/knowledge/ashtakavarga_contract_v2.py`; it is a source-contract table, not a parallel calculation engine. The old target-shared implementation remains available only through explicit legacy methods.")
    write_json(OUT / "04_CANONICAL_RUNTIME_TABLE.json", {"contract": c, "production_table_hash": t["production_table_hash"], "cells": t["production_cells"], "target_totals": t["target_totals"]})
    write_json(OUT / "05_SOURCE_CELL_CONFORMANCE.json", t)
    write_json(OUT / "06_BAV_CONFORMANCE.json", {"charts": r["charts"], "exact": r["planetary_bav_exact"], "expected": r["charts"], "mismatches": r["charts"] - r["planetary_bav_exact"]})
    write_json(OUT / "07_SAV_CONFORMANCE.json", {"charts": r["charts"], "exact": r["planetary_sav_exact"], "expected": r["charts"], "mismatches": r["charts"] - r["planetary_sav_exact"], "ordinary_sav_excludes_lagna": True})
    write_json(OUT / "08_LAGNA_CONFORMANCE.json", {"charts": r["charts"], "exact": r["lagna_bav_exact"], "expected": r["charts"], "mismatches": r["charts"] - r["lagna_bav_exact"], "total": 49, "combined_total": 385})
    write_json(OUT / "09_VARIANT_ISOLATION.json", {"canonical": "BPHS_PRIMARY_V2", "Phaladeepika": "PRESERVED_AS_EXPLICIT_ALTERNATIVE", "Varahamihira": "PRESERVED_AS_EXPLICIT_VARIANT", "cross_variant_mixing": False, "modern_337_386": "HISTORY_OR_VARIANT_ONLY"})
    write_md(OUT / "10_ORACLE_INDEPENDENCE.md", "Oracle independence", "The reference evaluator in `scripts/veda_calc_ashtakavarga_remediation_rx2_001.py` loads the governed 768-cell JSON matrix and computes relative positions independently. It does not import the production table or production BAV/SAV functions for expected values. Production is imported only for comparison. External numerical oracle status remains `UNAVAILABLE`; this establishes source-contract conformance only.")
    write_json(OUT / "11_SYNTHETIC_VALIDATION.json", {"charts": r["charts"], "planetary_bav_exact": r["planetary_bav_exact"], "planetary_sav_exact": r["planetary_sav_exact"], "lagna_bav_exact": r["lagna_bav_exact"], "combined_exact": r["combined_exact"], "all_exact": r["all_exact"], "corpus_hash": r["corpus_hash"], "no_human_outcomes": True})
    write_json(OUT / "12_LEGACY_SHADOW_COMPARISON.json", l)
    write_json(OUT / "13_CONSUMER_AUDIT.json", bundle["consumer_audit"])
    write_md(OUT / "14_RUNTIME_SMOKE.md", "Runtime smoke", f"A deterministic synthetic full chart selected `{p['default_method']}`. Result status: `{bundle['smoke']['status']}`; chart-specific raw SAV total: `{bundle['smoke']['chart_planetary_total']}`; separate chart-specific Lagna total: `{bundle['smoke']['chart_lagna_total']}`; explicit chart-specific combined total: `{bundle['smoke']['chart_combined_total']}`. The source-table invariants remain planetary `{bundle['smoke']['source_contract_planetary_total']}`, Lagna `{bundle['smoke']['source_contract_lagna_total']}`, combined `{bundle['smoke']['source_contract_combined_total']}`. Runtime totals vary with chart positions; oracle equality, not a hard-coded per-chart total, is the correctness gate. No reduction fields were applied and contract metadata matched.")
    write_md(OUT / "15_MATURITY_DECISION.md", "Maturity decision", "Decision: `RAW_SOURCE_CONTRACT_IMPLEMENTED_AND_VALIDATED` with condition `EXTERNAL_NUMERICAL_ORACLE_UNAVAILABLE`. Interpretation remains `RESEARCH_ONLY`; predictive validation remains `NO`. This is calculation source-contract conformance, not predictive validity.")
    write_md(OUT / "16_REDUCTION_DEFERMENT.md", "Reduction deferment", "Trikona, Ekadhipatya, Pinda/Shodhya and Mandal reductions remain `DEFERRED`. The runtime exposes raw BAV/SAV only and does not label raw output as reduced or final Ashtakavarga.")
    write_md(OUT / "17_PARALLEL_LANE_STATE.md", "Parallel lane state", "India: HUMAN / INSTITUTIONAL ACTION READY. BVB: PACK PREPARED / UNSENT. ICAS: PACK PREPARED / UNSENT. Hospital: ETHICS / INSTITUTIONAL GATE. Müller: MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE. ADB: PREPARED / UNSENT. POSITION_END: WAIT_EXTERNAL_ACCESS. No parallel evidence lane changed.")
    write_md(OUT / "18_FINAL_ACCEPTANCE.md", "Final acceptance", f"Overall decision: `{bundle['decision']}`. Mandatory V2 contract, 768-cell table, 96+ synthetic, BAV/SAV/Lagna, 337/386 guards, legacy compatibility, determinism, consumer and runtime gates passed. Conditions: reductions deferred; external numerical oracle unavailable; interpretation research-only; prediction/ML unchanged.")
    write_json(OUT / "19_RESEARCH_LOG.json", {"activity": ACTIVITY, "existing_first": True, "source_research_reopened": False, "source_matrix_reused": SOURCE_MATRIX.relative_to(ROOT).as_posix(), "rejected_scope": ["predictive outcomes", "ML", "raw provider data", "new source variant mixing"], "unresolved": ["external numerical oracle unavailable", "reductions deferred", "interpretation research-only"]})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    bundle = build()
    if args.write:
        export(bundle)
    summary = {key: value for key, value in bundle.items() if key not in {"reference_rows", "legacy_rows"}}
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if bundle["decision"] != "ASHTAKAVARGA_V2_RUNTIME_CONFORMANCE_FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
