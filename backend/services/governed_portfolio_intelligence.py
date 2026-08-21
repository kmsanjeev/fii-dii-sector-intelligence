"""Read-only governed Portfolio Intelligence contract.

The Phase-20 portfolio engine remains the owner of transactions and position
calculation.  This module only composes those factual positions with the
already governed Market contracts; it does not calculate a second stock,
sector, theme, fundamental, corporate, institutional, or risk engine.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import pandas as pd

from backend.services import data_loader
from backend.services import governed_theme_intelligence as theme_service
from backend.services.cross_layer_intelligence import build_cross_layer_intelligence
from engines.common import config as cfg
from engines.portfolio import portfolio_engine

CONTRACT_VERSION = "portfolio-intelligence-1.0"
CAPABILITY_VERSION = "0.1.0"

_RISK_FILES = {
    "var": cfg.INTELLIGENCE_DIR / "portfolio_risk.csv",
    "stress": cfg.INTELLIGENCE_DIR / "portfolio_stress.csv",
    "factor": cfg.INTELLIGENCE_DIR / "portfolio_factor_exposure.csv",
    "monte_carlo": cfg.INTELLIGENCE_DIR / "portfolio_mc_var.csv",
    "tca": cfg.INTELLIGENCE_DIR / "tca_summary.csv",
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


def _number(value: Any, digits: int = 2) -> float | None:
    value = _value(value)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return round(result, digits) if math.isfinite(result) else None


def _json_value(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.date().isoformat() if hasattr(value, "date") else value.isoformat()
    return value


def _latest_price(symbol: str) -> tuple[float | None, str | None]:
    path = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
    if not path.exists():
        return None, None
    try:
        frame = pd.read_parquet(path, columns=["date", "close"])
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame = frame.dropna(subset=["date", "close"]).sort_values("date")
        if frame.empty:
            return None, None
        row = frame.iloc[-1]
        return _number(row["close"]), row["date"].date().isoformat()
    except (OSError, ValueError, ImportError, KeyError):
        return None, None


def _data_status() -> dict[str, Any]:
    datasets = (
        "participant_intel",
        "sector_rotation",
        "technical",
        "valuation_scores",
        "announcements",
        "fno_intel",
    )
    status = data_loader.freshness_for(datasets, ())
    status.setdefault("limitations", [])
    status["limitations"] = list(status["limitations"]) + [
        "Portfolio data is local single-user data until a governed workspace persistence boundary exists.",
        "Missing prices and missing evidence remain missing; they are not converted to zero.",
    ]
    return status


def _risk_snapshot() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, path in _RISK_FILES.items():
        if not path.exists():
            result[name] = {"state": "NOT_AVAILABLE", "source": str(path)}
            continue
        try:
            frame = pd.read_csv(path)
            row = frame.iloc[-1].to_dict() if not frame.empty else {}
            result[name] = {
                "state": "AVAILABLE" if row else "NOT_AVAILABLE",
                "source": str(path),
                "as_of": _json_value(row.get("run_date", row.get("date"))),
                "values": {str(k): _json_value(v) for k, v in row.items()},
            }
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            result[name] = {"state": "ERROR", "source": str(path), "error": str(exc)}
    result["method"] = "Existing Phase-20/R1-R4 engines; no Portfolio risk recalculation in this contract."
    return result


def _legacy_audit() -> dict[str, Any]:
    return {
        "bull_run_probability.csv": "COMPATIBILITY_ONLY",
        "ml_bull_run_scores.csv": "LEGACY",
        "company_announcements.csv": "COMPATIBILITY_ONLY",
        "corporate_confidence_scores.csv": "LEGACY",
        "sector_rotation_intelligence.csv": "COMPATIBILITY_ONLY",
        "key_signal": "DEPRECATED_FOR_GOVERNED_PORTFOLIO",
        "trade_conviction_engine": "LEGACY_EXPERIMENTAL_NOT_AUTHORITATIVE",
        "buy_sell_labels": "NOT_AUTHORITATIVE",
        "governed_use": "Current Market contracts only; no predictive label is used as Portfolio evidence.",
    }


def _position(symbol: str, row: pd.Series) -> dict[str, Any]:
    price, price_as_of = _latest_price(symbol)
    qty = _number(row.get("qty"), 6) or 0.0
    avg_cost = _number(row.get("avg_cost"))
    invested = _number(row.get("invested"))
    market_value = _number(qty * price) if price is not None else None
    pnl = _number(market_value - invested) if market_value is not None and invested is not None else None
    pnl_pct = _number(pnl / invested * 100) if pnl is not None and invested else None
    return {
        "symbol": symbol,
        "isin": None,
        "quantity": qty,
        "average_cost": avg_cost,
        "invested_value": invested,
        "latest_price": price,
        "market_value": market_value,
        "unrealized_pnl": pnl,
        "unrealized_pnl_pct": pnl_pct,
        "first_acquired": _json_value(row.get("first_bought")),
        "last_transaction": _json_value(row.get("last_action_date")),
        "portfolio_weight": None,
        "source": "MANUAL_TRANSACTION_LEDGER",
        "price_as_of": price_as_of,
        "data_status": "AVAILABLE" if price is not None else "PRICE_NOT_AVAILABLE",
    }


def _sector_exposure(positions: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, dict[str, Any]] = {}
    total = sum(item["market_value"] or item["invested_value"] or 0 for item in positions)
    for item in positions:
        sector = str(item.get("sector") or "UNKNOWN")
        bucket = totals.setdefault(sector, {"sector": sector, "market_value": 0.0, "position_count": 0})
        bucket["market_value"] += item.get("market_value") or item.get("invested_value") or 0
        bucket["position_count"] += 1
    rows = []
    for bucket in totals.values():
        bucket["market_value"] = round(bucket["market_value"], 2)
        bucket["weight_pct"] = round(bucket["market_value"] / total * 100, 2) if total else None
        rows.append(bucket)
    rows.sort(key=lambda row: (-row["market_value"], row["sector"]))
    return {"items": rows, "largest_sector": rows[0]["sector"] if rows else None, "state": "AVAILABLE" if rows else "NOT_AVAILABLE"}


def _theme_exposure(positions: list[dict[str, Any]]) -> dict[str, Any]:
    themes: dict[str, dict[str, Any]] = {}
    overlaps: dict[str, list[str]] = {}
    for item in positions:
        try:
            memberships = theme_service.memberships_for(symbol=item["symbol"])
        except (OSError, ValueError, KeyError, TypeError, ImportError):
            memberships = []
            item.setdefault("data_warnings", []).append("THEME_PROVIDER_UNAVAILABLE")
        item["theme_memberships"] = memberships
        theme_ids = [str(member.get("theme_id")) for member in memberships if member.get("theme_id")]
        if len(theme_ids) > 1:
            overlaps[item["symbol"]] = sorted(theme_ids)
        for theme_id in theme_ids:
            bucket = themes.setdefault(theme_id, {"theme_id": theme_id, "member_symbols": [], "gross_market_value": 0.0})
            if item["symbol"] not in bucket["member_symbols"]:
                bucket["member_symbols"].append(item["symbol"])
            bucket["gross_market_value"] += item.get("market_value") or item.get("invested_value") or 0
    total = sum(item.get("market_value") or item.get("invested_value") or 0 for item in positions)
    for bucket in themes.values():
        bucket["gross_market_value"] = round(bucket["gross_market_value"], 2)
        bucket["gross_membership_weight_pct"] = round(bucket["gross_market_value"] / total * 100, 2) if total else None
        bucket["overlap_warning"] = "A position may contribute to multiple themes; gross membership weights are not independent capital allocations."
    return {
        "items": sorted(themes.values(), key=lambda row: row["theme_id"]),
        "overlapping_positions": overlaps,
        "state": "AVAILABLE" if themes else "NOT_AVAILABLE",
        "historical_membership": "DEFERRED_NON_BLOCKING",
    }


def build_governed_portfolio_intelligence() -> dict[str, Any]:
    """Return the read-only Portfolio Intelligence 1.0 contract."""
    transactions = portfolio_engine.load_transactions()
    factual = portfolio_engine.compute_positions(transactions)
    positions = [_position(str(row["symbol"]).upper(), row) for _, row in factual.iterrows()]
    total_value = sum(item.get("market_value") or item.get("invested_value") or 0 for item in positions)
    for item in positions:
        value = item.get("market_value") or item.get("invested_value")
        item["portfolio_weight"] = _number(value / total_value * 100) if total_value else None

    market_context: dict[str, Any]
    try:
        overview = build_cross_layer_intelligence(mode="MARKET_OVERVIEW", top_sectors=5, stocks_per_sector=1)
        market_context = overview.get("market", {})
        institutional_context = overview.get("institutional", {})
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        overview = {}
        market_context = {"state": "UNAVAILABLE", "error": str(exc)}
        institutional_context = {"state": "UNAVAILABLE", "error": str(exc)}

    for item in positions:
        try:
            evidence = build_cross_layer_intelligence(mode="SYMBOL_ANALYSIS", symbol=item["symbol"], stocks_per_sector=1)
            confirmation = evidence.get("stock_confirmation") or {}
            item["sector"] = confirmation.get("sector") or "UNKNOWN"
            item["position_intelligence"] = {
                "stock": evidence.get("stock_confirmation"),
                "sector": evidence.get("sectors", {}),
                "fundamental": evidence.get("stock_confirmation", {}).get("fundamental_evidence"),
                "corporate": evidence.get("stock_confirmation", {}).get("corporate_event_context"),
                "cross_layer": {
                    "alignment": evidence.get("alignment"),
                    "conflicts": evidence.get("conflicts", []),
                    "date_alignment": evidence.get("date_alignment"),
                },
                "data_status": evidence.get("data_status"),
            }
        except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
            item["sector"] = "UNKNOWN"
            item["position_intelligence"] = {"state": "UNAVAILABLE", "error": str(exc)}

    allocation = {
        "sector": _sector_exposure(positions),
        "theme": _theme_exposure(positions),
        "concentration": {
            "largest_position": max(positions, key=lambda item: item.get("market_value") or item.get("invested_value") or 0)["symbol"] if positions else None,
            "top_5": [item["symbol"] for item in sorted(positions, key=lambda item: -(item.get("market_value") or item.get("invested_value") or 0))[:5]],
        },
    }
    current_value = _number(total_value)
    invested = _number(sum(item.get("invested_value") or 0 for item in positions))
    pnl = _number(current_value - invested) if current_value is not None and invested is not None else None
    return {
        "contract_version": CONTRACT_VERSION,
        "provider_capability_version": CAPABILITY_VERSION,
        "portfolio_scope": "LOCAL_SINGLE_USER",
        "authorization_state": "WORKSPACE_BOUNDARY_REQUIRED_FOR_FORMAL_MULTI_USER_EXPOSURE",
        "as_of": max(
            (str(item.get("price_as_of")) for item in positions if item.get("price_as_of")),
            default=None,
        ),
        "source_summary": {
            "transactions": "MANUAL_TRANSACTION_LEDGER",
            "market_evidence": "FII-DII_GOVERNED_MARKET_CONTRACTS",
            "risk": "EXISTING_PHASE_20_R1_R4_OUTPUTS",
        },
        "valuation": {"invested": invested, "market_value": current_value, "pnl": pnl, "cash": None},
        "positions": positions,
        "allocation": allocation,
        "risk": _risk_snapshot(),
        "market_context": market_context,
        "institutional_context": institutional_context,
        "review_items": {
            "missing_data": [item["symbol"] for item in positions if item["data_status"] != "AVAILABLE"],
            "theme_overlap": sorted(allocation["theme"]["overlapping_positions"]),
            "stale_evidence": [],
            "conflicting_evidence": [
                item["symbol"] for item in positions
                if item.get("position_intelligence", {}).get("cross_layer", {}).get("conflicts")
            ],
        },
        "evidence_quality": {"type": "EVIDENCE_QUALITY_NOT_PREDICTIVE_CONFIDENCE", "state": "MIXED" if positions else "INSUFFICIENT_EVIDENCE"},
        "freshness": _data_status(),
        "limitations": [
            "This is descriptive read-only Portfolio Intelligence, not a recommendation, prediction, or execution instruction.",
            "Theme membership is current-universe only; historical membership is deferred and survivorship limitations remain.",
            "Cash, broker state and workspace persistence are unavailable unless separately connected and authorized.",
        ],
        "provenance": {
            "position_engine": "engines.portfolio.portfolio_engine",
            "market_contract": "cross-layer-1.0 and component governed contracts",
            "theme_contract": "theme-intelligence-1.0",
            "risk_engines": "R1_portfolio_risk/R2a_stress_test/R2b_factor_model/R3_monte_carlo/R4_tca",
        },
        "legacy_audit": _legacy_audit(),
        "data_status": _data_status(),
    }
