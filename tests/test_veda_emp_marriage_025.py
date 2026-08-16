from scripts.veda_emp_marriage_025 import build_replication


def test_marriage_replication_preserves_narrow_signal_and_25_case_threshold():
    result = build_replication()
    assert result["signal"]["id"] == "VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001"
    assert result["signal"]["hash"] == "b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080"
    assert result["selection_policy"].startswith("birth/event provenance")
    assert result["eligible_cases"] == 25
    assert result["chart_ready"] == 25
    assert result["excluded"] == [{"case_id": "MARRIAGE-026", "subject_id": "di-lorenzo-tina-1872-12-04", "reason": "MISSING_BIRTH_TIME"}]
    assert all(not row["chart_fit_used_for_selection"] for row in result["cases"])
    assert result["production_changes"] == "NONE"
