"""Governed provider-local Theme Intelligence contract.

This service deliberately sits beside the legacy Phase-E theme scorer.  It
owns no forecasts and no institutional theme attribution.  Membership is
derived from the governed classification/tagging artefacts; performance is an
equal-weight proxy over usable current members and the existing market
benchmark.  Missing prices remain missing and are excluded from denominators.
"""

from __future__ import annotations

import hashlib
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
RUNTIME_CACHE_DIR = cfg.CACHE_DIR / "theme_intelligence"
MEMBERSHIP_SNAPSHOT_PATH = RUNTIME_CACHE_DIR / "membership_snapshot.json"
PRICE_PROJECTION_PATH = RUNTIME_CACHE_DIR / "price_projection.json"
PRICE_MANIFEST_PATH = PRICE_CACHE_DIR / "manifest.json"
WINDOWS = ("1D", "3D", "5D", "10D", "20D")
ACTIVE_SOURCES = frozenset({"classification_v4", "cross_theme"})
MEMBERSHIP_ARTIFACT_SCHEMA = "theme-membership-snapshot-1.0"
PRICE_ARTIFACT_SCHEMA = "theme-price-projection-1.0"

_lock = threading.RLock()
_price_build_lock = threading.Lock()
_cache_key: tuple[int, int, int, int] | None = None
_registry: dict[str, Any] | None = None
_memberships: pd.DataFrame | None = None
_membership_fingerprint: str | None = None
_price_cache: dict[str, dict[str, float | str | None]] = {}
_price_projection_key: tuple[str, tuple[int, int] | None] | None = None
_source_fingerprint_key: tuple[int, int, int, int] | None = None
_source_fingerprint_value: str | None = None


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


def _file_state(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
        return int(stat.st_mtime_ns), int(stat.st_size)
    except OSError:
        return None


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_fingerprint() -> str:
    """Return a content fingerprint, hashing source files only when changed."""
    global _source_fingerprint_key, _source_fingerprint_value
    paths = (REGISTRY_PATH, CLASSIFICATION_PATH, TAGGING_PATH, FUNDAMENTALS_PATH)
    key = tuple(_file_signature(path) for path in paths)
    if _source_fingerprint_value is not None and _source_fingerprint_key == key:
        return _source_fingerprint_value
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.name).encode("utf-8"))
        try:
            digest.update(path.read_bytes())
        except OSError:
            digest.update(b"<missing>")
    _source_fingerprint_key = key
    _source_fingerprint_value = digest.hexdigest()
    return _source_fingerprint_value


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary.replace(path)


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


def _build_memberships(registry: dict[str, Any]) -> pd.DataFrame:
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
                "confidence": round(float(purity if purity is not None else 1.0), 2),
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
    return pd.DataFrame(rows).drop_duplicates(subset=["symbol", "theme_id", "source"])


def _membership_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    columns = [
        "symbol",
        "isin",
        "theme_id",
        "theme_code",
        "relationship_type",
        "exposure",
        "evidence",
        "method",
        "confidence",
        "quality",
        "effective_from",
        "effective_to",
        "last_verified",
        "source",
        "limitations",
        "status",
    ]
    available = [column for column in columns if column in frame.columns]
    view = frame[available].sort_values(
        ["theme_id", "symbol", "relationship_type", "source"]
    )
    return [
        {key: _safe(value) for key, value in record.items()}
        for record in view.to_dict(orient="records")
    ]


