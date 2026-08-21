"""Governed provider-local Theme Intelligence contract.

This service deliberately sits beside the legacy Phase-E theme scorer.  It
owns no forecasts and no institutional theme attribution.  Membership is
derived from the governed classification/tagging artefacts; performance is an
equal-weight proxy over usable current members and the existing market
benchmark.  Missing prices remain missing and are excluded from denominators.
"""

from __future__ import annotations

import json
import math
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pandas as pd

from backend.services import data_loader
from engines.common import config as cfg

CONTRACT_VERSION = "theme-intelligence-1.0"
REGISTRY_PATH = cfg.REFERENCE_DIR / "veda_theme_registry.json"
CLASSIFICATION_PATH = cfg.REFERENCE_DIR / "company_classification_v4.csv"
TAGGING_PATH = cfg.REFERENCE_DIR / "theme_tagging.csv"
FUNDAMENTALS_PATH = cfg.EQUITY_MASTER_DIR / "company_fundamentals_master.csv"
PRICE_CACHE_DIR = cfg.STOCK_HISTORY_CACHE
WINDOWS = ("1D", "3D", "5D", "10D", "20D")
ACTIVE_SOURCES = frozenset({"classification_v4", "cross_theme"})

_lock = threading.RLock()
_cache_key: tuple[int, int, int, int] | None = None
_registry: dict[str, Any] | None = None
_memberships: pd.DataFrame | None = None
_price_cache: dict[str, dict[str, float | str | None]] = {}


def _safe(value: Any) -> Any:
    if value is None:
        return None
    if value is pd.NA:
        return None
    if isinstance(value, (float, int)) and not math.isfinite(float(value)):
        return None
    if hasattr(value, "item"):
        return _safe(value.item())
    return value


def _file_signature(path: Path) -> int:
    try:
        stat = path.stat()
        return hash((stat.st_mtime_ns, stat.st_size))
    except OSError:
        return 0


def _load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    themes = payload.get("themes")
    if not isinstance(themes, list) or not themes:
        raise ValueError("veda_theme_registry.json has no themes")
    required = {"theme_id", "code", "display_name", "category", "aliases"}
    if any(not required.issubset(item) for item in themes if isinstance(item, dict)):
        raise ValueError("theme registry entry is incomplete")
    if len({item["theme_id"] for item in themes}) != len(themes):
        raise ValueError("theme registry contains duplicate theme_id")
    return payload


