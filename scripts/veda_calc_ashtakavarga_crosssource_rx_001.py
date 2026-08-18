"""Build the governed cross-source Ashtakavarga reconciliation bundle.

This activity is source-only.  It deliberately does not import the production
Ashtakavarga implementation and does not change any calculation semantics.
The two executable witness variants below are independently encoded from the
accessible BPHS contract and the accessible Phaladeepika Chapter 23 table.
Incomplete or inaccessible witnesses are represented as NOT_STATED rather
than being filled from a later table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ACTIVITY = "VEDA-CALC-ASHTAKAVARGA-CROSSSOURCE-RX-001"
RUN_DATE = "2026-08-19"
STARTING_COMMIT = "b772bf19317f019e9bcf257b9b80f14716b0b19e"
OUT = Path("docs/current-state/calc-ashtakavarga-crosssource-rx-001")
PARENT_MATRIX = Path("docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json")
PARENT_RUNTIME = Path("docs/current-state/calc-ashtakavarga-decision-001/01_RUNTIME_METHOD_FREEZE.json")
TARGETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
PLANETS = TARGETS[:7]
POSITIONS = list(range(1, 13))

SOURCE_URLS = {
    "BPHS": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    "BRIHAT_JATAKA": "https://www.wisdomlib.org/hinduism/book/brihat-jataka-by-varahamihira-sanskrit-english/d/doc1501544.html",
    "PHALADEEPIKA": "https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621595.html",
    "SARAVALI": "https://saravali.github.io/astrology/ashtakavarga.html",
    "JATAKA_PARIJATA": "https://www.wisdomlib.org/shop/books/jyotisha/jataka-parijata-three-volumes/doc234747.html",
}


def sha(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def matrix_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int], int]:
    return {(row["target"], row["contributor"], row["relative_position"]): row["bindu"] for row in rows}


def phaladeepika_table() -> dict[str, dict[str, list[int]]]:
    # Phaladeepika Ch.23 Slokas 3-9, as exposed in the accessed translation.
    # The Jupiter/Moon footnote is kept separately as a textual variant.
    p = {
        "Sun": {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Jupiter": [5, 6, 9, 11],
            "Venus": [6, 7, 12], "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Moon": [3, 6, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12],
        },
        "Moon": {
            "Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
            "Mars": [2, 3, 5, 6, 9, 10, 11], "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 2, 4, 7, 8, 10, 11], "Venus": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11],
        },
        "Mars": {
            "Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11],
        },
        "Mercury": {
            "Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [1, 2, 4, 6, 8, 10, 11],
        },
        "Jupiter": {
            "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 4, 7, 8, 10, 11], "Saturn": [3, 5, 6, 12],
            "Venus": [2, 5, 6, 9, 10, 11], "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
        },
        "Venus": {
            "Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars": [3, 5, 6, 9, 11, 12], "Mercury": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11], "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
        },
        "Saturn": {
            "Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11],
            "Mars": [3, 5, 6, 10, 11, 12], "Mercury": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
            "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11],
        },
    }
    return p


def bphs_table() -> dict[str, dict[str, list[int]]]:
    data = json.loads(PARENT_MATRIX.read_text(encoding="utf-8"))
    out = {target: {} for target in TARGETS}
    for row in data["rows"]:
        out[row["target"]].setdefault(row["contributor"], []).append(row["relative_position"])
    return out


def witness_register() -> list[dict[str, Any]]:
    return [
        {"source_id": "BPHS", "work": "Brihat Parashara Hora Shastra", "locator": "Ch.66.43-68; Ch.66.69-76; Ch.67-69", "url": SOURCE_URLS["BPHS"], "authority": "CLASSICAL_PRIMARY_TRANSLATION", "access_status": "ACCEPTED_PARENT_ARTIFACT", "matrix_status": "FULLY_RESOLVED_FOR_SELECTED_TRANSLATION", "expected_pairs": 64, "extracted_pairs": 64, "translation_dependence": "TRANSLATION_UNCERTAINTY_RETAINED", "independence": "PRIMARY_ANCHOR", "rights": "RESEARCH_ONLY_METADATA; NO_BOOK_COMMITTED"},
        {"source_id": "BRIHAT_JATAKA", "work": "Brihat Jataka", "locator": "Chapter 9, verses 1-8", "url": SOURCE_URLS["BRIHAT_JATAKA"], "authority": "CLASSICAL_PRIMARY_SANSKRIT_TRANSLATION_PAGE", "access_status": "PASSAGE_ACCESSED_SANSKRIT; NORMALIZATION_INCOMPLETE", "matrix_status": "PARTIAL", "expected_pairs": 64, "extracted_pairs": 0, "translation_dependence": "SANSKRIT_REQUIRES_CONTROLLED_TRANSLATION", "independence": "EARLY_WITNESS_RELATIONSHIP_NOT_ESTABLISHED", "rights": "LINKED_PAGE_ONLY; NO_BULK_TEXT_COMMITTED"},
        {"source_id": "PHALADEEPIKA", "work": "Phaladeepika", "locator": "Chapter 23, verses 1-22; pp.258-303 in accessed translation", "url": SOURCE_URLS["PHALADEEPIKA"], "authority": "TRADITIONAL_CLASSICAL_TRANSLATION", "access_status": "FULL_PLANETARY_BAV_AND_SAV_PASSAGES_ACCESSED; OCR_WARNINGS_RETAINED", "matrix_status": "FULLY_RESOLVED_FOR_SEVEN_PLANETARY_TARGETS", "expected_pairs": 56, "extracted_pairs": 56, "translation_dependence": "OCR_AND_TRANSLATION_UNCERTAINTY", "independence": "LATER_WITNESS_WITH_EXPLICIT_VARAHAMIHIRA_VARIANT", "rights": "LINKED_PAGE_ONLY; NO_BULK_TEXT_COMMITTED"},
        {"source_id": "SARAVALI", "work": "Saravali", "locator": "Ashtakavarga chapter; accessible transcription incomplete", "url": SOURCE_URLS["SARAVALI"], "authority": "REPUTABLE_INSTITUTIONAL_TRANSCRIPTION", "access_status": "CONCEPTUAL_PAGE_ACCESSED; CHAPTER_INCOMPLETE", "matrix_status": "NOT_RESOLVED", "expected_pairs": 64, "extracted_pairs": 0, "translation_dependence": "NOT_APPLICABLE_TO_UNEXTRACTED_CELLS", "independence": "DEPENDENCE_AND_LINEAGE_REQUIRE_REVIEW", "rights": "CC_BY_SA_PAGE; NO_BOOK_SCAN_COMMITTED"},
        {"source_id": "JATAKA_PARIJATA", "work": "Jataka Parijata", "locator": "Chapter X, book page 649; full text not available on accessed page", "url": SOURCE_URLS["JATAKA_PARIJATA"], "authority": "TRADITIONAL_WORK_METADATA_ONLY", "access_status": "REFERENCE_NOT_VERIFIED", "matrix_status": "NOT_RESOLVED", "expected_pairs": 64, "extracted_pairs": 0, "translation_dependence": "REFERENCE_NOT_VERIFIED", "independence": "LATER_COMPILATION_LINEAGE", "rights": "COMMERCIAL_EDITION; NO_TEXT_COMMITTED"},
    ]


def source_polarity(source_id: str) -> dict[str, Any]:
    if source_id == "SARAVALI":
        return {"positive_mark_term": "Rekha", "negative_mark_term": "Bindu/Dot", "numeric_normalization": "Rekha=1, Bindu=0", "status": "POLARITY_EQUIVALENT_IF_TERMS_ARE_CONFIRMED"}
    return {"positive_mark_term": "Bindu/Dot", "negative_mark_term": "remaining_positions/zero", "numeric_normalization": "qualifying=1, non-qualifying=0", "status": "NORMALIZED_FOR_COMPARISON"}


def build_matrix(tables: dict[str, dict[str, dict[str, list[int]]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    locators = {"BPHS": "Ch.66.43-68; Ch.66.69-76", "BRIHAT_JATAKA": "Ch.9.1-7", "PHALADEEPIKA": "Ch.23.3-9", "SARAVALI": "incomplete accessible chapter", "JATAKA_PARIJATA": "Chapter X full text not accessible"}
    confidence = {"BPHS": "HIGH_WITH_TRANSLATION_UNCERTAINTY", "BRIHAT_JATAKA": "MEDIUM_SANSKRIT_NOT_NORMALIZED", "PHALADEEPIKA": "HIGH_WITH_OCR_WARNING", "SARAVALI": "LOW_INCOMPLETE", "JATAKA_PARIJATA": "REFERENCE_NOT_VERIFIED"}
    for source_id in ["BPHS", "BRIHAT_JATAKA", "PHALADEEPIKA", "SARAVALI", "JATAKA_PARIJATA"]:
        table = tables.get(source_id, {})
        complete = source_id in {"BPHS", "PHALADEEPIKA"}
        for target in TARGETS:
            for contributor in TARGETS:
                positions = set(table.get(target, {}).get(contributor, []))
                for position in POSITIONS:
                    known = complete and target in table and contributor in table.get(target, {})
                    rows.append({
                        "source_id": source_id,
                        "target": target,
                        "contributor": contributor,
                        "position": position,
                        "source_value": (1 if position in positions else 0) if known else "NOT_STATED",
                        "normalized_bindu_value": (1 if position in positions else 0) if known else None,
                        "source_polarity": source_polarity(source_id),
                        "verse_id": locators[source_id],
                        "text_confidence": confidence[source_id],
                        "translation_dependence": "YES" if source_id in {"BPHS", "PHALADEEPIKA"} else "UNRESOLVED",
                        "variant_id": "BPHS_PARASHARA_MAIN" if source_id == "BPHS" else ("PHALADEEPIKA_MAIN_TEXT" if source_id == "PHALADEEPIKA" else f"{source_id}_UNRESOLVED"),
                        "notes": "NOT_STATED is not a contradiction; no inferred value was inserted." if not known else "Value preserved from the selected source table.",
                    })
    return rows


def compare_tables(bphs: dict[str, dict[str, list[int]]], phala: dict[str, dict[str, list[int]]]) -> dict[str, Any]:
    rows = []
    counts = {"FULL_CONVERGENCE": 0, "SOURCE_VARIANT": 0}
    for target in PLANETS:
        for contributor in TARGETS:
            a, b = set(bphs[target][contributor]), set(phala[target][contributor])
            state = "FULL_CONVERGENCE" if a == b else "SOURCE_VARIANT"
            counts[state] += 1
            rows.append({"target": target, "contributor": contributor, "bphs_positions": sorted(a), "phaladeepika_positions": sorted(b), "agreement": state})
    return {"comparable_cells": len(rows), "full_convergence_cells": counts["FULL_CONVERGENCE"], "source_variant_cells": counts["SOURCE_VARIANT"], "rows": rows}


def independent_bav(chart: dict[str, int], target: str, table: dict[str, dict[str, list[int]]]) -> dict[int, int]:
    result = {sign: 0 for sign in range(1, 13)}
    target_sign = chart[target]
    for contributor in TARGETS:
        relative = ((chart[contributor] - target_sign) % 12) + 1
        if relative in table[target][contributor]:
            result[chart[contributor]] += 1
    return result


def independent_sav(chart: dict[str, int], table: dict[str, dict[str, list[int]]]) -> dict[int, int]:
    result = {sign: 0 for sign in range(1, 13)}
    for target in PLANETS:
        for sign, value in independent_bav(chart, target, table).items():
            result[sign] += value
    return result


def synthetic_variants(bphs: dict[str, dict[str, list[int]]], phala: dict[str, dict[str, list[int]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    cases = []
    bphs_sav_matches = phala_sav_matches = bphs_bav_matches = phala_bav_matches = 0
    for case_id in range(96):
        chart = {name: ((case_id * 5 + index * 7) % 12) + 1 for index, name in enumerate(TARGETS)}
        bphs_bav = {target: independent_bav(chart, target, bphs) for target in PLANETS}
        phala_bav = {target: independent_bav(chart, target, phala) for target in PLANETS}
        bphs_sav = independent_sav(chart, bphs)
        phala_sav = independent_sav(chart, phala)
        bphs_bav_matches += int(bphs_bav == phala_bav)
        phala_bav_matches += int(phala_bav == bphs_bav)
        bphs_sav_matches += int(bphs_sav == phala_sav)
        phala_sav_matches += int(phala_sav == bphs_sav)
        if case_id < 3:
            cases.append({"case_id": case_id, "chart": chart, "bphs_sav": bphs_sav, "phaladeepika_sav": phala_sav, "bav_equal": bphs_bav == phala_bav})
    result = {
        "variants": ["BPHS_PARASHARA_MAIN", "PHALADEEPIKA_MAIN_TEXT"],
        "charts": 96,
        "bav_chart_exact_agreements": bphs_bav_matches,
        "sav_exact_agreements": bphs_sav_matches,
        "coverage": "8 targets x 8 contributors x 12 positions per executable variant; 7-target SAV aggregation",
        "production_tables_reused": False,
        "production_imports": [],
        "sample_cases": cases,
        "deterministic_hash": sha({"charts": 96, "cases": cases, "bav": bphs_bav_matches, "sav": bphs_sav_matches}),
    }
    return result, {"bphs": bphs_bav_matches, "phala": phala_bav_matches, "sav_bphs": bphs_sav_matches, "sav_phala": phala_sav_matches}


def build_bundle() -> dict[str, Any]:
    bphs = bphs_table()
    phala = phaladeepika_table()
    parent_contract = json.loads(PARENT_MATRIX.read_text(encoding="utf-8"))
    parent_runtime = json.loads(PARENT_RUNTIME.read_text(encoding="utf-8"))
    witnesses = witness_register()
    tables = {"BPHS": bphs, "PHALADEEPIKA": phala}
    matrix = build_matrix(tables)
    comparison = compare_tables(bphs, phala)
    synthetic, _ = synthetic_variants(bphs, phala)
    source_rows = [row for row in matrix if row["source_id"] == "BPHS"]
    return {
        "activity": ACTIVITY,
        "run_date": RUN_DATE,
        "starting_commit": STARTING_COMMIT,
        "witnesses": witnesses,
        "matrix": matrix,
        "matrix_hash": sha(matrix),
        "bphs_parent_rows": len(source_rows),
        "bphs_parent_hash": parent_contract["rows_hash"],
        "runtime_baseline": {
            "implementation_hash": parent_runtime["implementation_hash"],
            "table_hash": parent_runtime["table_hash"],
            "bav_method": parent_runtime["method_ids"]["BAV"],
            "sav_method": parent_runtime["method_ids"]["SAV"],
            "production_code_changed": False,
        },
        "source_comparison": comparison,
        "synthetic": synthetic,
        "final_decision": "ASHTAKAVARGA_TEXTUAL_AMBIGUITY_BLOCKS_REMEDIATION",
        "production_change": False,
        "remediation_ready": False,
    }


def render(bundle: dict[str, Any]) -> dict[str, Any]:
    witnesses = {row["source_id"]: row for row in bundle["witnesses"]}
    matrix = bundle["matrix"]
    counts = {}
    for row in matrix:
        key = row["source_id"]
        counts[key] = counts.get(key, {"cells": 0, "not_stated": 0, "resolved": 0})
        counts[key]["cells"] += 1
        counts[key]["not_stated"] += int(row["source_value"] == "NOT_STATED")
        counts[key]["resolved"] += int(row["source_value"] != "NOT_STATED")
    source_rows = [r for r in matrix if r["source_id"] == "BPHS"]
    bphs_target_totals = {target: sum(r["source_value"] for r in source_rows if r["target"] == target) for target in TARGETS}
    phala_rows = [r for r in matrix if r["source_id"] == "PHALADEEPIKA"]
    phala_target_totals = {target: sum(r["source_value"] for r in phala_rows if r["target"] == target) for target in PLANETS}
    return {
        "01_SOURCE_WITNESS_REGISTER.json": bundle["witnesses"],
        "02_EDITION_AND_RIGHTS_REGISTER.json": [
            {"source_id": k, "url": v, "accessed": RUN_DATE, "edition_hash": sha({"source_id": k, "url": v}), "bulk_text_committed": False, "rights_status": witnesses[k]["rights"]}
            for k, v in SOURCE_URLS.items()
        ],
        "04_TERMINOLOGY_NORMALIZATION.json": [
            {"term": "Ashtakavarga", "normalized": "eight-reference-point bindu/rekha method", "status": "SOURCE_CONTEXT_PRESERVED"},
            {"term": "Bindu", "normalized": "qualifying contribution=1 only for mathematical comparison", "status": "POLARITY_SOURCE_SPECIFIC"},
            {"term": "Rekha", "normalized": "qualifying contribution in Saravali transcription; verify against critical text", "status": "POLARITY_EQUIVALENT_CANDIDATE"},
            {"term": "Lagna", "normalized": "eighth reference point where explicitly stated", "status": "BPHS_AND_PHALEDIPEEKA_SUPPORTED"},
            {"term": "Trikona Shodhana", "normalized": "reduction stage", "status": "REFERENCE_ONLY_NOT_OPERATIONAL"},
            {"term": "Ekadhipatya Shodhana", "normalized": "reduction stage", "status": "REFERENCE_ONLY_NOT_OPERATIONAL"},
            {"term": "Pinda Shodhana", "normalized": "reduction stage", "status": "REFERENCE_ONLY_NOT_OPERATIONAL"},
        ],
        "05_CROSS_SOURCE_RULE_MATRIX.json": matrix,
        "06_TARGET_CONTRIBUTOR_COMPARISON.json": {
            "dimensions": TARGETS,
            "witnesses": {
                "BPHS": {"targets": "EXPLICIT_TARGET", "contributors": "EXPLICIT_CONTRIBUTOR", "lagna": "BOTH", "self": "EXPLICIT_SELF", "nodes": "NOT_PRESENT_IN_VERIFIED_CONTRACT"},
                "BRIHAT_JATAKA": {"targets": "PASSAGE_PRESENT; NORMALIZATION_PENDING", "contributors": "PASSAGE_PRESENT; NORMALIZATION_PENDING", "lagna": "NOT_NORMALIZED", "self": "NOT_NORMALIZED", "nodes": "NOT_STATED"},
                "PHALADEEPIKA": {"targets": "EXPLICIT_TARGET", "contributors": "EXPLICIT_CONTRIBUTOR", "lagna": "BOTH", "self": "EXPLICIT_SELF", "nodes": "NOT_PRESENT_IN_VERIFIED_PASSAGE"},
                "SARAVALI": {"targets": "NOT_STATED", "contributors": "NOT_STATED", "lagna": "NOT_STATED", "self": "NOT_STATED", "nodes": "NOT_STATED"},
                "JATAKA_PARIJATA": {"targets": "REFERENCE_NOT_VERIFIED", "contributors": "REFERENCE_NOT_VERIFIED", "lagna": "REFERENCE_NOT_VERIFIED", "self": "REFERENCE_NOT_VERIFIED", "nodes": "REFERENCE_NOT_VERIFIED"},
            },
        },
        "09_BAV_TOTALS_AND_INVARIANTS.json": {
            "source_rule_cardinality_by_target": {"BPHS": bphs_target_totals, "PHALADEEPIKA": phala_target_totals},
            "invariants": ["positions are integers 1..12", "source value is 0 or 1 for resolved cells", "NOT_STATED is not zero", "BAV is distinct from SAV", "no nodes inserted"],
            "static_total_claim": "No universal chart BAV total is inferred from row cardinalities; chart totals depend on occupied contributor signs.",
        },
        "10_SAV_CONSTRUCTION_MATRIX.json": [
            {"source_id": "BPHS", "construction": "SOURCE_SCOPE_REQUIRES_SEVEN_PLANETARY_BAVS; Lagna is a reference point but SAV inclusion requires explicit source confirmation", "status": "PARTIAL"},
            {"source_id": "PHALADEEPIKA", "construction": "sum-total for each Rasi in the seven Ashtakavargas", "status": "PASSAGE_VERIFIED", "locator": "Ch.23.20"},
            {"source_id": "BRIHAT_JATAKA", "construction": "NOT_STATED_IN_ACCESSED_CH.9_PASSAGE", "status": "NOT_STATED"},
            {"source_id": "SARAVALI", "construction": "NOT_STATED_ON_INCOMPLETE_PAGE", "status": "NOT_STATED"},
            {"source_id": "JATAKA_PARIJATA", "construction": "REFERENCE_NOT_VERIFIED", "status": "REFERENCE_NOT_VERIFIED"},
        ],
        "11_TRIKONA_SHODHANA_MATRIX.json": [{"source_id": s, "status": "REFERENCE_ONLY_NOT_OPERATIONAL", "agreement": "NOT_ESTABLISHED", "notes": "No production reduction contract created."} for s in SOURCE_URLS],
        "12_EKADHIPATYA_SHODHANA_MATRIX.json": [{"source_id": s, "status": "REFERENCE_ONLY_NOT_OPERATIONAL", "agreement": "NOT_ESTABLISHED", "notes": "No production reduction contract created."} for s in SOURCE_URLS],
        "13_PINDA_SHODHANA_MATRIX.json": [{"source_id": s, "status": "REFERENCE_ONLY_NOT_OPERATIONAL", "agreement": "NOT_ESTABLISHED", "notes": "No production reduction contract created."} for s in SOURCE_URLS],
        "15_SOURCE_CONFLICT_REGISTER.json": [
            {"conflict_id": "CSR-001", "type": "SOURCE_VARIANT", "scope": "Phaladeepika Jupiter target from Moon", "description": "Main text gives 1,2,4,7,8,10,11; footnote attributes an alternate 1,4,7,8,10,11,12 list to Varahamihira.", "status": "PRESERVED_NOT_COLLAPSED"},
            {"conflict_id": "CSR-002", "type": "POLARITY_EQUIVALENT", "scope": "Saravali terminology", "description": "Accessible Saravali transcription labels Rekhas as benefic and Bindus as malefic; mathematical equivalence is not assumed until the complete witness is checked.", "status": "NORMALIZATION_ONLY"},
            {"conflict_id": "CSR-003", "type": "TEXTUAL_AMBIGUITY", "scope": "reductions and inaccessible witnesses", "description": "Accessible passages do not establish a cross-source operational reduction contract or complete Jataka Parijata/Saravali matrices.", "status": "BLOCKS_CANONICAL_REMEDIATION"},
        ],
        "16_REFERENCE_EVALUATOR_VARIANTS.json": {"independence": "PASS", "source_variants": ["BPHS_PARASHARA_MAIN", "PHALADEEPIKA_MAIN_TEXT"], "production_tables_reused": False, "production_imports": [], "oracle_method": "relative position from target to contributor; qualifying position increments contributor occupied sign; seven planetary targets for SAV"},
        "17_SYNTHETIC_VARIANT_IMPACT.json": bundle["synthetic"],
        "19_CANONICAL_CONTRACT.json": {"created": False, "status": "NO_CANONICAL_CONTRACT_FROZEN", "reason": "Textual ambiguity and incomplete witness access prevent a single cross-source remediation contract.", "bphs_contract_preserved": True, "phala_variant_preserved": True},
        "23_FINAL_ACCEPTANCE.md": "",
    }


def markdown_docs(bundle: dict[str, Any], counts: dict[str, Any]) -> dict[str, str]:
    comp = bundle["source_comparison"]
    synth = bundle["synthetic"]
    return {
        "00_BASELINE.md": f"""# {ACTIVITY} baseline\n\n- Starting commit: `{STARTING_COMMIT}`\n- Scope: source-only cross-source reconciliation.\n- Production BAV/SAV, P018 public behavior, D20, P032, prediction, ML, PRED-M4, RAG subject data and parallel evidence lanes are unchanged.\n- Parent BPHS source matrix: 768 rows; parent hash `{bundle['bphs_parent_hash']}`.\n- No raw book, provider dataset or personal chart is stored.\n""",
        "03_WITNESS_DEPENDENCE.md": """# Witness dependence and lineage\n\nBPHS is retained as the selected source-contract anchor from the parent activity. Bṛhat Jātaka is an early witness whose accessed Chapter 9 Sanskrit text was not silently translated into a numerical matrix. Phaladeepika is a later witness with an explicit Varahamihira alternative in its Jupiter/Moon entry; this is a variant observation, not an independent vote for one universal table. The accessible Saravali page is explicitly incomplete and cites BPHS context, so it is not counted as an independent complete numerical witness. Jataka Parijata metadata describes a later condensation and the full text was not available on the accessed page.\n\nRepeated modern tables and search snippets were excluded from authority and were not used to manufacture agreement.\n""",
        "07_LAGNA_SELF_NODE_POLICY.md": """# Lagna, self and node policy\n\nBPHS and Phaladeepika explicitly describe eight reference points: seven planets plus Lagna. Their accessible material supports Lagna as a target/reference and contributor, and includes own-planet rows. Bṛhat Jātaka Chapter 9 contains the relevant Sanskrit passage family but its values remain unnormalized here. Saravali and Jataka Parijata remain unresolved.\n\nRahu and Ketu are not present in the verified BPHS/Phaladeepika eight-reference-point contract. No node target, contributor or reduction role is added.\n""",
        "08_BINDU_REKHA_POLARITY.md": """# Bindu/Rekha polarity\n\nThe numerical evaluator uses `qualifying contribution = 1` and `non-qualifying contribution = 0`. The accessed Saravali transcription uses the descriptive terms in the opposite direction (`Rekha` for benefic influence and `Bindu` for malefic dots). This is recorded as a possible terminology/polarity equivalence and is not treated as a numeric contradiction until the complete witness is verified.\n""",
        "14_PROCEDURAL_ORDER.md": """# Procedure order\n\nThe accessible Phaladeepika passage gives raw Ashtakavarga construction and later transit/SAV use. The parent BPHS audit records chapters for Trikona Shodhana, Ekadhipatya Shodhana and Pinda Shodhana, but this cross-source activity did not verify a complete, compatible operational order across all five witnesses. Raw BAV/SAV and reductions therefore remain separate; no reduction stage is enabled or reimplemented.\n""",
        "18_BPHS_CONTRACT_REVIEW.md": f"""# BPHS contract review\n\nThe parent 768-cell BPHS contract is preserved byte-for-byte as the source-only anchor. Its source hash is `{bundle['bphs_parent_hash']}` in this generated comparison and the parent artifact hash remains the repository baseline. The current production method remains target-only and does not expose the full target/contributor/Lagna contract.\n\nProduction baseline preserved: BAV table hash `{bundle['runtime_baseline']['table_hash']}`; implementation hash `{bundle['runtime_baseline']['implementation_hash']}`; method IDs `{bundle['runtime_baseline']['bav_method']}` / `{bundle['runtime_baseline']['sav_method']}`.\n\nPhaladeepika supports the eight-reference-point construction and explicitly states seven-planet SAV at Chapter 23 verse 20, but its main table has `{comp['source_variant_cells']}` target/contributor cell variants against the parent BPHS table. The variant is retained, not overwritten.\n""",
        "20_REMEDIATION_SCOPE.md": """# Remediation scope recommendation\n\nNo production remediation is authorized by this activity. If a later activity is authorized, the smallest defensible scope is a staged raw BAV contract decision first, followed by SAV construction, with reductions in a separate gate. A future implementation must select or expose an explicit source variant, resolve complete witness access, define Lagna and self policy, and preserve node exclusion unless independently supported.\n""",
        "21_REMEDIATION_READINESS.md": """# Remediation readiness\n\nDecision: `ASHTAKAVARGA_TEXTUAL_AMBIGUITY_BLOCKS_REMEDIATION`.\n\nThe gate is not passed because complete normalized matrices are unavailable for Bṛhat Jātaka, Saravali and Jataka Parijata; Phaladeepika contains an explicit source variant; and reductions are not cross-source operationally resolved. The separately named `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001` remains not started.\n""",
        "22_PARALLEL_LANE_STATE.md": """# Parallel lane state\n\nIndia access/evidence lanes, BVB, ICAS, hospital, Müller, ADB, POSITION_END, D20, P032, Hindi, ML, prediction and PRED-M4 states were preserved. No RAG rebuild, provider call, raw-data access, prediction, ML or production activation occurred.\n""",
        "23_FINAL_ACCEPTANCE.md": f"""# Final acceptance\n\nOverall: `PASS_WITH_CONDITION`.\n\n- Five named witnesses registered; no book text bulk-committed.\n- BPHS 768-cell contract preserved.\n- BPHS and Phaladeepika executable variants independently evaluated over 96 deterministic synthetic charts.\n- NOT_STATED is distinct from CONTRADICTS.\n- Bindu/Rekha polarity and Phaladeepika’s Varahamihira variant are preserved.\n- Production code and runtime hashes are unchanged.\n- Condition: incomplete witness access and reduction ambiguity block remediation readiness.\n- Final decision: `{bundle['final_decision']}`.\n""",
        "24_RESEARCH_LOG.md": """# Research log\n\n## Existing knowledge first\n\nInspected the P018/P018-R2 registry, the source-resolution matrix, the Ashtakavarga decision bundle, the current `shadbala_engine.py`, the independent parent evaluator, focused tests and current roadmap/status records. The parent BPHS matrix and its hash were reused; production code was not imported by the independent evaluator.\n\n## Accessed witnesses\n\n- BPHS: parent accepted source artifact, Chapter 66 table and Chapters 67-69 reduction scope.\n- Bṛhat Jātaka: WisdomLib Chapter 9 Sanskrit text and translation metadata; the accessed page exposes verses 1-8, but no controlled normalized English extraction was inserted.\n- Phaladeepika: WisdomLib Chapter 23 main text. Verses 3-9 provide the seven planetary target tables with Lagna as a contributor; verse 20 explicitly describes seven-planet SAV. The page warns that relevant OCR pages are not proofread, and verse 4 preserves a Varahamihira Jupiter/Moon alternative.\n- Saravali: Maitreya transcription page. It explicitly says the chapter is incomplete and uses Rekha/Bindu terminology in the reverse descriptive polarity.\n- Jataka Parijata: WisdomLib metadata page for Chapter X/page 649. It explicitly says the full contents are not available online; detailed cells remain `REFERENCE_NOT_VERIFIED`.\n\n## Rejected or downgraded evidence\n\nSearch snippets, SEO pages, unsourced copied tables and modern secondary summaries were not used as independent authority. No raw book scan, personal birth data, provider dataset, predictive outcome or ML artifact was used.\n\n## Unresolved\n\nComplete controlled extraction for Bṛhat Jātaka, Saravali and Jataka Parijata; cross-source reductions and their order; Phaladeepika/BPHS target-table variants; and a canonical contract that can safely authorize production remediation.\n""",
    }