def _load_membership_snapshot(
    registry: dict[str, Any], source_fingerprint: str
) -> pd.DataFrame | None:
    try:
        payload = json.loads(MEMBERSHIP_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        if payload.get("schema_version") != MEMBERSHIP_ARTIFACT_SCHEMA:
            return None
        if payload.get("source_fingerprint") != source_fingerprint:
            return None
        artifact_hash = payload.get("artifact_hash")
        body = {key: value for key, value in payload.items() if key != "artifact_hash"}
        if artifact_hash != _canonical_hash(body):
            return None
        records = payload.get("memberships")
        if not isinstance(records, list):
            return None
        frame = pd.DataFrame(records)
        if frame.empty or payload.get("row_count") != len(frame):
            return None
        valid_ids = {item["theme_id"] for item in registry["themes"]}
        required = {"symbol", "theme_id", "source", "status"}
        if not required.issubset(frame.columns):
            return None
        if not set(frame["theme_id"]).issubset(valid_ids):
            return None
        if not set(frame["source"]).issubset(ACTIVE_SOURCES):
            return None
        if set(frame["status"]) != {"ACTIVE"}:
            return None
        return frame
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _write_membership_snapshot(frame: pd.DataFrame, source_fingerprint: str) -> None:
    body: dict[str, Any] = {
        "schema_version": MEMBERSHIP_ARTIFACT_SCHEMA,
        "source_fingerprint": source_fingerprint,
        "row_count": len(frame),
        "memberships": _membership_records(frame),
    }
    _write_json_atomic(
        MEMBERSHIP_SNAPSHOT_PATH, {**body, "artifact_hash": _canonical_hash(body)}
    )


def _ensure_loaded() -> tuple[dict[str, Any], pd.DataFrame]:
    global _cache_key, _registry, _memberships, _membership_fingerprint
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
        source_fingerprint = _source_fingerprint()
        memberships = _load_membership_snapshot(registry, source_fingerprint)
        if memberships is None:
            memberships = _build_memberships(registry)
            _write_membership_snapshot(memberships, source_fingerprint)
        _registry, _memberships, _cache_key = registry, memberships, key
        _membership_fingerprint = _canonical_hash(_membership_records(memberships))
        _price_cache.clear()
        global _price_projection_key
        _price_projection_key = None
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


def _price_projection_key_for_current_membership() -> tuple[
    str, tuple[int, int] | None
]:
    return (
        _membership_fingerprint or "",
        _file_state(PRICE_MANIFEST_PATH),
    )


def _load_price_projection(
    symbols: list[str], key: tuple[str, tuple[int, int] | None]
) -> bool:
    try:
        payload = json.loads(PRICE_PROJECTION_PATH.read_text(encoding="utf-8"))
        if payload.get("schema_version") != PRICE_ARTIFACT_SCHEMA:
            return False
        if payload.get("membership_fingerprint") != key[0]:
            return False
        if tuple(payload.get("manifest_state") or ()) != key[1]:
            return False
        artifact_hash = payload.get("artifact_hash")
        body = {
            name: value for name, value in payload.items() if name != "artifact_hash"
        }
        if artifact_hash != _canonical_hash(body):
            return False
        prices = payload.get("prices")
        if not isinstance(prices, dict) or not set(symbols).issubset(prices):
            return False
        with _lock:
            _price_cache.update(
                {
                    symbol: value
                    for symbol, value in prices.items()
                    if isinstance(value, dict)
                }
            )
            global _price_projection_key
            _price_projection_key = key
        return True
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _write_price_projection(
    prices: dict[str, dict[str, float | str | None]],
    key: tuple[str, tuple[int, int] | None],
) -> None:
    body: dict[str, Any] = {
        "schema_version": PRICE_ARTIFACT_SCHEMA,
        "membership_fingerprint": key[0],
        "manifest_state": list(key[1]) if key[1] is not None else None,
        "symbol_count": len(prices),
        "prices": {
            symbol: {name: _safe(value) for name, value in prices[symbol].items()}
            for symbol in sorted(prices)
        },
        "limitations": [
            "Derived projection only; stock-history manifest is the price freshness authority.",
            "Static membership and dynamic price projection are invalidated independently.",
        ],
    }
    _write_json_atomic(
        PRICE_PROJECTION_PATH, {**body, "artifact_hash": _canonical_hash(body)}
    )


def _returns_for_symbols(
    symbols: list[str],
) -> dict[str, dict[str, float | str | None]]:
    """Load bounded local price histories concurrently, preserving symbol order."""
    if not symbols:
        return {}
    key = _price_projection_key_for_current_membership()
    with _price_build_lock:
        global _price_projection_key
        if _price_projection_key != key:
            with _lock:
                _price_cache.clear()
            _price_projection_key = key
        with _lock:
            cached = {
                symbol: _price_cache[symbol]
                for symbol in symbols
                if symbol in _price_cache
            }
        missing = [symbol for symbol in symbols if symbol not in cached]
        if missing and not cached:
            _load_price_projection(symbols, key)
            with _lock:
                cached = {
                    symbol: _price_cache[symbol]
                    for symbol in symbols
                    if symbol in _price_cache
                }
            missing = [symbol for symbol in symbols if symbol not in cached]
        if missing:
            workers = min(16, len(missing))
            with ThreadPoolExecutor(
                max_workers=workers, thread_name_prefix="theme-price"
            ) as executor:
                loaded = executor.map(_stock_returns, missing)
                cached.update(zip(missing, loaded, strict=True))
            with _lock:
                _write_price_projection(dict(_price_cache), key)
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


def build_runtime_cache(*, include_prices: bool = True) -> dict[str, Any]:
    """Build validated local runtime artifacts outside the request path."""
    _, memberships = _ensure_loaded()
    symbols = (
        sorted(set(memberships["symbol"].tolist())) if not memberships.empty else []
    )
    if include_prices:
        _returns_for_symbols(symbols)
    return {
        "membership_snapshot": str(MEMBERSHIP_SNAPSHOT_PATH),
        "membership_rows": len(memberships),
        "price_projection": str(PRICE_PROJECTION_PATH),
        "price_symbols": len(symbols) if include_prices else 0,
        "price_manifest_state": list(_file_state(PRICE_MANIFEST_PATH) or ()),
        "source_fingerprint": _source_fingerprint(),
    }


def reset_cache() -> None:
    global _price_projection_key
    with _lock:
        _price_cache.clear()
        _price_projection_key = None
