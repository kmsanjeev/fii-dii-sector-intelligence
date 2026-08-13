from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import gochar as gochar_router
from engines.transit_gochar import TransitGocharEngine, TransitReferenceType


def test_gochar_engine_uses_lagna_and_moon_reference_points(monkeypatch):
    engine = TransitGocharEngine()

    natal_chart = {
        "entity": {"name": "Fixture Native"},
        "lagna": {"sign": "Aries", "sign_num": 0, "full_longitude": 15.0},
        "planets": {"Moon": {"sign": "Taurus", "sign_num": 1, "longitude": 45.0}},
    }

    def _fixed_positions(_dt_utc):
        return {
            "Saturn": {
                "longitude": 10.0,
                "retrograde": False,
                "longitude_speed_deg_per_day": 0.05,
                "motion_state": "DIRECT",
            },
            "Jupiter": {
                "longitude": 130.0,
                "retrograde": False,
                "longitude_speed_deg_per_day": 0.09,
                "motion_state": "DIRECT",
            },
        }

    monkeypatch.setattr(engine, "_planet_positions", _fixed_positions)
    snapshot = engine.build_snapshot(natal_chart, reference_bases=[TransitReferenceType.LAGNA, TransitReferenceType.MOON])

    saturn_lagna = next(
        fact for fact in snapshot.relationship_facts
        if fact.graha == "Saturn" and fact.natal_reference_type == TransitReferenceType.LAGNA
    )
    saturn_moon = next(
        fact for fact in snapshot.relationship_facts
        if fact.graha == "Saturn" and fact.natal_reference_type == TransitReferenceType.MOON
    )

    assert saturn_lagna.angular_separation == 5.0
    assert saturn_lagna.relative_house == 1
    assert saturn_moon.angular_separation == 35.0
    assert saturn_moon.relative_house == 12

    rule = next(item for item in snapshot.rule_results if item.rule_id == "VEDA-P019-RUL-001")
    assert rule.matched is True
    assert rule.reference_type == TransitReferenceType.MOON
    assert rule.reference_entity == "Moon"


def test_gochar_stock_route_returns_kundli_and_gochar(monkeypatch):
    class DummyEngine:
        def build_snapshot(self, *args, **kwargs):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "entity_id": "RELIANCE",
                    "location_id": "LAGNA+MOON",
                    "gochar_metrics": {"fact_count": 2},
                }
            )

    class DummyService:
        def compute_stock_chart(self, *args, **kwargs):
            return SimpleNamespace(
                legacy_payload={
                    "entity": {"symbol": "RELIANCE"},
                    "lagna": {"sign": "Libra"},
                    "planets": {"Moon": {"sign": "Taurus"}},
                }
            )

    monkeypatch.setattr(
        gochar_router,
        "_load_equity_master",
        lambda: pd.DataFrame([{"symbol": "RELIANCE", "series": "EQ", "listing_date": "1995-11-29"}]).set_index("symbol"),
    )
    monkeypatch.setattr(gochar_router, "get_jyotisha_runtime_service", lambda: DummyService())
    monkeypatch.setattr(gochar_router, "_get_engine", lambda: DummyEngine())

    app = FastAPI()
    app.include_router(gochar_router.router)
    client = TestClient(app)

    response = client.get("/api/gochar/stock/RELIANCE")

    assert response.status_code == 200
    payload = response.json()
    assert payload["kundli"]["lagna"]["sign"] == "Libra"
    assert payload["gochar"]["entity_id"] == "RELIANCE"


def test_gochar_human_route_returns_gochar_payload(monkeypatch):
    class DummyEngine:
        def build_snapshot(self, *args, **kwargs):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "entity_id": "Fixture Human",
                    "location_id": "LAGNA+MOON",
                    "gochar_metrics": {"reference_counts": {"LAGNA": 4, "MOON": 4}},
                }
            )

    class DummyService:
        def compute_rest_human_chart(self, *args, **kwargs):
            return SimpleNamespace(
                legacy_payload={
                    "entity": {"name": "Fixture Human"},
                    "lagna": {"sign": "Aries"},
                    "planets": {"Moon": {"sign": "Cancer"}},
                }
            )

    monkeypatch.setattr(gochar_router, "get_jyotisha_runtime_service", lambda: DummyService())
    monkeypatch.setattr(gochar_router, "_get_engine", lambda: DummyEngine())

    app = FastAPI()
    app.include_router(gochar_router.router)
    client = TestClient(app)

    response = client.post(
        "/api/gochar/human",
        json={
            "name": "Fixture Human",
            "date_str": "1984-11-03",
            "time_str": "06:30:00",
            "lat": 19.076,
            "lon": 72.8777,
            "tz_offset": 5.5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kundli"]["lagna"]["sign"] == "Aries"
    assert payload["gochar"]["location_id"] == "LAGNA+MOON"
