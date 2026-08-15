from engines.ai.orchestration.cases import CaseRegistry
from scripts.veda_emp_010_sanity import build_report


def test_first_ten_sanity_is_conditional_and_not_accuracy_claim(tmp_path):
    report = build_report(
        {
            "astrology_used_for_selection": False,
            "accepted_cases": [
                {
                    "identity": {"timezone_status": "RESOLVED", "identity_confidence": "HIGH"},
                    "events": [{"verification_status": "VERIFIED_EXACT", "event_class": "DEATH", "date_precision": "EXACT", "source_quality": "REFERENCED"}],
                }
            ],
            "excluded_subjects": [],
        },
        CaseRegistry(db_path=tmp_path / "sanity.sqlite3"),
    )
    assert report["predictive_accuracy_claim"] is False
