import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.intelligence.kundli_engine import KundliEngine
from scripts.veda_calc_goldset_001 import (
    canonical_chart,
    local_time_from_node,
    parse_coord,
    standard_freeze,
    validate_user_benchmark_record,
)


def test_adb_compact_dmmss_coordinates_are_parsed():
    assert round(parse_coord("48n4959"), 8) == round(48 + 49 / 60 + 59 / 3600, 8)
    assert round(parse_coord("101w1001"), 8) == round(-(101 + 10 / 60 + 1 / 3600), 8)


def test_unknown_adb_time_uses_documentary_noon_placeholder():
    import xml.etree.ElementTree as ET

    node = ET.fromstring('<sbtime time_unknown="yes">unknown, 12:00 used</sbtime>')
    assert local_time_from_node(node) == "12:00:00"


def test_standard_freeze_keeps_d20_and_prediction_boundaries_explicit():
    freeze = standard_freeze()
    assert freeze["standard_id"] == "VEDA-CALC-STANDARD-001"
    assert "D20 method remains PARTIALLY_VALIDATED" in freeze["divisional_chart_policy"]
    assert freeze["predictive_maturity"] == "PRED-M3_OPERATIONAL_PLUS; PRED-M4 unchanged"


def test_chart_canonical_hash_is_stable_for_repeated_calculation():
    engine = KundliEngine()
    args = ("GOLDSET-ORDER", "1980-01-01", "12:00:00", 28.6139, 77.2090, 5.5)
    first = canonical_chart(engine.compute_human(*args))
    second = canonical_chart(engine.compute_human(*args))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_user_benchmark_requires_provenance_without_life_events():
    valid = {
        "case_id": "USER-001",
        "dob": "1990-01-01",
        "tob": "12:00:00",
        "place": "Delhi",
        "time_precision": "EXACT",
        "birth_source": "USER_PROVIDED",
        "documentary_status": "USER_ASSERTED",
    }
    assert validate_user_benchmark_record(valid) == []
    invalid = dict(valid)
    invalid.pop("documentary_status")
    assert "documentary_status" in validate_user_benchmark_record(invalid)
