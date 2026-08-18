"""Focused validation for VEDA-CALC-ASHTAKAVARGA-CROSSSOURCE-RX-001."""

import hashlib
import json
from pathlib import Path

from scripts.veda_calc_ashtakavarga_crosssource_rx_001 import (
    PARENT_MATRIX,
    TARGETS,
    bphs_table,
    build_bundle,
    phaladeepika_table,
    sha,
)


def test_five_witnesses_and_source_matrix_shape():
    bundle = build_bundle()
    assert {row["source_id"] for row in bundle["witnesses"]} == {
        "BPHS", "BRIHAT_JATAKA", "PHALADEEPIKA", "SARAVALI", "JATAKA_PARIJATA"
    }
    assert len(bundle["matrix"]) == 5 * 8 * 8 * 12
    assert bundle["bphs_parent_hash"] == json.loads(PARENT_MATRIX.read_text(encoding="utf-8"))["rows_hash"]


def test_bphs_contract_is_preserved_without_production_imports():
    bundle = build_bundle()
    assert bundle["bphs_parent_hash"] == "0B7A869F3A3682A3BFFADA28E82AC23DC96EFE7E6FF3763997317C5050EE159D"
    assert bundle["synthetic"]["production_tables_reused"] is False
    assert bundle["synthetic"]["production_imports"] == []
    assert bundle["production_change"] is False


def test_phaladeepika_lagna_target_gap_and_variant_are_explicit():
    bundle = build_bundle()
    phala = phaladeepika_table()
    assert set(phala) == set(TARGETS[:7])
    assert bundle["source_comparison"]["comparable_cells"] == 56
    assert bundle["source_comparison"]["source_variant_cells"] > 0
    phala_lagna_rows = [
        row for row in bundle["matrix"]
        if row["source_id"] == "PHALADEEPIKA" and row["target"] == "Lagna"
    ]
    assert phala_lagna_rows and all(row["source_value"] == "NOT_STATED" for row in phala_lagna_rows)


def test_not_stated_is_not_zero_and_nodes_are_not_added():
    bundle = build_bundle()
    unresolved = [row for row in bundle["matrix"] if row["source_value"] == "NOT_STATED"]
    assert unresolved
    assert all(row["normalized_bindu_value"] is None for row in unresolved)
    assert all("Rahu" not in row["target"] + row["contributor"] for row in bundle["matrix"])


def test_reductions_and_canonical_contract_remain_gated():
    bundle = build_bundle()
    assert bundle["final_decision"] == "ASHTAKAVARGA_TEXTUAL_AMBIGUITY_BLOCKS_REMEDIATION"
    assert bundle["remediation_ready"] is False


def test_two_builds_have_same_canonical_hash():
    first = build_bundle()
    second = build_bundle()
    assert sha(first["matrix"]) == sha(second["matrix"])
    assert first["synthetic"]["deterministic_hash"] == second["synthetic"]["deterministic_hash"]
