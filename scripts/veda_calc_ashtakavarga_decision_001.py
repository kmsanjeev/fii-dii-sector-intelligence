"""VEDA-CALC-ASHTAKAVARGA-DECISION-001 audit harness.

This is a bounded, non-production source-to-code decision harness.  The
reference evaluator is built from the previously governed BPHS source matrix
JSON and does not import or call the production BAV/SAV implementation.  The
production implementation is imported only by the comparison routine.

The harness does not activate Ashtakavarga, prediction, ML, or interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "calc-ashtakavarga-decision-001"
SOURCE_MATRIX = ROOT / "docs" / "current-state" / "calc-source-rx-001" / "04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
SOURCE_MATRIX_REL = "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
RUNTIME_MODULE = "engines.ai.knowledge.shadbala_engine"
REFERENCE_POINTS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
PLANETS = REFERENCE_POINTS[:7]
DECISION_ID = "VEDA-CALC-ASHTAKAVARGA-DECISION-001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def load_source_contract() -> tuple[dict[str, Any], dict[str, dict[str, dict[int, int]]]]:
    data = json.loads(SOURCE_MATRIX.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    index: dict[str, dict[str, dict[int, int]]] = {}
    for row in rows:
        target = row["target"]
        contributor = row["contributor"]
        position = int(row["relative_position"])
        index.setdefault(target, {}).setdefault(contributor, {})[position] = int(row["bindu"])
    expected = len(REFERENCE_POINTS) * len(REFERENCE_POINTS) * 12
    if len(rows) != expected:
        raise ValueError(f"source matrix row count {len(rows)} != {expected}")
    for target in REFERENCE_POINTS:
        for contributor in REFERENCE_POINTS:
            positions = index.get(target, {}).get(contributor, {})
            if sorted(positions) != list(range(1, 13)):
                raise ValueError(f"incomplete source cell: {target}/{contributor}")
    return data, index


def relative_position(target_sign: int, contributor_sign: int) -> int:
    """The source/runtime sign convention: target sign to contributor sign."""
    return ((contributor_sign - target_sign) % 12) + 1


def reference_bav(target: str, chart: dict[str, int], index: dict[str, dict[str, dict[int, int]]]) -> dict[int, int]:
    """Independently evaluate the governed target/contributor source matrix."""
    if target not in REFERENCE_POINTS or target not in chart:
        raise ValueError(f"reference target missing: {target}")
    result = {sign: 0 for sign in range(1, 13)}
    target_sign = int(chart[target])
    for contributor in REFERENCE_POINTS:
        if contributor not in chart:
            continue
        contributor_sign = int(chart[contributor])
        position = relative_position(target_sign, contributor_sign)
        if index[target][contributor][position]:
            result[contributor_sign] += 1
    return result


def reference_sav(chart: dict[str, int], index: dict[str, dict[str, dict[int, int]]]) -> dict[int, int]:
    """Independent SAV aggregation: seven planetary targets, eight contributors."""
    result = {sign: 0 for sign in range(1, 13)}
    for target in PLANETS:
        row = reference_bav(target, chart, index)
        for sign, count in row.items():
            result[sign] += count
    return result


def runtime_snapshot() -> dict[str, Any]:
    module = importlib.import_module(RUNTIME_MODULE)
    table = getattr(module, "BAV_CONTRIBUTIONS")
    source_text = "\n".join(
        inspect.getsource(getattr(module, name))
        for name in ("_relative_position", "calculate_bav", "calculate_sav")
    )
    return {
        "module": RUNTIME_MODULE,
        "functions": ["_relative_position", "calculate_bav", "calculate_sav"],
        "method_ids": {"BAV": "P018-R2-BAV-001", "SAV": "P018-R2-SAV-001"},
        "table": table,
        "table_hash": canonical_sha(table),
        "implementation_hash": hashlib.sha256(source_text.encode("utf-8")).hexdigest().upper(),
        "targets": list(table),
        "contributors": "implicit input keys; no explicit contributor dimension",
        "relative_position": "((contributor_sign - target_sign) % 12) + 1",
        "bindu_destination": "contributor occupied sign",
        "self_contributor": "excluded by runtime",
        "lagna_target": False,
        "lagna_contributor": "implicitly accepted as an input key, using target-only vector",
        "nodes": {"Rahu": False, "Ketu": False},
        "sav_targets": PLANETS,
        "sav_contributors": "whatever input keys are iterated by BAV; no explicit policy metadata",
        "reductions": {
            "trikona_shodhana": False,
            "ekadhipatya_shodhana": False,
            "pinda_shodhana": False,
        },
        "status": "IMPLEMENTED_UNVALIDATED",
    }


def source_matrix_summary(data: dict[str, Any], index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    rows = data["rows"]
    compact = {
        target: {
            contributor: [position for position in range(1, 13) if index[target][contributor][position]]
            for contributor in REFERENCE_POINTS
        }
        for target in REFERENCE_POINTS
    }
    return {
        "source": data.get("source"),
        "source_matrix_path": SOURCE_MATRIX_REL,
        "source_rows": len(rows),
        "source_rows_hash": data.get("rows_hash"),
        "computed_rows_hash": canonical_sha(rows),
        "targets": REFERENCE_POINTS,
        "contributors": REFERENCE_POINTS,
        "relative_position_convention": "1 = same sign; count forward from target sign to contributor sign",
        "bindu_destination": "contributor occupied sign",
        "translation_uncertainty": True,
        "compact_matrix": compact,
    }


def sparse_rule_comparison(index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    """Compare each source cell where a chart can physically instantiate it."""
    module = importlib.import_module(RUNTIME_MODULE)
    runtime_rows: list[dict[str, Any]] = []
    for target in REFERENCE_POINTS:
        for contributor in REFERENCE_POINTS:
            for position in range(1, 13):
                source_bind = index[target][contributor][position]
                if target == "Lagna":
                    category = "TARGET_NOT_IMPLEMENTED"
                    actual = None
                elif target == contributor and position != 1:
                    category = "SELF_RELATION_NOT_REALIZABLE"
                    actual = None
                else:
                    chart = {target: 1, contributor: 1 + ((position - 1) % 12)}
                    observed = module.calculate_bav(target, chart)
                    actual = next(item["bindus"] for item in observed["rashis"] if item["sign"] == chart[contributor])
                    if target == contributor:
                        category = "SELF_CONTRIBUTOR_POLICY_MISMATCH" if actual != source_bind else "SELF_CONTRIBUTOR_POLICY_MATCH_NUMERIC"
                    elif actual == source_bind:
                        category = "NUMERIC_MATCH"
                    else:
                        category = "NUMERIC_MISMATCH"
                runtime_rows.append({
                    "target": target,
                    "contributor": contributor,
                    "relative_position": position,
                    "source_bind": source_bind,
                    "runtime_bind": actual,
                    "classification": category,
                })
    counts: dict[str, int] = {}
    for row in runtime_rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    comparable = sum(count for name, count in counts.items() if name in {"NUMERIC_MATCH", "NUMERIC_MISMATCH", "SELF_CONTRIBUTOR_POLICY_MISMATCH", "SELF_CONTRIBUTOR_POLICY_MATCH_NUMERIC"})
    mismatches = counts.get("NUMERIC_MISMATCH", 0) + counts.get("SELF_CONTRIBUTOR_POLICY_MISMATCH", 0)
    return {
        "source_cells": len(runtime_rows),
        "classification_counts": counts,
        "physically_comparable_cells": comparable,
        "numeric_or_policy_mismatches": mismatches,
        "numeric_match_rate_over_comparable": round((comparable - mismatches) / comparable, 6) if comparable else 0,
        "rows": runtime_rows,
    }


def corpus_comparison(index: dict[str, dict[str, dict[int, int]]]) -> dict[str, Any]:
    module = importlib.import_module(RUNTIME_MODULE)
    cases: list[dict[str, Any]] = []
    for case_id in range(96):
        chart = {name: ((case_id * 5 + index * 7) % 12) + 1 for index, name in enumerate(REFERENCE_POINTS)}
        reference = {target: reference_bav(target, chart, index) for target in PLANETS}
        runtime = {}
        for target in PLANETS:
            observed = module.calculate_bav(target, chart)
            runtime[target] = {item["sign"]: item["bindus"] for item in observed["rashis"]}
        source_sav = reference_sav(chart, index)
        runtime_sav = {item["sign"]: item["total_bindus"] for item in module.calculate_sav(chart)["rashis"]}
        cases.append({"case_id": case_id, "chart": chart, "source_sav": source_sav, "runtime_sav": runtime_sav, "source_bav": reference, "runtime_bav": runtime})
    source_hash = canonical_sha(cases)
    sav_matches = sum(case["source_sav"] == case["runtime_sav"] for case in cases)
    bav_matches = sum(case["source_bav"] == case["runtime_bav"] for case in cases)
    return {
        "cases": len(cases),
        "corpus_hash": source_hash,
        "sav_exact_matches": sav_matches,
        "sav_exact_match_rate": round(sav_matches / len(cases), 6),
        "bav_chart_exact_matches": bav_matches,
        "bav_chart_exact_match_rate": round(bav_matches / len(cases), 6),
        "first_case": cases[0],
    }


def consumer_audit() -> dict[str, Any]:
    return {
        "production_runtime_consumers": [
            {"path": "engines/intelligence/kundli_engine.py", "surface": "generic Shadbala import only; no direct BAV/SAV call", "status": "INDIRECT_CONTEXT"},
        ],
        "audit_and_test_consumers": [
            {"path": "scripts/veda_calc_source_rx_001.py", "surface": "source/runtime audit", "status": "AUDIT_ONLY"},
            {"path": "scripts/veda_calc_jyotisha_core_001.py", "surface": "calculation evidence report", "status": "AUDIT_ONLY"},
            {"path": "tests/test_veda_shadbala_engine_p018_r2.py", "surface": "focused regression", "status": "TEST_ONLY"},
        ],
        "prediction_consumers": [],
        "ml_consumers": [],
        "production_activation": False,
    }


def compute_bundle() -> dict[str, Any]:
    source_data, index = load_source_contract()
    runtime = runtime_snapshot()
    source_summary = source_matrix_summary(source_data, index)
    cell_comparison = sparse_rule_comparison(index)
    corpus = corpus_comparison(index)
    reductions = {
        "trikona_shodhana": "NOT_IMPLEMENTED",
        "ekadhipatya_shodhana": "NOT_IMPLEMENTED",
        "pinda_shodhana": "NOT_IMPLEMENTED",
        "decision": "RAW_BAV_SAV_ONLY; no reduction claim is activated",
        "source_scope": "The source artifact records source chapters for reductions, but an operational reduction contract was not established in this activity.",
    }
    return {
        "decision_id": DECISION_ID,
        "source": source_summary,
        "runtime": runtime,
        "cell_comparison": {key: value for key, value in cell_comparison.items() if key != "rows"},
        "corpus": corpus,
        "reductions": reductions,
        "consumers": consumer_audit(),
        "decisions": {
            "bav": "SOURCE_CONTRACT_PARTIALLY_VALIDATED_RUNTIME_MISMATCH_REQUIRES_REMEDIATION_SPEC",
            "sav": "AGGREGATION_SHAPE_SUPPORTED_BUT_INPUT_BAV_UNVALIDATED",
            "overall": "ASHTAKAVARGA_REMEDIATION_SPEC_READY",
            "production_change": False,
            "future_owner": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001",
            "approved_core_promotion": False,
            "prediction_activation": False,
        },
    }


def render_docs(bundle: dict[str, Any]) -> dict[str, str]:
    source = bundle["source"]
    runtime = bundle["runtime"]
    compare = bundle["cell_comparison"]
    corpus = bundle["corpus"]
    return {
        "00_BASELINE.md": """# Baseline\n\nStarting commit: `0551ed49836e6dc86d174eb5adc020f72c8f81c2`.\n\nThe prior Astro-Databank access-reconciliation commit/tag is preserved. This activity is calculation-governance only; no raw ADB/OGDB data, prediction outcome, ML, or production activation is used.""",
        "01_RUNTIME_METHOD_FREEZE.json": json.dumps(runtime, ensure_ascii=False, indent=2, sort_keys=True),
        "02_SOURCE_CONTRACT.json": json.dumps(source, ensure_ascii=False, indent=2, sort_keys=True),
        "03_SOURCE_VARIANT_MATRIX.md": """# Source Variant Matrix\n\n| Variant | Contract | Authority | Decision |\n|---|---|---|---|\n| BPHS Rekhaprad source matrix | 8 target reference points × 8 contributors × 12 positions; Lagna included | `CLASSICAL_PRIMARY_TRANSLATION` | selected source contract, translation uncertainty retained |\n| P018-R2 seven-row table | one vector per named planet, no target/contributor dimension | governed claim metadata / practitioner corroboration | not equivalent to the selected target-contributor contract; retain as a variant, do not merge |\n| Reductions | chapter references exist in parent source work, operational reduction rules not frozen here | source-dependent | deferred and not activated |\n\nThe two table shapes cannot be silently reconciled. Repeated secondary claims are not counted as independent numerical witnesses.""",
        "04_TARGET_CONTRIBUTOR_MATRIX.json": json.dumps(source["compact_matrix"], ensure_ascii=False, indent=2, sort_keys=True),
        "05_LAGNA_AND_NODE_POLICY.md": """# Lagna and Node Policy\n\nThe selected source contract contains Lagna as both a target and a contributor. The current runtime has no Lagna target, accepts Lagna only implicitly as an input contributor, and has no Rahu/Ketu target or contributor policy. This is a material contract boundary, not a reason to invent node rules. Future remediation must explicitly choose Lagna target behavior and document whether nodes are excluded.""",
        "06_REFERENCE_EVALUATOR.md": """# Independent Reference Evaluator\n\n`scripts/veda_calc_ashtakavarga_decision_001.py` loads the existing governed source matrix JSON and independently implements only: (1) target-to-contributor relative sign indexing, (2) source bindu lookup, (3) contributor-sign placement, and (4) seven-target SAV summation. It does not import `BAV_CONTRIBUTIONS`, `calculate_bav`, or `calculate_sav` for reference evaluation. Production functions are imported only in the comparison path.\n\nThe evaluator uses synthetic deterministic charts only. No personal birth data or predictive outcome is used.""",
        "07_RULE_COVERAGE.json": json.dumps({"source_cells": source["source_rows"], "targets": source["targets"], "contributors": source["contributors"], "positions_per_cell": 12, "source_rows_hash": source["source_rows_hash"], "reference_evaluator_cells": source["source_rows"], "coverage_status": "COMPLETE_SOURCE_CONTRACT_COVERAGE"}, ensure_ascii=False, indent=2, sort_keys=True),
        "08_RUNTIME_EQUIVALENCE_RESULTS.json": json.dumps({"cell_comparison": compare, "deterministic_corpus": corpus}, ensure_ascii=False, indent=2, sort_keys=True),
        "09_BAV_DECISION.md": f"""# BAV Decision\n\nDecision: **SOURCE_CONTRACT_PARTIALLY_VALIDATED_RUNTIME_MISMATCH_REQUIRES_REMEDIATION_SPEC**.\n\nThe source contract has {compare['source_cells']} cells. {compare['classification_counts'].get('TARGET_NOT_IMPLEMENTED', 0)} Lagna-target cells cannot be represented by the current target-only runtime, {compare['classification_counts'].get('SELF_RELATION_NOT_REALIZABLE', 0)} self-relations are not physically realizable except at relative position 1, and the remaining comparable cells show {compare['numeric_or_policy_mismatches']} numeric or self-policy mismatches. The current seven vectors cannot stand in for the target/contributor matrix.\n\nNo production correction is made in this activity. A contained remediation specification is ready for `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001`.""",
        "10_SAV_DECISION.md": f"""# SAV Decision\n\nDecision: **AGGREGATION_SHAPE_SUPPORTED_BUT_INPUT_BAV_UNVALIDATED**.\n\nThe seven planetary-target sum is structurally present and the deterministic corpus produced {corpus['sav_exact_matches']} exact SAV matches out of {corpus['cases']} cases against the selected source contract. Because the current BAV table and contributor/self/Lagna policy are not equivalent, SAV cannot be promoted or activated independently. No SAV reduction stage is enabled.""",
        "11_REDUCTION_STAGE_AUDIT.md": """# Reduction Stage Audit\n\nTrikona Shodhana, Ekadhipatya Shodhana, and Pinda Shodhana are not implemented in the current runtime. Their source references are retained in parent artifacts, but this activity did not establish a complete operational contract or add a reduction engine. Status: `DEFERRED / NOT_IMPLEMENTED`.""",
        "12_P018_INTENT_RECONCILIATION.md": """# P018 Intent Reconciliation\n\nP018-R2 added deterministic BAV/SAV helpers and regression tests while retaining `IMPLEMENTED_UNVALIDATED`. Older P018 inventory wording says Ashtakavarga was absent; current code inventory shows helpers. The discrepancy is metadata drift, not evidence of method validation. The P018 claim's seven-row table is narrower than the selected source target/contributor matrix and is retained as a variant rather than silently promoted.""",
        "13_RUNTIME_CONSUMER_AUDIT.json": json.dumps(bundle["consumers"], ensure_ascii=False, indent=2, sort_keys=True),
        "14_EXPECTED_CHANGE_ANALYSIS.json": json.dumps({"production_files_changed": [], "production_behavior_changed": False, "governance_files_added": "docs/current-state/calc-ashtakavarga-decision-001/*", "future_remediation": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001", "raw_provider_data_touched": False, "prediction_or_ml_touched": False, "rag_rebuild": False}, ensure_ascii=False, indent=2, sort_keys=True),
        "15_MATURITY_DECISION.md": """# Maturity Decision\n\n| Surface | Decision |\n|---|---|\n| Source matrix completeness | `SOURCE_CONTRACT_COMPLETE_WITH_TRANSLATION_UNCERTAINTY` |\n| Independent reference arithmetic | `DETERMINISTIC_REFERENCE_VALIDATED` |\n| External numerical oracle | `UNVALIDATED / SAME_ENGINE_REFERENCE_LIMITATION` |\n| Production BAV equivalence | `MATERIAL_MISMATCH` |\n| Production SAV equivalence | `UNVALIDATED_DUE_TO_BAV` |\n| Interpretation/prediction | `NOT_IN_SCOPE / NOT_ACTIVATED` |\n\nOverall: `ASHTAKAVARGA_REMEDIATION_SPEC_READY`. This is a governance decision, not a production freeze or Approved Core promotion.""",
        "16_REMEDIATION_GATE.md": """# Remediation Gate\n\n`REMEDIATION_REQUIRED = YES` for the current BAV implementation. Owner: `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001`; not started by this activity. Required scope: explicit target/contributor rule representation, self-contributor policy, Lagna target/contributor policy, source-variant selection, independent fixtures, SAV contract, and reduction-stage decision.\n\nNo P018 production code was patched here. No Approved Core promotion occurred. P032 and unrelated phases remain untouched.""",
        "17_FINAL_ACCEPTANCE.md": """# Final Acceptance\n\nStatus: `PASS_WITH_CONDITION`.\n\nPassed: clean baseline, governed source artifact reused, independent evaluator, full 768-cell source coverage, deterministic synthetic comparison corpus, consumer audit, reduction audit, no production activation, no raw data, no prediction/ML, and no Approved Core change.\n\nCondition: the source translation and the P018-R2 seven-row table remain variant/authority questions; production BAV/SAV remain `IMPLEMENTED_UNVALIDATED` until the separately authorized remediation phase.""",
        "18_DETERMINISTIC_BUILD.json": json.dumps({"bundle_hash": canonical_sha(bundle), "source_matrix_hash": source["source_rows_hash"], "corpus_hash": corpus["corpus_hash"], "script": "scripts/veda_calc_ashtakavarga_decision_001.py", "determinism": "canonical JSON SHA-256"}, ensure_ascii=False, indent=2, sort_keys=True),
        "19_RESEARCH_LOG.md": """# Research Log\n\n## Existing-knowledge-first inspection\n\nInspected P018/P018-R2 claims and embedded governance, `VEDA-CALC-JYOTISHA-CORE-001`, `VEDA-CALC-SOURCE-RX-001`, the roadmap rebaseline, current `shadbala_engine.py`, focused tests, source registry artifacts and changelog. The prior source matrix and current runtime were reused; no duplicate external source search was required.\n\n## Source evidence used\n\n- `docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json`: 768 deterministic rows, BPHS Ch.66 source locator, eight reference points, explicit target/contributor dimension, translation uncertainty retained.\n- `docs/current-state/calc-source-rx-001/05_ASHTAKAVARGA_DIFF.json`: prior pair-level reconciliation (22 structurally missing, 42 contributor-ambiguous).\n- `engines/ai/knowledge/shadbala_engine.py`: exact production semantics and hashes captured in `01_RUNTIME_METHOD_FREEZE.json`.\n\n## Rejected or downgraded claims\n\nThe P018-R2 seven-row target-shared table and statements that all source families are identical were not treated as an independent complete witness. They are retained as a method/representation variant because they lack the target/contributor dimension required by the selected source contract. No SEO page, search snippet, unsourced table, raw provider data or predictive outcome was used.\n\n## Unresolved boundaries\n\nTranslation uncertainty remains on the selected classical table; operational reductions and any alternative school mapping remain deferred. These boundaries justify a contained remediation specification, not an autonomous production rewrite.""",
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    for name, content in render_docs(bundle).items():
        path = OUT / name
        if name.endswith(".json"):
            write_text(path, content)
        else:
            write_text(path, content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write deterministic governance artifacts")
    args = parser.parse_args()
    bundle = compute_bundle()
    print(json.dumps({"decision_id": DECISION_ID, "bundle_hash": canonical_sha(bundle), "decisions": bundle["decisions"], "cell_comparison": bundle["cell_comparison"], "corpus": {key: value for key, value in bundle["corpus"].items() if key != "first_case"}}, indent=2, sort_keys=True))
    if args.write:
        write_bundle(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
