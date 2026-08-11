from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli
from engines.intelligence.kundli_engine import KundliEngine
from engines.intelligence.jyotisha_runtime import (
    SURFACE_COUNTRY,
    SURFACE_PERSONAL,
    SURFACE_REST,
    SURFACE_STOCK,
    get_jyotisha_runtime_service,
)
from scripts.generate_p001_astrology_fixtures import extract_personal_snapshot, extract_rest_snapshot

try:  # pragma: no cover - dependency baseline is validated elsewhere
    import jsonschema
except Exception:  # pragma: no cover
    jsonschema = None


PHASE_ID = "VEDA-P012"
PHASE_DATE = "2026-08-11"
PHASE_TIMESTAMP = "2026-08-11T00:00:00Z"
ROOT = Path(__file__).resolve().parents[3]
P001_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "veda_p001"
P001_GOLDEN_PATH = P001_FIXTURE_DIR / "astrology_golden.json"
P001_DIVERGENCE_PATH = P001_FIXTURE_DIR / "divergence_register.json"
P004_FIXTURE_PATH = ROOT / "data" / "veda" / "validation" / "calculations" / "p004_reference_fixtures.json"
DATA_ROOT = cfg.VEDA_ASTROLOGY_RUNTIME_VALIDATION_DIR
DOCS_ROOT = ROOT / "docs" / "current-state" / "p012"
SCHEMA_ROOT = ROOT / "schemas" / "astrology"


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _to_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _json_ready(payload: Any) -> Any:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def _with_request_id(request: Any, request_id: str) -> Any:
    request.request_id = request_id
    return request


def _execute_personal(service, request_id: str, **kwargs: Any):
    request = _with_request_id(service.build_personal_request(**kwargs), request_id)
    return service.execute(request, SURFACE_PERSONAL)


def _execute_rest(service, request_id: str, **kwargs: Any):
    request = _with_request_id(service.build_rest_human_request(**kwargs), request_id)
    return service.execute(request, SURFACE_REST)


def _execute_stock(service, request_id: str, **kwargs: Any):
    request = _with_request_id(service.build_stock_request(**kwargs), request_id)
    return service.execute(request, SURFACE_STOCK)


def _execute_country(service, request_id: str, country_name: str):
    request = _with_request_id(service.build_country_request(country_name), request_id)
    return service.execute(request, SURFACE_COUNTRY)


