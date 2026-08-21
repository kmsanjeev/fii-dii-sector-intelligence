from __future__ import annotations

from backend.services import cross_layer_intelligence as composition


def _status(state: str = "EOD") -> dict:
    return {"state": state, "as_of": "2026-08-20", "source": ["fixture"], "limitations": []}


def _sector(name: str, leadership: str, rank: float, symbols: list[str]) -> dict:
    return {
        "sector": name,
        "contract_version": "sector-rotation-1.1",
        "as_of": "2026-08-20",
        "leadership": leadership,
        "rotation": leadership,
        "persistence": "PERSISTENT_LEADER" if leadership in {"LEADING", "IMPROVING"} else "MIXED",
        "relative_strength_rank_5d": rank,
        "relative_return_5d": 2.0,
        "relative_return_20d": 3.0,
        "breadth": {"positive_pct": 70.0, "coverage_pct": 95.0},
        "evidence_quality": "HIGH",
        "leaders": [{"symbol": symbol} for symbol in symbols],
        "laggards": [],
    }


def _stock(symbol: str, trend: str = "STRONG") -> dict:
    return {
        "identity": {"sector": "TECHNOLOGY"},
        "facts": {"volume": {"state": "CONFIRMING_UP_MOVE"}},
        "signals": {
            "trend_state": trend,
            "momentum_windows": {"5": 4.0},
            "market_relative_strength": {"5": 2.0},
            "sector_relative_strength": {"5": 1.0},
            "institutional_context": {"scope": "MARKET_LEVEL_CONTEXT_ONLY"},
        },
        "evidence_quality": "HIGH",
        "date_alignment": {"components": {"price": "2026-08-20", "fundamentals": "2026-08-01", "corporate_source_update": "2026-08-20"}},
    }


def _patch_sources(monkeypatch, sectors, institutional_state="MIXED"):
    monkeypatch.setattr(composition, "_market_snapshot", lambda: ({"state": "SUPPORTIVE", "regime": "BULLISH", "as_of": "2026-08-20", "evidence_quality": "HIGH"}, _status()))
    monkeypatch.setattr(composition, "_institutional_snapshot", lambda: ({"state": institutional_state, "scope": "MARKET_LEVEL_CONTEXT_ONLY", "cash_as_of": "2026-08-19", "fno_as_of": "2026-08-19", "evidence_quality": "HIGH", "contract_version": "institutional-flow-1.1"}, _status("DELAYED")))
    monkeypatch.setattr(composition, "_sector_snapshot", lambda: (sectors, _status()))
    monkeypatch.setattr(composition.data_loader, "freshness_for", lambda required, optional=(): _status())


def test_aligned_leadership_is_deterministic_and_bounded(monkeypatch) -> None:
    sectors = [_sector("TECHNOLOGY", "LEADING", 1, ["RELIANCE", "TCS"]), _sector("BANKING", "IMPROVING", 2, ["HDFCBANK"])]
    _patch_sources(monkeypatch, sectors)
    monkeypatch.setattr(composition, "_stock_contract", lambda symbol: _stock(symbol))

    result = composition.build_cross_layer_intelligence(mode="LEADERSHIP_DISCOVERY", top_sectors=1, stocks_per_sector=1)

    assert result["contract_version"] == "cross-layer-1.0"
    assert result["alignment"]["state"] == "PARTIAL_CONFIRMATION"
    assert len(result["candidates"]) == 1
    assert len(result["candidates"][0]["stocks"]) == 1
    assert result["candidates"][0]["stocks"][0]["alignment"] == "STOCK_SECTOR_ALIGNED"
    assert "smart money" in result["interpretation"].lower()


def test_conflicting_stock_sector_evidence_is_exposed(monkeypatch) -> None:
    sectors = [_sector("TECHNOLOGY", "LEADING", 1, ["RELIANCE"])]
    _patch_sources(monkeypatch, sectors, institutional_state="CAUTIOUS")
    monkeypatch.setattr(composition, "_stock_contract", lambda symbol: _stock(symbol, trend="WEAK"))

    result = composition.build_cross_layer_intelligence(mode="STOCK_CONFIRMATION", symbol="RELIANCE")

    assert result["alignment"]["state"] == "CONFLICTING"
    assert any(item["components"] == ["sector", "stock"] for item in result["conflicts"])
    assert result["institutional"]["scope"] == "MARKET_LEVEL_CONTEXT_ONLY"


def test_missing_layers_are_not_converted_to_neutral_or_predictive_score(monkeypatch) -> None:
    _patch_sources(monkeypatch, [], institutional_state="INSUFFICIENT")
    result = composition.build_cross_layer_intelligence(mode="MARKET_OVERVIEW")

    assert result["alignment"]["state"] == "INSUFFICIENT_EVIDENCE"
    assert result["evidence_quality"]["overall"] == "UNAVAILABLE"
    assert "smart_money_score" not in result
    assert "BUY" not in str(result).upper()
    assert "SELL" not in str(result).upper()
