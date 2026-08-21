"""Bounded, deterministic stock-intelligence contract.

This module is an additive contract layer around the existing stock endpoint.
It deliberately consumes provider-owned datasets and does not train models,
call LLMs, or turn market context into stock-specific institutional claims.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.services import data_loader
from backend.services.fundamental_evidence import build_fundamental_evidence
from backend.services.stock_institutional_evidence import (
    build_stock_institutional_evidence,
)

try:
    from engines.common.config import STOCK_HISTORY_CACHE as _CACHE_DIR
except (ImportError, AttributeError):  # pragma: no cover - defensive fallback
    _CACHE_DIR = Path("data/NSE/nsecache/stock_history")


CONTRACT_VERSION = "stock-intelligence-1.1"
WINDOWS = (1, 3, 5, 10, 20)
INSTITUTIONAL_SCOPES = {
    "DIRECT_STOCK_INSTITUTIONAL_DATA",
    "DERIVED_OWNERSHIP_CONFIRMATION",
    "DEAL_ACTIVITY_CONTEXT",
    "MARKET_LEVEL_CONTEXT_ONLY",
    "NOT_SUPPORTED",
    "IDENTITY_REVIEW_REQUIRED",
}


def _value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _number(value: Any) -> float | None:
    value = _value(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if not math.isfinite(number) else number


def _round(value: Any, digits: int = 2) -> float | None:
    number = _number(value)
    return round(number, digits) if number is not None else None


def _frame_row(frame: pd.DataFrame | None, symbol: str) -> pd.Series | None:
    if frame is None or frame.empty or "symbol" not in frame.columns:
        return None
    rows = frame[frame["symbol"].astype(str).str.upper() == symbol]
    return rows.iloc[0] if not rows.empty else None


def _sector_row(frame: pd.DataFrame | None, sector: str) -> pd.Series | None:
    if frame is None or frame.empty or "sector" not in frame.columns:
        return None
    rows = frame[frame["sector"].astype(str).str.upper() == sector]
    return rows.iloc[0] if not rows.empty else None


@lru_cache(maxsize=4096)
def _load_identity(symbol: str) -> dict[str, Any]:
    path = Path("data/NSE/equity_master/equity_master.csv")
    fundamental_path = Path("data/NSE/equity_master/company_fundamentals_master.csv")
    result: dict[str, Any] = {"symbol": symbol, "identity_state": "NOT_SUPPORTED"}
    try:
        master = pd.read_csv(path, dtype=str)
        row = master[master["SYMBOL"].astype(str).str.upper() == symbol]
        if not row.empty:
            item = row.iloc[0]
            result.update(
                {
                    "symbol": symbol,
                    "company": _value(item.get("COMPANY_NAME")),
                    "series": _value(item.get("SERIES")),
                    "isin": _value(item.get("ISIN")),
                    "listing_date": _value(item.get("LISTING_DATE")),
                    "is_active": str(item.get("IS_ACTIVE", "")).lower() == "true",
                    "identity_source": "NSE_EQUITY_MASTER",
                    "identity_state": "IDENTIFIED",
                }
            )
        else:
            result["identity_state"] = "UNKNOWN_SYMBOL"
    except (OSError, ValueError, KeyError):
        result["identity_state"] = "IDENTITY_SOURCE_UNAVAILABLE"
    try:
        fundamentals = pd.read_csv(fundamental_path, dtype=str)
        row = fundamentals[fundamentals["symbol"].astype(str).str.upper() == symbol]
        if not row.empty:
            item = row.iloc[0]
            result.update(
                {
                    "company": _value(item.get("company_name")) or result.get("company"),
                    "isin": _value(item.get("isin")) or result.get("isin"),
                    "sector": _value(item.get("sector_platform")),
                    "industry": _value(item.get("industry_nse")),
                    "market_cap_category": _value(item.get("market_cap_category")),
                    "identity_source": "NSE_EQUITY_MASTER+FUNDAMENTALS_MASTER",
                    "fundamentals_master_as_of": _value(item.get("last_updated")),
                }
            )
    except (OSError, ValueError, KeyError):
        pass
    return result


def _price_history(symbol: str) -> pd.DataFrame:
    path = _CACHE_DIR / f"{symbol}.parquet"
    if not path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_parquet(path)
        if "date" not in frame.columns or "close" not in frame.columns:
            return pd.DataFrame()
        frame = frame.copy()
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        if "volume" in frame.columns:
            frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce")
        frame = frame.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date")
        return frame.reset_index(drop=True)
    except (OSError, ValueError, ImportError):
        return pd.DataFrame()


def _windows(history: pd.DataFrame) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if history.empty:
        return ({str(window): {"return_pct": None, "from_date": None, "to_date": None,
                               "observations": 0, "expected_observations": window + 1,
                               "state": "NOT_AVAILABLE"} for window in WINDOWS},
                {"state": "NOT_AVAILABLE", "observations": 0})
    current = history.iloc[-1]
    for window in WINDOWS:
        key = str(window)
        required = window + 1
        usable = history.tail(required)
        value = None
        if len(usable) == required and float(usable.iloc[0]["close"]) > 0:
            value = (float(current["close"]) / float(usable.iloc[0]["close"]) - 1) * 100
        result[key] = {
            "return_pct": _round(value),
            "from_date": usable.iloc[0]["date"].date().isoformat() if len(usable) == required else None,
            "to_date": current["date"].date().isoformat(),
            "observations": max(0, len(usable) - 1),
            "expected_observations": window,
            "state": "AVAILABLE" if value is not None else "INSUFFICIENT_HISTORY",
        }
    return result, {
        "state": "AVAILABLE" if result["20"]["return_pct"] is not None else "INSUFFICIENT_HISTORY",
        "observations": len(history),
        "as_of": current["date"].date().isoformat(),
    }


def _volume_context(history: pd.DataFrame) -> dict[str, Any]:
    if history.empty or "volume" not in history.columns or len(history) < 2:
        return {"state": "NOT_AVAILABLE", "relative_volume": None, "as_of": None}
    latest = _number(history.iloc[-1].get("volume"))
    prior = pd.to_numeric(history.iloc[:-1].tail(20)["volume"], errors="coerce").dropna()
    average = float(prior.mean()) if not prior.empty else None
    relative = latest / average if latest is not None and average and average > 0 else None
    latest_return = None
    if len(history) >= 2 and _number(history.iloc[-2].get("close")):
        latest_return = (float(history.iloc[-1]["close"]) / float(history.iloc[-2]["close"]) - 1) * 100
    if relative is None or latest_return is None:
        state = "INSUFFICIENT_DATA"
    elif relative >= 1.5 and latest_return >= 0:
        state = "CONFIRMING_UP_MOVE"
    elif relative >= 1.5 and latest_return < 0:
        state = "CONFIRMING_DOWN_MOVE"
    else:
        state = "NORMAL_VOLUME"
    return {
        "state": state,
        "latest_volume": _round(latest, 0),
        "prior_20d_average": _round(average, 0),
        "relative_volume": _round(relative),
        "latest_return_pct": _round(latest_return),
        "as_of": history.iloc[-1]["date"].date().isoformat(),
        "interpretation": "Price/volume behavior only; this is not institutional-flow confirmation.",
    }


def _state_from_price(trend: Any, windows: dict[str, dict[str, Any]]) -> str:
    trend = str(trend or "").upper()
    five = _number(windows.get("5", {}).get("return_pct"))
    twenty = _number(windows.get("20", {}).get("return_pct"))
    if five is None or twenty is None:
        return "INSUFFICIENT_DATA"
    if "UPTREND" in trend and five > 0 and twenty > 0:
        return "STRONG"
    if "DOWNTREND" in trend and five < 0 and twenty < 0:
        return "WEAK"
    return "MIXED"


def _institutional_context(symbol: str) -> dict[str, Any]:
    return build_stock_institutional_evidence(symbol, identity=_load_identity(symbol))


def build_stock_intelligence_contract(
    symbol: str,
    row: pd.Series,
    *,
    fundamentals: dict[str, Any],
    technical: dict[str, Any],
    shareholding: dict[str, Any],
    holding_trends: list[dict[str, Any]],
    deal_info: dict[str, Any],
    upcoming_events: list[dict[str, Any]],
    fundamental_evidence: dict[str, Any] | None = None,
    corporate_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the governed additive stock contract from existing datasets."""
    symbol = symbol.upper()
    identity = _load_identity(symbol)
    sector = str(row.get("sector") or identity.get("sector") or "UNKNOWN").upper()
    history = _price_history(symbol)
    price_windows, history_meta = _windows(history)
    volume = _volume_context(history)
    sector_row = _sector_row(data_loader.get("sector_rotation"), sector)
    price_momentum = _frame_row(data_loader.get("price_momentum"), symbol)
    watchlist = _frame_row(data_loader.get("watchlist_metrics"), symbol)
    sector_windows = {}
    sector_context: dict[str, Any] = {"sector": sector, "state": "NOT_AVAILABLE"}
    if sector_row is not None:
        sector_windows = {
            str(window): _round(sector_row.get(f"sector_return_{window}d"))
            for window in WINDOWS
        }
        sector_context = {
            "sector": sector,
            "contract_version": _value(sector_row.get("contract_version")),
            "as_of": _value(sector_row.get("last_date", sector_row.get("date"))),
            "leadership_state": _value(sector_row.get("leadership_state")),
            "persistence_state": _value(sector_row.get("persistence_state")),
            "rotation_state": _value(sector_row.get("rotation_state")),
            "relative_strength_rank_5d": _round(sector_row.get("relative_strength_rank_5d")),
            "relative_return_5d": _round(sector_row.get("relative_return_5d")),
            "relative_return_20d": _round(sector_row.get("relative_return_20d")),
            "breadth_5d_positive_pct": _round(sector_row.get("breadth_5d_positive_pct")),
            "breadth_5d_coverage_pct": _round(sector_row.get("breadth_5d_coverage_pct")),
            "benchmark": _value(sector_row.get("benchmark")),
            "evidence_quality": _value(sector_row.get("evidence_quality")),
            "state": "AVAILABLE",
        }
    benchmark_windows = {
        str(window): _round(sector_row.get(f"benchmark_return_{window}d"))
        if sector_row is not None else None
        for window in WINDOWS
    }
    stock_returns = {key: price_windows[key].get("return_pct") for key in price_windows}
    market_rs = {
        key: _round(stock_returns[key] - benchmark_windows[key])
        if stock_returns[key] is not None and benchmark_windows[key] is not None else None
        for key in price_windows
    }
    sector_rs = {
        key: _round(stock_returns[key] - sector_windows.get(key))
        if stock_returns[key] is not None and sector_windows.get(key) is not None else None
        for key in price_windows
    }
    trend_state = _state_from_price(technical.get("trend_signal"), price_windows)
    stock_state = trend_state
    sector_state = str(sector_context.get("leadership_state") or "INSUFFICIENT_DATA")
    if stock_state == "STRONG" and sector_state in {"STRONG", "IMPROVING", "LEADER"}:
        cross_layer = "STRONG_STOCK_STRONG_SECTOR"
    elif stock_state == "STRONG" and sector_state in {"WEAK", "WEAKENING", "LAGGARD"}:
        cross_layer = "STRONG_STOCK_WEAK_SECTOR"
    elif stock_state == "WEAK" and sector_state in {"STRONG", "IMPROVING", "LEADER"}:
        cross_layer = "WEAK_STOCK_STRONG_SECTOR"
    elif stock_state == "WEAK" and sector_state in {"WEAK", "WEAKENING", "LAGGARD"}:
        cross_layer = "WEAK_STOCK_WEAK_SECTOR"
    else:
        cross_layer = "MIXED_OR_INSUFFICIENT"
    institutional = build_stock_institutional_evidence(symbol, identity=identity)
    fundamental_fields = {key: value for key, value in fundamentals.items() if not key.startswith("_")}
    fundamental_evidence = fundamental_evidence or build_fundamental_evidence(
        symbol, fundamentals=fundamentals, sector=sector
    )
    fundamental_as_of = (
        fundamental_evidence.get("dates", {}).get("latest_period_end")
        or fundamental_fields.get("as_of_date")
        or identity.get("fundamentals_master_as_of")
    )
    if corporate_evidence is None:
        from backend.services.corporate_intelligence import build_corporate_intelligence

        corporate_evidence = build_corporate_intelligence(symbol, days=90, limit=10)
    corporate_status = corporate_evidence.get("data_status", {})
    corporate = {
        "contract_version": corporate_evidence.get("contract_version", "corporate-intelligence-1.0"),
        "announcement_state": corporate_status.get("state", "UNAVAILABLE"),
        "recent_events": corporate_evidence.get("recent_events", []),
        "scheduled_events": upcoming_events,
        "event_role": "Corporate events are descriptive context; they are not automatically catalysts.",
        "source_update": corporate_status.get("as_of"),
        "evidence_quality": corporate_evidence.get("evidence_quality", "INSUFFICIENT"),
        "next_watch_items": corporate_evidence.get("next_watch_items", []),
        "limitations": corporate_evidence.get("limitations", []),
        "results_context": corporate_evidence.get("results_context", {}),
        "retrieval_metadata": corporate_evidence.get("retrieval_metadata", {}),
        "lifecycle_coverage": corporate_evidence.get("lifecycle_coverage", {}),
    }
    dates = {
        "price": history_meta.get("as_of"),
        "technical": technical.get("as_of_date"),
        "sector": sector_context.get("as_of"),
        "benchmark": sector_row.get("benchmark_price_as_of") if sector_row is not None else None,
        "institutional": (institutional.get("as_of", {}).get("latest_deal_source_date")
                          or institutional.get("as_of", {}).get("latest_ownership_submission")
                          or institutional.get("as_of", {}).get("latest_ownership_quarter_end")),
        "fundamentals": fundamental_as_of,
        "corporate_source_update": corporate.get("source_update"),
    }
    aligned = [str(value)[:10] for value in dates.values() if value]
    if not aligned:
        alignment_state = "UNKNOWN"
    elif len(set(aligned)) == 1:
        alignment_state = "ALIGNED"
    else:
        alignment_state = "PARTIALLY_ALIGNED"
    available = sum(
        bool(item)
        for item in (identity.get("identity_state") == "IDENTIFIED", history_meta.get("state") == "AVAILABLE",
                     bool(technical), sector_context.get("state") == "AVAILABLE",
                     fundamental_evidence.get("coverage", {}).get("usable_fields", 0) > 0,
                     corporate.get("announcement_state") == "AVAILABLE")
    )
    evidence_quality = "HIGH" if available >= 6 and alignment_state == "ALIGNED" else "MEDIUM" if available >= 4 else "LIMITED" if available >= 2 else "INSUFFICIENT"
    limitations = [
        "This contract describes facts and bounded signals; it is not a recommendation, forecast, target price, or expected return.",
        "Missing data remains missing and is not converted to zero.",
    ]
    if alignment_state != "ALIGNED":
        limitations.append("Component dates are not fully aligned; interpret cross-layer comparisons conditionally.")
    if sector_context.get("state") != "AVAILABLE":
        limitations.append("Sector intelligence is unavailable for this symbol's mapped sector.")
    if institutional["scope"] in {"MARKET_LEVEL_CONTEXT_ONLY", "IDENTITY_REVIEW_REQUIRED"}:
        limitations.append("Broad FII/DII positioning is market context only and cannot be attributed to this stock.")
    next_watch = []
    if price_windows["20"]["state"] != "AVAILABLE":
        next_watch.append("20D price-history coverage")
    if alignment_state != "ALIGNED":
        next_watch.append("component-date alignment")
    if not fundamental_fields:
        next_watch.append("fundamental coverage")
    if fundamental_evidence.get("coverage", {}).get("quality") in {"LIMITED", "INSUFFICIENT"}:
        next_watch.append("field-level fundamental evidence coverage")
    limitations.extend(fundamental_evidence.get("limitations", []))
    if institutional["scope"] in {"MARKET_LEVEL_CONTEXT_ONLY", "NOT_SUPPORTED", "IDENTITY_REVIEW_REQUIRED"}:
        next_watch.append("stock-specific ownership/deal evidence")
    return {
        "contract_version": CONTRACT_VERSION,
        "identity": identity,
        "facts": {
            "price_windows": price_windows,
            "close": _round(row.get("close_now")) or _round(technical.get("close_now")),
            "history": history_meta,
            "volume": volume,
            "legacy_price_context": {
                "ret_30d": _round(price_momentum.get("ret_30d")) if price_momentum is not None else None,
                "ret_60d": _round(price_momentum.get("ret_60d")) if price_momentum is not None else None,
                "ret_90d": _round(price_momentum.get("ret_90d")) if price_momentum is not None else None,
                "as_of": _value(price_momentum.get("as_of_date")) if price_momentum is not None else None,
            },
            "watchlist_context": {
                "rvol": _round(watchlist.get("rvol")) if watchlist is not None else None,
                "delivery_5d_pct": _round(watchlist.get("delivery_5d_pct")) if watchlist is not None else None,
                "as_of": _value(watchlist.get("as_of")) if watchlist is not None else None,
            },
            "technical": {key: technical.get(key) for key in ("trend_signal", "vs_dma_20", "vs_dma_50", "vs_dma_200", "rsi", "macd_cross", "obv_signal", "as_of_date")},
            "fundamentals": fundamental_fields,
            "fundamental_evidence": fundamental_evidence,
            "corporate": corporate,
        },
        "signals": {
            "trend_state": trend_state,
            "momentum_windows": stock_returns,
            "market_relative_strength": market_rs,
            "sector_relative_strength": sector_rs,
            "sector_context": sector_context,
            "cross_layer_state": cross_layer,
            "institutional_context": institutional,
            "institutional_evidence": institutional,
            "technical_accumulation_distribution": {
                "state": str(technical.get("obv_signal") or "NOT_AVAILABLE"),
                "volume_confirmation": volume.get("state"),
                "scope": "TECHNICAL_PRICE_VOLUME_ONLY",
            },
        },
        "interpretation": f"{symbol} has a {trend_state.lower()} price/trend state and {cross_layer.lower().replace('_', ' ')} cross-layer context; this is descriptive, not predictive.",
        "evidence_quality": evidence_quality,
        "date_alignment": {"state": alignment_state, "components": dates},
        "limitations": limitations,
        "next_watch_items": next_watch,
    }