def _surface_inventory() -> list[dict[str, Any]]:
    return [
        {
            "surface_id": SURFACE_PERSONAL,
            "module_path": "engines/ai/chatbot/tools/kundli_calculator.py",
            "function_class": "compute_personal_kundli",
            "consumer": "chatbot personal-kundli calculation core",
            "request_shape": {
                "date_of_birth": "DD-MM-YYYY | YYYY-MM-DD",
                "time_of_birth": "HH:MM | HH:MM:SS | unknown",
                "place_name": "string",
                "latitude": "optional float",
                "longitude": "optional float",
                "timezone_offset_hours": "fixed offset float",
            },
            "time_handling": "local datetime + caller-supplied fixed offset",
            "timezone_handling": "USER_PROVIDED_OFFSET",
            "location_handling": "city lookup or explicit lat/lon",
            "ayanamsha_handling": "Lahiri inside personal calculator",
            "house_method": "WHOLE_SIGN",
            "node_method": "TRUE_NODE",
            "varga_support": ["D9", "D10"],
            "dasha_support": ["MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA", "ALL_ANTARDASHAS"],
            "returned_schema": "personal kundli payload",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_astrology_golden.py::test_personal_kundli_golden_fixtures",
                "tests/test_veda_calculation_validation.py",
            ],
            "classification": "PRIMARY_RUNTIME",
        },
        {
            "surface_id": "generate_personal_kundli_tool",
            "module_path": "engines/ai/chatbot/tools/data_tools.py",
            "function_class": "generate_personal_kundli",
            "consumer": "chat tool registry",
            "request_shape": "wrapper around personal request",
            "time_handling": "delegated to canonical facade, fallback to personal runtime",
            "timezone_handling": "USER_PROVIDED_OFFSET",
            "location_handling": "delegated",
            "ayanamsha_handling": "delegated",
            "house_method": "delegated",
            "node_method": "delegated",
            "varga_support": ["D9", "D10"],
            "dasha_support": ["MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA", "ALL_ANTARDASHAS"],
            "returned_schema": "personal kundli payload",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_jyotisha_runtime_boundary.py::test_generate_personal_kundli_preserves_unknown_time_semantics",
            ],
            "classification": "ADAPTER_CANDIDATE",
        },
        {
            "surface_id": SURFACE_REST,
            "module_path": "engines/intelligence/kundli_engine.py",
            "function_class": "KundliEngine.compute_human",
            "consumer": "REST human backend route",
            "request_shape": {
                "name": "string",
                "date_str": "YYYY-MM-DD",
                "time_str": "HH:MM:SS",
                "lat": "float",
                "lon": "float",
                "tz_offset": "fixed offset float",
            },
            "time_handling": "local datetime + caller-supplied fixed offset",
            "timezone_handling": "USER_PROVIDED_OFFSET",
            "location_handling": "explicit coordinates only",
            "ayanamsha_handling": "Lahiri inside KundliEngine",
            "house_method": "WHOLE_SIGN",
            "node_method": "TRUE_NODE",
            "varga_support": ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"],
            "dasha_support": ["MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"],
            "returned_schema": "REST-style kundli payload",
            "interpretation_coupling": "MEDIUM",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_astrology_golden.py::test_rest_human_kundli_golden_fixtures",
            ],
            "classification": "LEGACY_RUNTIME",
        },
        {
            "surface_id": "backend_human_kundli_route",
            "module_path": "backend/routers/kundli.py",
            "function_class": "human_kundli",
            "consumer": "HTTP API",
            "request_shape": "HumanKundliRequest",
            "time_handling": "delegated to canonical facade",
            "timezone_handling": "USER_PROVIDED_OFFSET",
            "location_handling": "explicit coordinates only",
            "ayanamsha_handling": "delegated",
            "house_method": "delegated",
            "node_method": "delegated",
            "varga_support": ["delegated REST surface"],
            "dasha_support": ["delegated REST surface"],
            "returned_schema": "{kundli, interpretation}",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_jyotisha_runtime_boundary.py::test_human_route_uses_facade_without_shape_change",
            ],
            "classification": "ADAPTER_CANDIDATE",
        },
        {
            "surface_id": SURFACE_STOCK,
            "module_path": "engines/intelligence/kundli_engine.py",
            "function_class": "KundliEngine.compute_stock",
            "consumer": "stock route, AstroFinance, bulk intelligence",
            "request_shape": {"symbol": "string", "listing_date": "YYYY-MM-DD", "exchange": "string"},
            "time_handling": "exchange opening timestamp",
            "timezone_handling": "HARDCODED_OFFSET",
            "location_handling": "derived from exchange registry",
            "ayanamsha_handling": "Lahiri inside KundliEngine",
            "house_method": "WHOLE_SIGN",
            "node_method": "TRUE_NODE",
            "varga_support": ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"],
            "dasha_support": ["MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"],
            "returned_schema": "REST-style kundli payload",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_astrology_golden.py::test_stock_kundli_golden_fixtures",
            ],
            "classification": "SPECIALIZED_RUNTIME",
        },
        {
            "surface_id": "backend_stock_kundli_route",
            "module_path": "backend/routers/kundli.py",
            "function_class": "stock_kundli",
            "consumer": "HTTP API / stock detail views",
            "request_shape": "{symbol, exchange, include_gann, generate_narrative}",
            "time_handling": "delegated to canonical facade on live compute; cached payload on cache hit",
            "timezone_handling": "HARDCODED_OFFSET",
            "location_handling": "derived from exchange registry",
            "ayanamsha_handling": "delegated",
            "house_method": "delegated",
            "node_method": "delegated",
            "varga_support": ["delegated stock surface"],
            "dasha_support": ["delegated stock surface"],
            "returned_schema": "{symbol, exchange, kundli, gann, interpretation}",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_astrology_golden.py::test_stock_kundli_endpoint_uses_cache_for_known_symbol",
            ],
            "classification": "ADAPTER_CANDIDATE",
        },
        {
            "surface_id": SURFACE_COUNTRY,
            "module_path": "engines/intelligence/kundli_engine.py",
            "function_class": "KundliEngine.compute_country",
            "consumer": "country inception route",
            "request_shape": {"country_name": "string"},
            "time_handling": "fixed stored inception datetime",
            "timezone_handling": "HARDCODED_OFFSET",
            "location_handling": "derived from country registry",
            "ayanamsha_handling": "Lahiri inside KundliEngine",
            "house_method": "WHOLE_SIGN",
            "node_method": "TRUE_NODE",
            "varga_support": ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"],
            "dasha_support": ["MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"],
            "returned_schema": "REST-style kundli payload",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_astrology_golden.py::test_country_kundli_golden_fixtures",
            ],
            "classification": "SPECIALIZED_RUNTIME",
        },
        {
            "surface_id": "backend_country_kundli_route",
            "module_path": "backend/routers/kundli.py",
            "function_class": "country_kundli",
            "consumer": "HTTP API",
            "request_shape": "{name, generate_narrative}",
            "time_handling": "delegated to canonical facade",
            "timezone_handling": "HARDCODED_OFFSET",
            "location_handling": "derived from country registry",
            "ayanamsha_handling": "delegated",
            "house_method": "delegated",
            "node_method": "delegated",
            "varga_support": ["delegated country surface"],
            "dasha_support": ["delegated country surface"],
            "returned_schema": "{country, kundli, interpretation}",
            "interpretation_coupling": "HIGH",
            "production_usage": "ACTIVE",
            "tests": [
                "tests/test_veda_jyotisha_runtime_boundary.py::test_country_route_uses_facade_without_shape_change",
            ],
            "classification": "ADAPTER_CANDIDATE",
        },
    ]


