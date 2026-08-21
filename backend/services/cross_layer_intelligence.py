"""Deterministic Market -> Institutional -> Sector -> Stock composition.

This module composes the already governed provider contracts.  It does not
recalculate market, participant, sector, stock, fundamental, or corporate
signals and it never turns market-level participant data into stock/sector
institutional attribution.
"""

from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from backend.services import data_loader
from backend.services.stock_intelligence import build_stock_intelligence_contract
from engines.participant.institutional_contract import build_institutional_contract

CONTRACT_VERSION = "cross-layer-1.0"
CAPABILITY_VERSION = "0.1.0"
MODES = {
    "MARKET_OVERVIEW",
    "LEADERSHIP_DISCOVERY",
    "SECTOR_CONFIRMATION",
    "STOCK_CONFIRMATION",
    "SYMBOL_ANALYSIS",
}
FRESHNESS_ORDER = {"LIVE": 0, "EOD": 1, "DELAYED": 2, "STALE": 3, "QUALITY_WARNING": 4, "UNKNOWN": 4, "UNAVAILABLE": 5}
QUALITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "CONDITIONAL": 2, "LIMITED": 3, "INSUFFICIENT": 4, "UNAVAILABLE": 5}


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


def _number(value: Any, digits: int = 2) -> float | None:
    value = _value(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, digits) if math.isfinite(number) else None


def _row(frame: pd.DataFrame | None, symbol: str, column: str = "symbol") -> pd.Series | None:
    if frame is None or frame.empty or column not in frame.columns:
        return None
    rows = frame[frame[column].astype(str).str.upper() == symbol.upper()]
    return rows.iloc[0] if not rows.empty else None


def _record(row: pd.Series | None) -> dict[str, Any]:
    if row is None:
        return {}
    return {str(key): _value(value) for key, value in row.to_dict().items()}


def _json_value(value: Any, default: Any) -> Any:
    value = _value(value)
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError):
        return default
    return parsed


def _status(keys: tuple[str, ...], optional: tuple[str, ...] = ()) -> dict[str, Any]:
    return data_loader.freshness_for(keys, optional)


def _weakest(states: list[str], order: dict[str, int]) -> str:
    values = [state for state in states if state]
    return max(values, key=lambda state: order.get(state, max(order.values()))) if values else "UNAVAILABLE"


def _quality(value: Any) -> str:
    text = str(value or "UNAVAILABLE").upper()
    return text if text in QUALITY_ORDER else "UNAVAILABLE"


def _market_snapshot() -> tuple[dict[str, Any], dict[str, Any]]:
    intelligence = data_loader.get("participant_intel")
    latest = intelligence.sort_values("date").iloc[-1] if intelligence is not None and not intelligence.empty else None
    context = data_loader.get_market_context()
    bull = data_loader.get("bull_run")
    breadth: dict[str, int] = {}
    if bull is not None and not bull.empty and "label" in bull.columns:
        values = bull["label"].value_counts().to_dict()
        breadth = {str(key): int(value) for key, value in values.items()}
    regime = str(latest.get("Market_Regime", "UNKNOWN")) if latest is not None else "UNKNOWN"
    state = (
        "SUPPORTIVE" if regime.upper() in {"BULLISH", "RISK_ON", "ACCUMULATION", "POSITIVE"}
        else "CAUTIOUS" if regime.upper() in {"BEARISH", "RISK_OFF", "DISTRIBUTION", "NEGATIVE"}
        else "MIXED" if latest is not None else "INSUFFICIENT"
    )
    status = _status(("participant_intel",), ("participant_flows", "bull_run"))
    return {
        "state": state,
        "regime": regime,
        "trend": context.get("regime", regime),
        "risk_state": context.get("pcr_signal"),
        "breadth": breadth,
        "as_of": str(latest.get("date")) if latest is not None else None,
        "freshness": status,
        "evidence_quality": "MEDIUM" if latest is not None else "UNAVAILABLE",
        "limitations": [
            "Market state is provider-owned context; it is not a price forecast.",
            "Market breadth uses the current available universe where the upstream contract specifies it.",
        ],
    }, status


