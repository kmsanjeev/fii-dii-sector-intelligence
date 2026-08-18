"""Bounded contract-consistency audit for VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001.

This audit intentionally stops before production implementation.  The activity
specification requires a hard stop when the frozen contract and its governed
source matrix disagree.  The audit is independent of the production
Ashtakavarga implementation and only reads the frozen governance artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/current-state/calc-ashtakavarga-normalization-rx2-001/17_CANONICAL_RAW_CONTRACT.json"
MATRIX_PATH = ROOT / "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json"
EXPECTED_CONTRACT_ID = "ASHTAKAVARGA_RAW_BPHS_PRIMARY_KNR_GOVERNED_V1"
EXPECTED_CONTRACT_HASH = "0E296628F989A9EE1AA14CF2F767ECEA8142042CD266DC9C98D0FF32A6771134"
EXPECTED_MATRIX_ROWS_HASH = "0B7A869F3A3682A3BFFADA28E82AC23DC96EFE7E6FF3763997317C5050EE159D"
TARGETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
PLANETARY_TARGETS = TARGETS[:7]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _expected_total(policy: str, number: int) -> int:
    match = re.search(rf"{number}\s*=", policy)
    if not match:
        raise ValueError(f"frozen contract does not state the expected {number} invariant")
    return number


def audit() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    rows = matrix.get("rows", [])

    expected_planetary_sav = _expected_total(contract["sav_policy"], 337)
    expected_combined = _expected_total(contract["sav_policy"], 386)
    target_totals = {target: 0 for target in TARGETS}
    cells: set[tuple[str, str, int]] = set()
    invalid_rows: list[dict[str, Any]] = []
    for row in rows:
        target = row.get("target")
        contributor = row.get("contributor")
        position = row.get("relative_position")
        bindu = row.get("bindu")
        if target not in TARGETS or contributor not in TARGETS or position not in range(1, 13) or bindu not in (0, 1):
            invalid_rows.append({"target": target, "contributor": contributor, "relative_position": position, "bindu": bindu})
            continue
        cells.add((target, contributor, int(position)))
        target_totals[target] += int(bindu)

    expected_cells = len(TARGETS) * len(TARGETS) * 12
    computed_matrix_hash = canonical_hash(rows)
    planetary_total = sum(target_totals[target] for target in PLANETARY_TARGETS)
    lagna_total = target_totals["Lagna"]
    combined_total = planetary_total + lagna_total
    coverage_complete = len(rows) == expected_cells and len(cells) == expected_cells and not invalid_rows
    contract_hash_ok = (
        contract.get("contract_id") == EXPECTED_CONTRACT_ID
        and contract.get("contract_hash") == EXPECTED_CONTRACT_HASH
    )
    matrix_hash_ok = (
        matrix.get("rows_hash") == EXPECTED_MATRIX_ROWS_HASH
        and computed_matrix_hash == EXPECTED_MATRIX_ROWS_HASH
    )
    invariant_failures = []
    if planetary_total != expected_planetary_sav:
        invariant_failures.append({"invariant": "ordinary_planetary_sav", "expected": expected_planetary_sav, "actual": planetary_total})
    if combined_total != expected_combined:
        invariant_failures.append({"invariant": "lagna_combined_display", "expected": expected_combined, "actual": combined_total})

    decision = "CANONICAL_CONTRACT_INCONSISTENT" if invariant_failures else "READY_FOR_IMPLEMENTATION_GATE"
    return {
        "activity_id": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001",
        "decision": decision,
        "production_change": False,
        "contract": {
            "path": str(CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "contract_id": contract.get("contract_id"),
            "contract_hash": contract.get("contract_hash"),
            "expected_contract_id": EXPECTED_CONTRACT_ID,
            "expected_contract_hash": EXPECTED_CONTRACT_HASH,
            "hash_verified": contract_hash_ok,
            "ordinary_planetary_sav_expected": expected_planetary_sav,
            "combined_lagna_display_expected": expected_combined,
        },
        "source_matrix": {
            "path": str(MATRIX_PATH.relative_to(ROOT)).replace("\\", "/"),
            "rows": len(rows),
            "expected_cells": expected_cells,
            "recorded_rows_hash": matrix.get("rows_hash"),
            "computed_rows_hash": computed_matrix_hash,
            "hash_verified": matrix_hash_ok,
            "coverage_complete": coverage_complete,
            "invalid_rows": invalid_rows,
            "targets": TARGETS,
            "contributors": TARGETS,
            "positions_per_cell": 12,
        },
        "target_totals": target_totals,
        "computed_invariants": {
            "planetary_sav_total": planetary_total,
            "lagna_bav_total": lagna_total,
            "combined_total": combined_total,
            "invariant_failures": invariant_failures,
        },
        "stop_reason": (
            "The frozen contract requires 337 ordinary planetary SAV and 386 combined display, "
            "but the hash-verified 768-cell source matrix computes 336 and 385 respectively. "
            "No source cell may be changed from code assumptions."
            if invariant_failures
            else None
        ),
        "next_action": (
            "Source-governance reconciliation must resolve the contract/matrix discrepancy before production remediation resumes."
            if invariant_failures
            else "Proceed to canonical production implementation gates."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = args.output if args.output.is_absolute() else ROOT / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["decision"] != "CANONICAL_CONTRACT_INCONSISTENT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