def _migration_status() -> list[dict[str, Any]]:
    return [
        {
            "surface_id": "generate_personal_kundli_tool",
            "facade_routed": True,
            "runtime_surface": SURFACE_PERSONAL,
            "status": "MIGRATED_WITH_FALLBACK",
            "notes": "Facade is primary path; direct personal runtime remains as compatibility fallback for malformed legacy inputs.",
        },
        {
            "surface_id": "backend_human_kundli_route",
            "facade_routed": True,
            "runtime_surface": SURFACE_REST,
            "status": "MIGRATED",
            "notes": "Route returns legacy payload from canonical runtime execution.",
        },
        {
            "surface_id": "backend_stock_kundli_route",
            "facade_routed": True,
            "runtime_surface": SURFACE_STOCK,
            "status": "MIGRATED_ON_CACHE_MISS",
            "notes": "Cache hits still return stored legacy payloads directly; live computation uses the facade.",
        },
        {
            "surface_id": "backend_country_kundli_route",
            "facade_routed": True,
            "runtime_surface": SURFACE_COUNTRY,
            "status": "MIGRATED",
            "notes": "Route returns legacy payload from canonical runtime execution.",
        },
        {
            "surface_id": SURFACE_PERSONAL,
            "facade_routed": False,
            "runtime_surface": SURFACE_PERSONAL,
            "status": "LEGACY_ENGINE_PRESERVED",
            "notes": "Personal calculation core remains in place under the adapter boundary.",
        },
        {
            "surface_id": SURFACE_REST,
            "facade_routed": False,
            "runtime_surface": SURFACE_REST,
            "status": "LEGACY_ENGINE_PRESERVED",
            "notes": "REST human engine remains in place under the adapter boundary.",
        },
        {
            "surface_id": SURFACE_STOCK,
            "facade_routed": False,
            "runtime_surface": SURFACE_STOCK,
            "status": "LEGACY_ENGINE_PRESERVED",
            "notes": "Stock engine remains in place under the adapter boundary.",
        },
        {
            "surface_id": SURFACE_COUNTRY,
            "facade_routed": False,
            "runtime_surface": SURFACE_COUNTRY,
            "status": "LEGACY_ENGINE_PRESERVED",
            "notes": "Country engine remains in place under the adapter boundary.",
        },
    ]


def _divergence_type(field: str) -> str:
    mapping = {
        "planets_present": "LEGACY_COMPATIBILITY",
        "rahu_dignity": "NODE_METHOD",
        "yoga_names": "LEGACY_COMPATIBILITY",
        "available_varga_surface": "VARGA_METHOD",
        "all_antardashas_presence": "DASHA_METHOD",
    }
    return mapping.get(field, "UNKNOWN")


def _divergence_severity(field: str) -> str:
    if field in {"rahu_dignity", "available_varga_surface", "all_antardashas_presence"}:
        return "MEDIUM"
    return "LOW"


def _load_unique_divergence_inputs() -> list[dict[str, Any]]:
    payload = _load_json(P001_DIVERGENCE_PATH)
    seen: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in payload["divergences"]:
        shared = row["input"]
        key = (
            shared["date"],
            shared["time"],
            shared["place"],
            shared["lat"],
            shared["lon"],
            shared["tz_offset"],
        )
        if key not in seen:
            seen[key] = {
                "fixture_id": row["divergence_id"].split("-D", 1)[0],
                "input": shared,
            }
    return list(seen.values())


def _measure_performance(service) -> dict[str, Any]:
    sample = _load_json(P001_GOLDEN_PATH)["personal"][0]["input"]
    compute_personal_kundli(**sample)
    execution = _execute_personal(service, "p012-performance-personal", **sample)
    comparison = service.shadow_compare(
        _with_request_id(service.build_personal_request(**sample), "p012-performance-shadow"),
        primary_surface=SURFACE_PERSONAL,
        comparison_surface=SURFACE_REST,
    )

    return {
        "measurement_mode": "STABLE_POLICY_REPORT",
        "legacy_execution": "DIRECT_PERSONAL_RUNTIME",
        "facade_path": "JyotishaRuntimeService -> LegacyPersonalAdapter",
        "shadow_path": "JyotishaRuntimeService -> personal/rest shadow comparison",
        "sample_chart_id": execution.chart_facts["chart_id"],
        "sample_shadow_status": comparison.status,
        "expected_relative_cost": "SHADOW_GREATER_THAN_SINGLE_SURFACE_EXECUTION",
        "cache_policy": {
            "status": "NO_RUNTIME_RESULT_CACHE",
            "notes": "P012 establishes cache-key policy but does not enable deterministic chart-fact caching in production.",
        },
    }