def _institutional_snapshot() -> tuple[dict[str, Any], dict[str, Any]]:
    flows = data_loader.get("participant_flows")
    intelligence = data_loader.get("participant_intel")
    status = _status(("participant_flows", "participant_intel"))
    contract = build_institutional_contract(flows, intelligence, status)
    derived = contract.get("derived_signals", {})
    market_regime = str(derived.get("market_regime") or "").upper()
    latest = intelligence.sort_values("date").iloc[-1] if intelligence is not None and not intelligence.empty else None
    fii = _number(latest.get("FII_flow_score")) if latest is not None else None
    dii = _number(latest.get("DII_flow_score")) if latest is not None else None
    if not market_regime and fii is None and dii is None:
        state = "INSUFFICIENT"
    elif market_regime in {"BULLISH", "RISK_ON", "ACCUMULATION", "POSITIVE"}:
        state = "SUPPORTIVE"
    elif market_regime in {"BEARISH", "RISK_OFF", "DISTRIBUTION", "NEGATIVE"}:
        state = "CAUTIOUS"
    elif fii is not None and dii is not None and fii * dii > 0:
        state = "SUPPORTIVE" if fii > 0 else "CAUTIOUS"
    else:
        state = "MIXED"
    date_alignment = contract.get("derivatives", {}).get("date_alignment", {})
    return {
        "state": state,
        "scope": "MARKET_LEVEL_CONTEXT_ONLY",
        "cash": contract.get("cash_participants", {}),
        "derivatives": contract.get("participants", {}),
        "cash_as_of": date_alignment.get("cash_as_of"),
        "fno_as_of": date_alignment.get("fno_as_of"),
        "date_alignment": date_alignment,
        "freshness": status,
        "evidence_quality": _quality(contract.get("evidence_quality", {}).get("state")),
        "contract_version": contract.get("contract_version", "institutional-flow-1.1"),
        "limitations": [
            "Institutional positioning is market-level context only; it is not sector- or stock-specific flow attribution.",
            "Cash and aggregate futures units are preserved separately and are not normalized into one score.",
        ],
    }, status


def _sector_snapshot() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame = data_loader.get("sector_rotation")
    status = _status(("sector_rotation",))
    if frame is None or frame.empty:
        return [], status
    result: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        result.append({
            "sector": str(row.get("sector", "")),
            "contract_version": str(row.get("contract_version", "sector-rotation-1.1")),
            "as_of": _value(row.get("last_date", row.get("date"))),
            "leadership": str(row.get("leadership_state", "INSUFFICIENT_HISTORY")),
            "rotation": str(row.get("rotation_state", "UNAVAILABLE")),
            "persistence": str(row.get("persistence_state", "UNAVAILABLE")),
            "acceleration": str(row.get("acceleration_state", "UNAVAILABLE")),
            "relative_strength_rank_5d": _number(row.get("relative_strength_rank_5d")),
            "relative_return_5d": _number(row.get("relative_return_5d")),
            "relative_return_20d": _number(row.get("relative_return_20d")),
            "breadth": {
                "positive_pct": _number(row.get("breadth_5d_positive_pct")),
                "coverage_pct": _number(row.get("breadth_5d_coverage_pct")),
                "expected": _number(row.get("breadth_5d_expected"), 0),
                "usable": _number(row.get("breadth_5d_usable"), 0),
            },
            "evidence_quality": _quality(row.get("evidence_quality")),
            "leaders": _json_value(row.get("leaders_json"), []),
            "laggards": _json_value(row.get("laggards_json"), []),
            "limitations": [
                "Breadth uses the upstream current constituent universe and retains its survivorship limitation.",
                "Institutional context in the sector source is market-level only.",
            ],
        })
    result.sort(key=lambda item: (item["relative_strength_rank_5d"] is None, item["relative_strength_rank_5d"] or 999, item["sector"]))
    return result, status


