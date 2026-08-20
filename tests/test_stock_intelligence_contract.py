from __future__ import annotations

import pandas as pd

from backend.services import stock_intelligence as contract


def _history() -> pd.DataFrame:
    dates = pd.date_range("2026-08-01", periods=25, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "close": [100 + index for index in range(25)],
            "volume": [1000] * 24 + [2500],
        }
    )


def test_price_windows_require_complete_trading_observations() -> None:
    windows, meta = contract._windows(_history())

    assert meta["state"] == "AVAILABLE"
    assert windows["1"]["return_pct"] == 0.81
    assert windows["5"]["return_pct"] == 4.2
    assert windows["20"]["return_pct"] == 19.23
    assert windows["20"]["observations"] == 20


def test_volume_signal_is_technical_and_not_institutional_attribution() -> None:
    context = contract._volume_context(_history())

    assert context["state"] == "CONFIRMING_UP_MOVE"
    assert context["relative_volume"] == 2.5
    assert "institutional" in context["interpretation"].lower()


def test_contract_preserves_missing_data_and_separates_cross_layer_context(monkeypatch) -> None:
    frames = {
        "sector_rotation": pd.DataFrame(
            [{
                "sector": "TECHNOLOGY",
                "contract_version": "sector-rotation-1.1",
                "last_date": "2026-08-20",
                "sector_return_5d": 2.0,
                "sector_return_20d": 4.0,
                "benchmark_return_5d": 1.0,
                "benchmark_return_20d": 2.0,
                "relative_return_5d": 1.0,
                "relative_return_20d": 2.0,
                "leadership_state": "IMPROVING",
                "persistence_state": "MIXED",
                "rotation_state": "IMPROVING",
                "benchmark": "NIFTY 50 equal-weight constituent return proxy",
                "evidence_quality": "MEDIUM",
                "benchmark_price_as_of": "2026-08-20",
            }]
        ),
        "price_momentum": pd.DataFrame(),
        "watchlist_metrics": pd.DataFrame(),
        "deal_signals": pd.DataFrame(),
        "holding_trends": pd.DataFrame(),
        "participant_flows": pd.DataFrame(),
        "announcements": pd.DataFrame(),
    }
    monkeypatch.setattr(contract.data_loader, "get", lambda key: frames.get(key))
    monkeypatch.setattr(contract, "_price_history", lambda symbol: _history())
    result = contract.build_stock_intelligence_contract(
        "RELIANCE",
        pd.Series({"symbol": "RELIANCE", "sector": "TECHNOLOGY", "close_now": 124.0}),
        fundamentals={},
        technical={"trend_signal": "STRONG_UPTREND", "close_now": 124.0, "as_of_date": "2026-08-20"},
        shareholding={},
        holding_trends=[],
        deal_info={},
        upcoming_events=[],
    )

    assert result["contract_version"] == "stock-intelligence-1.1"
    assert result["signals"]["cross_layer_state"] == "STRONG_STOCK_STRONG_SECTOR"
    assert result["signals"]["institutional_context"]["scope"] == "NOT_SUPPORTED"
    assert result["facts"]["fundamentals"] == {}
    assert result["date_alignment"]["state"] == "PARTIALLY_ALIGNED"
    assert "forecast" in result["interpretation"] or "predictive" in result["interpretation"]
