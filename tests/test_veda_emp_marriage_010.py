import json

from scripts.veda_emp_marriage_010 import build_pilot


def test_marriage_pilot_freezes_ten_cases_without_chart_selection():
    result = build_pilot()
    assert result["eligible_cases"] == 10
    assert result["chart_ready"] == 10
    assert result["selection_policy"].startswith("birth/event provenance")
    assert all(not item["chart_fit_used_for_selection"] for item in result["frozen_cases"])
    assert len({item["case_hash"] for item in result["frozen_cases"]}) == 10


def test_split_and_holdout_are_isolated_and_masked():
    result = build_pilot()
    split = result["split"]
    assert split["frozen"] is True
    assert split["holdout_masked"] is True
    assert len(split["design"]) == 4
    assert len(split["validation"]) == 3
    assert len(split["holdout"]) == 3
    assert not set(split["design"]) & set(split["validation"]) & set(split["holdout"])
    assert all(row["masked"] for row in result["evaluations"] if row["case_id"] in split["holdout"])


def test_signal_immutable_and_controls_prepared_before_scoring():
    result = build_pilot()
    assert result["signal"]["id"] == "VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001"
    assert result["signal"]["version"] == "1.0.0"
    assert result["signal"]["hash"] == "b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080"
    assert result["controls"]["prepared"] is True
    assert result["pilot"]["holdout_protected"] is True
    assert result["production_changes"] == "NONE"
