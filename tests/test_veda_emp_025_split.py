from scripts.veda_emp_025_split import build_split


def test_subject_split_is_deterministic_and_exclusive():
    first = build_split(["b", "a", "a", "c"])
    second = build_split(["c", "b", "a"])
    assert first == second
    assert first["subject_level"] is True
    assert first["method_tuning_allowed"] is False
    assert sum(first["counts"].values()) == 3
    assert {item["split"] for item in first["records"]} == {"DESIGN", "VALIDATION", "HOLDOUT"}
