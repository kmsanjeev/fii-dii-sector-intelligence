from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engines.ai.chatbot.tools.data_tools import generate_personal_kundli
from engines.ai.knowledge.astrology_runtime_boundary import validate_exported_bundle
from engines.intelligence.jyotisha_runtime import get_jyotisha_runtime_service


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "veda" / "validation" / "runtime"


def _load_json(name: str):
    with open(DATA_ROOT / name, encoding="utf-8") as handle:
        return json.load(handle)


def test_generate_personal_kundli_preserves_unknown_time_semantics():
    payload = generate_personal_kundli(
        date_of_birth="03-11-1984",
        time_of_birth="unknown",
        place_name="Mumbai",
        latitude=19.076,
        longitude=72.8777,
        timezone_offset_hours=5.5,
    )

    assert payload["entity"]["time_approximate"] is True
    assert payload["entity"]["inception_time"] == "06:00:00"
    assert payload["birth_details"]["local_datetime"].endswith("06:00:00")


def test_stock_request_preserves_exchange_offset_profile():
    service = get_jyotisha_runtime_service()
    request = service.build_stock_request("RELIANCE", "1995-11-29", "NYSE")

    assert request.runtime_profile == "STOCK_MARKET"
    assert request.timezone == "UTC-05:00"
    assert request.metadata["exchange_timezone_name"] == "America/New_York"


def test_chart_facts_include_ontology_ids_and_retrieval_context():
    service = get_jyotisha_runtime_service()
    execution = service.compute_personal_chart(
        date_of_birth="1984-11-03",
        time_of_birth="06:30",
        place_name="Mumbai",
        latitude=19.076,
        longitude=72.8777,
        timezone_offset_hours=5.5,
    )
    context = service.build_retrieval_fact_context(execution.chart_facts)

    assert execution.chart_facts["lagna"]["entity_id"] == "VEDA-LAGNA-ASCENDANT"
    assert execution.chart_facts["planets"][0]["entity_id"] == "VEDA-GRAHA-SUN"
    assert execution.chart_facts["houses"][0]["entity_id"] == "VEDA-BHAVA-01"
    assert "VEDA-GRAHA-SUN" in context["ontology_tokens"]
    assert any(tag.startswith("Lagna in ") for tag in context["fact_tags"])


def test_human_route_uses_facade_without_shape_change(monkeypatch):
    from backend.routers import kundli as kundli_router

    calls = {"count": 0}

    class DummyService:
        def compute_rest_human_chart(self, **kwargs):
            calls["count"] += 1
            return SimpleNamespace(
                legacy_payload={"lagna": {"sign": "Libra"}, "astro_action": "HOLD", "planets": {}}
            )

    class DummyInterpretator:
        def interpret(self, chart, generate_narrative=False):
            return {"mode": "rest", "generate_narrative": generate_narrative, "lagna": chart["lagna"]["sign"]}

    monkeypatch.setattr(kundli_router, "get_jyotisha_runtime_service", lambda: DummyService())
    monkeypatch.setattr(kundli_router, "_get_engines", lambda: (None, None, DummyInterpretator()))

    app = FastAPI()
    app.include_router(kundli_router.router)
    client = TestClient(app)
    response = client.post(
        "/api/kundli/human",
        json={
            "name": "Fixture Mumbai 1984",
            "date_str": "1984-11-03",
            "time_str": "06:30:00",
            "lat": 19.076,
            "lon": 72.8777,
            "tz_offset": 5.5,
        },
    )

    assert response.status_code == 200
    assert calls["count"] == 1
    payload = response.json()
    assert payload["kundli"]["lagna"]["sign"] == "Libra"
    assert payload["interpretation"]["mode"] == "rest"


def test_country_route_uses_facade_without_shape_change(monkeypatch):
    from backend.routers import kundli as kundli_router

    calls = {"count": 0}

    class DummyService:
        def compute_country_chart(self, country_name: str):
            calls["count"] += 1
            return SimpleNamespace(
                legacy_payload={"lagna": {"sign": "Taurus"}, "astro_action": "BUY", "planets": {}}
            )

    class DummyInterpretator:
        def interpret(self, chart, generate_narrative=False):
            return {"mode": "country", "lagna": chart["lagna"]["sign"]}

    monkeypatch.setattr(kundli_router, "get_jyotisha_runtime_service", lambda: DummyService())
    monkeypatch.setattr(kundli_router, "_get_engines", lambda: (None, None, DummyInterpretator()))

    app = FastAPI()
    app.include_router(kundli_router.router)
    client = TestClient(app)
    response = client.get("/api/kundli/country/India")

    assert response.status_code == 200
    assert calls["count"] == 1
    payload = response.json()
    assert payload["country"] == "India"
    assert payload["kundli"]["lagna"]["sign"] == "Taurus"
    assert payload["interpretation"]["mode"] == "country"


def test_p012_export_bundle_is_current():
    report = validate_exported_bundle(ROOT)
    assert report["is_valid"] is True
    assert report["missing_files"] == []
    assert report["mismatched_files"] == []
    assert report["schema_errors"] == []


def test_p012_summary_records_migration_and_fixture_pass_counts():
    payload = _load_json("p012_summary.json")
    summary = payload["summary"]

    assert summary["runtime_surfaces_identified"] == 8
    assert summary["production_paths_routed_through_facade"] == 4
    assert summary["p001_pass_count"] == summary["p001_total"] == 11
    assert summary["p004_pass_count"] == summary["p004_total"] == 25
    assert summary["legacy_engines_removed"] == 0
    assert summary["production_astrology_calculation_semantics_changed"] == "NO"
    assert summary["production_astrology_interpretation_semantics_changed"] == "NO"
    assert summary["approved_core_changed"] == "NO"
    assert summary["production_rules_activated"] == 0


def test_p012_shadow_results_capture_known_differences():
    payload = _load_json("p012_shadow_comparison_results.json")

    assert len(payload) == 2
    assert all(row["status"] == "KNOWN_DIVERGENCE" for row in payload)
    assert any(
        item["fact"] in {"non_core_graha_surface", "varga_surface", "all_antardashas_presence"}
        for row in payload
        for item in row["divergences"]
    )
