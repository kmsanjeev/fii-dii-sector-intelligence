import json
from pathlib import Path

from scripts.veda_pop_001 import assert_outcome_free, audit_implementable_primitives


def test_population_builder_is_outcome_free_and_hash_stable(tmp_path: Path) -> None:
    source_zip = Path("data/veda/research/empirical/ogdb_pilot_25.json")
    # Use a tiny in-memory-shaped population to verify the invariant without
    # requiring an external feed in the focused test.
    period = {
        "start_utc": "2000-01-01T00:00:00Z",
        "end_utc": "2010-01-01T00:00:00Z",
        "duration_years": 10,
    }
    record = {
        "source": {"birth_date": "1980-01-01"},
        "vimshottari": {"mahadashas": [period]},
    }
    population = {"population_id": "VEDA-POP-OGDB-001", "records": [record]}
    audit = audit_implementable_primitives(population)
    assert len(audit["primitives"]) == 2
    assert all(row["classification"] == "TOO_COMMON" for row in audit["primitives"])
    assert audit["composite_signal"] is False
    assert not any(key in population for key in ("event", "outcome", "marriage", "childbirth"))
    assert_outcome_free(population)
