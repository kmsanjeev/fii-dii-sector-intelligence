from __future__ import annotations

import json
from pathlib import Path

import pytest
import swisseph as swe

from engines.common.astronomy_policy import (
    assert_backend_flags,
    backend_name_from_flags,
    policy_payload,
)
from scripts.veda_calc_oracle_001 import (
    ascendant_report,
    circular_error,
    oracle_cases,
    timezone_report,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "docs" / "current-state" / "calc-oracle-001" / "artifacts"


def _load(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def test_astronomy_policy_explicitly_observes_moseph():
    payload = policy_payload(swe)
    assert payload["requested_backend"] == "MOSEPH"
    assert payload["actual_backend_probe"] == "MOSEPH"
    assert backend_name_from_flags(swe, swe.FLG_MOSEPH) == "MOSEPH"
    assert assert_backend_flags(swe, swe.FLG_MOSEPH) == "MOSEPH"
    with pytest.raises(RuntimeError, match="Unauthorized ephemeris backend"):
        assert_backend_flags(swe, swe.FLG_SWIEPH)


def test_oracle_cases_and_circular_error_are_stable():
    cases = oracle_cases()
    assert len(cases) == 72
    assert len({case["case_id"] for case in cases}) == 72
    assert circular_error(359.9, 0.1) == pytest.approx(0.2)


def test_external_oracle_artifact_has_full_pass_matrix():
    result = _load("06_ORACLE_RESULTS.json")
    assert len(result["rows"]) == 504
    assert all(summary["pass"] == 72 and summary["fail"] == 0 for summary in result["summary"].values())


def test_ascendant_report_reproduces_frozen_reference_and_preserves_boundary():
    report = ascendant_report()
    assert report["decision"] == "REFERENCE_REPRODUCED_RUNTIME_BOUNDARY_REMAINS"
    rows = {row["case_id"]: row for row in report["rows"]}
    assert rows["VEDA-FIX-CALC-000005"]["houses_ex_sidereal_deg"] == pytest.approx(179.9959072113)
    assert rows["VEDA-FIX-CALC-000006"]["houses_ex_sidereal_deg"] == pytest.approx(149.9988035456)
    assert rows["VEDA-FIX-CALC-000005"]["runtime_sign"] != rows["VEDA-FIX-CALC-000005"]["houses_ex_sign"]


def test_timezone_report_does_not_assign_false_precision():
    report = timezone_report()
    assert report["passed"] == 7
    assert report["unresolved"] == ["dst_start_gap"]
    assert report["ambiguous"] == ["dst_end_fold"]


def test_oracle_run_report_preserves_governance_boundaries():
    report = _load("00_RUN_REPORT.json")
    assert report["overall_decision"] == "CALC-M5_PARTIAL_EXTERNAL_VALIDATION"
    assert report["governance"]["predictive_validation"] is False
    assert report["governance"]["ml"] == "LOCKED"
    assert report["governance"]["d20_interpretation"] == "NOT_VALIDATED"
    assert report["gold_policy"]["promoted"] == {"gold_a": 0, "gold_b": 0, "gold_c": 25}