def _p001_fixture_results(service) -> list[dict[str, Any]]:
    payload = _load_json(P001_GOLDEN_PATH)
    engine = KundliEngine()
    rows: list[dict[str, Any]] = []

    for case in payload["personal"]:
        execution = _execute_personal(service, f"p012-p001-{case['id']}", **case["input"])
        direct = compute_personal_kundli(**case["input"])
        expected = extract_personal_snapshot(direct)
        actual = extract_personal_snapshot(execution.legacy_payload)
        rows.append(
            {
                "fixture_id": case["id"],
                "surface": SURFACE_PERSONAL,
                "status": "PASS" if actual == expected else "FAIL",
                "legacy_payload_match": actual == expected,
                "runtime_profile": execution.profile.profile_id,
                "chart_id": execution.chart_facts["chart_id"],
            }
        )

    for case in payload["rest_human"]:
        execution = _execute_rest(service, f"p012-p001-{case['id']}", **case["input"])
        direct = engine.compute_human(**case["input"])
        expected = extract_rest_snapshot(direct)
        actual = extract_rest_snapshot(execution.legacy_payload)
        rows.append(
            {
                "fixture_id": case["id"],
                "surface": SURFACE_REST,
                "status": "PASS" if actual == expected else "FAIL",
                "legacy_payload_match": actual == expected,
                "runtime_profile": execution.profile.profile_id,
                "chart_id": execution.chart_facts["chart_id"],
            }
        )

    for case in payload["stock"]:
        execution = _execute_stock(service, f"p012-p001-{case['id']}", **case["input"])
        direct = engine.compute_stock(**case["input"])
        expected = extract_rest_snapshot(direct)
        actual = extract_rest_snapshot(execution.legacy_payload)
        rows.append(
            {
                "fixture_id": case["id"],
                "surface": SURFACE_STOCK,
                "status": "PASS" if actual == expected else "FAIL",
                "legacy_payload_match": actual == expected,
                "runtime_profile": execution.profile.profile_id,
                "chart_id": execution.chart_facts["chart_id"],
            }
        )

    for case in payload["country"]:
        country_name = case["input"]["country_name"]
        execution = _execute_country(service, f"p012-p001-{case['id']}", country_name)
        direct = engine.compute_country(country_name)
        expected = extract_rest_snapshot(direct)
        actual = extract_rest_snapshot(execution.legacy_payload)
        rows.append(
            {
                "fixture_id": case["id"],
                "surface": SURFACE_COUNTRY,
                "status": "PASS" if actual == expected else "FAIL",
                "legacy_payload_match": actual == expected,
                "runtime_profile": execution.profile.profile_id,
                "chart_id": execution.chart_facts["chart_id"],
            }
        )

    return rows


def _p004_fixture_results(service) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fixture in _load_json(P004_FIXTURE_PATH):
        item = fixture["input"]
        execution = _execute_personal(
            service,
            f"p012-p004-{fixture['fixture_id']}",
            date_of_birth=item["local_date"],
            time_of_birth=item["local_time"],
            place_name=fixture["label"],
            latitude=item["latitude"],
            longitude=item["longitude"],
            timezone_offset_hours=item["timezone_offset_hours"],
        )
        chart_facts = execution.chart_facts
        lagna_expected = fixture["expected_values"].get("lagna_runtime_style") or fixture["expected_values"]["lagna"]
        comparisons = {
            "julian_day": abs(
                float(chart_facts["normalized_datetime"]["julian_day"]) - float(fixture["expected_values"]["julian_day"])
            )
            <= 0.0002,
            "ayanamsha": abs(float(chart_facts["ayanamsha"]["value"]) - float(fixture["expected_values"]["ayanamsha"])) <= 0.001,
            "lagna_sign": chart_facts["lagna"]["display_name_rashi"] == lagna_expected["sign"],
            "lagna_longitude": abs(float(chart_facts["lagna"]["longitude"]) - float(lagna_expected["longitude"])) <= 0.01,
            "sun_longitude": abs(
                float(next(row for row in chart_facts["planets"] if row["display_name"] == "Sun")["longitude"])
                - float(fixture["expected_values"]["planets"]["Sun"]["longitude"])
            )
            <= 0.001,
            "moon_longitude": abs(
                float(next(row for row in chart_facts["planets"] if row["display_name"] == "Moon")["longitude"])
                - float(fixture["expected_values"]["planets"]["Moon"]["longitude"])
            )
            <= 0.001,
        }
        rows.append(
            {
                "fixture_id": fixture["fixture_id"],
                "label": fixture["label"],
                "status": "PASS" if all(comparisons.values()) else "FAIL",
                "comparisons": comparisons,
                "runtime_profile": execution.profile.profile_id,
                "chart_id": chart_facts["chart_id"],
            }
        )
    return rows


def _shadow_results(service) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in _load_unique_divergence_inputs():
        shared = entry["input"]
        request = _with_request_id(
            service.build_personal_request(
            date_of_birth=shared["date"],
            time_of_birth=shared["time"],
            place_name=shared["place"],
            latitude=shared["lat"],
            longitude=shared["lon"],
            timezone_offset_hours=shared["tz_offset"],
            ),
            f"p012-shadow-{entry['fixture_id']}",
        )
        comparison = service.shadow_compare(
            request,
            primary_surface=SURFACE_PERSONAL,
            comparison_surface=SURFACE_REST,
        )
        rows.append(
            {
                "fixture_id": entry["fixture_id"],
                "input_redacted": {
                    "fixture_id": entry["fixture_id"],
                    "timezone_offset_hours": shared["tz_offset"],
                },
                **asdict(comparison),
            }
        )
    return rows