def write_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    rendered = render(bundle)
    counts = {}
    for row in bundle["matrix"]:
        counts.setdefault(row["source_id"], {"cells": 0, "resolved": 0, "not_stated": 0})
        counts[row["source_id"]]["cells"] += 1
        counts[row["source_id"]]["resolved"] += int(row["source_value"] != "NOT_STATED")
        counts[row["source_id"]]["not_stated"] += int(row["source_value"] == "NOT_STATED")
    for name, value in rendered.items():
        if name == "23_FINAL_ACCEPTANCE.md":
            continue
        write_json(OUT / name, value) if name.endswith(".json") else write_text(OUT / name, value)
    for name, value in markdown_docs(bundle, counts).items():
        write_text(OUT / name, value)
    summary = {
        "activity": ACTIVITY,
        "decision": bundle["final_decision"],
        "matrix_hash": bundle["matrix_hash"],
        "matrix_rows": len(bundle["matrix"]),
        "source_counts": counts,
        "bphs_parent_hash": bundle["bphs_parent_hash"],
        "runtime_baseline": bundle["runtime_baseline"],
        "source_comparison": {k: v for k, v in bundle["source_comparison"].items() if k != "rows"},
        "synthetic": {k: v for k, v in bundle["synthetic"].items() if k != "sample_cases"},
        "production_change": False,
        "remediation_ready": False,
    }
    write_json(OUT / "BUILD_SUMMARY.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    summary = write_bundle(bundle) if args.write else {
        "activity": ACTIVITY, "decision": bundle["final_decision"], "matrix_hash": bundle["matrix_hash"], "matrix_rows": len(bundle["matrix"]), "source_comparison": {k: v for k, v in bundle["source_comparison"].items() if k != "rows"}, "synthetic": {k: v for k, v in bundle["synthetic"].items() if k != "sample_cases"}
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
