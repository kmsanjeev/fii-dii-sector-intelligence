from datetime import datetime, timezone
import gzip
import json

from engines.transit_gochar import HISTORICAL_TRANSIT_METHOD_ID, TransitGocharEngine
from scripts.veda_transit_fnd_001 import POPULATION_HASH, _read_population, build


def test_historical_transit_contract_and_boundaries():
    engine = TransitGocharEngine()
    position = engine.calculate_transit(datetime(2000, 1, 1, tzinfo=timezone.utc), "Jupiter")
    assert position.method_id == HISTORICAL_TRANSIT_METHOD_ID
    assert 0 <= position.sidereal_longitude < 360
    assert 0 <= position.tropical_longitude < 360
    assert 0 <= position.ayanamsha < 30
    assert position.sign_num == int(position.sidereal_longitude // 30)
    assert position.transit_time_utc == "2000-01-01T00:00:00Z"


def test_historical_transit_cache_is_deterministic():
    engine = TransitGocharEngine()
    timestamp = datetime(1950, 6, 1, tzinfo=timezone.utc)
    first = engine.calculate_transit(timestamp, "Saturn").model_dump(mode="json")
    second = engine.calculate_transit(timestamp, "Saturn").model_dump(mode="json")
    assert first == second


def test_foundation_build_locks_population_and_reference_validation():
    population = _read_population(__import__("pathlib").Path("data/veda/research/populations/veda_pop_ogdb_001.json.gz"))
    assert population["population_hash"] == POPULATION_HASH
    artifact = build(population)
    assert artifact["population_hash"] == POPULATION_HASH
    assert artifact["reference_validation"]["status"] == "PASS"
    assert artifact["record_count"] > 1000
    assert artifact["cadence"] == "DAILY_00Z"
