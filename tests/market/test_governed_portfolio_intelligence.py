from __future__ import annotations

import pandas as pd

from backend.services import governed_portfolio_intelligence as service


def test_empty_portfolio_is_explicit_and_read_only() -> None:
    result = service.build_governed_portfolio_intelligence()
    assert result["contract_version"] == "portfolio-intelligence-1.0"
    assert result["portfolio_scope"] == "LOCAL_SINGLE_USER"
    assert result["positions"] == []
    assert result["valuation"] == {"invested": 0.0, "market_value": 0.0, "pnl": 0.0, "cash": None}
    assert result["legacy_audit"]["buy_sell_labels"] == "NOT_AUTHORITATIVE"
    assert "BUY" not in result["legacy_audit"]["buy_sell_labels"]
    assert "SELL" not in result["legacy_audit"]["buy_sell_labels"]


def test_positions_use_governed_theme_overlap_and_missing_price(monkeypatch) -> None:
    monkeypatch.setattr(
        service.portfolio_engine,
        "load_transactions",
        lambda: pd.DataFrame([{"date": "2026-08-20", "symbol": "AAA", "action": "BUY", "qty": 10, "price": 100}]),
    )
    monkeypatch.setattr(
        service.portfolio_engine,
        "compute_positions",
        lambda _: pd.DataFrame(
            [{"symbol": "AAA", "qty": 10, "avg_cost": 100, "invested": 1000, "first_bought": "2026-08-20", "last_action_date": "2026-08-20"}]
        ),
    )
    monkeypatch.setattr(service, "_latest_price", lambda symbol: (120.0, "2026-08-21"))
    monkeypatch.setattr(service, "_data_status", lambda: {"state": "EOD", "limitations": []})
    monkeypatch.setattr(service, "_risk_snapshot", lambda: {"method": "existing", "var": {"state": "NOT_AVAILABLE"}})
    monkeypatch.setattr(
        service,
        "build_cross_layer_intelligence",
        lambda **kwargs: {
            "market": {},
            "institutional": {},
            "stock_confirmation": {"sector": "TECH", "fundamental_evidence": {}, "corporate_event_context": {}},
            "sectors": {},
            "alignment": {},
            "conflicts": [],
            "date_alignment": {},
            "data_status": {},
        },
    )
    monkeypatch.setattr(
        service.theme_service,
        "memberships_for",
        lambda **kwargs: [{"theme_id": "theme.a"}, {"theme_id": "theme.b"}],
    )

    result = service.build_governed_portfolio_intelligence()
    position = result["positions"][0]
    assert position["latest_price"] == 120.0
    assert position["market_value"] == 1200.0
    assert position["portfolio_weight"] == 100.0
    assert result["allocation"]["sector"]["items"][0]["sector"] == "TECH"
    assert result["allocation"]["theme"]["overlapping_positions"] == {
        "AAA": ["theme.a", "theme.b"]
    }
    assert result["allocation"]["theme"]["items"][0]["gross_membership_weight_pct"] == 100.0


def test_missing_price_is_not_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "_latest_price",
        lambda symbol: (None, None),
    )
    row = pd.Series(
        {
            "qty": 2,
            "avg_cost": 50,
            "invested": 100,
            "first_bought": "2026-08-20",
            "last_action_date": "2026-08-20",
        }
    )
    item = service._position("AAA", row)
    assert item["latest_price"] is None
    assert item["market_value"] is None
    assert item["unrealized_pnl"] is None
    assert item["data_status"] == "PRICE_NOT_AVAILABLE"
