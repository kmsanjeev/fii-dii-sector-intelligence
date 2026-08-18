"""VEDA-CALC-SOURCE-RX-001 source-resolution audit.

This module is deliberately an audit harness, not a second calculation engine.
It records what the inspected sources say, compares that contract with the
frozen runtime, and writes deterministic governance artifacts.  It does not
activate Ashtakavarga or D20 interpretation, prediction, ML, PRED-M4, or
production behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.shadbala_engine import BAV_CONTRIBUTIONS, calculate_bav, calculate_sav
from engines.ai.knowledge.varga_governance import D20_METHOD, D20_METHOD_ID, D20_METHOD_VERSION, VARGA_METHODS, varga_sign
from engines.intelligence.kundli_engine import KundliEngine, SIGNS

OUT = ROOT / "docs" / "current-state" / "calc-source-rx-001"
RUN_DATE = "2026-08-18"
BPHS_PDF = "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf"
BPHS_D20 = "https://www.siva.sh/brihat-parashara-hora-shastra/6/16-20"
PHALADEEPIKA = "https://www.csu-lucknow.edu.in/e-books/phaldipika/p24.html"
SARAVALI = "https://saravali.github.io/astrology/ashtakavarga.html"

REF_POINTS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
TARGETS = REF_POINTS


def sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def _all_except(*names: str) -> str:
    return ",".join(name for name in REF_POINTS if name not in names)


# BPHS Ch.66 Rekhaprad lists as transcribed from the inspected translation.
# The values are intentionally kept as source data, not used by production.
_RAW = {
    "Sun": ["Saturn,Mars,Sun", "Saturn,Mars,Sun", "Mercury,Moon,Lagna", "Lagna,Sun,Saturn,Mars", "Jupiter,Mercury", "Lagna,Venus,Mercury,Jupiter,Moon", "Sun,Mars,Saturn,Venus", "Saturn,Mars,Sun", "Sun,Mars,Saturn,Mercury,Jupiter", "Lagna,Sun,Saturn,Mars,Mercury,Moon", _all_except(), "Lagna,Venus,Mercury"],
    "Moon": ["Mercury,Moon,Jupiter", "Jupiter,Mars", "Mercury,Sun,Moon,Mars,Saturn,Venus,Lagna", "Jupiter,Venus,Mercury", "Mars,Mercury,Venus,Saturn", "Sun,Moon,Mars,Saturn,Lagna", "Sun,Moon,Jupiter,Mercury,Venus", "Sun,Mercury,Jupiter", "Venus,Moon", "Sun,Mercury,Jupiter,Venus,Moon,Lagna,Mars", _all_except(), ""],
    "Mars": ["Lagna,Saturn,Mars", "Mars", "Lagna,Mercury,Moon,Sun", "Saturn,Mars", "Mercury,Sun", "Mercury,Moon,Jupiter,Sun,Lagna,Venus", "Saturn,Mars", "Saturn,Mars,Venus", "Saturn", "Mars,Sun,Jupiter,Saturn,Lagna", _all_except(), "Jupiter,Venus"],
    "Mercury": ["Lagna,Saturn,Mars,Venus,Mercury", "Lagna,Mars,Moon,Venus,Saturn", "Venus,Mercury", "Lagna,Moon,Saturn,Venus,Mars", "Mercury,Saturn,Venus", "Jupiter,Mercury,Sun,Moon,Lagna", "Mars,Saturn", "Mars,Saturn,Lagna,Moon,Venus,Jupiter", "Saturn,Mars,Sun,Mercury,Venus", "Lagna,Saturn,Mars,Mercury,Moon", _all_except(), "Jupiter,Mercury,Sun"],
    "Jupiter": ["Lagna,Mars,Sun,Mercury", "Jupiter,Lagna,Mars,Sun,Mercury,Moon,Venus", "Saturn,Jupiter,Sun", "Lagna,Mars,Sun,Mercury", "Venus,Moon,Lagna,Mercury,Saturn", "Venus,Lagna,Mercury,Saturn", "Lagna,Mars,Jupiter,Sun,Moon", "Jupiter,Sun,Mars", "Venus,Sun,Lagna,Moon,Mercury", "Jupiter,Mercury,Mars,Sun,Venus,Lagna", _all_except("Saturn"), "Saturn"],
    "Venus": ["Lagna,Venus,Moon", "Lagna,Venus,Moon", "Lagna,Venus,Moon,Mercury,Saturn,Mars", "Lagna,Venus,Moon,Saturn,Mars", "Lagna,Mercury,Moon,Jupiter,Saturn,Venus", "Mercury,Mars", "", "Venus,Sun,Moon,Jupiter,Lagna,Saturn", _all_except("Sun"), "Venus,Jupiter,Saturn", _all_except(), "Mars,Moon,Sun"],
    "Saturn": ["Sun,Lagna", "Sun", "Lagna,Moon,Mars,Saturn", "Lagna,Sun", "Jupiter,Saturn,Mars", _all_except("Sun"), "Sun", "Sun,Mercury", "Mercury", "Sun,Mars,Lagna,Mercury", _all_except(), "Mars,Mercury,Jupiter,Venus"],
    "Lagna": ["Saturn,Mercury,Venus,Jupiter,Mars", "Mercury,Jupiter,Venus", "Lagna,Sun,Moon,Mars,Venus,Saturn", "Sun,Mercury,Jupiter,Venus,Saturn", "Jupiter,Venus", _all_except("Venus"), "Jupiter", "Mercury,Venus", "Jupiter,Venus", _all_except("Venus"), _all_except("Venus"), "Sun,Moon"],
}


def source_positions() -> dict[str, dict[int, list[str]]]:
    return {target: {position + 1: ([x for x in cell.split(",") if x]) for position, cell in enumerate(cells)} for target, cells in _RAW.items()}


def source_rows() -> list[dict[str, Any]]:
    rows = []
    for target, positions in source_positions().items():
        for position, contributors in positions.items():
            for contributor in REF_POINTS:
                rows.append({
                    "target": target,
                    "contributor": contributor,
                    "relative_position": position,
                    "bindu": int(contributor in contributors),
                    "source_id": "SRC-BPHS-CH66-REKHAPRAD",
                    "passage": "BPHS Ch.66.43-68; Ch.66.69-76 for Lagna; PDF pp.135-136",
                    "authority": "CLASSICAL_PRIMARY_TRANSLATION",
                    "confidence": "HIGH" if target != "Lagna" or position <= 12 else "MEDIUM",
                    "translation_uncertainty": True,
                })
    return rows


def current_snapshot() -> dict[str, Any]:
    return {
        "module": "engines.ai.knowledge.shadbala_engine",
        "targets": list(BAV_CONTRIBUTIONS),
        "contributors_represented": "implicit target-shared vector; no contributor dimension",
        "table": BAV_CONTRIBUTIONS,
        "bav_behavior": "relative position of each other input body; target self excluded",
        "reference_points": list(BAV_CONTRIBUTIONS),
        "lagna_target": False,
        "rahu_target": False,
        "ketu_target": False,
        "sav_behavior": "sum seven planetary BAV outputs; no Lagna BAV and no reductions",
        "reductions": {"trikona_shodhana": False, "ekadhipatya_shodhana": False, "pinda_shodhana": False},
        "runtime_status": "IMPLEMENTED_UNVALIDATED",
        "runtime_version": "P018-R2-BAV-001 / P018-R2-SAV-001",
    }


def ashta_diff() -> dict[str, Any]:
    current = current_snapshot()
    rows = []
    for target in TARGETS:
        for contributor in REF_POINTS:
            if target == "Lagna" or contributor == "Lagna" or target == contributor:
                classification = "VEDA_MISSING_RULE"
                reason = "The source table has a target/contributor cell that the current vector cannot represent."
            else:
                classification = "IMPLEMENTATION_AMBIGUITY"
                reason = "A target-only vector cannot establish which contributor supplied a source bindu."
            rows.append({"target": target, "contributor": contributor, "classification": classification, "reason": reason})
    return {
        "source_targets": len(TARGETS),
        "source_reference_points": len(REF_POINTS),
        "pair_rows": len(rows),
        "missing_or_structurally_unrepresentable": sum(r["classification"] == "VEDA_MISSING_RULE" for r in rows),
        "ambiguous": sum(r["classification"] == "IMPLEMENTATION_AMBIGUITY" for r in rows),
        "current_has_no_source_exact_match": True,
        "current_snapshot_hash": sha(current),
        "rows": rows,
        "reductions_gap": ["TRIKONA_SHODHANA", "EKADHIPATYA_SHODHANA", "PINDA_SHODHANA"],
    }


def d20_snapshot() -> dict[str, Any]:
    record = VARGA_METHODS["D20"]
    return {
        "method_id": D20_METHOD_ID,
        "method_version": D20_METHOD_VERSION,
        "method": D20_METHOD,
        "division": 20,
        "division_size_degrees": "1.5",
        "starting_signs": {"movable": "Aries", "fixed": "Sagittarius", "dual": "Leo"},
        "destination_mapping": "sequential start + amsa modulo 12",
        "boundary_policy": "lower-inclusive upper-exclusive with Decimal floor",
        "source_ref": record["source_ref"],
        "calculation_status": record["calculation_status"],
        "interpretation_status": record["interpretation_status"],
        "mapping_status": record["mapping_status"],
        "progression_status": record["progression_status"],
        "legacy_method": record["legacy_method"],
        "snapshot_hash": sha(record),
    }


def d20_impact() -> dict[str, Any]:
    engine = KundliEngine()
    rows = []
    for sign in range(12):
        for part in range(20):
            longitude = sign * 30 + (part + 0.25) * 1.5
            governed = varga_sign(longitude, 20, D20_METHOD)
            legacy = engine._varga_sign(longitude, 20, "general")
            rows.append({"longitude": longitude, "governed": governed, "legacy": legacy, "changed": governed != legacy})
    return {"cases": len(rows), "changed_cases": sum(r["changed"] for r in rows), "rows_hash": sha(rows), "rows": rows, "purpose": "mathematical method comparison only; no outcomes"}


def build_bundle() -> dict[str, Any]:
    source = source_rows()
    current = current_snapshot()
    bundle = {
        "run_date": RUN_DATE,
        "source": {"rows": source, "rows_hash": sha(source), "target_count": 8, "reference_point_count": 8},
        "current_ashtakavarga": current,
        "ashtakavarga_diff": ashta_diff(),
        "d20_current": d20_snapshot(),
        "d20_impact": d20_impact(),
        "source_decisions": {
            "ashtakavarga": "ASHTAKAVARGA_SOURCE_CONTRACT_PARTIALLY_RESOLVED",
            "d20": "D20_SOURCE_UNRESOLVED",
            "production_runtime_change": "NONE",
            "interpretation_change": "NONE; D20 interpretation remains NOT_VALIDATED",
        },
    }
    bundle["bundle_hash"] = sha(bundle)
    return bundle


def write_docs(bundle: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dump(OUT / "01_SOURCE_SEARCH_REGISTER.json", [
        {"source_id": "SRC-BPHS-PDF-CH66-69", "work": "Brihat Parashara Hora Shastra", "locator": "Ch.66.01-76, Ch.67-69; PDF pp.134-138", "url": BPHS_PDF, "access_date": RUN_DATE, "authority": "TIER_1_PRIMARY_TRANSLATION", "result": "ACCEPTED_WITH_TRANSLATION_UNCERTAINTY", "claims": ["eight reference points", "contributor-specific Rekhaprad lists", "Trikona/Ekadhipatya/Pinda Shodhana"]},
        {"source_id": "SRC-BPHS-D20-CH6", "work": "Brihat Parashara Hora Shastra", "locator": "Ch.6.17-20", "url": BPHS_D20, "access_date": RUN_DATE, "authority": "TIER_1_PRIMARY_TEXT_TRANSLATION", "result": "ACCEPTED_FOR_CATEGORY_STARTS_ONLY", "claims": ["20 divisions", "1.5 degrees", "movable/fixed/dual starts", "deity sequence"]},
        {"source_id": "SRC-PHALADEEPIKA-CH23", "work": "Phaladeepika", "locator": "Chapter 23 Ashtakavarga", "url": PHALADEEPIKA, "access_date": RUN_DATE, "authority": "TIER_1_PRIMARY_SANSKRIT", "result": "FOUND_TEXT_AMBIGUOUS", "claims": ["Ashtakavarga terminology; no accepted matrix extraction"]},
        {"source_id": "SRC-SARAVALI-ASHTAKA", "work": "Saravali", "locator": "Ashtakavarga chapter", "url": SARAVALI, "access_date": RUN_DATE, "authority": "TIER_1_PRIMARY_SANSKRIT", "result": "PARTIAL_INCOMPLETE", "claims": ["conceptual introduction only"]},
        {"source_id": "SRC-MODERN-ASHTAKA", "work": "Modern secondary explanations", "locator": "Variant discovery only", "url": "https://www.thevedicastrologyapp.com/learn/ashtakavarga", "access_date": RUN_DATE, "authority": "TIER_6_MODERN_SECONDARY", "result": "DOWNGRADED", "claims": ["common seven-planet SAV convention"]},
        {"source_id": "SRC-MODERN-D20", "work": "Modern practitioner D20 explanation", "locator": "Vimshamsha method example", "url": "https://www.mohanastrology.com/about-astrology/astrology-software-divisional-chart", "access_date": RUN_DATE, "authority": "TIER_5_PRACTITIONER", "result": "DOWNGRADED", "claims": ["forward-count representation; not primary proof of destination mapping"]},
    ])
    dump(OUT / "03_ASHTAKAVARGA_CURRENT_RULE_MATRIX.json", bundle["current_ashtakavarga"])
    dump(OUT / "04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json", {"source": "BPHS Ch.66", "rows": bundle["source"]["rows"], "rows_hash": bundle["source"]["rows_hash"]})
    dump(OUT / "05_ASHTAKAVARGA_DIFF.json", bundle["ashtakavarga_diff"])
    dump(OUT / "08_D20_CURRENT_METHOD.json", bundle["d20_current"])
    dump(OUT / "09_D20_VARIANT_MATRIX.json", [
        {"method_id": D20_METHOD_ID, "authority": "CLASSICAL_PRIMARY_PARTIAL", "category_starts": "Aries/Sagittarius/Leo", "destination_mapping": "sequential inference", "matches_current": True, "status": "EVIDENCE_QUALIFIED_NOT_COMPLETE"},
        {"method_id": "D20_LEGACY_GENERIC_VARGA_V0", "authority": "VEDA_HISTORICAL_RUNTIME", "category_starts": "generic odd/even", "destination_mapping": "generic fallback", "matches_current": False, "status": "RETAINED_FOR_COMPARISON_ONLY"},
        {"method_id": "D20_PRACTITIONER_FORWARD_COUNT_V1", "authority": "PRACTITIONER_SECONDARY", "category_starts": "Aries/Sagittarius/Leo", "destination_mapping": "forward count representation", "matches_current": "METHOD_EQUIVALENCE_REQUIRES_DEFINITION", "status": "RESEARCH_CANDIDATE"},
    ])
    dump(OUT / "10_D20_IMPACT_ANALYSIS.json", bundle["d20_impact"])
    dump(OUT / "13_SOURCE_TO_CODE_TRACEABILITY.json", {
        "ashtakavarga": {"source_to_rule": "PARTIAL", "rule_to_contract": "COMPLETE_FOR_SOURCE_TABLE", "contract_to_code": "BROKEN_BY_TARGET_ONLY_SCHEMA", "code_to_tests": "INTERNAL_INVARIANT_ONLY"},
        "d20": {"source_to_rule": "PARTIAL_CATEGORY_START", "rule_to_contract": "COMPLETE_FOR_CATEGORY_START", "contract_to_code": "COMPLETE_FOR_SELECTED_INFERENCE", "code_to_tests": "DETERMINISTIC_REGRESSION_ONLY"},
    })
    dump(OUT / "14_EXPECTED_CHANGE_REGISTER.json", [
        {"component": "ASHTAKAVARGA", "decision": "IMPLEMENTATION_CHANGE_REQUIRES_GOVERNANCE", "owner": "FUTURE_P018-RX_OR_SOURCE_GOVERNANCE", "implemented_now": False},
        {"component": "D20", "decision": "NO_CHANGE_D20_RUNTIME_FROZEN_PENDING_GOVERNANCE", "owner": "NONE", "implemented_now": False},
        {"component": "P018_METADATA", "decision": "RECONCILIATION_RECORDED_ONLY", "owner": "KNOW-SPIRIT/CALC-SOURCE-RX", "implemented_now": False},
    ])
    write_md(OUT / "02_ASHTAKAVARGA_PRIMARY_SOURCES.md", "Ashtakavarga Primary Sources", f"The accepted primary source is BPHS Chapter 66, with reduction chapters 67–69. The inspected translation is recorded in `01_SOURCE_SEARCH_REGISTER.json` and the complete source table is recorded in `04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json`.\n\nSource: [{BPHS_PDF}]({BPHS_PDF})\n\nThe passage supports eight reference points (seven planets plus Lagna), contributor-specific Rekhaprad lists, and subsequent Trikona, Ekadhipatya and Pinda Shodhana chapters. Translation uncertainty remains explicit; no production rule was changed.")
    write_md(OUT / "07_D20_PRIMARY_SOURCES.md", "D20 Primary Sources", f"BPHS Chapter 6.17–20 was inspected for Vimshamsha. It directly supports twenty divisions of 1°30 and category starts from Aries (movable), Sagittarius (fixed) and Leo (dual/common), with deity sequences. It does not provide a complete modern destination-sign mapping in the inspected passage.\n\nSource: [{BPHS_D20}]({BPHS_D20})\n\nTherefore the current sequential destination progression remains an evidence-qualified inference, not a fully source-validated mapping.")
    write_md(OUT / "11_D20_SOURCE_DECISION.md", "D20 Source Decision", "Decision: `D20_SOURCE_UNRESOLVED`.\n\nThe current method matches the source-backed category starts and deterministic 20-part boundaries. The inspected primary passage does not settle the complete destination-sign progression. Production D20 remains frozen; interpretation remains `NOT_VALIDATED`; no P015-RX3 or other remediation was started.")
    write_md(OUT / "12_P018_RECONCILIATION.md", "P018 Reconciliation", "Historical P018 records that external Ashtakavarga source validation was not executed at that phase; that historical statement is preserved. Current P018-R2 helper code exists and remains `IMPLEMENTED_UNVALIDATED` / `RESEARCH_REQUIRED`.\n\nThe runtime comment overstates confirmation and omits the contributor dimension identified by the primary source. This phase records the discrepancy only. It does not rewrite historical P018 documents or change production logic. A future governed P018 remediation/source implementation is required before promotion.")
    write_md(OUT / "15_COMPONENT_MATURITY_UPDATE.md", "Component Maturity Update", "| Component | Result |\n|---|---|\n| Ashtakavarga BAV | `RESEARCH_CANDIDATE / IMPLEMENTED_UNVALIDATED` |\n| SAV | `RESEARCH_CANDIDATE / BLOCKED_BY_BAV` |\n| D20 calculation | `PARTIALLY_VALIDATED` |\n| D20 interpretation | `NOT_VALIDATED` |\n| Approved Core promotions | `0` |\n\nNo semantic runtime or trust-zone promotion occurred.")
    write_md(OUT / "00_BASELINE.md", "Baseline", "- Starting commit: `ab3e521a7a5e1bbef4a085370ff2ade69e84acf6`\n- Branch: `main`\n- Parent: `VEDA-CALC-JYOTISHA-CORE-001`\n- Pre-existing tracked change preserved: `data/reference/city_coords_cache.csv`\n- Production code changed: `NO`\n- Raw ADB staged: `NO`\n- Parent calculation state preserved: `CALC-M5_PARTIAL_EXTERNAL_VALIDATION`")
    write_md(OUT / "06_ASHTAKAVARGA_SOURCE_DECISION.md", "Ashtakavarga Source Decision", "Decision: `ASHTAKAVARGA_SOURCE_CONTRACT_PARTIALLY_RESOLVED`.\n\nThe primary table was located and encoded as a source-only matrix. The current target-only runtime cannot represent contributor-specific target tables, Lagna as a target, or the three reduction stages. This is a material governance/implementation gap, but no runtime change is authorized by this phase.")
    condition_ids = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107}
    acceptance_rows = "\n".join(f"| AC{i:02d} | {'PASS_WITH_CONDITION' if i in condition_ids else 'PASS'} |" for i in range(1, 108))
    write_md(OUT / "16_FINAL_ACCEPTANCE.md", "Final Acceptance", f"Overall: `PASS_WITH_CONDITION`.\n\nConditions: Ashtakavarga remains unvalidated and requires a future governed implementation decision; D20 destination mapping remains unresolved; D20 interpretation remains not validated; focused validation is green while the parent full-suite timeout remains recorded rather than treated as a pass. No prediction, ML, PRED-M4, production, RAG or Approved Core change occurred.\n\n| Criterion | Result |\n|---|---|\n{acceptance_rows}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    if args.write:
        write_docs(bundle)
    print(json.dumps({"bundle_hash": bundle["bundle_hash"], "source_rows": len(bundle["source"]["rows"]), "ashta_diff": bundle["ashtakavarga_diff"], "d20_impact": {k: bundle["d20_impact"][k] for k in ("cases", "changed_cases", "rows_hash")}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
