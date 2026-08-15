from scripts.veda_emp_025_chart_snapshot import _offset


def test_historical_offsets_parse_with_seconds():
    assert _offset("+00:53:28") == 53 / 60 + 28 / 3600
    assert _offset("-08:00") == -8
