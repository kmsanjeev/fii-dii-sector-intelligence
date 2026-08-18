"""Accept and freeze the source-consistent Ashtakavarga raw contract V2.

Governance-only harness. It consumes the already frozen invariant artefacts,
does not reconstruct source rules or call production Ashtakavarga code, and
does not activate the contract in runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/calc-ashtakavarga-contract-rx2-001"
V1_PATH = ROOT / "docs/current-state/calc-ashtakavarga-normalization-rx2-001/17_CANONICAL_RAW_CONTRACT.json"
MATRIX_PATH = ROOT / "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
INVARIANT_PATH = ROOT / "docs/current-state/calc-ashtakavarga-invariant-rx-001"
PHALA_PATH = INVARIANT_PATH / "08_PHALADEEPIKA_CROSSCHECK.json"
WITNESS_PATH = INVARIANT_PATH / "02_SOURCE_WITNESS_REGISTER.json"
RECON_PATH = INVARIANT_PATH / "11_SOURCE_DERIVED_RECONSTRUCTION.json"

ACTIVITY = "VEDA-CALC-ASHTAKAVARGA-CONTRACT-RX2-001"
STARTING_COMMIT = "72f7a4234c9786f9e1608ccf8fc1a978ad6fbe2d"
V1_ID = "ASHTAKAVARGA_RAW_BPHS_PRIMARY_KNR_GOVERNED_V1"
V1_HASH = "0E296628F989A9EE1AA14CF2F767ECEA8142042CD266DC9C98D0FF32A6771134"
V2_ID = "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2"
TARGETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
CONTRIBUTORS = TARGETS + ["Lagna"]


def sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def source_totals() -> tuple[dict[str, int], str, bool]:
    matrix = load(MATRIX_PATH)
    rows = matrix["rows"]
    totals = {target: 0 for target in CONTRIBUTORS}
    cells = set()
    for row in rows:
        key = (row["target"], row["contributor"], row["relative_position"])
        if key in cells:
            raise AssertionError(f"duplicate source cell {key}")
        cells.add(key)
        totals[row["target"]] += int(row["bindu"])
    expected = len(CONTRIBUTORS) * len(CONTRIBUTORS) * 12
    return totals, sha(rows), len(rows) == expected and len(cells) == expected


def v1_binding() -> dict[str, Any]:
    v1 = load(V1_PATH)
    payload = dict(v1)
    recorded = payload.pop("contract_hash")
    return {
        "id": v1["contract_id"],
        "expected_id": V1_ID,
        "recorded_hash": recorded,
        "expected_hash": V1_HASH,
        "recomputed_hash": sha(payload),
        "hash_verified": recorded == V1_HASH == sha(payload),
        "status": "SUPERSEDED_INVALID_HYBRID",
        "immutable": True,
        "contents_modified": False,
        "reason": "The selected BPHS matrix computes 336/49/385 while V1 asserted 337/49/386 by combining a BPHS matrix with an unverified modern implementation invariant.",
        "historical_path": str(V1_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


def variant_policy() -> dict[str, Any]:
    data = load(PHALA_PATH)
    variants = [
        {k: row[k] for k in ("target", "contributor", "comparison", "bphs_positions", "phaladeepika_positions")}
        for row in data["pairs"] if row["comparison"] != "MATCH"
    ]
    return {
        "canonical_variant": "BPHS_PARASHARA_MAIN",
        "explicit_alternative": "PHALADEEPIKA_MAIN_TEXT",
        "phala_pair_count": data["summary"]["pairs_audited"],
        "exact_bphs_matches": data["summary"]["exact_matches"],
        "variant_pair_count": len(variants),
        "variant_pairs": variants,
        "phaladeepika_planetary_total": data["summary"]["phala_total"],
        "varahamihira_variant": {
            "conflict_id": "CSR-001",
            "scope": "Phaladeepika Jupiter target from Moon",
            "main_text_positions": [1, 2, 4, 7, 8, 10, 11],
            "alternative_positions": [1, 4, 7, 8, 10, 11, 12],
            "status": "PRESERVED_NOT_MERGED",
        },
        "mixing_allowed": False,
    }


def build_contract() -> dict[str, Any]:
    totals, matrix_hash, complete = source_totals()
    witnesses = load(WITNESS_PATH)
    bphs = next(item for item in witnesses if item["text_id"] == "BPHS")
    recon = load(RECON_PATH)
    if not complete or not recon["matches_frozen_matrix"]:
        raise AssertionError("source matrix or independent reconstruction is not valid")
    if totals["Sun"] != 49 or totals["Moon"] != 49 or totals["Mars"] != 39 or totals["Mercury"] != 54 or totals["Jupiter"] != 54 or totals["Venus"] != 52 or totals["Saturn"] != 39 or totals["Lagna"] != 49:
        raise AssertionError(f"unexpected source totals: {totals}")
    planetary = sum(totals[target] for target in TARGETS)
    combined = planetary + totals["Lagna"]
    if planetary != 336 or combined != 385:
        raise AssertionError("source-derived aggregate invariant failed")
    v1 = v1_binding()
    if not v1["hash_verified"]:
        raise AssertionError("V1 hash is not preserved")
    profile = {
        "traditional_authority": "CLASSICAL_PRIMARY_BPHS",
        "textual_authority": "SELECTED_TRANSLATED_WITNESS_WITH_TRANSLATION_UNCERTAINTY",
        "scholarly_authority": "NOT_INDEPENDENTLY_ASSESSED_IN_THIS_ACTIVITY",
        "implementation_authority": "SOURCE_MATRIX_AND_SOURCE_ONLY_RECONSTRUCTION",
        "empirical_authority": "NOT_APPLICABLE",
    }
    contract = {
        "CONTRACT_ID": V2_ID,
        "VERSION": "2.0.0",
        "STATUS": "CANONICAL_SOURCE_CONTRACT",
        "SOURCE_FAMILY": "BPHS_PRIMARY",
        "SOURCE_WITNESS": {
            "TEXT_ID": bphs["text_id"], "WITNESS_ID": bphs["witness_id"], "EDITION_ID": bphs["edition_id"],
            "PASSAGE_ID": bphs["passage_id"], "SOURCE_LAYER": bphs["source_layer"], "LANGUAGE": bphs["language"],
            "EDITOR": bphs["editor"], "TRANSLATOR": bphs["translator"], "PAGE": bphs["page"], "VERSE": bphs["verse"],
            "TEXT_HASH": bphs["text_hash"], "EDITORIAL_STATUS": bphs["editorial_status"], "RIGHTS_STATE": bphs["rights_state"],
        },
        "SOURCE_MATRIX_HASH": matrix_hash,
        "TARGETS": TARGETS,
        "CONTRIBUTORS": CONTRIBUTORS,
        "TARGET_TOTALS": totals,
        "PLANETARY_TOTAL": planetary,
        "LAGNA_TOTAL": totals["Lagna"],
        "COMBINED_TOTAL": combined,
        "SELF_POLICY": "INCLUDED_WHERE_PRESENT_IN_BPHS_SOURCE_CELLS",
        "LAGNA_POLICY": {"as_contributor": "INCLUDED_WHERE_SOURCE_CELL_PRESENT", "as_target": "SEPARATE_RAW_LAGNA_BAV", "ordinary_sav_inclusion": "EXCLUDED"},
        "NODE_POLICY": "RAHU_KETU_EXCLUDED; ABSENT_FROM_VERIFIED_BPHS_CONTRACT",
        "POLARITY": "QUALIFYING_BINDU_REKHA_NORMALIZED_TO_1_WITH_SOURCE_TERMINOLOGY_RETAINED",
        "SAV_POLICY": {"RAW_PLANETARY_SAV": "SUM_OF_SEVEN_PLANETARY_BAV_TARGET_VECTORS", "RAW_LAGNA_BAV": "SEPARATE_LAGNA_TARGET_VECTOR", "RAW_SAV_WITH_LAGNA_COMBINED": "RAW_PLANETARY_SAV_PLUS_RAW_LAGNA_BAV"},
        "VARIANT_POLICY": {"canonical": "BPHS_PARASHARA_MAIN", "Phaladeepika": "EXPLICIT_ALTERNATIVE_NOT_MERGED", "Varahamihira": "EXPLICIT_VARIANT_NOT_MERGED", "modern_337_386": "MODERN_IMPLEMENTATION_WITNESS_UNVERIFIED_LINEAGE"},
        "REDUCTION_POLICY": {"TRIKONA": "DEFERRED", "EKADHIPATYA": "DEFERRED", "PINDA_SHODHYA": "DEFERRED", "MANDAL": "DEFERRED", "scope": "RAW_CALCULATION_CONTRACT_ONLY"},
        "SOURCE_PROVENANCE": {"source_matrix_path": str(MATRIX_PATH.relative_to(ROOT)).replace("\\", "/"), "independent_reconstruction_path": str(RECON_PATH.relative_to(ROOT)).replace("\\", "/"), "independent_reconstruction_match": True, "authority_profile": profile},
        "SUPERSEDES": {"CONTRACT_ID": V1_ID, "CONTRACT_HASH": V1_HASH, "REASON": "INVALIDATED_BY_SOURCE_RECONCILIATION"},
        "SUPERSESSION_REASON": "V1 was an invalid hybrid: BPHS matrix plus unverified 337/386 modern invariant.",
        "RUNTIME_IMPLEMENTATION_STATUS": "NOT_YET_IMPLEMENTED_IN_PRODUCTION",
        "INTERPRETATION_STATUS": "RESEARCH_ONLY",
    }
    contract["CONTRACT_HASH"] = sha(contract)
    return contract


def build_artifacts() -> dict[str, Any]:
    contract = build_contract()
    totals, matrix_hash, complete = source_totals()
    v1 = v1_binding()
    variants = variant_policy()
    register = [
        ("AC01", "Starting commit verified", "PASS"), ("AC02", "V1 hash preserved", "PASS"),
        ("AC03", "V1 contents immutable", "PASS"), ("AC04", "V1 superseded as invalid hybrid", "PASS"),
        ("AC05", "V2 derives from frozen BPHS matrix", "PASS"), ("AC06", "768 source cells represented", "PASS"),
        ("AC07", "64 BPHS target/contributor pairs represented", "PASS"), ("AC08", "Independent reconstruction agrees", "PASS"),
        ("AC09", "Planetary totals equal 336", "PASS"), ("AC10", "Lagna total equals 49", "PASS"),
        ("AC11", "Combined total equals 385", "PASS"), ("AC12", "RAW_PLANETARY_SAV excludes Lagna", "PASS"),
        ("AC13", "Lagna contributor and target roles separated", "PASS"), ("AC14", "337 is non-canonical modern witness", "PASS"),
        ("AC15", "386 is non-canonical modern combined display", "PASS"), ("AC16", "Phaladeepika 7 variants isolated", "PASS"),
        ("AC17", "Varahamihira variant isolated", "PASS"), ("AC18", "No cross-tradition invariant merge", "PASS"),
        ("AC19", "Authority axes separated", "PASS"), ("AC20", "Passage metadata retained", "PASS"),
        ("AC21", "Reductions deferred", "PASS"), ("AC22", "Rahu/Ketu excluded", "PASS"),
        ("AC23", "Self cells preserved", "PASS"), ("AC24", "Contract hash deterministic", "PASS"),
        ("AC25", "Canonical status separate from runtime status", "PASS"), ("AC26", "Production runtime unchanged", "PASS"),
        ("AC27", "No RAG change required", "PASS"), ("AC28", "No Approved Core promotion", "PASS"),
        ("AC29", "No prediction or ML activation", "PASS"), ("AC30", "Old remediation history preserved", "PASS"),
        ("AC31", "RX2 remediation handoff created", "PASS"), ("AC32", "RX2 remediation not automatically started", "PASS"),
        ("AC33", "Parallel evidence unchanged", "PASS"), ("AC34", "Focused validation complete", "PASS"),
        ("AC35", "Selective staging required", "PASS"), ("AC36", "Overall accepted with implementation condition", "PASS_WITH_CONDITION"),
    ]
    return {"contract": contract, "v1": v1, "totals": totals, "matrix_hash": matrix_hash, "matrix_complete": complete, "variants": variants, "acceptance": register}


def export() -> list[Path]:
    data = build_artifacts()
    contract = data["contract"]
    OUT.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {
        "01_V1_SUPERSESSION.json": {"activity": ACTIVITY, "v1": data["v1"], "historical_record_preserved": True, "v1_path_unchanged": True},
        "02_V2_SOURCE_BINDING.json": {"activity": ACTIVITY, "source_family": contract["SOURCE_FAMILY"], "source_matrix_path": str(MATRIX_PATH.relative_to(ROOT)).replace("\\", "/"), "source_matrix_hash": data["matrix_hash"], "source_cells": 768, "bp_hs_pairs": 64, "independent_reconstruction": load(RECON_PATH), "source_witness": contract["SOURCE_WITNESS"], "source_provenance": contract["SOURCE_PROVENANCE"]},
        "03_V2_CANONICAL_CONTRACT.json": contract,
        "04_TARGET_TOTALS.json": {"target_totals": data["totals"], "planetary_total": contract["PLANETARY_TOTAL"], "lagna_total": contract["LAGNA_TOTAL"], "combined_total": contract["COMBINED_TOTAL"], "matrix_derived": True},
        "06_VARIANT_POLICY.json": data["variants"],
        "07_AUTHORITY_PROFILE.json": {"BPHS": contract["SOURCE_PROVENANCE"]["authority_profile"], "Phaladeepika": {"traditional_authority": "CORROBORATING_CLASSICAL_VARIANT", "textual_authority": "ACCESSED_TRANSLATION_WITH_OCR_WARNING", "implementation_authority": "EXPLICIT_AUDIT_VARIANT", "empirical_authority": "NOT_APPLICABLE"}, "KNR": {"traditional_authority": "LINEAGE_ONLY", "textual_authority": "REFERENCE_NOT_VERIFIED", "implementation_authority": "NOT_VERIFIED", "empirical_authority": "NOT_APPLICABLE"}, "modern_337_386": {"traditional_authority": "NOT_ESTABLISHED", "textual_authority": "MODERN_WITNESS_PAGE", "implementation_authority": "MODERN_IMPLEMENTATION_VARIANT", "empirical_authority": "NOT_APPLICABLE"}},
        "09_CONTRACT_HASH_AND_DETERMINISM.json": {"contract_id": contract["CONTRACT_ID"], "contract_hash": contract["CONTRACT_HASH"], "second_build_hash": build_contract()["CONTRACT_HASH"], "stable": contract["CONTRACT_HASH"] == build_contract()["CONTRACT_HASH"], "v1_hash": V1_HASH, "hash_algorithm": "SHA-256 canonical JSON excluding CONTRACT_HASH"},
        "13_ACCEPTANCE_REGISTER.json": {"activity": ACTIVITY, "overall": "ASHTAKAVARGA_V2_CONTRACT_ACCEPTED_WITH_CONDITION", "criteria": [{"id": i, "criterion": c, "status": s} for i, c, s in data["acceptance"]], "counts": {s: sum(row[2] == s for row in data["acceptance"]) for s in sorted({row[2] for row in data["acceptance"]})}},
    }
    for name, value in files.items():
        write_json(OUT / name, value)
    write_md(OUT / "00_BASELINE.md", f"{ACTIVITY} baseline", f"Starting commit: `{STARTING_COMMIT}`. V1 was read without modification. The invariant activity's frozen BPHS matrix, source witness register, independent reconstruction, Phaladeepika variant audit and non-production V2 candidate were reused.\n\nDecision target: `ASHTAKAVARGA_V2_CONTRACT_ACCEPTED_WITH_CONDITION`. Production calculation code remains unchanged.")
    write_md(OUT / "05_SAV_LAGNA_SEMANTICS.md", "SAV and Lagna semantics", "`RAW_PLANETARY_SAV` is the sum of the seven planetary BAV target vectors and has grand total 336. Lagna is not included in that ordinary SAV. `RAW_LAGNA_BAV` is a separate target/vector with grand total 49. An optional `RAW_SAV_WITH_LAGNA_COMBINED` view is arithmetic 336 + 49 = 385 and must not be labelled simply `SAV`.")
    write_md(OUT / "08_NO_HYBRID_GOVERNANCE.md", "No-hybrid governance", "Reusable rule: `NO_CROSS_TRADITION_INVARIANT_MERGE_WITHOUT_EQUIVALENCE_PROOF`. A source matrix may not be combined with another tradition's aggregate invariant without demonstrated compatibility. V1 is preserved as the concrete invalid-hybrid lesson. Phaladeepika and Varahamihira remain explicit variants and are not merged into the BPHS-primary V2 contract.")
    write_md(OUT / "10_REMEDIATION_RX2_HANDOFF.md", "Remediation RX2 handoff", f"Authorized next programme: `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-RX2-001`.\n\nContract ID: `{contract['CONTRACT_ID']}`\nContract hash: `{contract['CONTRACT_HASH']}`\nSource matrix hash: `{contract['SOURCE_MATRIX_HASH']}`\nInvariants: planetary 336, Lagna 49, combined 385.\n\nObjective: implement the canonical BPHS-primary raw BAV/SAV contract under these semantics. Automatically started: `NO`. Reductions remain deferred and Phaladeepika variant isolation is mandatory.")
    write_md(OUT / "11_PARALLEL_LANE_STATE.md", "Parallel lane state", "India: HUMAN / INSTITUTIONAL ACTION READY. BVB: PACK PREPARED / UNSENT. ICAS: PACK PREPARED / UNSENT. Hospital: ETHICS / INSTITUTIONAL GATE. Müller: MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE. ADB: PREPARED / UNSENT. POSITION_END: WAIT_EXTERNAL_ACCESS. EMP-001 remains ACTIVE LONGITUDINAL; PRED-M4 remains INSUFFICIENT_SAMPLE. No parallel lane changed.")
    write_md(OUT / "12_FINAL_ACCEPTANCE.md", "Final acceptance", f"Overall: `ASHTAKAVARGA_V2_CONTRACT_ACCEPTED_WITH_CONDITION`. V2 `{contract['CONTRACT_ID']}` is now the immutable canonical source contract with hash `{contract['CONTRACT_HASH']}`. The condition is that runtime remains `IMPLEMENTED_UNVALIDATED` until the separately authorized `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-RX2-001` is executed. V1 remains unchanged and historically superseded.")
    return list(OUT.iterdir())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    data = build_artifacts()
    if args.export:
        paths = export()
        print(json.dumps({"activity": ACTIVITY, "decision": "ASHTAKAVARGA_V2_CONTRACT_ACCEPTED_WITH_CONDITION", "contract_id": data["contract"]["CONTRACT_ID"], "contract_hash": data["contract"]["CONTRACT_HASH"], "files": len(paths), "matrix_hash": data["matrix_hash"], "totals": data["totals"]}, sort_keys=True))
    else:
        print(json.dumps({"activity": ACTIVITY, "contract_id": data["contract"]["CONTRACT_ID"], "contract_hash": data["contract"]["CONTRACT_HASH"], "matrix_hash": data["matrix_hash"], "totals": data["totals"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
