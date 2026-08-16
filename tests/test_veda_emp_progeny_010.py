from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.veda_emp_progeny_010 import build_pilot, candidates, freeze_case, split_cases
from scripts.veda_signal_progeny_001 import signal_hash


def test_progeny_case_ledger_has_ten_public_cases_and_explicit_precision():
    rows = candidates()
    assert len(rows) == 10
    assert len({row["subject_id"] for row in rows}) == 10
    assert all(row["chart_fit_used_for_selection"] is False for row in rows)
    assert {row["childbirth_event"]["precision"] for row in rows} == {"EXACT_DAY", "MONTH", "YEAR"}
    assert sum(row["childbirth_event"]["sequence"] == "FIRST_CHILD_BIRTH" for row in rows) == 9


def test_pilot_is_deterministic_and_signal_immutable(tmp_path: Path):
    first = build_pilot()
    second = build_pilot()
    assert first == second
    assert first["signal"]["hash"] == "564bec942c8361ad1f3292093c9b067d72ebf17aea07fc7f69bd6740e1c4a8db"
    assert first["signal"]["hash"] == signal_hash()
    assert first["signal"]["d7_used"] is False

    left = tmp_path / "one.json"
    right = tmp_path / "two.json"
    left.write_text(json.dumps(first, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    right.write_text(json.dumps(second, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert hashlib.sha256(left.read_bytes()).hexdigest() == hashlib.sha256(right.read_bytes()).hexdigest()


def test_case_hashes_are_frozen_before_signal_evaluation():
    result = build_pilot()
    assert all(row["evaluation_lock"] == "FROZEN_BEFORE_SIGNAL_EVALUATION" for row in result["frozen_cases"])
    assert all("case_hash" in row for row in result["frozen_cases"])
    assert result["holdout_unseal_audit"]["single_use"] is True
    assert result["split"]["holdout_masked"] is True


def test_subject_isolated_split_and_negative_result_preserved():
    result = build_pilot()
    split = result["split"]
    assert set(split["design"]).isdisjoint(split["validation"])
    assert set(split["design"]).isdisjoint(split["holdout"])
    assert set(split["validation"]).isdisjoint(split["holdout"])
    assert result["pilot"]["result_state"] in {"NO_SEPARATION", "WEAK_SEPARATION", "PROMISING_SEPARATION", "CONTRADICTORY", "INSUFFICIENT_SAMPLE"}
    assert result["production_changes"] == "NONE"
    assert result["pred_m4"] == "INSUFFICIENT_SAMPLE / INSUFFICIENT_REPLICATED_DISCRIMINATION"
