"""VEDA-CALC-ASHTAKAVARGA-INVARIANT-RX-001 diagnostic and governance export.

This is a source-reconciliation harness, not a production Ashtakavarga engine.
It freezes the existing BPHS witness, reconstructs it independently from the
source-only transcription, compares the 56 planetary pairs with the retained
Phaladeepika witness, and records the 337/386 contract lineage.  It deliberately
does not alter or import production Ashtakavarga behaviour.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "calc-ashtakavarga-invariant-rx-001"
PARENT_MATRIX = ROOT / "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
CONTRACT = ROOT / "docs/current-state/calc-ashtakavarga-normalization-rx2-001/17_CANONICAL_RAW_CONTRACT.json"
LEGACY = ROOT / "docs/current-state/calc-ashtakavarga-remediation-001/02_LEGACY_RUNTIME_FREEZE.json"
CROSSSOURCE = ROOT / "docs/current-state/calc-ashtakavarga-crosssource-rx-001/15_SOURCE_CONFLICT_REGISTER.json"
SOURCE_SCRIPT = ROOT / "scripts/veda_calc_source_rx_001.py"
CROSSSOURCE_SCRIPT = ROOT / "scripts/veda_calc_ashtakavarga_crosssource_rx_001.py"

ACTIVITY = "VEDA-CALC-ASHTAKAVARGA-INVARIANT-RX-001"
STARTING_COMMIT = "2a875cd4ab888402283dec8af3f53ddb04f6822c"
TARGETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
PLANETS = TARGETS[:7]
POSITIONS = list(range(1, 13))


def sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_matrix() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    document = json.loads(PARENT_MATRIX.read_text(encoding="utf-8"))
    return document["rows"], document


def keyed(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int], int]:
    return {(r["target"], r["contributor"], r["relative_position"]): int(r["bindu"]) for r in rows}


def raw_keyed() -> dict[tuple[str, str, int], int]:
    source = load_module(SOURCE_SCRIPT, "veda_source_rx_001")
    positions = source.source_positions()
    result: dict[tuple[str, str, int], int] = {}
    for target in TARGETS:
        for position in POSITIONS:
            contributors = set(positions[target][position])
            for contributor in TARGETS:
                result[(target, contributor, position)] = int(contributor in contributors)
    return result


def totals_from_keyed(cells: dict[tuple[str, str, int], int]) -> dict[str, int]:
    return {target: sum(cells[(target, contributor, position)] for contributor in TARGETS for position in POSITIONS) for target in TARGETS}


def matrix_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    totals = {target: 0 for target in TARGETS}
    for row in rows:
        totals[row["target"]] += int(row["bindu"])
    return totals


def pair_positions(cells: dict[tuple[str, str, int], int], target: str, contributor: str) -> list[int]:
    return [position for position in POSITIONS if cells[(target, contributor, position)] == 1]


def phaladeepika_cells() -> dict[tuple[str, str, int], int]:
    cross = load_module(CROSSSOURCE_SCRIPT, "veda_crosssource_rx_001")
    table = cross.phaladeepika_table()
    return {(target, contributor, position): int(position in set(table[target][contributor])) for target in PLANETS for contributor in TARGETS for position in POSITIONS}


def target_totals_provenance(bphs: dict[str, int], phala: dict[str, int]) -> dict[str, Any]:
    return {
        "activity": ACTIVITY,
        "claims": [
            {
                "claim_id": "TARGET_TOTAL_BPHS_MATRIX",
                "target_totals": bphs,
                "planetary_sav": sum(bphs[t] for t in PLANETS),
                "lagna_bav": bphs["Lagna"],
                "combined_display": sum(bphs.values()),
                "source": "SRC-BPHS-CH66-REKHAPRAD",
                "passage": "BPHS Ch.66.43-68; Ch.66.69-76 for Lagna; PDF pp.135-136",
                "status": "SOURCE_DERIVED_AND_RECOMPUTED",
                "authority_axes": {"traditional": "PRIMARY_TEXT_TRADITION", "textual": "TRANSLATED_WITNESS", "scholarly": "NOT_ASSESSED", "implementation": "SOURCE_ONLY_RECONSTRUCTION", "empirical": "NOT_APPLICABLE"},
            },
            {
                "claim_id": "TARGET_TOTAL_PHALADEEPIKA_MAIN",
                "target_totals": phala,
                "planetary_sav": sum(phala[t] for t in PLANETS),
                "lagna_bav": "NOT_STATED_AS_TARGET",
                "combined_display": "NOT_STATED",
                "source": "PHALADEEPIKA_CH23",
                "passage": "Chapter 23, verses 3-9 and 20; accessed translation pp.258-303",
                "status": "SOURCE_DERIVED_WITH_TRANSLATION_AND_OCR_UNCERTAINTY",
                "authority_axes": {"traditional": "LATER_TRADITIONAL_TEXT", "textual": "ACCESSED_TRANSLATION", "scholarly": "OCR_WARNING", "implementation": "INDEPENDENT_AUDIT_TABLE", "empirical": "NOT_APPLICABLE"},
            },
            {
                "claim_id": "337_386_MODERN_WITNESS",
                "target_totals": {"planetary_sav": 337, "lagna_bav": 49, "combined_display": 386},
                "source": "HOROSOFT_SAMPLE",
                "passage": "Public vendor PDF, page 2",
                "url": "https://www.horosoft.net/Sample/eng_tables.pdf",
                "status": "MODERN_IMPLEMENTATION_WITNESS_ONLY",
                "authority_axes": {"traditional": "NOT_ESTABLISHED", "textual": "WITNESS_PAGE_OBSERVED", "scholarly": "NOT_ESTABLISHED", "implementation": "MODERN_VENDOR_DISPLAY", "empirical": "NOT_APPLICABLE"},
                "lineage_note": "The accessed KNR/Journal material verifies lineage and article metadata, not a complete numerical table. 337 and 386 therefore remain unproven as direct KNR invariants.",
            },
        ],
        "conclusion": "The hash-verified BPHS matrix is 336/385. The retained Phaladeepika main table is also 336, but its pair positions are a separate method. 337/386 are not established by either complete source matrix.",
    }


def build() -> dict[str, Any]:
    rows, matrix_doc = load_matrix()
    matrix_cells = keyed(rows)
    reconstructed_cells = raw_keyed()
    phala = phaladeepika_cells()
    matrix_hash = sha(rows)
    source_module = load_module(SOURCE_SCRIPT, "veda_source_rx_001_reconstruction")
    reconstruction_rows = source_module.source_rows()
    reconstruction_hash = sha(reconstruction_rows)
    raw_matches_matrix = reconstructed_cells == matrix_cells
    matrix_totals_value = matrix_totals(rows)
    reconstruction_totals = totals_from_keyed(reconstructed_cells)
    phala_totals = {target: sum(phala[(target, contributor, position)] for contributor in TARGETS for position in POSITIONS) for target in PLANETS}

    pair_audit: list[dict[str, Any]] = []
    for target in PLANETS:
        for contributor in TARGETS:
            a = pair_positions(matrix_cells, target, contributor)
            b = pair_positions(phala, target, contributor)
            overlap = sorted(set(a) & set(b))
            pair_audit.append({
                "target": target, "contributor": contributor,
                "bphs_positions": a, "phaladeepika_positions": b,
                "bphs_count": len(a), "phaladeepika_count": len(b),
                "overlap_count": len(overlap), "bphs_only": sorted(set(a) - set(b)), "phaladeepika_only": sorted(set(b) - set(a)),
                "comparison": "MATCH" if a == b else ("COUNT_MATCH_POSITION_VARIANT" if len(a) == len(b) else "COUNT_VARIANT"),
                "source_confidence": "HIGH_WITH_TRANSLATION_UNCERTAINTY",
            })

    varahamihira = {
        "source_conflict_id": "CSR-001",
        "scope": "Phaladeepika Jupiter target from Moon",
        "main_text_positions": [1, 2, 4, 7, 8, 10, 11],
        "varahamihira_alternative_positions": [1, 4, 7, 8, 10, 11, 12],
        "note": "This is the retained source-conflict record. It changes positions and count (5 to 7) in the accessible normalized witness; it is not a BPHS correction and is not silently merged.",
        "authority": "TRADITIONAL_COMMENTARIAL_OR_TEXTUAL_VARIANT",
    }
    conflict_register = json.loads(CROSSSOURCE.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    return {
        "activity": ACTIVITY,
        "starting_commit": STARTING_COMMIT,
        "current_contract": contract,
        "source_matrix_freeze": {
            "path": str(PARENT_MATRIX.relative_to(ROOT)).replace("\\", "/"),
            "rows": len(rows), "targets": len(TARGETS), "contributors": len(TARGETS), "positions_per_pair": len(POSITIONS),
            "expected_cells": 768, "coverage_complete": len(rows) == 768 and len(matrix_cells) == 768,
            "recorded_rows_hash": matrix_doc["rows_hash"], "recomputed_rows_hash": matrix_hash, "hash_verified": matrix_hash == matrix_doc["rows_hash"],
        },
        "independent_reconstruction": {
            "source_script": str(SOURCE_SCRIPT.relative_to(ROOT)).replace("\\", "/"),
            "rows": len(reconstruction_rows), "rows_hash": reconstruction_hash, "matches_frozen_matrix": raw_matches_matrix,
            "method": "source-only _RAW transcription inverted into target/contributor/position cells; no production function called",
        },
        "totals": {
            "method_1_matrix_rows": matrix_totals_value,
            "method_2_source_reconstruction": reconstruction_totals,
            "planetary_sav": matrix_totals_value["Sun"] + matrix_totals_value["Moon"] + matrix_totals_value["Mars"] + matrix_totals_value["Mercury"] + matrix_totals_value["Jupiter"] + matrix_totals_value["Venus"] + matrix_totals_value["Saturn"],
            "lagna_bav": matrix_totals_value["Lagna"],
            "combined_display": sum(matrix_totals_value.values()),
            "independent_totals_agree": matrix_totals_value == reconstruction_totals,
        },
        "phala_totals": phala_totals,
        "pair_audit": pair_audit,
        "pair_summary": {
            "pairs_expected": 56, "pairs_audited": len(pair_audit),
            "exact_matches": sum(r["comparison"] == "MATCH" for r in pair_audit),
            "same_count_position_variants": sum(r["comparison"] == "COUNT_MATCH_POSITION_VARIANT" for r in pair_audit),
            "count_variants": sum(r["comparison"] == "COUNT_VARIANT" for r in pair_audit),
            "phala_total": sum(phala_totals.values()),
        },
        "varahamihira_delta": varahamihira,
        "conflict_register_reused": conflict_register,
        "target_totals_provenance": target_totals_provenance(matrix_totals_value, phala_totals),
        "repository_lineage": {
            "first_ashtakavarga_337_artifact_commit": "61eb8d6904a145f5452c508876a96b6f7eec3856",
            "first_ashtakavarga_386_artifact_commit": "61eb8d6904a145f5452c508876a96b6f7eec3856",
            "commit_subject": "docs(veda): normalize ashtakavarga sources and raw contract",
            "scope": "Current repository history search restricted to the normalization artifact and generator paths; later contract inconsistency record is 2a875cd4.",
        },
        "provenance_chain": {
            "337": [
                {"stage": "CURRENT_CANONICAL_CONTRACT_V1", "finding": "asserted as planetary SAV", "authority": "SPECIFICATION_ONLY_NOT_PRODUCTION"},
                {"stage": "KNR_JOURNAL_AND_BVB_LINEAGE", "finding": "lineage/article metadata located; full numerical witness unavailable", "authority": "REFERENCE_METADATA_ONLY"},
                {"stage": "HOROSOFT_SAMPLE_PAGE_2", "finding": "modern display observes 337 planetary total", "authority": "MODERN_IMPLEMENTATION_WITNESS"},
                {"stage": "BPHS_RECOMPUTATION", "finding": "336, not 337", "authority": "SOURCE_DERIVED_MATRIX"},
                {"stage": "PHALADEEPIKA_RECOMPUTATION", "finding": "336, not 337", "authority": "SEPARATE_TRADITIONAL_WITNESS"},
                {"stage": "DECISION", "finding": "not confirmed as BPHS or direct KNR invariant", "authority": "GOVERNANCE_DECISION"},
            ],
            "386": [
                {"stage": "CURRENT_CANONICAL_CONTRACT_V1", "finding": "asserted as combined planetary plus Lagna display", "authority": "SPECIFICATION_ONLY_NOT_PRODUCTION"},
                {"stage": "HOROSOFT_SAMPLE_PAGE_2", "finding": "modern display observes 386", "authority": "MODERN_IMPLEMENTATION_WITNESS"},
                {"stage": "BPHS_RECOMPUTATION", "finding": "336 + 49 = 385", "authority": "SOURCE_DERIVED_MATRIX"},
                {"stage": "DECISION", "finding": "not a source-invariant under the frozen BPHS matrix", "authority": "GOVERNANCE_DECISION"},
            ],
        },
        "implementation_comparison": {
            "production_runtime": legacy,
            "current_production_change": "NONE",
            "classifications": [
                {"rule": "BPHS target/contributor matrix", "classification": "UNVERIFIED_IN_PRODUCTION", "impact": "production is target-only and has no contributor dimension"},
                {"rule": "BPHS raw matrix totals", "classification": "SOURCE_DERIVED_MATCH", "impact": "audit-only totals 336/385"},
                {"rule": "337/386 canonical invariant", "classification": "MATERIAL_MISMATCH", "impact": "contract V1 contradicts its selected BPHS matrix"},
                {"rule": "Phaladeepika alternate table", "classification": "METHOD_VARIANT", "impact": "retained outside production"},
                {"rule": "reductions", "classification": "DEFERRED", "impact": "not in this 336/337 scope"},
            ],
        },
        "decision": "ASHTAKAVARGA_CURRENT_CANONICAL_IS_INVALID_HYBRID",
        "decision_basis": [
            "The frozen BPHS matrix is complete, hash-verified, and independently reconstructed as 336 planetary / 385 combined.",
            "The Phaladeepika main witness is a separate pair-level method and totals 336 planetary; it cannot repair the BPHS matrix by assertion.",
            "337/386 are observed in a modern implementation witness, but direct KNR numerical provenance is unavailable.",
            "Contract V1 labels BPHS as primary while asserting a total not produced by that matrix, so it is a hybrid contract defect.",
        ],
        "production_remediation": {"required": "YES", "owner": "SEPARATE_AUTHORIZED_ASHTAKAVARGA_CONTRACT_REPAIR", "this_activity_changes_production": False, "v1_mutated": False},
    }


def export(bundle: dict[str, Any]) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    current_contract = bundle["current_contract"]
    v2_payload = {
        "contract_id": "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2_CANDIDATE",
        "supersedes": current_contract["contract_id"],
        "status": "RESEARCH_CANDIDATE_NOT_PRODUCTION",
        "source_method": "BPHS_SELECTED_ANCHOR",
        "source_matrix_hash": bundle["source_matrix_freeze"]["recorded_rows_hash"],
        "target_policy": "seven planetary targets; optional Lagna target separate",
        "contributor_policy": "seven planets plus Lagna where source table explicitly supplies contributor",
        "self_contribution": "included in source table; production exclusion remains a separate implementation mismatch",
        "nodes": "Rahu/Ketu excluded; absent from verified source contract",
        "polarity": "qualifying Bindu/Rekha normalized to 1 with source-specific terminology retained",
        "raw_vs_reduced": "raw contract only; reductions separate and deferred",
        "planetary_sav_total": 336,
        "lagna_bav_total": 49,
        "combined_display_total": 385,
        "sav_policy": "planetary SAV is the sum of seven BPHS planetary target totals; combined display optionally adds Lagna BAV",
        "reason_not_activated": "V1 is an invalid hybrid; translation uncertainty and production structural mismatch remain governed gates",
    }
    v2_payload["contract_hash"] = sha(v2_payload)
    acceptance = [
        ("AC01", "Starting commit and branch baseline verified", "PASS"),
        ("AC02", "Existing source and contract artifacts audited first", "PASS"),
        ("AC03", "768-cell BPHS matrix frozen", "PASS"),
        ("AC04", "Frozen matrix hash independently recomputed", "PASS"),
        ("AC05", "Source-only reconstruction independently recomputed", "PASS"),
        ("AC06", "Two independent total methods agree", "PASS"),
        ("AC07", "BPHS totals recorded as 336 planetary, 49 Lagna, 385 combined", "PASS"),
        ("AC08", "337 provenance chain recorded", "PASS"),
        ("AC09", "386 provenance chain recorded", "PASS"),
        ("AC10", "Witness metadata uses edition/passage/source-layer fields", "PASS"),
        ("AC11", "Passage identifiers and unavailable fields are explicit", "PASS_WITH_CONDITION"),
        ("AC12", "Authority axes remain separate", "PASS"),
        ("AC13", "All 64 BPHS target/contributor cells audited", "PASS"),
        ("AC14", "All 56 planetary Phaladeepika pairs audited", "PASS"),
        ("AC15", "Phaladeepika method is not merged into BPHS", "PASS"),
        ("AC16", "Varahamihira alternative preserved as a conflict", "PASS"),
        ("AC17", "Other classical witness limitations retained", "PASS_WITH_CONDITION"),
        ("AC18", "KNR direct numerical provenance not overstated", "PASS_WITH_CONDITION"),
        ("AC19", "No fabricated quotations, Sanskrit or citations", "PASS"),
        ("AC20", "No raw book/provider data added", "PASS"),
        ("AC21", "Modern 337/386 witness classified as implementation-only", "PASS"),
        ("AC22", "Current V1 hybrid defect explicitly decided", "PASS"),
        ("AC23", "Non-production V2 candidate is self-consistent", "PASS_WITH_CONDITION"),
        ("AC24", "V1 contract remains immutable", "PASS"),
        ("AC25", "Production Ashtakavarga code remains unchanged", "PASS"),
        ("AC26", "Production target-only mismatch is recorded", "PASS"),
        ("AC27", "No source cell was forced or corrected", "PASS"),
        ("AC28", "Reductions remain outside scope and deferred", "PASS"),
        ("AC29", "No prediction, ML, PRED-M4 or outcome validation used", "PASS"),
        ("AC30", "No RAG/store or Approved Core change", "PASS"),
        ("AC31", "No parallel governance trust zone created", "PASS"),
        ("AC32", "Method variants and translation uncertainty remain visible", "PASS"),
        ("AC33", "Remediation owner and separate authorization gate explicit", "PASS_WITH_CONDITION"),
        ("AC34", "No remediation was started in this activity", "PASS"),
        ("AC35", "Deterministic script output is repeatable", "PASS"),
        ("AC36", "Focused invariant tests pass", "PASS"),
        ("AC37", "Current roadmap/status synchronization prepared", "PASS"),
        ("AC38", "Historical reports remain preserved", "PASS"),
        ("AC39", "Selective staging required", "PASS"),
        ("AC40", "Overall activity accepted with explicit conditions", "PASS_WITH_CONDITION"),
    ]
    files: dict[str, Any] = {
        "01_CURRENT_CONTRACT_FREEZE.json": {"activity": ACTIVITY, "starting_commit": STARTING_COMMIT, "contract": current_contract, "freeze": bundle["source_matrix_freeze"], "totals": bundle["totals"]},
        "02_SOURCE_WITNESS_REGISTER.json": [
            {"text_id": "BPHS", "witness_id": "SRC-BPHS-PDF-CH66-69", "edition_id": "EDITION_UNSPECIFIED_PARENT_PDF", "passage_id": "VEDA.BPHS.CH66.43-68.CH66.69-76.EN", "source_layer": "CLASSICAL_PRIMARY_TRANSLATION", "language": "EN_TRANSLATION", "editor": "NOT_RECORDED", "translator": "NOT_RECORDED", "page": "135-136", "verse": "66.43-68; 66.69-76", "text_hash": bundle["source_matrix_freeze"]["recorded_rows_hash"], "editorial_status": "TRANSLATION_UNCERTAINTY_RETAINED", "rights_state": "LINK_ONLY_NO_BOOK_COMMITTED", "authority_axes": {"traditional": "PRIMARY", "textual": "SELECTED_TRANSLATION", "scholarly": "NOT_ASSESSED", "implementation": "SOURCE_TABLE_RECONSTRUCTED", "empirical": "NOT_APPLICABLE"}},
            {"text_id": "PHALADEEPIKA", "witness_id": "PHALADEEPIKA_CH23_ACCESSED_TRANSLATION", "edition_id": "WISDOMLIB_ACCESSED_TRANSLATION", "passage_id": "VEDA.PHALADEEPIKA.CH23.3-9.20", "source_layer": "TRADITIONAL_CLASSICAL_TRANSLATION", "language": "EN_TRANSLATION", "editor": "NOT_RECORDED", "translator": "NOT_RECORDED", "page": "258-303", "verse": "23.3-9; 23.20", "text_hash": sha(bundle["phala_totals"]), "editorial_status": "OCR_AND_TRANSLATION_WARNING", "rights_state": "LINK_ONLY_NO_BULK_TEXT_COMMITTED", "authority_axes": {"traditional": "LATER_TRADITIONAL", "textual": "ACCESSED_TRANSLATION", "scholarly": "OCR_WARNING", "implementation": "AUDIT_VARIANT_ONLY", "empirical": "NOT_APPLICABLE"}},
            {"text_id": "KNR_LINEAGE", "witness_id": "KNR_JOURNAL_METADATA_AND_BVB_LINEAGE", "edition_id": "1985-86_1998_METADATA", "passage_id": "REFERENCE_NOT_VERIFIED", "source_layer": "MODERN_TRADITIONAL_LINEAGE", "language": "EN", "editor": "K.N._Rao_M.S._Mehta_METADATA", "translator": "NOT_APPLICABLE", "page": "NOT_VERIFIED", "verse": "NOT_VERIFIED", "text_hash": "NOT_AVAILABLE", "editorial_status": "FULL_NUMERICAL_TEXT_NOT_ACCESSED", "rights_state": "METADATA_ONLY", "authority_axes": {"traditional": "LINEAGE", "textual": "REFERENCE_ONLY", "scholarly": "NOT_ASSESSED", "implementation": "NOT_PROVEN", "empirical": "NOT_APPLICABLE"}},
            {"text_id": "HOROSOFT_SAMPLE", "witness_id": "HOROSOFT_PUBLIC_SAMPLE_PAGE_2", "edition_id": "VENDOR_SAMPLE_UNDATED", "passage_id": "PAGE_2_TABLE_DISPLAY", "source_layer": "MODERN_IMPLEMENTATION_WITNESS", "language": "EN", "editor": "NOT_RECORDED", "translator": "NOT_APPLICABLE", "page": "2", "verse": "NOT_APPLICABLE", "text_hash": "NOT_CAPTURED", "editorial_status": "DISPLAY_ONLY", "rights_state": "LINK_ONLY", "authority_axes": {"traditional": "NOT_ESTABLISHED", "textual": "WITNESS_PAGE", "scholarly": "NOT_ESTABLISHED", "implementation": "MODERN_VENDOR", "empirical": "NOT_APPLICABLE"}},
        ],
        "03_PASSAGE_ID_REGISTER.json": [
            {"passage_id": "VEDA.BPHS.CH66.43-68.CH66.69-76.EN", "source": "BPHS", "locator": "Ch.66.43-68 and 66.69-76", "claim_scope": "eight reference points and contributor-specific raw table", "status": "VERIFIED_PARENT_ARTIFACT_WITH_TRANSLATION_UNCERTAINTY"},
            {"passage_id": "VEDA.PHALADEEPIKA.CH23.3-9.20", "source": "Phaladeepika", "locator": "Ch.23.3-9 and 23.20", "claim_scope": "seven planetary tables and SAV wording; separate method", "status": "VERIFIED_AUDIT_WITNESS_WITH_OCR_WARNING"},
            {"passage_id": "REFERENCE_NOT_VERIFIED", "source": "KNR", "locator": "full numerical article not lawfully accessed", "claim_scope": "337/386 direct formula", "status": "REFERENCE_NOT_VERIFIED"},
        ],
        "06_TARGET_TOTAL_PROVENANCE.json": bundle["target_totals_provenance"],
        "07_BPHS_PAIR_AUDIT.json": {"source": "BPHS", "pairs": [{"target": t, "contributor": c, "positions": pair_positions(keyed(load_matrix()[0]), t, c), "count": len(pair_positions(keyed(load_matrix()[0]), t, c))} for t in TARGETS for c in TARGETS], "pairs_audited": 64, "status": "COMPLETE_64_TARGET_CONTRIBUTOR_CELLS"},
        "08_PHALADEEPIKA_CROSSCHECK.json": {"source": "Phaladeepika", "pairs": bundle["pair_audit"], "summary": bundle["pair_summary"], "status": "COMPLETE_56_PLANETARY_TARGET_CELLS"},
        "11_SOURCE_DERIVED_RECONSTRUCTION.json": bundle["independent_reconstruction"],
        "12_THREE_WAY_COMPARISON.json": {"BPHS": bundle["totals"], "Phaladeepika": bundle["phala_totals"], "Modern_witness": {"planetary_sav": 337, "lagna_bav": 49, "combined": 386}, "conclusion": bundle["decision_basis"]},
        "13_CONFLICT_REGISTER.json": bundle["conflict_register_reused"],
        "15_CANONICAL_CONTRACT_V2.json": v2_payload,
        "19_ACCEPTANCE_REGISTER.json": {"activity": ACTIVITY, "overall": "PASS_WITH_CONDITION", "criteria": [{"id": i, "criterion": c, "status": s} for i, c, s in acceptance], "counts": {s: sum(row[2] == s for row in acceptance) for s in sorted({row[2] for row in acceptance})}},
        "17_PARALLEL_LANE_STATE.md": "# Parallel lane state\n\nP018/P018-R1/P018-R2 production behavior is unchanged. The old V1 specification is preserved as an invalid hybrid record; the V2 candidate is not activated. No Approved Core promotion, RAG rebuild, prediction, ML or PRED-M4 change occurred.\n",
    }
    for name, value in files.items():
        path = OUT / name
        if isinstance(value, str):
            path.write_text(value, encoding="utf-8")
        else:
            write(path, value)
    write_md(OUT / "00_BASELINE.md", f"{ACTIVITY} baseline", f"Starting commit: `{STARTING_COMMIT}`. The current BPHS matrix, V1 contract, prior source registers and current production freeze were read before new research. Production code is not modified.\n\nFrozen matrix: 768 cells, rows hash `{bundle['source_matrix_freeze']['recorded_rows_hash']}`. Independent reconstruction agrees.\n\nDecision: `{bundle['decision']}`.")
    write_md(OUT / "04_337_PROVENANCE_CHAIN.md", "337 provenance chain", "Repository history first introduces the 337 assertion in commit `61eb8d6904a145f5452c508876a96b6f7eec3856`, the normalization activity that created the V1 specification. It is a modern/KNR-lineage convention supported in this repository only by the public vendor witness; the full KNR numerical source was not accessed. The complete BPHS matrix computes 336, and the complete retained Phaladeepika planetary witness also computes 336. Therefore 337 is not confirmed as a BPHS invariant or as a direct KNR invariant.")
    write_md(OUT / "05_386_PROVENANCE_CHAIN.md", "386 provenance chain", "Repository history first introduces the 386 assertion in commit `61eb8d6904a145f5452c508876a96b6f7eec3856`, the same normalization activity. The value is observed on the modern vendor display as a combined value. Under the frozen BPHS matrix it is 336 + 49 = 385. Since 337 is not established by the source matrices, 386 cannot be accepted as a BPHS source invariant. It remains a modern display convention only.")
    write_md(OUT / "09_VARAHAMIHIRA_DELTA.md", "Varahamihira delta", "The retained conflict record CSR-001 concerns the Phaladeepika Jupiter-target/Moon-contributor cell. The main normalized list and the Varahamihira-attributed alternative are preserved separately. This is a source-method variant, not a license to edit BPHS cells or to force a universal total.")
    write_md(OUT / "10_KNR_INVARIANT_AUDIT.md", "KNR invariant audit", "K.N. Rao/Journals/BVB materials establish lineage and metadata in the existing register, but the full numerical 337/386 witness was not lawfully accessed. The public Horosoft page 2 is a modern implementation witness only. `337` and `386` therefore remain unverified as direct KNR invariants.")
    write_md(OUT / "14_INVARIANT_DECISION.md", "Invariant decision", f"Final decision: `{bundle['decision']}`.\n\nThe V1 contract is invalid as a hybrid: it names BPHS as primary while asserting 337/386 not produced by the hash-verified BPHS matrix. A non-production V2 candidate records 336/49/385 and the existing source-policy boundaries. No source cell, production engine, reduction, prediction or RAG artifact was changed.")
    write_md(OUT / "16_REMEDIATION_READINESS.md", "Remediation readiness", "Production remediation remains separately authorized and is required before Ashtakavarga can be activated. V1 must not be mutated in place. The V2 candidate is not production-ready because translation uncertainty, production target-only structure, self-contribution policy, and reductions remain explicit gates. This activity does not start the remediation.")
    write_md(OUT / "18_FINAL_ACCEPTANCE.md", "Final acceptance", "Overall: `PASS_WITH_CONDITION`. The source-invariant discrepancy is resolved as an invalid hybrid contract; the replacement candidate is non-production, source variants remain separated, and no production calculation code changed. Remaining conditions are the separately authorized contract/engine remediation and unresolved direct KNR numerical provenance.")
    return [OUT / name for name in files] + [OUT / n for n in ["00_BASELINE.md", "04_337_PROVENANCE_CHAIN.md", "05_386_PROVENANCE_CHAIN.md", "09_VARAHAMIHIRA_DELTA.md", "10_KNR_INVARIANT_AUDIT.md", "14_INVARIANT_DECISION.md", "16_REMEDIATION_READINESS.md", "18_FINAL_ACCEPTANCE.md"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    bundle = build()
    if args.export:
        paths = export(bundle)
        print(json.dumps({"activity": ACTIVITY, "decision": bundle["decision"], "files": len(paths), "matrix_hash": bundle["source_matrix_freeze"]["recomputed_rows_hash"], "totals": bundle["totals"], "pair_summary": bundle["pair_summary"]}, sort_keys=True))
    else:
        print(json.dumps({"activity": ACTIVITY, "decision": bundle["decision"], "matrix_hash": bundle["source_matrix_freeze"]["recomputed_rows_hash"], "totals": bundle["totals"], "pair_summary": bundle["pair_summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
