import json

from scripts.veda_ogdb_pilot import profile_csv


def test_ogdb_profile_is_bounded_and_not_empirical(tmp_path):
    source = tmp_path / "ogdb.csv"
    source.write_text(
        "OGID;GNAME;FNAME;DATE;PLACE;CY;TZO\n"
        "one;Pierre;Adam;1924-04-24 20:00;Paris;FR;+01:00\n"
        "two;No;Time;;Paris;FR;+01:00\n",
        encoding="utf-8",
    )
    output = tmp_path / "pilot.json"
    payload = profile_csv(source, output, limit=1)
    assert payload["timed_records_profiled"] == 1
    assert payload["usable_empirical_cases"] == 0
    assert payload["records"][0]["case_eligibility"] == "RESEARCH_ONLY_NO_EVENT"
    assert json.loads(output.read_text(encoding="utf-8"))["feed_id"] == "VEDA-EMP-OGDB-001"