def _ensure_loaded() -> tuple[dict[str, Any], pd.DataFrame]:
    global _cache_key, _registry, _memberships
    key = tuple(
        _file_signature(path)
        for path in (
            REGISTRY_PATH,
            CLASSIFICATION_PATH,
            TAGGING_PATH,
            FUNDAMENTALS_PATH,
        )
    )
    with _lock:
        if _registry is not None and _memberships is not None and _cache_key == key:
            return _registry, _memberships
        registry = _load_registry()
        code_to_id = {item["code"]: item["theme_id"] for item in registry["themes"]}
        tagging = pd.read_csv(TAGGING_PATH, dtype=str).fillna("")
        fundamentals = (
            pd.read_csv(FUNDAMENTALS_PATH, dtype=str).fillna("")
            if FUNDAMENTALS_PATH.exists()
            else pd.DataFrame()
        )
        isin_by_symbol = {}
        if not fundamentals.empty and {"symbol", "isin"}.issubset(fundamentals.columns):
            isin_by_symbol = {
                symbol: (
                    None
                    if not str(isin).strip() or str(isin).lower() == "nan"
                    else str(isin).strip()
                )
                for symbol, isin in zip(
                    fundamentals["symbol"].str.upper(), fundamentals["isin"]
                )
            }
        rows: list[dict[str, Any]] = []
        for _, row in tagging.iterrows():
            code = str(row.get("THEME", "")).strip().upper()
            source = str(row.get("SOURCE", "")).strip().lower()
            symbol = str(row.get("SYMBOL", "")).strip().upper()
            if code not in code_to_id or not symbol or source not in ACTIVE_SOURCES:
                continue
            primary = (
                str(row.get("IS_PRIMARY", "")).lower() == "true"
                or source == "classification_v4"
            )
            try:
                purity = float(row.get("PURITY_SCORE", ""))
            except (TypeError, ValueError):
                purity = None
            exposure = (
                "CORE"
                if primary
                else "MATERIAL"
                if purity is not None and purity >= 0.70
                else "SECONDARY"
            )
            quality = "HIGH" if source == "classification_v4" else "MEDIUM"
            rows.append(
                {
                    "symbol": symbol,
                    "isin": isin_by_symbol.get(symbol),
                    "theme_id": code_to_id[code],
                    "theme_code": code,
                    "relationship_type": "PRIMARY" if primary else "CROSS_THEME",
                    "exposure": exposure,
                    "evidence": [
                        {
                            "source": "data/reference/company_classification_v4.csv"
                            if source == "classification_v4"
                            else "data/reference/theme_tagging.csv",
                            "method": source,
                        }
                    ],
                    "method": "DETERMINISTIC_CLASSIFICATION"
                    if source == "classification_v4"
                    else "DETERMINISTIC_CROSS_THEME",
                    "confidence": round(
                        float(purity if purity is not None else 1.0), 2
                    ),
                    "quality": quality,
                    "effective_from": "2026-06-30",
                    "effective_to": None,
                    "last_verified": "2026-06-30",
                    "source": source,
                    "limitations": [
                        "Current-universe membership; historical membership snapshots unavailable."
                    ],
                    "status": "ACTIVE",
                }
            )
        memberships = pd.DataFrame(rows).drop_duplicates(
            subset=["symbol", "theme_id", "source"]
        )
        _registry, _memberships, _cache_key = registry, memberships, key
        _price_cache.clear()
        return registry, memberships


def registry() -> dict[str, Any]:
    reg, memberships = _ensure_loaded()
    out = dict(reg)
    counts = (
        memberships.groupby("theme_id")["symbol"].nunique().to_dict()
        if not memberships.empty
        else {}
    )
    out["themes"] = [
        {**item, "active_membership_count": int(counts.get(item["theme_id"], 0))}
        for item in reg["themes"]
    ]
    return out


def memberships_for(
    theme_id: str | None = None, symbol: str | None = None
) -> list[dict[str, Any]]:
    _, df = _ensure_loaded()
    if df.empty:
        return []
    view = df
    if theme_id:
        view = view[view["theme_id"] == theme_id]
    if symbol:
        view = view[view["symbol"] == symbol.upper()]
    records = view.sort_values(["theme_id", "symbol", "relationship_type"]).to_dict(
        orient="records"
    )
    return [{key: _safe(value) for key, value in record.items()} for record in records]


def _stock_returns(symbol: str) -> dict[str, float | str | None]:
    with _lock:
        if symbol in _price_cache:
            return _price_cache[symbol]
    path = PRICE_CACHE_DIR / f"{symbol}.parquet"
    result: dict[str, float | str | None] = {window: None for window in WINDOWS}
    result["as_of"] = None
    try:
        if path.exists():
            frame = pd.read_parquet(path, columns=["date", "close"])
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
            frame = frame.dropna(subset=["date", "close"]).sort_values("date")
            if len(frame) >= 2:
                close = frame["close"].astype(float).tolist()
                result["as_of"] = frame["date"].iloc[-1].date().isoformat()
                for window, offset in zip(WINDOWS, (1, 3, 5, 10, 20), strict=True):
                    if len(close) > offset and close[-1 - offset] > 0:
                        result[window] = round(
                            (close[-1] / close[-1 - offset] - 1) * 100, 4
                        )
    except (OSError, TypeError, ValueError, KeyError):
        # A single unavailable stock cannot fail a theme request.
        pass
    with _lock:
        _price_cache[symbol] = result
    return result


