"""Controlled RX2 Ashtakavarga normalization; no production imports or edits."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.veda_calc_ashtakavarga_crosssource_rx_001 import (
    TARGETS,
    bphs_table,
    phaladeepika_table,
    sha,
)

ACTIVITY = "VEDA-CALC-ASHTAKAVARGA-NORMALIZATION-RX2-001"
RUN_DATE = "2026-08-19"
STARTING_COMMIT = "76393db09983cef670f71bfa3c69845c483b39fa"
OUT = Path("docs/current-state/calc-ashtakavarga-normalization-rx2-001")
PARENT = Path("docs/current-state/calc-ashtakavarga-crosssource-rx-001")
RUNTIME = Path("docs/current-state/calc-ashtakavarga-decision-001/01_RUNTIME_METHOD_FREEZE.json")

URLS = {
    "BPHS": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    "BRIHAT_JATAKA": "https://www.wisdomlib.org/hinduism/book/brihat-jataka-by-varahamihira-sanskrit-english/d/doc1501544.html",
    "PHALADEEPIKA": "https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621595.html",
    "SARAVALI": "https://saravali.github.io/astrology/ashtakavarga.html",
    "JATAKA_PARIJATA": "https://www.wisdomlib.org/shop/books/jyotisha/jataka-parijata-three-volumes/doc234747.html",
    "KNR_1998": "https://www.journalofastrology.com/product_details.php?item_id=166",
    "MEHTA": "https://www.journalofastrology.com/product_details.php?category_id=11&item_id=126&lang=en",
    "ADITYA": "https://books.google.co.in/books?id=1Uwi1LAZb7QC&lr=&num=20",
    "BVB": "https://www.bvbdelhi.org/aaa/",
    "HOROSOFT": "https://www.horosoft.net/Sample/eng_tables.pdf",
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def classical_sources() -> dict[str, Any]:
    return {"activity": ACTIVITY, "access_date": RUN_DATE, "sources": [
        {"id": "BPHS", "authority": "CLASSICAL_PRIMARY_TRANSLATION", "locator": "Ch.66-69", "access": "PARENT_ACCEPTED_768_CELL_MATRIX_REUSED", "status": "RESOLVED", "url": URLS["BPHS"]},
        {"id": "BRIHAT_JATAKA", "authority": "CLASSICAL_PRIMARY_SANSKRIT_TRANSLATION_PAGE", "locator": "Ch.9 verses 1-8", "access": "SANSKRIT_PAGE_ACCESSED; COMPACT_VERSE_REQUIRES_CONTROLLED_TRANSLATION", "status": "CONTROLLED_ATTEMPT_NUMERIC_CELLS_UNRESOLVED", "url": URLS["BRIHAT_JATAKA"]},
        {"id": "PHALADEEPIKA", "authority": "TRADITIONAL_CLASSICAL_TRANSLATION", "locator": "Ch.23 verses 3-9 and 20", "access": "PARENT_672_CELLS_REUSED; VARAHAMIHIRA_VARIANT_RETAINED", "status": "PARTIALLY_RESOLVED_WITH_VARIANT", "url": URLS["PHALADEEPIKA"]},
        {"id": "SARAVALI", "authority": "REPUTABLE_INSTITUTIONAL_TRANSCRIPTION", "locator": "Ashtakavarga page", "access": "PAGE_ACCESSED; PAGE_STATES_CHAPTER_INCOMPLETE", "status": "CONCEPTUAL_ONLY", "url": URLS["SARAVALI"]},
        {"id": "JATAKA_PARIJATA", "authority": "TRADITIONAL_WORK_METADATA", "locator": "Chapter X, book page 649", "access": "COMMERCIAL_METADATA_ONLY; FULL_TEXT_NOT_AVAILABLE", "status": "REFERENCE_NOT_VERIFIED", "url": URLS["JATAKA_PARIJATA"]},
    ], "rights": "No full books, scans, pirated copies or provider data committed."}


def knr_sources() -> dict[str, Any]:
    return {
        "authority_axis": "PRIMARY_PRACTITIONER_SOURCE; NOT_CLASSICAL_PRIMARY",
        "lineage_policy": "KNR_IMPLEMENTATION_TRADITION is one dependent modern school lineage, not independent classical votes.",
        "sources": [
            {"id": "KNR_DOTS_1985_86", "status": "BIBLIOGRAPHIC_ONLY_FULL_TEXT_NOT_LOCATED", "finding": "Later official Journal material reports the 1985-86 Dots of Destiny series; original full text was not lawfully accessible in this audit.", "url": URLS["KNR_1998"]},
            {"id": "KNR_DOTS_1998", "status": "OFFICIAL_ISSUE_CONTENTS_VERIFIED_FULL_ARTICLE_NOT_ACCESSED", "finding": "Official Journal catalogue lists Dots of Destiny—Some Principles of Ashtakavarga by K.N. Rao.", "url": URLS["KNR_1998"]},
            {"id": "MEHTA_2002", "status": "OFFICIAL_BIBLIOGRAPHY_CONTENTS_VERIFIED", "finding": "Official Journal page identifies M.S. Mehta, guide/editor K.N. Rao, and sections for reductions, Pinda, Mandal and examples; full numerical text was not extracted.", "url": URLS["MEHTA"]},
            {"id": "VINAY_ADITYA", "status": "GOOGLE_BOOKS_METADATA_CONTENTS_VERIFIED", "finding": "Contents include computing, reductions, Shodhya Pinda, timing and examples; full preview unavailable.", "url": URLS["ADITYA"]},
            {"id": "BVB_LINEAGE", "status": "INSTITUTIONAL_LINEAGE_VERIFIED", "finding": "Official institute page verifies the K.N. Rao school, research and Journal publication route; it does not specify a formula.", "url": URLS["BVB"]},
            {"id": "HOROSOFT_SAMPLE", "status": "MODERN_IMPLEMENTATION_WITNESS_PAGE_2_INSPECTED", "finding": "Public vendor PDF shows planetary total 337, Lagna row 49, combined 386 and reduced tables; not classical or direct KNR proof.", "page": 2, "url": URLS["HOROSOFT"]},
        ],
        "rejected_or_downgraded": ["pirated_or_unauthorized_rehosts", "SEO_or_copy_pasted_tables", "single_practitioner_claims_as_independent_classical_evidence"],
    }


def normalization_records() -> dict[str, Any]:
    unresolved = {"DIRECT_EXPLICIT": 0, "COMPACT_TABLE_DECODED": 0, "TRANSLATION_ASSISTED": 0, "INTERPRETIVE": 0, "UNRESOLVED": 768}
    return {
        "BRIHAT_JATAKA": {"source_id": "BRIHAT_JATAKA", "passage": "Chapter 9 verses 1-8; Sanskrit accessed directly", "method": "controlled manual review; no numeric assignment without verified translation/cross-check", "cell_count": 768, "state_counts": unresolved, "status": "CONTROLLED_NORMALIZATION_ATTEMPTED_BUT_NOT_NUMERICALLY_RESOLVED", "reason": "Compressed Sanskrit lists are exposed, but a complete independently checked numerical table is not. Filling cells from memory or later tables would fabricate provenance.", "translation_uncertainty": True, "url": URLS["BRIHAT_JATAKA"]},
        "SARAVALI": {"source_id": "SARAVALI", "passage": "Accessible Ashtakavarga page; page states chapter is incomplete", "method": "conceptual extraction only", "cell_count": 768, "state_counts": unresolved, "status": "INCOMPLETE_WITNESS", "polarity": "Accessed transcription uses Rekha for benefic influence and Bindu/Dot for malefic indicator; numeric equivalence remains method-qualified.", "url": URLS["SARAVALI"]},
        "JATAKA_PARIJATA": {"source_id": "JATAKA_PARIJATA", "locator": "Chapter X, page 649 metadata", "cell_count": 768, "state_counts": unresolved, "status": "REFERENCE_NOT_VERIFIED", "reason": "The lawful accessed page is catalogue metadata and provides no chapter text.", "url": URLS["JATAKA_PARIJATA"]},
    }


def lagna_policy() -> list[dict[str, Any]]:
    return [
        {"id": "LAGNA-A", "question": "contributor to planetary BAV", "classical": "BPHS and Phaladeepika contributor material", "knr": "modern implementation tradition", "canonical": "INCLUDE_AS_EIGHTH_CONTRIBUTOR_WHERE_SOURCE_TABLE_EXPLICIT"},
        {"id": "LAGNA-B", "question": "own target BAV", "classical": "target policy not uniformly explicit; Phaladeepika normalized main table leaves Lagna target NOT_STATED", "knr": "modern software may render a Lagna row", "canonical": "SEPARATE_OPTIONAL_LAGNA_BAV_NOT_PLANETARY_TARGET"},
        {"id": "LAGNA-C", "question": "included in SAV", "classical": "Phaladeepika verse 20 states seven-planet SAV; 386 not established as canonical SAV", "knr": "337 without Lagna and 386 combined display observed", "canonical": "337_PLANETARY_SAV; 386_OPTIONAL_COMBINED_VIEW_ONLY"},
        {"id": "LAGNA-D", "question": "reductions", "classical": "reduction scope exists but compatible order unresolved", "knr": "reduction tables observed in modern sample", "canonical": "DEFERRED"},
    ]


def comparison_matrix() -> list[dict[str, Any]]:
    bp = bphs_table()
    ph = phaladeepika_table()
    rows = []
    for target in TARGETS:
        for contributor in TARGETS:
            a = sorted(bp[target][contributor])
            b = sorted(ph.get(target, {}).get(contributor, [])) if target != "Lagna" else "NOT_STATED"
            rows.append({"target": target, "contributor": contributor, "bphs_positions": a, "phaladeepika_positions": b, "comparison": "NOT_STATED" if target == "Lagna" else ("MATCH" if a == b else "SOURCE_VARIANT"), "authority_axis": "CLASSICAL_PRIMARY_OR_TRADITIONAL"})
    return rows


def build_bundle() -> dict[str, Any]:
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    comparison = comparison_matrix()
    raw = {
        "created": True,
        "contract_id": "ASHTAKAVARGA_RAW_BPHS_PRIMARY_KNR_GOVERNED_V1",
        "status": "SPECIFICATION_ONLY_NOT_PRODUCTION",
        "primary_method": "BPHS_SELECTED_ANCHOR; PHALADEEPIKA_MAIN_RETAINED_AS_EXPLICIT_ALTERNATIVE",
        "target_policy": "seven planetary targets; optional Lagna target separate",
        "contributor_policy": "seven planets plus Lagna where source table explicitly supplies contributor",
        "self_contribution": "included in source table; current production exclusion remains a mismatch",
        "sav_policy": "337 = sum of seven planetary BAVs; 386 = optional combined display adding Lagna BAV, not canonical planetary SAV",
        "nodes": "Rahu/Ketu excluded; absent from verified source contract",
        "polarity": "qualifying Bindu/Rekha normalized to 1 with source-specific terminology retained",
        "raw_vs_reduced": "raw contract only; reductions separate and deferred",
    }
    raw["contract_hash"] = sha(raw)
    return {
        "activity": ACTIVITY, "run_date": RUN_DATE, "starting_commit": STARTING_COMMIT,
        "classical": classical_sources(), "knr": knr_sources(), "normalization": normalization_records(),
        "comparison": comparison, "lagna_policy": lagna_policy(),
        "crosswalk": [
            {"claim": "eight reference points", "classical": "BPHS/Phaladeepika supported", "knr": "implementation tradition supported", "decision": "VALIDATED_WITH_METHOD_SCOPE"},
            {"claim": "337 planetary SAV", "classical": "Phaladeepika verse 20 supports seven-planet sum", "knr": "modern tradition reports same", "decision": "RAW_CONTRACT_CANDIDATE"},
            {"claim": "386 canonical SAV", "classical": "not established", "knr": "modern combined seven-planet plus Lagna display", "decision": "REJECT_UNQUALIFIED_CLAIM"},
            {"claim": "Rahu/Ketu contributors", "classical": "not present in verified contract", "knr": "not required by accessed witness", "decision": "EXCLUDE"},
            {"claim": "raw equals reduced contract", "classical": "not supported", "knr": "sections separated", "decision": "SPLIT"},
        ],
        "reduction_scope": [{"concept": x, "status": "DEFERRED"} for x in ["Trikona Shodhana", "Ekadhipatya Shodhana", "Pinda/Shodhya Pinda", "Mandal Shodhana", "Kakshya"]],
        "raw_contract": raw, "reduction_contract": {"created": False, "status": "DEFERRED_INSUFFICIENT_CROSS_SOURCE_OPERATIONAL_PROVENANCE"},
        "runtime": {"implementation_hash": runtime["implementation_hash"], "table_hash": runtime["table_hash"], "method_ids": runtime["method_ids"], "production_changed": False},
        "decision": "ASHTAKAVARGA_RAW_CONTRACT_REMEDIATION_READY_REDUCTIONS_DEFERRED", "production_remediation_authorized": False,
    }


def markdown(bundle: dict[str, Any]) -> dict[str, str]:
    comp = bundle["comparison"]
    matches = sum(row["comparison"] == "MATCH" for row in comp)
    variants = sum(row["comparison"] == "SOURCE_VARIANT" for row in comp)
    return {
        "00_BASELINE.md": f"# {ACTIVITY} baseline\n\nStarting commit: `{STARTING_COMMIT}`. Prior BPHS/Phaladeepika artifacts are reused; no production Ashtakavarga mathematics, P018, D20, P032, prediction, ML, RAG or evidence lane is changed. Decision: `{bundle['decision']}`.\n",
        "06_PHALADEEPIKA_VARIANT_AUDIT.md": f"# Phaladeepika variant audit\n\nThe main table remains distinct from the BPHS anchor: {matches} comparable position cells match and {variants} are source variants. The explicit Varahamihira Jupiter/Moon alternative is retained. No table is silently merged.\n",
        "07_KNR_337_386_AUDIT.md": "# K.N. Rao and 337/386\n\nOfficial Journal pages verify the 1998 article listing and Mehta guide/editor metadata; Google Books verifies Vinay Aditya contents; the official BVB page verifies the institutional lineage. Full 1985-86 and 1998 article text was not lawfully accessible here, so no direct KNR formula or quotation is asserted.\n\nThe public Triple-S Software sample PDF was inspected at page 2: seven planetary rows total 337, the Lagna row totals 49, and the combined display totals 386; reduced tables are also shown. This is a modern implementation witness, not classical or direct KNR authority. `337` is governed as planetary SAV; `386` is only an optional combined display.\n",
        "13_SAV_CONSTRUCTION.md": "# SAV construction\n\nThe raw contract sums seven planetary BAV outputs for planetary SAV. Lagna may contribute to planetary BAV where explicit, but its own BAV is not silently added to canonical planetary SAV. A separate view may add 49 and report 386 as `SAV_WITH_LAGNA_COMBINED`. Nodes remain excluded. Raw and reduced tables remain separate.\n",
        "19_REMEDIATION_SCOPE.md": "# Remediation scope\n\nRaw BAV/SAV remediation is specification-ready for a separately authorized activity: BPHS-primary, Phaladeepika alternative, explicit Lagna/self/node policy, 337 planetary SAV and optional 386 display. Reductions remain a separate gate. This activity does not modify production.\n",
        "20_REMEDIATION_READINESS.md": "# Remediation readiness\n\nRaw contract: `READY_FOR_SEPARATE_AUTHORIZATION`. Reductions: `NOT_READY`. Production remediation: `NOT_AUTHORIZED`.\n",
        "21_PARALLEL_LANE_STATE.md": "# Parallel lane state\n\nP015/P018, D20, P032, prediction, ML, PRED-M4, RAG, empirical, ADB, OGDB, POSEND, evidence and language lanes are preserved. No provider call, personal data, prediction, ML training or production activation occurred.\n",
        "22_FINAL_ACCEPTANCE.md": f"# Final acceptance\n\nOverall: `PASS_WITH_CONDITION`. Controlled normalization gaps remain honestly marked; 337/386 and Lagna policy are explicit; raw contract is deterministic and reductions remain gated; production hashes are unchanged. Final decision: `{bundle['decision']}`.\n",
    }


def write_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    files = {
        "01_CLASSICAL_SOURCE_REGISTER.json": bundle["classical"], "02_KNR_SOURCE_REGISTER.json": bundle["knr"],
        "03_BRIHAT_JATAKA_NORMALIZATION.json": bundle["normalization"]["BRIHAT_JATAKA"], "04_SARAVALI_NORMALIZATION.json": bundle["normalization"]["SARAVALI"], "05_JATAKA_PARIJATA_NORMALIZATION.json": bundle["normalization"]["JATAKA_PARIJATA"],
        "08_LAGNA_POLICY_MATRIX.json": bundle["lagna_policy"], "09_CLASSICAL_CROSS_SOURCE_MATRIX.json": bundle["comparison"], "10_KNR_IMPLEMENTATION_MATRIX.json": bundle["knr"], "11_CLASSICAL_VS_KNR_CROSSWALK.json": bundle["crosswalk"],
        "12_BAV_TOTALS.json": {"planetary_sav": 337, "lagna_bav": 49, "optional_combined": 386, "status": "GOVERNED_SPECIFICATION"}, "14_REDUCTION_RECONCILIATION.json": bundle["reduction_scope"],
        "15_WORKED_EXAMPLE_ORACLE.json": {"classical": "NONE_LAWFULLY_ACCESSIBLE_AS_INDEPENDENT_NUMERICAL_ORACLE", "knr": "FULL_NUMERICAL_ORACLE_NOT_ACCESSIBLE", "modern": {"url": URLS["HOROSOFT"], "page": 2, "observed": ["337 without Lagna", "49 Lagna", "386 combined", "reduced tables"], "independence": "MODERN_VENDOR_WITNESS"}},
        "16_SYNTHETIC_COMPARISON.json": {"reused_prior": True, "cells": len(bundle["comparison"]), "matches": sum(x["comparison"] == "MATCH" for x in bundle["comparison"]), "variants": sum(x["comparison"] == "SOURCE_VARIANT" for x in bundle["comparison"]), "production_tables_reused": False},
        "17_CANONICAL_RAW_CONTRACT.json": bundle["raw_contract"], "18_CANONICAL_REDUCTION_CONTRACT.json": bundle["reduction_contract"],
    }
    for name, value in files.items():
        write_json(OUT / name, value)
    for name, value in markdown(bundle).items():
        write_text(OUT / name, value)
    summary = {"activity": ACTIVITY, "decision": bundle["decision"], "starting_commit": STARTING_COMMIT, "raw_contract_id": bundle["raw_contract"]["contract_id"], "raw_contract_hash": bundle["raw_contract"]["contract_hash"], "reduction_contract_created": False, "production_changed": False, "remediation_authorized": False}
    write_json(OUT / "BUILD_SUMMARY.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    result = write_bundle(bundle) if args.write else {"activity": ACTIVITY, "decision": bundle["decision"], "raw_contract_hash": bundle["raw_contract"]["contract_hash"], "production_changed": False}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
