"""Build the bounded historical transit foundation for research infrastructure."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.ai.knowledge.astrology_calculation_validation import _planet_positions_reference
from engines.transit_gochar import HISTORICAL_TRANSIT_METHOD_ID, SUPPORTED_HISTORICAL_PLANETS, TransitGocharEngine

POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
POPULATION_ID = "VEDA-POP-OGDB-001"
CADENCE = "DAILY_00Z"
METHOD_VERSION = "1.0"


def _read_population(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        population = json.load(handle)
    if population.get("population_id") != POPULATION_ID or population.get("population_hash") != POPULATION_HASH:
        raise AssertionError("POP-001 population hash lock failed")
    if population.get("outcome_fields_present") is not False or population.get("outcome_joins_performed") is not False:
        raise AssertionError("outcome-free population invariant failed")
    return population


def _plus_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _canonical_hash(value: dict[str, Any]) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _date_range(population: dict[str, Any]) -> tuple[datetime, datetime]:
    births = [datetime.fromisoformat(row["source"]["utc_datetime"].replace("Z", "+00:00")) for row in population["records"]]
    return (
        _plus_years(min(births), 18).replace(hour=0, minute=0, second=0, microsecond=0),
        _plus_years(max(births), 70).replace(hour=0, minute=0, second=0, microsecond=0),
    )


def _reference_validation(engine: TransitGocharEngine) -> dict[str, Any]:
    samples = [
        datetime(1804, 1, 1, tzinfo=timezone.utc),
        datetime(1900, 1, 1, tzinfo=timezone.utc),
        datetime(1950, 6, 1, tzinfo=timezone.utc),
        datetime(2000, 1, 1, tzinfo=timezone.utc),
    ]
    rows = []
    max_error = 0.0
    for timestamp in samples:
        reference = _planet_positions_reference(engine._jd(timestamp))  # noqa: SLF001 - independent validation path
        for planet in SUPPORTED_HISTORICAL_PLANETS:
            actual = engine.calculate_transit(timestamp, planet)
            expected = float(reference[planet]["longitude"])
            error = abs(actual.sidereal_longitude - expected)
            error = min(error, 360.0 - error)
            max_error = max(max_error, error)
            rows.append({"timestamp": actual.transit_time_utc, "planet": planet, "error_deg": round(error, 10)})
    return {"status": "PASS" if max_error <= 0.0001 else "FAIL", "tolerance_deg": 0.0001, "max_longitude_error_deg": round(max_error, 10), "samples": rows}


def build(population: dict[str, Any]) -> dict[str, Any]:
    engine = TransitGocharEngine()
    start, end = _date_range(population)
    reference = _reference_validation(engine)
    records = []
    cursor = start
    while cursor <= end:
        row = {"timestamp_utc": cursor.isoformat().replace("+00:00", "Z"), "positions": {}}
        for planet in SUPPORTED_HISTORICAL_PLANETS:
            position = engine.calculate_transit(cursor, planet)
            row["positions"][planet] = {
                "julian_day": position.julian_day,
                "tropical_longitude": position.tropical_longitude,
                "ayanamsha": position.ayanamsha,
                "sidereal_longitude": position.sidereal_longitude,
                "sign_num": position.sign_num,
                "sign": position.sign,
                "retrograde": position.retrograde,
                "speed_deg_per_day": position.speed_deg_per_day,
            }
        records.append(row)
        cursor += timedelta(days=1)
    artifact = {
        "foundation_id": "VEDA-TRANSIT-FND-001",
        "version": METHOD_VERSION,
        "population_id": POPULATION_ID,
        "population_hash": POPULATION_HASH,
        "method_id": HISTORICAL_TRANSIT_METHOD_ID,
        "ephemeris": "Swiss Ephemeris",
        "ephemeris_version": "pyswisseph " + str(engine._kundli._swe.version),  # noqa: SLF001
        "ayanamsha": "LAHIRI",
        "zodiac": "SIDEREAL",
        "planets": list(SUPPORTED_HISTORICAL_PLANETS),
        "cadence": CADENCE,
        "date_range": {"start_utc": start.isoformat().replace("+00:00", "Z"), "end_utc": end.isoformat().replace("+00:00", "Z")},
        "record_count": len(records),
        "reference_validation": reference,
        "records": records,
    }
    artifact["artifact_hash"] = _canonical_hash(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("population", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    artifact = build(_read_population(args.population))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if args.output.suffix == ".gz":
        with args.output.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, filename="", mode="wb", mtime=0) as handle:
                handle.write(serialized)
    else:
        args.output.write_bytes(serialized)
    print(json.dumps({"foundation_id": artifact["foundation_id"], "records": artifact["record_count"], "hash": artifact["artifact_hash"], "reference": artifact["reference_validation"]["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
