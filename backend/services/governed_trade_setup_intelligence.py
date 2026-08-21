"""Governed EOD Swing and Positional setup intelligence.

This is a transparent evidence composition layer. It deliberately does not
replace the technical or F&O engines, does not consume legacy composite/ML
scores, and cannot place or draft orders.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from backend.services import data_loader
from backend.services.governed_fno_intelligence import build_governed_fno_intelligence
from backend.services.governed_theme_intelligence import (
    intelligence as theme_intelligence,
)
from backend.services.governed_theme_intelligence import memberships_for
from backend.services.stock_intelligence import build_stock_intelligence_contract

CONTRACT_VERSION = "trade-setup-intelligence-1.0"
HORIZONS = {"SWING", "POSITIONAL"}
SCREEN_LIMIT_MAX = 50


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _boolean(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        try:
            return _clean(value.item())
        except (TypeError, ValueError):
            return None
    return value


def _round(value: Any, digits: int = 2) -> float | None:
    value = _number(value)
    return round(value, digits) if value is not None else None


def _row(frame: pd.DataFrame | None, symbol: str) -> pd.Series | None:
    if frame is None or frame.empty or "symbol" not in frame.columns:
        return None
    matches = frame[frame["symbol"].astype(str).str.upper() == symbol]
    return matches.iloc[0] if not matches.empty else None


def _record(row: pd.Series | None) -> dict[str, Any]:
    return (
        {} if row is None else {str(key): _clean(value) for key, value in row.items()}
    )


def _upcoming_events(symbol: str) -> list[dict[str, Any]]:
    frame = data_loader.get("event_calendar")
    if (
        frame is None
        or frame.empty
        or not {"symbol", "event_date"}.issubset(frame.columns)
    ):
        return []
    dates = pd.to_datetime(frame["event_date"], errors="coerce")
    today = pd.Timestamp.now().normalize()
    rows = frame[
        (frame["symbol"].astype(str).str.upper() == symbol)
        & (dates >= today)
        & (dates <= today + pd.Timedelta(days=45))
    ].copy()
    if rows.empty:
        return []
    rows["_event_date"] = pd.to_datetime(rows["event_date"], errors="coerce")
    rows = rows.sort_values("_event_date").head(5)
    return [
        {
            "event_date": str(row.get("event_date", ""))[:10],
            "purpose_type": _clean(row.get("purpose_type")),
            "bm_desc": str(row.get("bm_desc", ""))[:300],
        }
        for _, row in rows.iterrows()
    ]


def _stock_contract(symbol: str) -> dict[str, Any]:
    technical_row = _row(data_loader.get("technical"), symbol)
    momentum_row = _row(data_loader.get("price_momentum"), symbol)
    valuation_row = _row(data_loader.get("valuation_scores"), symbol)
    extended_row = _row(data_loader.get("extended_financials"), symbol)
    source = technical_row if technical_row is not None else momentum_row
    if source is None:
        raise KeyError(symbol)
    sector_source = (
        valuation_row
        if valuation_row is not None
        else momentum_row
        if momentum_row is not None
        else source
    )
    sector = str(sector_source.get("sector", "UNKNOWN") or "UNKNOWN").upper()
    row = pd.Series(
        {"symbol": symbol, "sector": sector, "close_now": source.get("close_now")}
    )
    fundamentals = {**_record(valuation_row), **_record(extended_row)}
    return build_stock_intelligence_contract(
        symbol,
        row,
        fundamentals=fundamentals,
        technical=_record(technical_row),
        shareholding={},
        holding_trends=[],
        deal_info={},
        upcoming_events=_upcoming_events(symbol),
    )


def _market_context() -> dict[str, Any]:
    participant = data_loader.get("participant_intel")
    if participant is None or participant.empty or "date" not in participant.columns:
        return {"state": "UNAVAILABLE", "as_of": None, "regime": None}
    latest = participant.sort_values("date").iloc[-1]
    regime = str(latest.get("Market_Regime") or "UNKNOWN").upper()
    state = (
        "SUPPORTIVE"
        if regime in {"BULLISH", "UPTREND", "POSITIVE"}
        else "ADVERSE"
        if regime in {"BEARISH", "DOWNTREND", "NEGATIVE"}
        else "MIXED"
    )
    return {
        "state": state,
        "regime": regime,
        "as_of": str(latest.get("date", ""))[:10],
        "smart_money_score": _round(latest.get("Smart_Money_Score")),
        "scope": "MARKET_LEVEL_CONTEXT_ONLY",
    }


def _theme_context(symbol: str) -> list[dict[str, Any]]:
    try:
        memberships = memberships_for(symbol=symbol)
    except (FileNotFoundError, KeyError, ValueError):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for membership in memberships[:5]:
        theme_id = str(membership.get("theme_id", ""))
        if not theme_id or theme_id in seen:
            continue
        seen.add(theme_id)
        try:
            detail = theme_intelligence(theme_id)
        except (FileNotFoundError, KeyError, ValueError):
            detail = {}
        leadership = detail.get("leadership", {}) if isinstance(detail, dict) else {}
        result.append(
            {
                "theme_id": theme_id,
                "theme_code": membership.get("theme_code"),
                "relationship_type": membership.get("relationship_type"),
                "exposure": membership.get("exposure"),
                "state": leadership.get("state", "UNAVAILABLE"),
                "relative_strength_5d": detail.get("performance", {})
                .get("relative_strength", {})
                .get("5D")
                if detail
                else None,
                "as_of": detail.get("as_of") if detail else None,
                "evidence_quality": detail.get("evidence", {}).get(
                    "quality", "UNAVAILABLE"
                )
                if detail
                else "UNAVAILABLE",
                "membership_scope": "CURRENT_MEMBERSHIP_ONLY",
            }
        )
    return result


def _trend(technical: dict[str, Any]) -> dict[str, Any]:
    raw = str(technical.get("trend_signal") or "").upper()
    if "UPTREND" in raw:
        state = "BULLISH"
    elif "DOWNTREND" in raw:
        state = "BEARISH"
    elif raw in {"CONSOLIDATING", "RANGING"}:
        state = "RANGE_BOUND"
    else:
        state = "INSUFFICIENT_DATA"
    return {
        "state": state,
        "source_signal": raw or "NOT_AVAILABLE",
        "as_of": technical.get("as_of_date"),
    }


def _momentum(
    technical: dict[str, Any], windows: dict[str, Any], momentum: dict[str, Any]
) -> dict[str, Any]:
    five = _number(windows.get("5", {}).get("return_pct"))
    twenty = _number(windows.get("20", {}).get("return_pct"))
    medium = _number(momentum.get("ret_60d"))
    long = _number(momentum.get("ret_90d"))
    macd = str(technical.get("macd_cross") or "").upper()
    rsi = _number(technical.get("rsi"))
    bb_pct = _number(technical.get("bb_pct"))
    if five is None or twenty is None:
        state = "INSUFFICIENT_DATA"
    elif five > 0 and twenty > 0 and macd not in {"BEARISH", "BEARISH_CROSS"}:
        state = "POSITIVE"
    elif five < 0 and twenty < 0 and macd not in {"BULLISH", "BULLISH_CROSS"}:
        state = "NEGATIVE"
    else:
        state = "MIXED"
    phase = "NORMAL"
    if (rsi is not None and rsi >= 70) or (bb_pct is not None and bb_pct >= 90):
        phase = "OVEREXTENDED"
    elif macd in {"BULLISH_CROSS", "BEARISH_CROSS"}:
        phase = "ACCELERATING"
    return {
        "state": state,
        "phase": phase,
        "short_return_5d_pct": _round(five),
        "swing_return_20d_pct": _round(twenty),
        "positional_return_60d_pct": _round(medium),
        "positional_return_90d_pct": _round(long),
        "rsi": _round(rsi),
        "macd_cross": macd or "NOT_AVAILABLE",
        "as_of": technical.get("as_of_date") or momentum.get("as_of_date"),
    }


def _volatility(technical: dict[str, Any]) -> dict[str, Any]:
    atr_pct = _number(technical.get("atr_pct"))
    bb_signal = str(technical.get("bb_signal") or "NOT_AVAILABLE")
    if atr_pct is None:
        state = "INSUFFICIENT_DATA"
    elif atr_pct >= 6:
        state = "HIGH"
    elif atr_pct <= 2:
        state = "LOW"
    else:
        state = "MODERATE"
    return {
        "state": state,
        "atr_14": _round(technical.get("atr_14"), 4),
        "atr_pct": _round(atr_pct),
        "bb_signal": bb_signal,
        "bb_width": _round(technical.get("bb_width")),
    }


def _sector(stock: dict[str, Any]) -> dict[str, Any]:
    value = stock.get("signals", {}).get("sector_context", {})
    leadership = str(value.get("leadership_state") or "").upper()
    relative = _number(value.get("relative_return_5d"))
    if leadership in {"LEADING", "IMPROVING"} or (
        relative is not None and relative > 0
    ):
        state = "SUPPORTIVE"
    elif leadership in {"WEAKENING", "LAGGING", "WEAK"} or (
        relative is not None and relative < 0
    ):
        state = "CONFLICTING"
    else:
        state = "UNAVAILABLE"
    return {
        "sector": value.get("sector"),
        "state": state,
        "leadership_state": leadership or "NOT_AVAILABLE",
        "relative_return_5d": _round(relative),
        "evidence_quality": value.get("evidence_quality", "UNAVAILABLE"),
        "as_of": value.get("as_of"),
    }


def _fno(symbol: str) -> dict[str, Any]:
    # The governed daily F&O projection is already loaded by the provider's
    # data-loader. Prefer it for request-time composition; rebuilding raw
    # bhavcopy selection for every symbol would turn a detail/screen request
    # into an avoidable multi-second N+1 operation.
    loaded = data_loader.get("fno_intel")
    if loaded is not None and not loaded.empty and "symbol" in loaded.columns:
        rows = loaded[loaded["symbol"].astype(str).str.upper() == symbol]
        if rows.empty:
            return {
                "state": "NOT_APPLICABLE",
                "applicability": "FNO_NOT_APPLICABLE",
                "as_of": None,
                "record": None,
            }
        record = {str(key): _clean(value) for key, value in rows.iloc[0].items()}
        signal = str(record.get("oi_signal") or "INSUFFICIENT_EVIDENCE")
        roll = _boolean(record.get("roll_detected", False))
        return {
            "state": "LIMITED"
            if roll
            else "SUPPORTIVE"
            if signal in {"LONG_BUILDUP", "SHORT_COVERING"}
            else "CONFLICTING"
            if signal in {"SHORT_BUILDUP", "LONG_UNWINDING"}
            else "NEUTRAL",
            "applicability": "FNO_APPLICABLE",
            "as_of": record.get("as_of_date"),
            "record": record,
            "roll_state": "ROLL_TRANSITION" if roll else "STABLE_CONTRACT",
        }
    try:
        result = build_governed_fno_intelligence(symbol=symbol)
    except (OSError, ValueError, KeyError):
        return {"state": "UNAVAILABLE", "applicability": "UNKNOWN", "record": None}
    futures = result.get("futures", [])
    if not futures:
        return {
            "state": "NOT_APPLICABLE",
            "applicability": "FNO_NOT_APPLICABLE",
            "as_of": result.get("as_of_date"),
            "record": None,
        }
    record = futures[0]
    signal = str(record.get("oi_signal") or "INSUFFICIENT_EVIDENCE")
    state = (
        "LIMITED"
        if _boolean(record.get("roll_detected"))
        else "SUPPORTIVE"
        if signal in {"LONG_BUILDUP", "SHORT_COVERING"}
        else "CONFLICTING"
        if signal in {"SHORT_BUILDUP", "LONG_UNWINDING"}
        else "NEUTRAL"
    )
    return {
        "state": state,
        "applicability": "FNO_APPLICABLE",
        "as_of": result.get("as_of_date"),
        "record": record,
        "roll_state": "ROLL_TRANSITION"
        if _boolean(record.get("roll_detected"))
        else "STABLE_CONTRACT",
    }


def _invalidations(
    close: float | None,
    trend_state: str,
    technical: dict[str, Any],
    volatility: dict[str, Any],
) -> dict[str, Any]:
    dma = _number(technical.get("dma_20"))
    atr = _number(volatility.get("atr_14"))
    if close is None or (dma is None and atr is None):
        return {
            "state": "NOT_AVAILABLE",
            "numeric": False,
            "level": None,
            "method": "DMA20_OR_TWO_ATR_BUFFER",
            "limitations": ["No usable price, DMA20 or ATR evidence."],
        }
    if trend_state == "BULLISH":
        candidates = [
            value
            for value in (dma, close - 2 * atr if atr is not None else None)
            if value is not None
        ]
        level = min(candidates) if candidates else None
    elif trend_state == "BEARISH":
        candidates = [
            value
            for value in (dma, close + 2 * atr if atr is not None else None)
            if value is not None
        ]
        level = max(candidates) if candidates else None
    else:
        level = dma
    if level is None or level <= 0:
        return {
            "state": "NOT_AVAILABLE",
            "numeric": False,
            "level": None,
            "method": "DMA20_OR_TWO_ATR_BUFFER",
            "limitations": ["Invalidation inputs did not produce a positive level."],
        }
    return {
        "state": "AVAILABLE",
        "numeric": True,
        "level": round(level, 2),
        "method": "BULLISH=min(DMA20,CLOSE-2*ATR14); BEARISH=max(DMA20,CLOSE+2*ATR14); RANGE=DMA20",
        "is_order": False,
        "limitations": [
            "Technical invalidation context only; not a broker stop order and not guaranteed optimal."
        ],
    }


def _dates(
    stock: dict[str, Any],
    fno: dict[str, Any],
    themes: list[dict[str, Any]],
    market: dict[str, Any],
) -> dict[str, Any]:
    components = dict(stock.get("date_alignment", {}).get("components", {}))
    components["fno"] = fno.get("as_of")
    components["theme"] = themes[0].get("as_of") if themes else None
    components["market"] = market.get("as_of")
    fast = [
        str(components.get(key))[:10]
        for key in ("price", "technical", "fno")
        if components.get(key)
    ]
    if not fast:
        state = "UNAVAILABLE"
    elif len(set(fast)) == 1:
        state = "ALIGNED"
    elif len(set(fast)) <= 2:
        state = "PARTIALLY_ALIGNED"
    else:
        state = "MISALIGNED"
    return {
        "state": state,
        "components": components,
        "semantics": "Latest completed EOD evidence; slow fundamentals retain their own period/freshness.",
    }


def _quality(
    stock: dict[str, Any],
    dates: dict[str, Any],
    fno: dict[str, Any],
    themes: list[dict[str, Any]],
    horizon: str,
) -> str:
    if (
        stock.get("facts", {}).get("history", {}).get("state") != "AVAILABLE"
        or dates["state"] == "MISALIGNED"
    ):
        return "INSUFFICIENT"
    technical = stock.get("facts", {}).get("technical", {})
    if not technical or dates["state"] == "UNAVAILABLE":
        return "LIMITED"
    if (
        horizon == "POSITIONAL"
        and stock.get("facts", {})
        .get("fundamental_evidence", {})
        .get("coverage", {})
        .get("quality")
        == "INSUFFICIENT"
    ):
        return "LIMITED"
    if fno.get("state") == "LIMITED" or not themes:
        return "MEDIUM"
    return "HIGH"


def build_trade_setup_intelligence(
    symbol: str, *, horizon: str = "SWING", include_themes: bool = True
) -> dict[str, Any]:
    symbol = str(symbol or "").strip().upper()
    horizon = str(horizon or "SWING").strip().upper()
    if not symbol or horizon not in HORIZONS:
        raise ValueError(
            "symbol and horizon must be valid; horizon is SWING or POSITIONAL"
        )
    stock = _stock_contract(symbol)
    technical = stock.get("facts", {}).get("technical", {})
    momentum_row = _record(_row(data_loader.get("price_momentum"), symbol))
    trend = _trend(technical)
    momentum = _momentum(
        technical, stock.get("facts", {}).get("price_windows", {}), momentum_row
    )
    volatility = _volatility(technical)
    volume = stock.get("facts", {}).get("volume", {"state": "NOT_AVAILABLE"})
    market = _market_context()
    sector = _sector(stock)
    fno = _fno(symbol)
    themes = _theme_context(symbol) if include_themes else []
    dates = _dates(stock, fno, themes, market)
    direction = (
        "LONG_BIAS"
        if trend["state"] == "BULLISH"
        else "SHORT_BIAS"
        if trend["state"] == "BEARISH"
        else "NEUTRAL"
        if trend["state"] == "RANGE_BOUND"
        else "UNAVAILABLE"
    )
    conflicts: list[dict[str, Any]] = []
    if direction == "LONG_BIAS" and fno["state"] == "CONFLICTING":
        conflicts.append(
            {
                "components": ["trend", "fno"],
                "severity": "MATERIAL",
                "reason": "Bullish price trend conflicts with nearest-expiry futures positioning.",
            }
        )
    if direction == "SHORT_BIAS" and fno["state"] == "SUPPORTIVE":
        conflicts.append(
            {
                "components": ["trend", "fno"],
                "severity": "MATERIAL",
                "reason": "Bearish price trend conflicts with supportive nearest-expiry futures positioning.",
            }
        )
    if direction == "LONG_BIAS" and sector["state"] == "CONFLICTING":
        conflicts.append(
            {
                "components": ["trend", "sector"],
                "severity": "MATERIAL",
                "reason": "Stock trend is positive while mapped sector evidence is weak or lagging.",
            }
        )
    if direction == "SHORT_BIAS" and sector["state"] == "SUPPORTIVE":
        conflicts.append(
            {
                "components": ["trend", "sector"],
                "severity": "MATERIAL",
                "reason": "Stock trend is negative while mapped sector evidence is supportive.",
            }
        )
    if momentum["phase"] == "OVEREXTENDED":
        conflicts.append(
            {
                "components": ["momentum", "volatility"],
                "severity": "MATERIAL",
                "reason": "Momentum is extended by deterministic RSI/Bollinger conditions.",
            }
        )
    if fno["state"] == "LIMITED":
        conflicts.append(
            {
                "components": ["fno"],
                "severity": "MINOR",
                "reason": "Contract roll transition limits F&O confirmation.",
            }
        )
    for theme in themes:
        if direction == "LONG_BIAS" and theme["state"] in {"WEAKENING", "LAGGING"}:
            conflicts.append(
                {
                    "components": ["trend", "theme"],
                    "severity": "MATERIAL",
                    "theme_id": theme["theme_id"],
                    "reason": "Stock trend is positive while a current Theme context is weak.",
                }
            )
    corporate = stock.get("facts", {}).get("corporate", {})
    event_risk = bool(corporate.get("scheduled_events"))
    if event_risk:
        conflicts.append(
            {
                "components": ["corporate"],
                "severity": "MATERIAL",
                "reason": "A scheduled corporate event is near; outcome is not predicted.",
            }
        )
    medium = _number(momentum.get("positional_return_60d_pct"))
    long = _number(momentum.get("positional_return_90d_pct"))
    medium_positive = (
        medium is not None and medium > 0 and long is not None and long > 0
    )
    medium_negative = (
        medium is not None and medium < 0 and long is not None and long < 0
    )
    horizon_core = (
        momentum["state"] == "POSITIVE"
        if horizon == "SWING"
        else (
            (trend["state"] == "BULLISH" and medium_positive)
            or (trend["state"] == "BEARISH" and medium_negative)
        )
    )
    if (
        trend["state"] == "INSUFFICIENT_DATA"
        or momentum["state"] == "INSUFFICIENT_DATA"
    ):
        setup_state = "INSUFFICIENT_EVIDENCE"
    elif trend["state"] == "RANGE_BOUND":
        setup_state = "RANGE_BOUND"
    elif not horizon_core:
        setup_state = (
            "WATCHLIST_SETUP"
            if trend["state"] in {"BULLISH", "BEARISH"}
            else "NO_SETUP"
        )
    elif conflicts and any(item["severity"] == "MATERIAL" for item in conflicts):
        setup_state = (
            "EXTENDED"
            if momentum["phase"] == "OVEREXTENDED" and not event_risk
            else "CONFLICTING_EVIDENCE"
        )
    else:
        setup_state = (
            "BULLISH_SETUP" if trend["state"] == "BULLISH" else "BEARISH_SETUP"
        )
    phase = (
        "EXTENDED"
        if momentum["phase"] == "OVEREXTENDED"
        else "DEVELOPING"
        if setup_state == "WATCHLIST_SETUP"
        else "CONFIRMED"
        if setup_state in {"BULLISH_SETUP", "BEARISH_SETUP"}
        else "WEAKENING"
        if conflicts
        else "INVALIDATED"
        if setup_state == "NO_SETUP"
        else "UNAVAILABLE"
    )
    if event_risk and setup_state in {"BULLISH_SETUP", "BEARISH_SETUP"}:
        setup_state = "VALID_WITH_EVENT_RISK"
    quality = _quality(stock, dates, fno, themes, horizon)
    if quality == "INSUFFICIENT" and setup_state not in {
        "INSUFFICIENT_EVIDENCE",
        "NO_SETUP",
    }:
        setup_state = "INSUFFICIENT_EVIDENCE"
    invalidation = _invalidations(
        _number(stock.get("facts", {}).get("close")),
        trend["state"],
        technical,
        volatility,
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "provider_capability": "market.trade-setup.intelligence",
        "symbol": symbol,
        "isin": stock.get("identity", {}).get("isin"),
        "as_of": dates["components"].get("price")
        or dates["components"].get("technical"),
        "horizon": horizon,
        "horizon_definition": {
            "SWING": "Approximately 2-20 trading sessions; fast EOD evidence leads.",
            "POSITIONAL": "Approximately 10-60+ trading sessions; medium-term structure and context lead.",
        }[horizon],
        "data_status": {
            "state": "AVAILABLE" if quality != "INSUFFICIENT" else "LIMITED",
            "frequency": "EOD",
            "latest_completed_session": dates["components"].get("price"),
        },
        "directional_bias": direction,
        "setup_state": setup_state,
        "setup_phase": phase,
        "technical": {
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility,
            "volume": volume,
            "relative_strength": {
                "market": stock.get("signals", {}).get("market_relative_strength", {}),
                "sector": stock.get("signals", {}).get("sector_relative_strength", {}),
            },
        },
        "fno": fno,
        "market": market,
        "sector": sector,
        "themes": themes,
        "institutional": stock.get("signals", {}).get(
            "institutional_context", {"scope": "NOT_SUPPORTED"}
        ),
        "fundamental": stock.get("facts", {}).get("fundamental_evidence", {}),
        "corporate": {
            "event_risk": event_risk,
            "scheduled_events": corporate.get("scheduled_events", []),
            "recent_events": corporate.get("recent_events", []),
            "evidence_quality": corporate.get("evidence_quality", "UNAVAILABLE"),
        },
        "date_alignment": dates,
        "conflicts": conflicts,
        "risks": [
            "Evidence quality is not predictive probability.",
            "EOD data is not live or intraday.",
        ]
        + (
            ["F&O confirmation is limited during contract roll."]
            if fno["state"] == "LIMITED"
            else []
        ),
        "invalidation": invalidation,
        "entry_context": {
            "state": "WAIT_FOR_PULLBACK"
            if phase == "EXTENDED"
            else "NO_VALID_ENTRY_CONTEXT",
            "numeric": False,
            "method": "No numeric entry range is generated; no legacy percentage band is used.",
        },
        "portfolio_context": {
            "state": "NOT_REQUESTED",
            "limitations": [
                "Portfolio concentration is available only through the authenticated Portfolio capability."
            ],
        },
        "evidence_quality": {
            "overall": quality,
            "type": "EVIDENCE_QUALITY_NOT_PREDICTIVE_CONFIDENCE",
            "components": {
                "technical": "AVAILABLE" if technical else "UNAVAILABLE",
                "fno": fno["state"],
                "sector": sector["state"],
                "theme": "AVAILABLE" if themes else "NOT_AVAILABLE",
                "market": market["state"],
                "fundamental": stock.get("facts", {})
                .get("fundamental_evidence", {})
                .get("coverage", {})
                .get("quality", "UNAVAILABLE"),
                "corporate": corporate.get("evidence_quality", "UNAVAILABLE"),
            },
        },
        "facts": {
            "close": stock.get("facts", {}).get("close"),
            "technical_as_of": technical.get("as_of_date"),
            "price_windows": stock.get("facts", {}).get("price_windows", {}),
        },
        "interpretation": "This is a deterministic EOD setup state assembled from governed evidence; it is not an order, recommendation, forecast, target price or probability.",
        "watch_items": [
            "Next completed EOD price/technical session",
            "Whether trend and horizon-specific momentum persist",
        ]
        + (
            ["Scheduled corporate event outcome is unknown; monitor disclosure"]
            if event_risk
            else []
        ),
        "limitations": stock.get("limitations", [])
        + [
            "Theme context uses current membership; historical Theme membership is unavailable.",
            "No target price, position size, order draft or execution action is generated.",
        ],
        "provenance": {
            "technical": "existing technical_engine output",
            "stock": "stock-intelligence-1.1",
            "fno": "fno-intelligence-1.0",
            "sector": "sector-rotation-1.1",
            "theme": "theme-intelligence-1.0",
            "institutional": "stock-institutional-evidence-1.1",
            "legacy_isolation": {
                "bull_run_probability": False,
                "ml_scores_combined": False,
                "trade_conviction": False,
                "signal_recommender": False,
            },
        },
    }


def _cheap_prefilter(horizon: str) -> pd.DataFrame:
    frame = data_loader.get("technical")
    if frame is None or frame.empty:
        return pd.DataFrame()
    work = frame.copy()
    allowed = {"STRONG_UPTREND", "UPTREND", "DOWNTREND", "CONSOLIDATING"}
    work = work[work["trend_signal"].astype(str).str.upper().isin(allowed)]
    if horizon == "POSITIONAL":
        momentum = data_loader.get("price_momentum")
        if momentum is not None and not momentum.empty:
            cols = [
                item
                for item in ("symbol", "ret_60d", "ret_90d")
                if item in momentum.columns
            ]
            work = work.merge(momentum[cols], on="symbol", how="left")
            usable = pd.Series(False, index=work.index)
            for column in ("ret_60d", "ret_90d"):
                if column in work.columns:
                    usable |= pd.to_numeric(work[column], errors="coerce").notna()
            work = work[usable]
    return work.sort_values(["trend_signal", "symbol"], kind="mergesort")


def screen_trade_setups(
    *, horizon: str = "SWING", limit: int = 20, fno_only: bool = False
) -> dict[str, Any]:
    horizon = str(horizon or "SWING").strip().upper()
    if horizon not in HORIZONS:
        raise ValueError("horizon is SWING or POSITIONAL")
    limit = max(1, min(int(limit), SCREEN_LIMIT_MAX))
    prefiltered = _cheap_prefilter(horizon)
    if fno_only:
        loaded_fno = data_loader.get("fno_intel")
        eligible = (
            set(loaded_fno["symbol"].astype(str).str.upper())
            if loaded_fno is not None
            and not loaded_fno.empty
            and "symbol" in loaded_fno.columns
            else set()
        )
        prefiltered = prefiltered[
            prefiltered["symbol"].astype(str).str.upper().isin(eligible)
        ]
    candidate_count = min(len(prefiltered), max(limit * 3, 20))
    candidates = prefiltered.head(candidate_count)
    rows: list[dict[str, Any]] = []
    for symbol in candidates["symbol"].astype(str).str.upper():
        try:
            item = build_trade_setup_intelligence(
                symbol, horizon=horizon, include_themes=False
            )
        except (KeyError, OSError, ValueError, ImportError):
            continue
        rows.append(
            {
                "symbol": symbol,
                "horizon": horizon,
                "setup_state": item["setup_state"],
                "directional_bias": item["directional_bias"],
                "setup_phase": item["setup_phase"],
                "as_of": item.get("as_of"),
                "evidence_quality": item["evidence_quality"]["overall"],
                "key_confirmations": [
                    item["technical"]["trend"]["state"],
                    item["technical"]["momentum"]["state"],
                ],
                "key_conflicts": item["conflicts"][:3],
            }
        )
    rank = {
        "BULLISH_SETUP": 0,
        "BEARISH_SETUP": 1,
        "VALID_WITH_EVENT_RISK": 2,
        "WATCHLIST_SETUP": 3,
        "CONFLICTING_EVIDENCE": 4,
        "EXTENDED": 5,
        "RANGE_BOUND": 6,
        "INSUFFICIENT_EVIDENCE": 7,
        "NO_SETUP": 8,
    }
    rows.sort(key=lambda item: (rank.get(item["setup_state"], 9), item["symbol"]))
    state_counts = (
        pd.Series([item["setup_state"] for item in rows]).value_counts().to_dict()
        if rows
        else {}
    )
    technical = data_loader.get("technical")
    return {
        "contract_version": CONTRACT_VERSION,
        "horizon": horizon,
        "frequency": "EOD",
        "universe": {
            "technical_universe": len(technical) if technical is not None else 0,
            "prefilter_count": len(prefiltered),
            "deep_analysed": len(rows),
            "fno_only": fno_only,
        },
        "results": rows[:limit],
        "counts_by_state": {
            str(key): int(value) for key, value in state_counts.items()
        },
        "data_status": data_loader.freshness_for(
            ("technical",), ("price_momentum", "sector_rotation", "fno_intel")
        ),
        "limitations": [
            "Prefilter is deterministic and bounded; only the candidate set is deeply composed.",
            "Screen ranking is state/quality ordering, not a score or predictive ranking.",
            "No legacy bull-run, ML or conviction output is used.",
        ],
        "provenance": {
            "prefilter": "technical snapshot plus horizon-specific price history",
            "deep_composition": CONTRACT_VERSION,
        },
    }
