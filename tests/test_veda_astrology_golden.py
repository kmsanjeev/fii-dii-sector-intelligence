from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli
from engines.intelligence.kundli_engine import KundliEngine


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "veda_p001"
GOLDEN_PATH = FIXTURE_DIR / "astrology_golden.json"
DIVERGENCE_PATH = FIXTURE_DIR / "divergence_register.json"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _rest_snapshot(payload: dict) -> dict:
    from scripts.generate_p001_astrology_fixtures import extract_rest_snapshot

    return extract_rest_snapshot(payload)


def _personal_snapshot(payload: dict) -> dict:
    from scripts.generate_p001_astrology_fixtures import extract_personal_snapshot

    return extract_personal_snapshot(payload)


def _assert_snapshot(actual, expected, path: str = "root") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        assert set(actual.keys()) == set(expected.keys()), f"{path}: key mismatch"
        for key in expected:
            _assert_snapshot(actual[key], expected[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(actual) == len(expected), f"{path}: length mismatch"
        for idx, item in enumerate(expected):
            _assert_snapshot(actual[idx], item, f"{path}[{idx}]")
        return
    if isinstance(expected, float):
        tol = 1e-6
        if path.endswith("julian_date") or path.endswith("ayanamsha"):
            tol = 0.0002
        elif path.endswith("longitude") or path.endswith("full_longitude"):
            tol = 0.001
        elif path.endswith("degree"):
            tol = 0.01
        elif path.endswith("astro_score"):
            tol = 0.1
        assert abs(float(actual) - expected) <= tol, f"{path}: expected {expected}, got {actual}, tol={tol}"
        return
    assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"


def test_personal_kundli_golden_fixtures():
    payload = _load_json(GOLDEN_PATH)

    for case in payload["personal"]:
        result = compute_personal_kundli(**case["input"])
        _assert_snapshot(_personal_snapshot(result), case["expected"], case["id"])


def test_rest_human_kundli_golden_fixtures():
    payload = _load_json(GOLDEN_PATH)
    engine = KundliEngine()

    for case in payload["rest_human"]:
        result = engine.compute_human(**case["input"])
        _assert_snapshot(_rest_snapshot(result), case["expected"], case["id"])


def test_stock_kundli_golden_fixtures():
    payload = _load_json(GOLDEN_PATH)
    engine = KundliEngine()

    for case in payload["stock"]:
        result = engine.compute_stock(**case["input"])
        _assert_snapshot(_rest_snapshot(result), case["expected"], case["id"])


def test_country_kundli_golden_fixtures():
    payload = _load_json(GOLDEN_PATH)
    engine = KundliEngine()

    for case in payload["country"]:
        result = engine.compute_country(**case["input"])
        _assert_snapshot(_rest_snapshot(result), case["expected"], case["id"])


def test_stock_kundli_endpoint_uses_cache_for_known_symbol(monkeypatch):
    from backend.routers import kundli as kundli_router

    app = FastAPI()
    app.include_router(kundli_router.router)
    client = TestClient(app)

    cache_file = Path("data/intelligence/kundli/RELIANCE_kundli.json")
    expected = _load_json(cache_file)

    def _cache_miss_guard():
        raise AssertionError("cache miss should not occur for RELIANCE fixture")

    monkeypatch.setattr(kundli_router, "_load_equity_master", _cache_miss_guard)
    response = client.get("/api/stocks/RELIANCE/kundli", params={"include_gann": "false"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["kundli"]["lagna"]["sign"] == expected["lagna"]["sign"]
    assert payload["kundli"]["planets"]["Sun"]["longitude"] == expected["planets"]["Sun"]["longitude"]


def test_personal_vs_rest_divergence_register():
    payload = _load_json(DIVERGENCE_PATH)
    engine = KundliEngine()

    for row in payload["divergences"]:
        shared = row["input"]
        personal = compute_personal_kundli(
            shared["date"],
            shared["time"][:5],
            shared["place"],
            latitude=shared["lat"],
            longitude=shared["lon"],
            timezone_offset_hours=shared["tz_offset"],
        )
        rest = engine.compute_human(
            row["divergence_id"],
            shared["date"],
            shared["time"],
            shared["lat"],
            shared["lon"],
            shared["tz_offset"],
        )

        if row["field"] == "planets_present":
            actual_a = sorted(personal["planets"].keys())
            actual_b = sorted(rest["planets"].keys())
        elif row["field"] == "rahu_dignity":
            actual_a = personal["planets"]["Rahu"]["dignity"]
            actual_b = rest["planets"]["Rahu"]["dignity"]
        elif row["field"] == "yoga_names":
            actual_a = _personal_snapshot(personal)["yoga_names"]
            actual_b = _rest_snapshot(rest)["yoga_names"]
        elif row["field"] == "available_varga_surface":
            actual_a = sorted(personal["vargas"].keys())
            actual_b = sorted(rest["divisional_charts"].keys())
        elif row["field"] == "all_antardashas_presence":
            actual_a = "all_antardashas" in personal["current_dasha"]
            actual_b = "all_antardashas" in rest["current_dasha"]
        else:
            raise AssertionError(f"Unhandled divergence field: {row['field']}")

        assert actual_a == row["output_a"], row["divergence_id"]
        assert actual_b == row["output_b"], row["divergence_id"]
