from scripts.veda_emp_marriage_050 import build_replication


def test_marriage_50_isolates_initial_and_extension_cohorts():
    result = build_replication()
    assert result["signal"]["immutable"] is True
    assert result["signal"]["hash"] == "b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080"
    assert result["initial_25"] == 25
    assert result["new_25"] == 25
    assert result["combined_50"] == 50
    assert any(row["case_id"] == "MARRIAGE-046" for row in result["excluded"])
    assert all(row["cohort"] in {"INITIAL_EMPIRICAL_COHORT", "REPLICATION_EXTENSION"} for row in result["cases"])
