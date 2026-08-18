"""Focused validation for VEDA-CALC-SIDEREAL-ASC-TZ-001."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.veda_calc_sidereal_asc_tz_001 import (
    ascendant_report,
    boundary_regression,
    official_iae_reference,
    rashi_nakshatra_pada,
    timezone_report,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "docs" / "current-state" / "calc-sidereal-asc-tz-001" / "artifacts"


def _load(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def test_iae_reference_is_bounded_and_not_overclaimed():
    report = official_iae_reference()
    assert report["authority_state"] == "REFERENCE_STANDARD_PARTIALLY_RESOLVED"
    assert report["edition_standard"]["reference_epoch"] == "J2000.0"
    assert report["edition_standard"]["ephemeris_argument"] == "Terrestrial Time (TT)"
    assert len(report["comparisons"]) == 6
    assert max(row["absolute_difference_arcsec"] for row in report["comparisons"]) < 5


def test_nirayana_artifact_is_deterministic_regression_only():
    report = _load("02_NIRAYANA_REGRESSION.json")
    assert report["row_count"] == 224
    assert report["independence_class"] == "SAME_ENGINE_REFERENCE_LIMITATION"
    assert report["external_reference_status"] == "IMD_BOUNDED_AYANAMSHA_ONLY"


def test_rashi_nakshatra_pada_endpoint_convention():
    assert rashi_nakshatra_pada(0.0)["rashi_index"] == 0
    assert rashi_nakshatra_pada(30.0)["rashi_index"] == 1
    assert rashi_nakshatra_pada(360.0)["rashi_index"] == 0
    assert rashi_nakshatra_pada(360.0 / 27.0)["nakshatra_index"] == 1
    assert rashi_nakshatra_pada(360.0 / 108.0)["pada_index"] == 1


def test_boundary_regression_covers_all_required_boundaries():
    report = boundary_regression()
    assert report["rashi_boundaries"] == 12
    assert report["nakshatra_boundaries"] == 27
    assert report["pada_boundaries"] == 108
    assert len(report["rows"]) == (12 + 27 + 108) * 4 * 2


def test_ascendant_corpus_passes_independent_tropical_check_and_preserves_policy():
    report = ascendant_report()
    assert report["case_count"] == 120
    assert report["degree_fail"] == 0
    assert report["decision"] == "BOUNDARY_POLICY_REQUIRED"
    parent = report["known_parent_boundary_cases"]
    assert parent["decision"] == "REFERENCE_REPRODUCED_RUNTIME_BOUNDARY_REMAINS"


def test_timezone_corpus_records_version_and_does_not_assign_false_precision():
    report = timezone_report()
    assert report["case_count"] == 64
    assert report["tzdata_package_version"] == "2025.2"
    assert report["status_counts"]["NONEXISTENT_LOCAL_TIME"] == 1
    assert report["status_counts"]["AMBIGUOUS_UNRESOLVED"] == 1
    assert report["status_counts"]["PRE_STANDARD_LMT"] > 0


def test_governance_boundaries_are_explicit():
    result = _load("00_RUN_REPORT.json")
    assert result["governance"]["predictive_validation"] is False
    assert result["governance"]["ml"] == "LOCKED"
    assert result["governance"]["d20_interpretation"] == "NOT_VALIDATED"
    assert result["governance"]["gold_whole_chart_promotion"] is False
    assert result["official_iae_reference"]["authority_state"] == "REFERENCE_STANDARD_PARTIALLY_RESOLVED"


@pytest.mark.parametrize("artifact", [
    "00_RUN_REPORT.json", "01_IAE_REFERENCE.json", "02_NIRAYANA_REGRESSION.json",
    "03_BOUNDARY_REGRESSION.json", "04_ASCENDANT_CORPUS.json", "05_ASCENDANT_RESULTS.json",
    "06_TIMEZONE_CORPUS.json", "07_TIMEZONE_RESULTS.json",
])
def test_required_artifacts_exist(artifact: str):
    assert (ARTIFACTS / artifact).exists()
