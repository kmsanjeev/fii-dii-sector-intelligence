from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_fno_routes_are_read_only_and_expose_governed_contract(monkeypatch) -> None:
    from backend.routers import fno

    monkeypatch.setattr(
        fno,
        "build_governed_fno_intelligence",
        lambda **kwargs: {
            "contract_version": "fno-intelligence-1.0",
            "status": "AVAILABLE",
            "futures": [{"symbol": kwargs.get("symbol", "ABC"), "underlying_type": "STOCK"}],
            "pcr": {},
            "data_status": {"state": "AVAILABLE", "as_of": "2026-08-19", "source": ["fixture"], "last_successful_update": "2026-08-19", "limitations": []},
        },
    )
    client = TestClient(app)
    response = client.get("/api/fno/stocks/ABC")
    assert response.status_code == 200
    assert response.json()["contract_version"] == "fno-intelligence-1.0"
    assert response.json()["futures"][0]["symbol"] == "ABC"
    assert client.post("/api/fno/summary").status_code == 405