def _returns_for_symbols(
    symbols: list[str],
) -> dict[str, dict[str, float | str | None]]:
    """Load bounded local price histories concurrently, preserving symbol order."""
    if not symbols:
        return {}
    with _lock:
        cached = {
            symbol: _price_cache[symbol] for symbol in symbols if symbol in _price_cache
        }
    missing = [symbol for symbol in symbols if symbol not in cached]
    if missing:
        workers = min(16, len(missing))
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="theme-price"
        ) as executor:
            loaded = executor.map(_stock_returns, missing)
            cached.update(zip(missing, loaded, strict=True))
    return {symbol: cached[symbol] for symbol in symbols}


def _benchmark() -> dict[str, Any]:
    frame = data_loader.get("sector_rotation")
    if frame is None or frame.empty:
        return {
            "name": "NIFTY 50 equal-weight constituent return proxy",
            **{window: None for window in WINDOWS},
            "as_of": None,
        }
    row = frame.sort_values("date").iloc[-1]
    return {
        "name": str(
            row.get("benchmark", "NIFTY 50 equal-weight constituent return proxy")
        ),
        **{
            window: _safe(row.get(f"benchmark_return_{window.lower()}"))
            for window in WINDOWS
        },
        "as_of": _safe(row.get("benchmark_price_as_of", row.get("date"))),
    }


def _leadership(
    performance: dict[str, Any], breadth: dict[str, Any]
) -> tuple[str, str]:
    r5, r20 = (
        performance.get("relative_strength", {}).get("5D"),
        performance.get("relative_strength", {}).get("20D"),
    )
    positive = breadth.get("5D", {}).get("positive_pct")
    if r5 is None or r20 is None or positive is None:
        return "INSUFFICIENT_HISTORY", "UNAVAILABLE"
    if r5 > 0 and r20 > 0 and positive >= 55:
        state = "LEADING"
    elif r5 > 0 and r20 <= 0:
        state = "IMPROVING"
    elif r5 < 0 and r20 > 0:
        state = "WEAKENING"
    elif r5 < 0 and r20 < 0 and positive < 45:
        state = "LAGGING"
    else:
        state = "MIXED"
    acceleration = (
        "ACCELERATING"
        if r5 > r20 + 0.25
        else "DECELERATING"
        if r5 < r20 - 0.25
        else "STABLE"
    )
    return state, acceleration


