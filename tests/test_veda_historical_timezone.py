from scripts.veda_historical_timezone import resolve_historical_timezone


def test_historical_berlin_offset_is_not_current_standard_time():
    result = resolve_historical_timezone("Europe/Berlin", "1835-10-31")
    assert result["historical_offset"] == "+00:53:28"
    assert result["timezone_method"] == "IANA_HISTORICAL_ZONE"


def test_reunion_zone_is_reusable_for_historical_case_resolution():
    result = resolve_historical_timezone("Indian/Reunion", "1924-04-12")
    assert result["historical_offset"] == "+04:00:00"