def _stock_inputs(symbol: str) -> tuple[pd.Series, dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    technical_row = _row(data_loader.get("technical"), symbol)
    momentum_row = _row(data_loader.get("price_momentum"), symbol)
    valuation_row = _row(data_loader.get("valuation_scores"), symbol)
    extended_row = _row(data_loader.get("extended_financials"), symbol)
    source = technical_row if technical_row is not None else momentum_row if momentum_row is not None else valuation_row
    if source is None:
        raise ValueError(f"unknown or unsupported symbol: {symbol}")
    sector_source = valuation_row if valuation_row is not None else momentum_row if momentum_row is not None else source
    sector = _value(sector_source.get("sector")) or "UNKNOWN"
    row = pd.Series({"symbol": symbol, "sector": sector, "close_now": source.get("close_now")})
    technical = _record(technical_row)
    fundamentals = {**_record(valuation_row), **_record(extended_row)}
    events = data_loader.get("event_calendar")
    event_rows = events[events["symbol"].astype(str).str.upper() == symbol.upper()].tail(3) if events is not None and not events.empty and "symbol" in events.columns else pd.DataFrame()
    upcoming = [_record(item) for _, item in event_rows.iterrows()]
    return row, technical, fundamentals, upcoming


def _stock_contract(symbol: str) -> dict[str, Any]:
    row, technical, fundamentals, upcoming = _stock_inputs(symbol)
    return build_stock_intelligence_contract(
        symbol,
        row,
        fundamentals=fundamentals,
        technical=technical,
        shareholding={},
        holding_trends=[],
        deal_info={},
        upcoming_events=upcoming,
    )


def _stock_summary(symbol: str, contract: dict[str, Any], sector: dict[str, Any]) -> dict[str, Any]:
    signals = contract.get("signals", {})
    trend = str(signals.get("trend_state", "INSUFFICIENT_DATA"))
    leadership = str(sector.get("leadership", "INSUFFICIENT_DATA"))
    strong_stock = trend == "STRONG"
    strong_sector = leadership in {"LEADING", "IMPROVING"}
    weak_stock = trend == "WEAK"
    weak_sector = leadership in {"WEAKENING", "LAGGING"}
    alignment = (
        "STOCK_SECTOR_ALIGNED" if strong_stock and strong_sector
        else "STOCK_OUTPERFORMS_WEAK_SECTOR" if strong_stock and weak_sector
        else "STOCK_LAGS_LEADING_SECTOR" if weak_stock and strong_sector
        else "STOCK_SECTOR_WEAK" if weak_stock and weak_sector
        else "PARTIAL_OR_INSUFFICIENT"
    )
    facts = contract.get("facts", {})
    return {
        "symbol": symbol,
        "sector": sector.get("sector", "UNKNOWN"),
        "alignment": alignment,
        "trend": trend,
        "momentum": signals.get("momentum_windows", {}),
        "market_relative_strength": signals.get("market_relative_strength", {}),
        "sector_relative_strength": signals.get("sector_relative_strength", {}),
        "volume": facts.get("volume", {}),
        "sector_context": {
            "leadership": leadership,
            "breadth": sector.get("breadth", {}),
            "persistence": sector.get("persistence"),
            "evidence_quality": sector.get("evidence_quality"),
        },
        "institutional_scope": contract.get("signals", {}).get("institutional_context", {}).get("scope"),
        "institutional_evidence": contract.get("signals", {}).get("institutional_evidence", {}),
        "evidence_quality": _quality(contract.get("evidence_quality")),
        "date_alignment": contract.get("date_alignment", {}),
        "reason": f"{symbol} is {alignment.lower().replace('_', ' ')} based on existing stock trend, relative-strength, sector leadership and breadth outputs.",
    }


def _candidate_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    alignment_rank = {
        "STOCK_SECTOR_ALIGNED": 0,
        "STOCK_OUTPERFORMS_WEAK_SECTOR": 1,
        "PARTIAL_OR_INSUFFICIENT": 2,
        "STOCK_LAGS_LEADING_SECTOR": 3,
        "STOCK_SECTOR_WEAK": 4,
    }
    return (alignment_rank.get(item.get("alignment"), 9), -(_number(item.get("sector_relative_strength", {}).get("5")) or -999), item.get("symbol", ""))


def _sector_groups(sectors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"leaders": [], "improving": [], "weakening": [], "laggards": []}
    for sector in sectors:
        state = sector.get("leadership")
        if state == "LEADING":
            groups["leaders"].append(sector)
        elif state == "IMPROVING":
            groups["improving"].append(sector)
        elif state == "WEAKENING":
            groups["weakening"].append(sector)
        elif state == "LAGGING":
            groups["laggards"].append(sector)
    return groups


def _build_candidates(sectors: list[dict[str, Any]], institutional: dict[str, Any], top_sectors: int, stocks_per_sector: int, sector_filter: str | None = None) -> list[dict[str, Any]]:
    selected = [item for item in sectors if not sector_filter or item["sector"].upper() == sector_filter.upper()]
    selected = selected[:top_sectors]
    candidates: list[dict[str, Any]] = []
    for sector in selected:
        symbols = []
        for source_key in ("leaders", "laggards"):
            values = sector.get(source_key) or []
            if isinstance(values, str):
                try:
                    values = json.loads(values)
                except (TypeError, ValueError):
                    values = []
            for value in values:
                symbol = value.get("symbol") if isinstance(value, dict) else value
                if symbol and str(symbol).upper() not in symbols:
                    symbols.append(str(symbol).upper())
        stock_items = []
        for symbol in symbols[:stocks_per_sector]:
            try:
                stock_items.append(_stock_summary(symbol, _stock_contract(symbol), sector))
            except (OSError, ValueError, KeyError, ImportError):
                continue
        stock_items.sort(key=_candidate_sort_key)
        candidates.append({
            "sector": sector["sector"],
            "sector_leadership": sector["leadership"],
            "sector_breadth": sector["breadth"],
            "sector_persistence": sector["persistence"],
            "stocks": stock_items,
            "institutional_market_context": institutional["state"],
            "selection_method": "upstream sector leaders/laggards, bounded stock contract confirmation, deterministic alignment ordering",
        })
    return candidates


def _alignment(market: dict[str, Any], institutional: dict[str, Any], candidates: list[dict[str, Any]], sector: dict[str, Any] | None = None, stock: dict[str, Any] | None = None) -> dict[str, Any]:
    components = {
        "market": "SUPPORTIVE" if market.get("state") == "SUPPORTIVE" else "CAUTIOUS" if market.get("state") == "CAUTIOUS" else "MIXED",
        "institutional": institutional.get("state", "INSUFFICIENT"),
    }
    if sector is not None:
        components["sector"] = "LEADING" if sector.get("leadership") in {"LEADING", "IMPROVING"} else str(sector.get("leadership", "INSUFFICIENT"))
    if stock is not None:
        components["stock"] = stock.get("alignment", "PARTIAL_OR_INSUFFICIENT")
    if "stock" in components and components["stock"] in {"STOCK_LAGS_LEADING_SECTOR", "STOCK_SECTOR_WEAK"}:
        state = "CONFLICTING"
    elif institutional.get("state") in {"MIXED", "CAUTIOUS"} and (sector or candidates):
        state = "PARTIAL_CONFIRMATION"
    elif any(item.get("stocks") for item in candidates) or stock is not None:
        state = "ALIGNED" if institutional.get("state") == "SUPPORTIVE" else "PARTIAL_CONFIRMATION"
    else:
        state = "INSUFFICIENT_EVIDENCE"
    return {"state": state, "components": components, "reason": "Agreement and disagreement remain visible as component states; no opaque aggregate score is used."}


def _conflicts(market: dict[str, Any], institutional: dict[str, Any], sectors: list[dict[str, Any]], candidates: list[dict[str, Any]], date_alignment: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if market.get("state") in {"SUPPORTIVE", "CAUTIOUS"} and institutional.get("state") in {"SUPPORTIVE", "CAUTIOUS"} and market.get("state") != institutional.get("state"):
        result.append({"severity": "MATERIAL", "components": ["market", "institutional"], "reason": "Market regime and institutional context disagree."})
    if date_alignment not in {"ALIGNED", "NOT_COMPARABLE"}:
        result.append({"severity": "MINOR", "components": ["dates"], "reason": f"Cross-layer sources have {date_alignment.lower().replace('_', ' ')} observation dates/frequencies."})
    for group in candidates:
        for stock in group.get("stocks", []):
            if stock.get("alignment") in {"STOCK_LAGS_LEADING_SECTOR", "STOCK_OUTPERFORMS_WEAK_SECTOR"}:
                result.append({"severity": "MATERIAL", "components": ["sector", "stock"], "sector": group["sector"], "symbol": stock["symbol"], "reason": stock["reason"]})
            if stock.get("trend") == "STRONG" and stock.get("volume", {}).get("state") in {"NORMAL_VOLUME", "INSUFFICIENT_DATA"}:
                result.append({"severity": "MINOR", "components": ["stock", "volume"], "sector": group["sector"], "symbol": stock["symbol"], "reason": "Stock trend strength lacks strong volume confirmation."})
    return result[:20]


def build_cross_layer_intelligence(
    *,
    mode: str = "MARKET_OVERVIEW",
    symbol: str | None = None,
    sector: str | None = None,
    top_sectors: int = 5,
    stocks_per_sector: int = 3,
) -> dict[str, Any]:
    """Build one bounded cross-layer result from existing local contracts."""
    mode = mode.upper()
    if mode not in MODES:
        raise ValueError(f"unsupported cross-layer mode: {mode}")
    top_sectors = max(1, min(int(top_sectors), 10))
    stocks_per_sector = max(1, min(int(stocks_per_sector), 5))
    market, market_status = _market_snapshot()
    institutional, institutional_status = _institutional_snapshot()
    sectors, sector_status = _sector_snapshot()
    groups = _sector_groups(sectors)
    stock_summary = None
    stock_contract: dict[str, Any] | None = None
    selected_sectors = [item for item in sectors if not sector or item["sector"].upper() == sector.upper()]
    selected_sectors = selected_sectors[:top_sectors]
    selected_sector = selected_sectors[0] if selected_sectors else None
    if symbol:
        stock_contract = _stock_contract(symbol.upper())
        sector_name = str(stock_contract.get("identity", {}).get("sector") or sector or "UNKNOWN")
        selected_sector = next((item for item in sectors if item["sector"].upper() == sector_name.upper()), selected_sector)
        if selected_sector is None:
            selected_sector = {"sector": sector_name, "leadership": "INSUFFICIENT_DATA", "breadth": {}, "persistence": "UNAVAILABLE", "evidence_quality": "UNAVAILABLE"}
        stock_summary = _stock_summary(symbol.upper(), stock_contract, selected_sector)
    candidates = (
        []
        if mode in {"SYMBOL_ANALYSIS", "STOCK_CONFIRMATION"}
        else _build_candidates(selected_sectors, institutional, top_sectors, stocks_per_sector, sector)
    )
    dates = {
        "market": market.get("as_of"),
        "institutional_cash": institutional.get("cash_as_of"),
        "institutional_fno": institutional.get("fno_as_of"),
        "sector": selected_sector.get("as_of") if selected_sector else (sectors[0].get("as_of") if sectors else None),
        "stock": stock_summary.get("date_alignment", {}).get("components", {}).get("price") if stock_summary else None,
        "fundamental": stock_summary.get("date_alignment", {}).get("components", {}).get("fundamentals") if stock_summary else None,
        "corporate": stock_summary.get("date_alignment", {}).get("components", {}).get("corporate_source_update") if stock_summary else None,
    }
    normalized_dates = [str(value)[:10] for value in dates.values() if value]
    if not normalized_dates:
        date_alignment = "NOT_COMPARABLE"
    elif len(set(normalized_dates)) == 1:
        date_alignment = "ALIGNED"
    elif dates.get("fundamental") and any(str(dates.get(key) or "")[:10] != str(dates["fundamental"])[:10] for key in ("market", "sector", "stock") if dates.get(key)):
        date_alignment = "MIXED_FREQUENCY"
    else:
        date_alignment = "PARTIALLY_ALIGNED"
    freshness_components = {
        "market": market_status.get("state", "UNAVAILABLE"),
        "institutional": institutional_status.get("state", "UNAVAILABLE"),
        "sector": sector_status.get("state", "UNAVAILABLE"),
        "stock": _status(("technical",), ()).get("state", "UNAVAILABLE") if symbol else "NOT_REQUESTED",
        "fundamental": _status(("valuation_scores",), ()).get("state", "UNAVAILABLE") if symbol else "NOT_REQUESTED",
        "corporate": _status(("announcements",), ()).get("state", "UNAVAILABLE") if symbol else "NOT_REQUESTED",
    }
    material_freshness = [value for value in freshness_components.values() if value != "NOT_REQUESTED"]
    quality_components = [market.get("evidence_quality", "UNAVAILABLE"), institutional.get("evidence_quality", "UNAVAILABLE")]
    if market.get("state") == "INSUFFICIENT" or institutional.get("state") == "INSUFFICIENT":
        quality_components.append("UNAVAILABLE")
    quality_components.extend(item.get("evidence_quality", "UNAVAILABLE") for item in selected_sectors)
    if not selected_sectors:
        quality_components.append("UNAVAILABLE")
    if stock_summary:
        quality_components.append(stock_summary.get("evidence_quality", "UNAVAILABLE"))
    overall_quality = _weakest([_quality(item) for item in quality_components], QUALITY_ORDER)
    overall_freshness = _weakest(material_freshness, FRESHNESS_ORDER)
    alignment = _alignment(market, institutional, candidates, selected_sector, stock_summary)
    conflicts = _conflicts(market, institutional, sectors, candidates, date_alignment)
    if stock_summary and stock_summary.get("alignment") in {"STOCK_LAGS_LEADING_SECTOR", "STOCK_OUTPERFORMS_WEAK_SECTOR"}:
        conflicts.append({
            "severity": "MATERIAL",
            "components": ["sector", "stock"],
            "sector": stock_summary.get("sector"),
            "symbol": stock_summary.get("symbol"),
            "reason": stock_summary.get("reason"),
        })
    result = {
        "contract_version": CONTRACT_VERSION,
        "provider_capability_version": CAPABILITY_VERSION,
        "data_status": _status(
            ("participant_intel", "participant_flows", "sector_rotation"),
            ("technical", "valuation_scores", "announcements"),
        ),
        "query": {"mode": mode, "symbol": symbol.upper() if symbol else None, "sector": sector.upper() if sector else None, "top_sectors": top_sectors, "stocks_per_sector": stocks_per_sector},
        "component_dates": dates,
        "date_alignment": {"state": date_alignment, "rule": "Different source dates and frequencies remain explicit; slower fundamentals are structural context, not same-session confirmation."},
        "freshness": {"components": freshness_components, "overall": overall_freshness, "rule": "Overall freshness is the weakest material component; requested-only stock components are excluded from overview freshness."},
        "evidence_quality": {"components": {"market": market.get("evidence_quality"), "institutional": institutional.get("evidence_quality"), "sector": [_quality(item.get("evidence_quality")) for item in selected_sectors], "stock": stock_summary.get("evidence_quality") if stock_summary else "NOT_REQUESTED"}, "overall": overall_quality, "type": "EVIDENCE_QUALITY_NOT_PREDICTIVE_CONFIDENCE"},
        "market": market,
        "institutional": institutional,
        "sectors": {"leaders": groups["leaders"][:top_sectors], "improving": groups["improving"][:top_sectors], "weakening": groups["weakening"][:top_sectors], "laggards": groups["laggards"][:top_sectors], "evaluated": len(sectors), "contract_version": "sector-rotation-1.1"},
        "candidates": candidates,
        "stock_confirmation": stock_summary,
        "alignment": alignment,
        "conflicts": conflicts,
        "limitations": [
            "This is descriptive cross-layer intelligence, not a prediction, recommendation, target price, or portfolio instruction.",
            "Market-level institutional context is not attributed to sectors or stocks.",
            "Fundamentals and corporate observations retain their own frequency and freshness.",
        ],
        "what_to_watch": [
            "Whether sector breadth and persistence remain supportive on the next observation.",
            "Whether institutional market context converges with or diverges from Market and sector leadership.",
            "Whether stock/sector relative strength persists with volume confirmation.",
        ],
        "interpretation": "Market leadership is described through component evidence and explicit conflicts; 'smart money' means institutional/professional participant context plus observable Market leadership, not a claim that a named institution bought a sector or stock.",
        "provenance": {"market": "market context and participant contracts", "institutional": "institutional-flow-1.1", "sector": "sector-rotation-1.1", "stock": "stock-intelligence-1.1"},
    }
    return result