def intelligence(
    theme_id: str, *, include_members: bool = False, member_limit: int = 50
) -> dict[str, Any]:
    reg, membership_frame = _ensure_loaded()
    theme = next((item for item in reg["themes"] if item["theme_id"] == theme_id), None)
    if theme is None:
        raise KeyError(theme_id)
    members = membership_frame[membership_frame["theme_id"] == theme_id]
    symbols = sorted(set(members["symbol"].tolist()))
    returns = _returns_for_symbols(symbols)
    benchmark = _benchmark()
    performance: dict[str, Any] = {
        "windows": {},
        "relative_strength": {},
        "benchmark": benchmark,
    }
    breadth: dict[str, Any] = {}
    leaders: list[dict[str, Any]] = []
    laggards: list[dict[str, Any]] = []
    for window in WINDOWS:
        usable = [
            (symbol, value[window])
            for symbol, value in returns.items()
            if value.get(window) is not None
        ]
        values = [float(value) for _, value in usable]
        avg = round(sum(values) / len(values), 4) if values else None
        bench = benchmark.get(window)
        performance["windows"][window] = {
            "return_pct": avg,
            "expected_members": len(symbols),
            "usable_members": len(values),
            "coverage_pct": round(len(values) / len(symbols) * 100, 2)
            if symbols
            else 0.0,
        }
        performance["relative_strength"][window] = (
            round(avg - float(bench), 4)
            if avg is not None and bench is not None
            else None
        )
        breadth[window] = {
            "positive_pct": round(
                sum(1 for value in values if value > 0) / len(values) * 100, 2
            )
            if values
            else None,
            "positive_members": sum(1 for value in values if value > 0),
            "usable_members": len(values),
            "expected_members": len(symbols),
        }
    usable_5 = [
        (symbol, value["5D"])
        for symbol, value in returns.items()
        if value.get("5D") is not None
    ]
    usable_5.sort(key=lambda item: item[1], reverse=True)
    leaders = [
        {"symbol": symbol, "return_5d_pct": round(float(value), 4)}
        for symbol, value in usable_5[:5]
    ]
    laggards = [
        {"symbol": symbol, "return_5d_pct": round(float(value), 4)}
        for symbol, value in usable_5[-5:][::-1]
    ]
    state, acceleration = _leadership(performance, breadth)
    out: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "theme": theme,
        "as_of": benchmark.get("as_of"),
        "membership": {
            "expected": len(symbols),
            "active": len(symbols),
            "current_universe": True,
            "historical_snapshots": "NOT_AVAILABLE",
            "coverage_limitation": "Current membership is used for all windows; survivorship bias is possible.",
        },
        "performance": performance,
        "breadth": breadth,
        "leadership": {
            "state": state,
            "persistence": "INSUFFICIENT_HISTORY",
            "acceleration": acceleration,
            "persistence_basis": "No governed multi-date theme membership/performance history is available.",
        },
        "leaders": leaders,
        "laggards": laggards,
        "institutional_context": {
            "scope": "MARKET_LEVEL_CONTEXT_ONLY",
            "theme_attribution": "NO_THEME_INSTITUTIONAL_ATTRIBUTION",
            "limitations": ["Broad FII/DII context is not attributed to this theme."],
        },
        "cross_layer_context": {
            "corporate": "MEMBERSHIP_SUPPORT_ONLY",
            "fundamental": "MEMBERSHIP_SUPPORT_ONLY",
            "stock": "REUSES_PROVIDER_STOCK_DATA; NO_NEW_STOCK_SCORE",
        },
        "evidence": {
            "authority": reg.get("authority"),
            "classification_source": str(CLASSIFICATION_PATH),
            "membership_source": str(TAGGING_PATH),
            "method": "DETERMINISTIC_CLASSIFICATION_AND_CROSS_THEME",
            "quality": "HIGH_PRIMARY_WITH_MEDIUM_SECONDARY",
        },
        "data_status": {
            "state": "AVAILABLE" if symbols else "UNAVAILABLE",
            "as_of": benchmark.get("as_of"),
            "source": [
                str(CLASSIFICATION_PATH),
                str(TAGGING_PATH),
                str(PRICE_CACHE_DIR),
            ],
            "last_successful_update": reg.get("last_verified"),
            "limitations": reg.get("limitations", []),
        },
        "limitations": [
            "Performance is an equal-weight proxy, not an official theme index.",
            "Missing prices remain missing and are excluded from denominators.",
            "No outcome or predictive claim is made.",
        ],
    }
    if include_members:
        out["memberships"] = memberships_for(theme_id)[: max(1, min(member_limit, 500))]
    return out


def summary() -> dict[str, Any]:
    reg, _ = _ensure_loaded()
    records = []
    for theme in reg["themes"]:
        detail = intelligence(theme["theme_id"])
        records.append(
            {
                "theme_id": theme["theme_id"],
                "code": theme["code"],
                "display_name": theme["display_name"],
                "category": theme["category"],
                "membership": detail["membership"],
                "performance": detail["performance"],
                "breadth": detail["breadth"],
                "leadership": detail["leadership"],
                "data_status": detail["data_status"],
            }
        )
    return {
        "contract_version": CONTRACT_VERSION,
        "count": len(records),
        "themes": records,
        "institutional_context_scope": "MARKET_LEVEL_CONTEXT_ONLY",
        "data_status": {
            "state": "AVAILABLE",
            "as_of": _benchmark().get("as_of"),
            "source": [
                str(REGISTRY_PATH),
                str(CLASSIFICATION_PATH),
                str(TAGGING_PATH),
                str(PRICE_CACHE_DIR),
            ],
            "last_successful_update": reg.get("last_verified"),
            "limitations": reg.get("limitations", []),
        },
    }


def reset_cache() -> None:
    with _lock:
        _price_cache.clear()
