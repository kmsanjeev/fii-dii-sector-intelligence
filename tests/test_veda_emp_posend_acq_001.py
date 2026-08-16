import json

from scripts.veda_emp_posend_acq_001 import EXPECTED_FAMILY_HASH, OUT, build


def test_acquisition_freezes_independent_cohort_without_feature_scoring():
    result = build()
    assert result["feature_family_hash"] == EXPECTED_FAMILY_HASH
    assert result["feature_contracts_changed"] is False
    assert result["astrology_inspected_during_acquisition"] is False
    assert result["feature_based_selection"] is False
    assert result["funnel"]["independent_eligible"] == 20
    assert len(result["cohort"]["validation_subjects"]) == 14
    assert len(result["cohort"]["holdout_subjects"]) == 6
    assert result["cohort"]["holdout_protected"] is True


def test_prior_exposure_and_controls_are_governed():
    result = build()
    assert result["funnel"]["legacy_subjects"] == 4
    assert result["funnel"]["exclusions"] == []
    assert all(not row["scored"] for row in result["controls"]["matched_controls_prepared"])
    assert result["controls"]["event_shuffled_prepared"] is True
    assert result["controls"]["subject_event_permutation_prepared"] is True


def test_artifacts_and_safety_states_are_written():
    for name in ["01_ACQUISITION_MANIFEST.json", "02_COHORT_FREEZE.json", "03_CONTROL_FREEZE.json", "04_FINAL_MANIFEST.json"]:
        assert (OUT / name).exists()
    manifest = json.loads((OUT / "04_FINAL_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["feature_family_hash"] == EXPECTED_FAMILY_HASH
    assert manifest["ml_used"] is False
    assert manifest["composition_used"] is False
    assert manifest["production_changed"] is False
    assert manifest["pred_m4"] == "INSUFFICIENT_SAMPLE"