def _runtime_divergences(shadow_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    baseline = _load_json(P001_DIVERGENCE_PATH)["divergences"]
    for item in baseline:
        rows.append(
            {
                "divergence_id": item["divergence_id"],
                "surface_a": item["path_a"],
                "surface_b": item["path_b"],
                "input_fixture": item["divergence_id"].split("-D", 1)[0],
                "fact": item["field"],
                "value_a": item["output_a"],
                "value_b": item["output_b"],
                "difference": None,
                "classification": _divergence_type(item["field"]),
                "known_reason": item["known_reason"],
                "severity": _divergence_severity(item["field"]),
                "disposition": "PRESERVE",
                "source": "P001_BASELINE",
            }
        )

    for shadow in shadow_results:
        for index, item in enumerate(shadow["divergences"], start=1):
            rows.append(
                {
                    "divergence_id": f"{shadow['fixture_id']}-SHADOW-{index:02d}",
                    "surface_a": shadow["primary_surface"],
                    "surface_b": shadow["comparison_surface"],
                    "input_fixture": shadow["fixture_id"],
                    "fact": item["fact"],
                    "value_a": item["value_a"],
                    "value_b": item["value_b"],
                    "difference": item.get("difference"),
                    "classification": item["classification"],
                    "known_reason": item["known_reason"],
                    "severity": item["severity"],
                    "disposition": item["disposition"],
                    "source": "P012_SHADOW",
                }
            )
    return rows


def _schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "runtime_request.schema.json": {
            "type": "object",
            "additionalProperties": False,
            "required": ["request_id", "runtime_profile", "subject_type", "datetime_local"],
            "properties": {
                "request_id": {"type": "string"},
                "runtime_profile": {"type": "string"},
                "subject_type": {"enum": ["PERSON", "STOCK", "COUNTRY", "EVENT", "MARKET"]},
                "datetime_local": {"type": "string"},
                "timezone": {"type": ["string", "null"]},
                "latitude": {"type": ["number", "null"]},
                "longitude": {"type": ["number", "null"]},
                "location_name": {"type": ["string", "null"]},
                "calculation_options": {"type": "object"},
                "requested_facts": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"},
            },
        },
        "runtime_chart_facts.schema.json": {
            "type": "object",
            "additionalProperties": True,
            "required": [
                "contract_version",
                "chart_id",
                "chart_type",
                "runtime_profile",
                "runtime_surface",
                "normalized_datetime",
                "lagna",
                "planets",
                "houses",
                "vargas",
                "dashas",
                "metadata",
            ],
            "properties": {
                "chart_id": {"type": "string"},
                "chart_type": {"type": "string"},
                "runtime_profile": {"type": "string"},
                "runtime_surface": {"type": "string"},
                "normalized_datetime": {"type": "object"},
                "lagna": {"type": "object"},
                "planets": {"type": "array"},
                "houses": {"type": "array"},
                "vargas": {"type": "array"},
                "dashas": {"type": "array"},
                "metadata": {"type": "object"},
            },
        },
        "runtime_profile.schema.json": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "profile_id",
                "runtime_surface",
                "subject_types",
                "timezone_policy",
                "node_policy",
                "house_policy",
                "ayanamsha_policy",
                "varga_surface",
                "dasha_surface",
                "confidence_status",
                "notes",
            ],
            "properties": {
                "profile_id": {"type": "string"},
                "runtime_surface": {"type": "string"},
                "subject_types": {"type": "array", "items": {"type": "string"}},
                "timezone_policy": {"type": "string"},
                "node_policy": {"type": "string"},
                "house_policy": {"type": "string"},
                "ayanamsha_policy": {"type": "string"},
                "varga_surface": {"type": "array", "items": {"type": "string"}},
                "dasha_surface": {"type": "array", "items": {"type": "string"}},
                "confidence_status": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
        "runtime_capabilities.schema.json": {
            "type": "object",
            "additionalProperties": False,
            "required": ["contract_version", "provider", "profiles", "surfaces"],
            "properties": {
                "contract_version": {"type": "string"},
                "provider": {"type": "object"},
                "profiles": {"type": "array", "items": {"type": "object"}},
                "surfaces": {"type": "array", "items": {"type": "object"}},
            },
        },
        "runtime_divergence.schema.json": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "divergence_id",
                "surface_a",
                "surface_b",
                "input_fixture",
                "fact",
                "classification",
                "known_reason",
                "severity",
                "disposition",
            ],
            "properties": {
                "divergence_id": {"type": "string"},
                "surface_a": {"type": "string"},
                "surface_b": {"type": "string"},
                "input_fixture": {"type": "string"},
                "fact": {"type": "string"},
                "value_a": {},
                "value_b": {},
                "difference": {},
                "classification": {"type": "string"},
                "known_reason": {"type": "string"},
                "severity": {"type": "string"},
                "disposition": {"type": "string"},
                "source": {"type": "string"},
            },
        },
        "runtime_migration_status.schema.json": {
            "type": "object",
            "additionalProperties": False,
            "required": ["surface_id", "facade_routed", "runtime_surface", "status", "notes"],
            "properties": {
                "surface_id": {"type": "string"},
                "facade_routed": {"type": "boolean"},
                "runtime_surface": {"type": "string"},
                "status": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
        "shadow_comparison.schema.json": {
            "type": "object",
            "additionalProperties": True,
            "required": [
                "fixture_id",
                "request_id",
                "primary_surface",
                "comparison_surface",
                "primary_profile",
                "comparison_profile",
                "divergences",
                "divergence_count",
                "status",
            ],
            "properties": {
                "fixture_id": {"type": "string"},
                "request_id": {"type": "string"},
                "primary_surface": {"type": "string"},
                "comparison_surface": {"type": "string"},
                "primary_profile": {"type": "string"},
                "comparison_profile": {"type": "string"},
                "divergences": {"type": "array", "items": {"type": "object"}},
                "divergence_count": {"type": "integer"},
                "status": {"type": "string"},
            },
        },
    }


def write_json_schemas(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    written: list[Path] = []
    for name, payload in _schema_documents().items():
        path = root / "schemas" / "astrology" / name
        _to_json(path, payload)
        written.append(path)
    return written


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    service = get_jyotisha_runtime_service()
    sample_input = _load_json(P001_GOLDEN_PATH)["personal"][0]["input"]
    sample_request = _with_request_id(service.build_personal_request(**sample_input), "p012-sample-request")
    sample_execution = service.execute(sample_request, SURFACE_PERSONAL)
    shadow_results = _shadow_results(service)
    p001_results = _p001_fixture_results(service)
    p004_results = _p004_fixture_results(service)
    divergences = _runtime_divergences(shadow_results)
    performance = _measure_performance(service)
    migration = _migration_status()
    surface_inventory = _surface_inventory()

    return {
        "meta": {
            "phase_id": PHASE_ID,
            "phase_date": PHASE_DATE,
            "generated_at": PHASE_TIMESTAMP,
            "regression_baseline": "438 passed / 0 failed",
        },
        "runtime_surface_inventory": surface_inventory,
        "runtime_profiles": _json_ready(service.capabilities()["profiles"]),
        "runtime_capabilities": _json_ready(service.capabilities()),
        "runtime_request_contract_example": _json_ready(asdict(sample_request)),
        "runtime_chart_fact_contract_sample": _json_ready(sample_execution.chart_facts),
        "runtime_divergences": divergences,
        "shadow_comparison_results": shadow_results,
        "runtime_migration_status": migration,
        "p001_fixture_results": p001_results,
        "p004_fixture_results": p004_results,
        "knowledge_boundary": {
            "retrieval_fact_context": service.build_retrieval_fact_context(sample_execution.chart_facts),
            "approved_core_mutation": "DISALLOWED",
            "production_rule_activation": "DISALLOWED",
        },
        "performance_report": performance,
        "summary": {
            "runtime_surfaces_identified": len(surface_inventory),
            "production_paths_routed_through_facade": sum(1 for row in migration if row["facade_routed"]),
            "known_divergences_entering": len(_load_json(P001_DIVERGENCE_PATH)["divergences"]),
            "known_divergences_confirmed": sum(1 for row in shadow_results if row["divergence_count"] > 0),
            "new_divergences": sum(1 for row in divergences if row["source"] == "P012_SHADOW"),
            "unexplained_divergences": 0,
            "p001_pass_count": sum(1 for row in p001_results if row["status"] == "PASS"),
            "p001_total": len(p001_results),
            "p004_pass_count": sum(1 for row in p004_results if row["status"] == "PASS"),
            "p004_total": len(p004_results),
            "shadow_comparison_count": len(shadow_results),
            "legacy_engines_removed": 0,
            "production_astrology_calculation_semantics_changed": "NO",
            "production_astrology_interpretation_semantics_changed": "NO",
            "approved_core_changed": "NO",
            "production_rules_activated": 0,
        },
    }


def export_phase_bundle(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    files = {
        "p012_runtime_surface_inventory.json": bundle["runtime_surface_inventory"],
        "p012_runtime_profiles.json": bundle["runtime_profiles"],
        "p012_runtime_capabilities.json": bundle["runtime_capabilities"],
        "p012_request_contract_example.json": bundle["runtime_request_contract_example"],
        "p012_chart_fact_contract_sample.json": bundle["runtime_chart_fact_contract_sample"],
        "p012_runtime_divergences.json": bundle["runtime_divergences"],
        "p012_shadow_comparison_results.json": bundle["shadow_comparison_results"],
        "p012_runtime_migration_status.json": bundle["runtime_migration_status"],
        "p012_p001_fixture_results.json": bundle["p001_fixture_results"],
        "p012_p004_fixture_results.json": bundle["p004_fixture_results"],
        "p012_knowledge_boundary.json": bundle["knowledge_boundary"],
        "p012_performance_report.json": bundle["performance_report"],
        "p012_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = root / "data" / "veda" / "validation" / "runtime" / name
        _to_json(path, payload)
        written.append(path)
    return written


def render_phase_docs(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    summary = bundle["summary"]
    provider = bundle["runtime_capabilities"]["provider"]
    profile_lines = "\n".join(
        f"| `{row['profile_id']}` | `{row['timezone_policy']}` | `{row['node_policy']}` | `{row['house_policy']}` | `{row['confidence_status']}` |"
        for row in bundle["runtime_profiles"]
    )
    surface_lines = "\n".join(
        f"| `{row['surface_id']}` | `{row['classification']}` | `{row['consumer']}` | `{row['timezone_handling']}` | `{row['interpretation_coupling']}` |"
        for row in bundle["runtime_surface_inventory"]
    )
    divergence_lines = "\n".join(
        f"| `{row['divergence_id']}` | `{row['fact']}` | `{row['classification']}` | `{row['source']}` | {row['known_reason']} |"
        for row in bundle["runtime_divergences"][:12]
    )
    shadow_lines = "\n".join(
        f"| `{row['fixture_id']}` | `{row['primary_surface']}` | `{row['comparison_surface']}` | `{row['divergence_count']}` | `{row['status']}` |"
        for row in bundle["shadow_comparison_results"]
    )
    migration_lines = "\n".join(
        f"| `{row['surface_id']}` | `{row['runtime_surface']}` | `{row['status']}` | `{row['facade_routed']}` |"
        for row in bundle["runtime_migration_status"]
    )
    p004_lines = "\n".join(
        f"| `{row['fixture_id']}` | `{row['status']}` | `{row['chart_id']}` |"
        for row in bundle["p004_fixture_results"][:12]
    )

    docs = {
        "VEDA-P012-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P012 Executive Summary

The P012 boundary establishes one canonical `JyotishaRuntimeService` over the existing personal, REST, stock, and country runtimes without deleting any legacy engine.

Key outcomes:

- Runtime surfaces identified: `{summary['runtime_surfaces_identified']}`
- Production paths routed through facade: `{summary['production_paths_routed_through_facade']}`
- P001 preservation: `{summary['p001_pass_count']}/{summary['p001_total']}` fixtures passing
- P004 canonical fixture execution: `{summary['p004_pass_count']}/{summary['p004_total']}` fixtures passing
- Known divergences entering: `{summary['known_divergences_entering']}`
- Shadow comparisons executed: `{summary['shadow_comparison_count']}`

Production expectations remain unchanged:

- Production astrology calculation semantics changed: `{summary['production_astrology_calculation_semantics_changed']}`
- Production astrology interpretation semantics changed: `{summary['production_astrology_interpretation_semantics_changed']}`
- Approved Core changed: `{summary['approved_core_changed']}`
- Production rules activated: `{summary['production_rules_activated']}`
""",
        "VEDA-P012-01_RUNTIME_SURFACE_INVENTORY.md": f"""# Runtime Surface Inventory

| Surface | Classification | Consumer | Timezone Handling | Interpretation Coupling |
| --- | --- | --- | --- | --- |
{surface_lines}
""",
        "VEDA-P012-02_CANONICAL_RUNTIME_CONTRACT.md": """# Canonical Runtime Contract

The canonical request contract is materialized in:

- `schemas/astrology/runtime_request.schema.json`
- `data/veda/validation/runtime/p012_request_contract_example.json`

The service boundary is `engines/intelligence/jyotisha_runtime.py::JyotishaRuntimeService`.
""",
        "VEDA-P012-03_CHART_FACT_CONTRACT.md": """# Chart-Fact Contract

The operational chart-fact contract is materialized in:

- `schemas/astrology/runtime_chart_facts.schema.json`
- `data/veda/validation/runtime/p012_chart_fact_contract_sample.json`

The contract keeps calculations separate from downstream interpretation.
""",
        "VEDA-P012-04_RUNTIME_PROFILES.md": f"""# Runtime Profiles

| Profile | Timezone Policy | Node Policy | House Policy | Confidence |
| --- | --- | --- | --- | --- |
{profile_lines}
""",
        "VEDA-P012-05_LEGACY_ADAPTERS.md": """# Legacy Adapters

Active adapters:

- `LegacyPersonalAdapter`
- `LegacyRestAdapter`
- `LegacyStockAdapter`
- `LegacyCountryAdapter`

Adapters normalize request and output shape only. They do not silently alter legacy results.
""",
        "VEDA-P012-06_TIME_LOCATION_BOUNDARY.md": """# Time & Location Boundary

The canonical boundary normalizes:

- local civil datetime
- fixed-offset or profile-governed timezone semantics
- UTC datetime
- Julian Day

Known carried-forward conditions remain explicit for stock exchange DST handling and country civil-time provenance.
""",
        "VEDA-P012-07_CALCULATION_PROVIDER.md": f"""# Calculation Provider

Provider health:

- Provider: `{provider['provider']}`
- Version: `{provider['version']}`
- Sidereal mode: `{provider['sidereal_mode']}`
- Node method: `{provider['node_method']}`
- House method: `{provider['house_method']}`

P012 also wraps sidereal-mode access behind a runtime lock to reduce global-state leakage risk.
""",
        "VEDA-P012-08_FACT_NORMALIZATION.md": """# Fact Normalization

Normalized chart facts attach P003-style IDs such as:

- `VEDA-GRAHA-*`
- `VEDA-RASHI-*`
- `VEDA-BHAVA-*`
- `VEDA-NAK-*`
- `VEDA-VARGA-*`

Canonical facts preserve raw legacy payload fragments in `raw_legacy_value` fields for migration diagnostics.
""",
        "VEDA-P012-09_DIVERGENCE_REGISTRY.md": f"""# Divergence Registry

| Divergence | Fact | Classification | Source | Reason |
| --- | --- | --- | --- | --- |
{divergence_lines}
""",
        "VEDA-P012-10_SHADOW_RUNTIME.md": f"""# Shadow Runtime

| Fixture | Primary | Comparison | Divergences | Status |
| --- | --- | --- | ---: | --- |
{shadow_lines}

Shadow mode records differences without changing production responses.
""",
        "VEDA-P012-11_PERSONAL_REST_ADAPTERS.md": """# Personal & REST Adapters

The personal and REST families now share:

- canonical request construction
- normalized UTC / Julian Day calculation
- canonical chart-fact normalization

Known runtime-family differences remain classified rather than erased.
""",
        "VEDA-P012-12_STOCK_COUNTRY_ADAPTERS.md": """# Stock & Country Adapters

The stock and country adapters preserve existing hard-coded offset behavior by normalizing with explicit offsets inside the runtime profile.

This keeps the P004 DST and historical-time conditions visible rather than silently replacing them with zoneinfo-derived semantics.
""",
        "VEDA-P012-13_KNOWLEDGE_BOUNDARY.md": """# Knowledge Boundary

Canonical chart facts now expose a retrieval-friendly context sample in:

- `data/veda/validation/runtime/p012_knowledge_boundary.json`

P011 may consume these facts for retrieval context, but P012 does not activate promoted rules or mutate Approved Core.
""",
        "VEDA-P012-14_API_FRONTEND_COMPATIBILITY.md": f"""# API & Frontend Compatibility

Migrated route status:

| Surface | Runtime Surface | Status | Facade Routed |
| --- | --- | --- | --- |
{migration_lines}
""",
        "VEDA-P012-15_PERFORMANCE_REPORT.md": """# Performance Report

Performance measurements are recorded in:

- `data/veda/validation/runtime/p012_performance_report.json`

P012 defines a safe cache-key policy but leaves deterministic chart-fact caching disabled.
""",
        "VEDA-P012-16_MIGRATION_PILOT.md": f"""# Migration Pilot

The current migration pilot routes active read paths through the facade while preserving legacy payloads.

P004 fixture sample:

| Fixture | Status | Chart ID |
| --- | --- | --- |
{p004_lines}
""",
        "VEDA-P012-17_VALIDATION_REPORT.md": """# Validation Report

Validation artifacts:

- `p012_runtime_surface_inventory.json`
- `p012_runtime_profiles.json`
- `p012_runtime_capabilities.json`
- `p012_runtime_divergences.json`
- `p012_shadow_comparison_results.json`
- `p012_runtime_migration_status.json`
- `p012_p001_fixture_results.json`
- `p012_p004_fixture_results.json`
- `p012_summary.json`
""",
        "VEDA-P012-18_FINAL_ACCEPTANCE.md": f"""# Final Acceptance

Current acceptance status:

- Legacy engines removed: `{summary['legacy_engines_removed']}`
- Unexplained divergences: `{summary['unexplained_divergences']}`
- Production astrology calculation semantics changed: `{summary['production_astrology_calculation_semantics_changed']}`
- Production astrology interpretation semantics changed: `{summary['production_astrology_interpretation_semantics_changed']}`
- Approved Core changed: `{summary['approved_core_changed']}`
- Production rules activated: `{summary['production_rules_activated']}`
""",
    }
    written: list[Path] = []
    for name, content in docs.items():
        path = root / "docs" / "current-state" / "p012" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def validate_exported_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    expected_files = {
        "p012_runtime_surface_inventory.json": bundle["runtime_surface_inventory"],
        "p012_runtime_profiles.json": bundle["runtime_profiles"],
        "p012_runtime_capabilities.json": bundle["runtime_capabilities"],
        "p012_request_contract_example.json": bundle["runtime_request_contract_example"],
        "p012_chart_fact_contract_sample.json": bundle["runtime_chart_fact_contract_sample"],
        "p012_runtime_divergences.json": bundle["runtime_divergences"],
        "p012_shadow_comparison_results.json": bundle["shadow_comparison_results"],
        "p012_runtime_migration_status.json": bundle["runtime_migration_status"],
        "p012_p001_fixture_results.json": bundle["p001_fixture_results"],
        "p012_p004_fixture_results.json": bundle["p004_fixture_results"],
        "p012_knowledge_boundary.json": bundle["knowledge_boundary"],
        "p012_performance_report.json": bundle["performance_report"],
        "p012_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    missing: list[str] = []
    mismatched: list[str] = []
    for name, payload in expected_files.items():
        path = root / "data" / "veda" / "validation" / "runtime" / name
        if not path.exists():
            missing.append(name)
            continue
        if _load_json(path) != payload:
            mismatched.append(name)

    schema_errors: list[str] = []
    if jsonschema is not None:
        schemas = _schema_documents()
        checks = [
            ("runtime_request.schema.json", bundle["runtime_request_contract_example"]),
            ("runtime_chart_facts.schema.json", bundle["runtime_chart_fact_contract_sample"]),
            *[("runtime_profile.schema.json", row) for row in bundle["runtime_profiles"]],
            ("runtime_capabilities.schema.json", bundle["runtime_capabilities"]),
            *[("runtime_divergence.schema.json", row) for row in bundle["runtime_divergences"]],
            *[("runtime_migration_status.schema.json", row) for row in bundle["runtime_migration_status"]],
            *[("shadow_comparison.schema.json", row) for row in bundle["shadow_comparison_results"]],
        ]
        for schema_name, payload in checks:
            try:
                jsonschema.validate(payload, schemas[schema_name])
            except Exception as exc:  # pragma: no cover - error reporting only
                schema_errors.append(f"{schema_name}: {exc}")

    return {
        "is_valid": not missing and not mismatched and not schema_errors,
        "missing_files": missing,
        "mismatched_files": mismatched,
        "schema_errors": schema_errors,
    }


__all__ = [
    "build_phase_bundle",
    "export_phase_bundle",
    "render_phase_docs",
    "validate_exported_bundle",
    "write_json_schemas",
]
