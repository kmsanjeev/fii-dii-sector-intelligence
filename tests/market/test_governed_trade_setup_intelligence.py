from __future__ import annotations

from pathlib import Path

from backend.services import governed_trade_setup_intelligence as service


def _stock_fixture() -> dict:
    technical = {
        "trend_signal": "STRONG_UPTREND",
        "as_of_date": "2026-08-20",
        "rsi": 62,
        "macd_cross": "BULLISH",
        "atr_14": 4,
        "atr_pct": 2,
        "bb_pct": 55,
        "bb_signal": "MID_BAND",
        "bb_width": 8,
        "dma_20": 100,
    }
    return {
        "identity": {"isin": "INE000A01000"},
        "facts": {
            "close": 110,
            "technical": technical,
            "history": {"state": "AVAILABLE", "as_of": "2026-08-20"},
            "price_windows": {
                "5": {"return_pct": 4, "state": "AVAILABLE"},
                "20": {"return_pct": 8, "state": "AVAILABLE"},
            },
            "volume": {"state": "CONFIRMING_UP_MOVE"},
            "fundamental_evidence": {"coverage": {"quality": "HIGH"}},
            "corporate": {
                "scheduled_events": [],
                "recent_events": [],
                "evidence_quality": "HIGH",
            },
        },
        "signals": {
            "market_relative_strength": {"5": 2},
            "sector_relative_strength": {"5": 3},
            "sector_context": {
                "sector": "IT",
                "leadership_state": "LEADING",
                "relative_return_5d": 2,
                "evidence_quality": "HIGH",
                "as_of": "2026-08-20",
            },
            "institutional_context": {"scope": "MARKET_LEVEL_CONTEXT_ONLY"},
        },
        "date_alignment": {
            "components": {
                "price": "2026-08-20",
                "technical": "2026-08-20",
                "fundamentals": "2026-06-30",
            }
        },
        "limitations": [],
    }


def test_swing_and_positional_are_distinct(monkeypatch):
    monkeypatch.setattr(service, "_stock_contract", lambda symbol: _stock_fixture())
    monkeypatch.setattr(
        service,
        "_row",
        lambda frame, symbol: {
            "ret_60d": -3,
            "ret_90d": -5,
            "as_of_date": "2026-08-20",
        },
    )
    monkeypatch.setattr(
        service,
        "_fno",
        lambda symbol: {
            "state": "SUPPORTIVE",
            "applicability": "FNO_APPLICABLE",
            "as_of": "2026-08-20",
            "record": {},
        },
    )
    monkeypatch.setattr(
        service,
        "_market_context",
        lambda: {"state": "SUPPORTIVE", "as_of": "2026-08-20", "regime": "BULLISH"},
    )
    swing = service.build_trade_setup_intelligence(
        "TEST", horizon="SWING", include_themes=False
    )
    positional = service.build_trade_setup_intelligence(
        "TEST", horizon="POSITIONAL", include_themes=False
    )
    assert swing["setup_state"] == "BULLISH_SETUP"
    assert positional["setup_state"] == "WATCHLIST_SETUP"
    assert swing["horizon"] != positional["horizon"]


def test_roll_and_fno_absence_remain_explicit(monkeypatch):
    fixture = _stock_fixture()
    monkeypatch.setattr(service, "_stock_contract", lambda symbol: fixture)
    monkeypatch.setattr(
        service,
        "_row",
        lambda frame, symbol: {"ret_60d": 4, "ret_90d": 8, "as_of_date": "2026-08-20"},
    )
    monkeypatch.setattr(
        service,
        "_fno",
        lambda symbol: {
            "state": "LIMITED",
            "applicability": "FNO_APPLICABLE",
            "as_of": "2026-08-19",
            "roll_state": "ROLL_TRANSITION",
            "record": {},
        },
    )
    result = service.build_trade_setup_intelligence(
        "TEST", horizon="POSITIONAL", include_themes=False
    )
    assert result["fno"]["roll_state"] == "ROLL_TRANSITION"
    assert any(item["components"] == ["fno"] for item in result["conflicts"])
    assert "F&O confirmation is limited during contract roll." in result["risks"]


def test_legacy_scores_are_not_dependencies():
    source = Path(service.__file__).read_text(encoding="utf-8")
    assert "bull_run_probability.csv" not in source
    assert "ml_scores_combined.csv" not in source
    assert "trade_conviction_scores.csv" not in source
    assert "from engines.execution" not in source


def test_invalidation_is_context_not_order():
    result = service._invalidations(
        110,
        "BULLISH",
        _stock_fixture()["facts"]["technical"],
        service._volatility(_stock_fixture()["facts"]["technical"]),
    )
    assert result["numeric"] is True
    assert result["is_order"] is False
    assert "broker stop" in result["limitations"][0]
