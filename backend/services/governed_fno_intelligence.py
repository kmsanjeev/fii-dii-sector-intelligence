"""Governed, read-only F&O intelligence projection.

The acquisition engine remains the owner of NSE bhavcopy downloads.  This
module only normalizes the two schemas present in the local archive and
projects bounded, descriptive intelligence for the latest EOD session.  It
does not infer trades, recommendations, Greeks, Max Pain, or participant
options attribution.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from engines.common import config as cfg

CONTRACT_VERSION = "fno-intelligence-1.0"
FNO_DIR = cfg.NSE_DIR / "bhavcopy" / "fno"
LOOKBACK_SESSIONS = 5
_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}

_TYPE_MAP = {
    "STF": ("FUTURE", "STOCK"),
    "IDF": ("FUTURE", "INDEX"),
    "STO": ("OPTION", "STOCK"),
    "IDO": ("OPTION", "INDEX"),
    "FUTSTK": ("FUTURE", "STOCK"),
    "FUTIDX": ("FUTURE", "INDEX"),
    "OPTSTK": ("OPTION", "STOCK"),
    "OPTIDX": ("OPTION", "INDEX"),
}


def _column(frame: pd.DataFrame, *names: str, default: Any = None) -> pd.Series:
    for name in names:
        if name in frame.columns:
            return frame[name]
    return pd.Series(default, index=frame.index)


def _numeric(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) and math.isfinite(number) else None


def _date_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return None if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def _date_series(values: pd.Series) -> pd.Series:
    """Parse both ISO current files and legacy ``DD-Mon-YYYY`` values once."""
    text = values.astype("string").str.strip()
    parsed = pd.to_datetime(text, errors="coerce", format="mixed")
    missing = parsed.isna()
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(text.loc[missing], errors="coerce", dayfirst=True, format="mixed")
    return parsed.dt.strftime("%Y-%m-%d")


def _round(value: Any, digits: int = 4) -> float | None:
    number = _numeric(value)
    return None if number is None else float(round(number, digits))


def _file_date(path: Path) -> str | None:
    value = path.stem.removeprefix("fo_")
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return _date_value(value)


def discover_fno_files(fno_dir: Path = FNO_DIR, limit: int = LOOKBACK_SESSIONS) -> list[Path]:
    """Return the latest bounded set of dated bhavcopy files."""
    files = [path for path in fno_dir.rglob("fo_*.csv") if _file_date(path)] if fno_dir.exists() else []
    return sorted(files, key=lambda path: (_file_date(path) or "", path.name))[-limit:]


def _instrument_key(value: Any) -> tuple[str, str]:
    return _TYPE_MAP.get(str(value or "").strip().upper(), ("UNKNOWN", "UNKNOWN"))


def normalize_fno_frame(frame: pd.DataFrame, *, source_file: str = "") -> pd.DataFrame:
    """Normalize current NSE and legacy NSE derivative schemas."""
    if frame.empty:
        return pd.DataFrame()
    raw_type = _column(frame, "FinInstrmTp", "INSTRUMENT", default="").astype(str).str.strip().str.upper()
    mapped = raw_type.map(_TYPE_MAP)
    out = pd.DataFrame(index=frame.index)
    out["trade_date"] = _date_series(_column(frame, "TradDt", "TIMESTAMP", default=""))
    out["expiry_date"] = _date_series(_column(frame, "XpryDt", "EXPIRY_DT", default=""))
    out["raw_instrument_type"] = raw_type
    out["instrument_class"] = mapped.map(lambda item: item[0] if isinstance(item, tuple) else "UNKNOWN")
    out["underlying_type"] = mapped.map(lambda item: item[1] if isinstance(item, tuple) else "UNKNOWN")
    out["underlying_symbol"] = _column(frame, "TckrSymb", "SYMBOL", default="").astype(str).str.strip().str.upper()
    out["strike"] = pd.to_numeric(_column(frame, "StrkPric", "STRIKE_PR"), errors="coerce")
    out["option_type"] = _column(frame, "OptnTp", "OPTION_TYP", default="").astype(str).str.strip().str.upper()
    out["open"] = pd.to_numeric(_column(frame, "OpnPric", "OPEN"), errors="coerce")
    out["high"] = pd.to_numeric(_column(frame, "HghPric", "HIGH"), errors="coerce")
    out["low"] = pd.to_numeric(_column(frame, "LwPric", "LOW"), errors="coerce")
    out["price"] = pd.to_numeric(_column(frame, "ClsPric", "CLOSE"), errors="coerce")
    out["settlement"] = pd.to_numeric(_column(frame, "SttlmPric", "SETTLE_PR"), errors="coerce")
    out["underlying_price"] = pd.to_numeric(_column(frame, "UndrlygPric"), errors="coerce")
    out["open_interest"] = pd.to_numeric(_column(frame, "OpnIntrst", "OPEN_INT"), errors="coerce")
    out["oi_change"] = pd.to_numeric(_column(frame, "ChngInOpnIntrst", "CHG_IN_OI"), errors="coerce")
    out["volume"] = pd.to_numeric(_column(frame, "TtlTradgVol", "CONTRACTS"), errors="coerce")
    out["turnover"] = pd.to_numeric(_column(frame, "TtlTrfVal", "VAL_INLAKH"), errors="coerce")
    out["provider_id"] = "NSE_BHAVCOPY"
    out["schema_variant"] = "nse_current_v2" if "FinInstrmTp" in frame.columns else "nse_legacy_v1"
    raw_id = _column(frame, "FinInstrmId", default="").astype(str).str.strip()
    expiry = out["expiry_date"].fillna("")
    strike = out["strike"].fillna(0).map(lambda value: f"{value:g}" if isinstance(value, (int, float)) else str(value))
    option = out["option_type"].replace({"NAN": "", "NONE": ""})
    namespace = out["underlying_type"].map(lambda value: "INDEX" if value == "INDEX" else "STOCK")
    fallback_id = (
        namespace + ":" + out["underlying_symbol"] + ":" + expiry + ":" + strike.astype(str) + ":" + option
    )
    out["contract_id"] = raw_id.where(~raw_id.isin({"", "NAN", "NONE"}), fallback_id)
    out["underlying_id"] = out["underlying_type"].map(
        lambda value: "INDEX:" if value == "INDEX" else "STOCK:"
    ) + out["underlying_symbol"]
    out["identity_status"] = out.apply(
        lambda row: "IDENTITY_REVIEW_REQUIRED"
        if not str(row.get("underlying_symbol", "")).strip()
        else "INDEX_NAMESPACE" if row.get("underlying_type") == "INDEX" else "SYMBOL_EXACT_NO_FUZZY_MATCH",
        axis=1,
    )
    out = out.reset_index(drop=True)
    key = ["trade_date", "instrument_class", "underlying_id", "expiry_date", "strike", "option_type", "contract_id"]
    out = out.drop_duplicates(subset=key, keep="last")
    out["source_file"] = source_file
    return out


def _activity_sort(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    for column in ("volume", "open_interest", "turnover"):
        work[f"_{column}"] = pd.to_numeric(work[column], errors="coerce").fillna(-1)
    return work.sort_values(
        ["_volume", "_open_interest", "_turnover", "expiry_date", "contract_id"],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    )


def _select_future(frame: pd.DataFrame, *, trade_date: str | None) -> pd.DataFrame:
    futures = frame[frame["instrument_class"] == "FUTURE"].copy()
    if futures.empty:
        return futures
    valid = futures[futures["expiry_date"].notna()].copy()
    if trade_date:
        active = valid[valid["expiry_date"] >= trade_date]
        if not active.empty:
            valid = active
    valid = valid.sort_values(["underlying_id", "expiry_date", "contract_id"], kind="mergesort")
    nearest_expiry = valid.groupby("underlying_id", sort=False)["expiry_date"].transform("first")
    selected = valid[valid["expiry_date"] == nearest_expiry]
    return _activity_sort(selected).drop_duplicates("underlying_id", keep="first").drop(
        columns=[column for column in selected.columns if column.startswith("_")], errors="ignore"
    )


def _select_most_active(frame: pd.DataFrame, *, trade_date: str | None) -> pd.DataFrame:
    futures = frame[frame["instrument_class"] == "FUTURE"].copy()
    if trade_date:
        active = futures[futures["expiry_date"].notna() & (futures["expiry_date"] >= trade_date)]
        if not active.empty:
            futures = active
    return _activity_sort(futures).drop_duplicates("underlying_id", keep="first").drop(
        columns=[column for column in futures.columns if column.startswith("_")], errors="ignore"
    )


def _pcr(call_oi: float | None, put_oi: float | None, call_volume: float | None, put_volume: float | None) -> dict[str, Any]:
    def ratio(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator is None or denominator <= 0:
            return None
        return float(round(numerator / denominator, 6))

    return {
        "call_oi": _round(call_oi, 0),
        "put_oi": _round(put_oi, 0),
        "pcr_oi": ratio(put_oi, call_oi),
        "call_volume": _round(call_volume, 0),
        "put_volume": _round(put_volume, 0),
        "pcr_volume": ratio(put_volume, call_volume),
    }


def _positioning_state(oi_change: float | None, price_change: float | None, *, roll_detected: bool) -> str:
    if roll_detected:
        return "ROLL_TRANSITION"
    if oi_change is None or price_change is None:
        return "INSUFFICIENT_EVIDENCE"
    if oi_change == 0 or price_change == 0:
        return "NEUTRAL"
    if oi_change > 0 and price_change > 0:
        return "LONG_BUILDUP"
    if oi_change > 0 and price_change < 0:
        return "SHORT_BUILDUP"
    if oi_change < 0 and price_change < 0:
        return "LONG_UNWINDING"
    return "SHORT_COVERING"


def _record(
    row: pd.Series,
    previous: pd.Series | None,
    five_day: float | None,
    *,
    roll_detected: bool,
    five_day_continuous: bool,
) -> dict[str, Any]:
    current_price = _numeric(row.get("price"))
    previous_price = _numeric(previous.get("price")) if previous is not None else None
    price_change = None if roll_detected or current_price is None or previous_price is None else current_price - previous_price
    oi_change = _numeric(row.get("oi_change"))
    underlying_price = _numeric(row.get("underlying_price"))
    basis = current_price - underlying_price if current_price is not None and underlying_price is not None else None
    return {
        "symbol": str(row.get("underlying_symbol", "")),
        "underlying_id": str(row.get("underlying_id", "")),
        "underlying_type": str(row.get("underlying_type", "UNKNOWN")),
        "instrument_class": "FUTURE",
        "contract_id": str(row.get("contract_id", "")),
        "selection": "NEAREST_EXPIRY_THEN_LIQUIDITY",
        "identity_status": row.get("identity_status"),
        "open": _round(row.get("open"), 6),
        "high": _round(row.get("high"), 6),
        "low": _round(row.get("low"), 6),
        "futures_oi": _round(row.get("open_interest"), 0),
        "oi_1d": _round(oi_change, 0),
        "oi_5d": _round(five_day, 0),
        "price_change_1d": _round(price_change, 6),
        "oi_signal": _positioning_state(oi_change, price_change, roll_detected=roll_detected),
        "fut_close": _round(current_price, 6),
        "underlying_price": _round(underlying_price, 6),
        "basis": _round(basis, 6),
        "basis_pct": _round((basis / underlying_price) * 100, 6) if basis is not None and underlying_price else None,
        "expiry": row.get("expiry_date"),
        "days_to_expiry": (
            (pd.Timestamp(row.get("expiry_date")) - pd.Timestamp(row.get("trade_date"))).days
            if row.get("expiry_date") and row.get("trade_date") else None
        ),
        "contract_status": (
            "ACTIVE"
            if row.get("expiry_date") and row.get("trade_date") and row.get("expiry_date") >= row.get("trade_date")
            else "UNKNOWN"
        ),
        "contracts_volume": _round(row.get("volume"), 0),
        "turnover": _round(row.get("turnover"), 6),
        "as_of_date": row.get("trade_date"),
        "data_status": "EOD",
        "roll_detected": roll_detected,
        "five_day_contract_continuous": five_day_continuous,
        "evidence_quality": "SOURCE_REPORTED_OI_WITH_SAME_CONTRACT_PRICE_CHECK",
        "source": {
            "provider": row.get("provider_id", "NSE_BHAVCOPY"),
            "schema_variant": row.get("schema_variant"),
            "source_file": row.get("source_file"),
        },
    }


def build_governed_fno_intelligence(
    *,
    symbol: str | None = None,
    fno_dir: Path = FNO_DIR,
    lookback: int = LOOKBACK_SESSIONS,
    reader: Callable[..., pd.DataFrame] = pd.read_csv,
) -> dict[str, Any]:
    files = discover_fno_files(fno_dir, max(2, min(int(lookback), 10)))
    cache_key = (
        str(fno_dir.resolve()),
        symbol.upper() if symbol else None,
        int(lookback),
        tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in files),
    )
    if cache_key in _CACHE:
        return copy.deepcopy(_CACHE[cache_key])
    if not files:
        result = {
            "contract_version": CONTRACT_VERSION,
            "status": "UNAVAILABLE",
            "data_status": _data_status(None, "No local NSE F&O bhavcopy files found"),
            "futures": [],
            "pcr": {},
        }
        _CACHE[cache_key] = result
        return copy.deepcopy(result)
    frames = [normalize_fno_frame(reader(path, low_memory=False), source_file=path.name) for path in files]
    frames = [frame for frame in frames if not frame.empty]
    latest = frames[-1]
    trade_date = str(latest["trade_date"].dropna().iloc[0]) if latest["trade_date"].notna().any() else _file_date(files[-1])
    previous = frames[-2] if len(frames) >= 2 else pd.DataFrame()
    selected = _select_future(latest, trade_date=trade_date)
    most_active = _select_most_active(latest, trade_date=trade_date)
    previous_selected = _select_future(previous, trade_date=None) if not previous.empty else pd.DataFrame()
    previous_by_underlying = {
        str(row["underlying_id"]): row for _, row in previous_selected.iterrows()
    }

    records: list[dict[str, Any]] = []
    for _, row in selected.iterrows():
        if symbol and str(row["underlying_symbol"]).upper() != symbol.upper():
            continue
        prior = previous_by_underlying.get(str(row["underlying_id"]))
        roll_detected = bool(prior is not None and str(prior.get("expiry_date")) != str(row.get("expiry_date")))
        five_day_values: list[float] = []
        continuous = True
        for frame in frames:
            same_contract = frame[
                (frame["instrument_class"] == "FUTURE")
                & (frame["underlying_id"] == row["underlying_id"])
                & (frame["expiry_date"] == row["expiry_date"])
            ]
            if same_contract.empty:
                continuous = False
                break
            picked = _activity_sort(same_contract).iloc[0]
            value = _numeric(picked.get("oi_change"))
            if value is None:
                continuous = False
                break
            five_day_values.append(value)
        five_day = sum(five_day_values) if continuous and len(five_day_values) == len(frames) else None
        records.append(_record(row, prior if not roll_detected else None, five_day, roll_detected=roll_detected, five_day_continuous=continuous))

    option_frame = latest[
        (latest["instrument_class"] == "OPTION")
        & latest["expiry_date"].notna()
        & (latest["expiry_date"] >= trade_date)
    ].copy()
    option_frame["call_oi"] = option_frame.apply(lambda row: _numeric(row["open_interest"]) if row["option_type"] == "CE" else 0, axis=1)
    option_frame["put_oi"] = option_frame.apply(lambda row: _numeric(row["open_interest"]) if row["option_type"] == "PE" else 0, axis=1)
    option_frame["call_volume"] = option_frame.apply(lambda row: _numeric(row["volume"]) if row["option_type"] == "CE" else 0, axis=1)
    option_frame["put_volume"] = option_frame.apply(lambda row: _numeric(row["volume"]) if row["option_type"] == "PE" else 0, axis=1)
    stock_options = option_frame[option_frame["underlying_type"] == "STOCK"]
    index_options = option_frame[option_frame["underlying_type"] == "INDEX"]
    stock_pcr = _pcr(stock_options["call_oi"].sum(), stock_options["put_oi"].sum(), stock_options["call_volume"].sum(), stock_options["put_volume"].sum())
    index_pcr = _pcr(index_options["call_oi"].sum(), index_options["put_oi"].sum(), index_options["call_volume"].sum(), index_options["put_volume"].sum())
    by_index: dict[str, Any] = {}
    for name, group in index_options.groupby("underlying_id", sort=True):
        by_index[name] = _pcr(group["call_oi"].sum(), group["put_oi"].sum(), group["call_volume"].sum(), group["put_volume"].sum())

    result = {
        "contract_version": CONTRACT_VERSION,
        "status": "AVAILABLE",
        "as_of_date": trade_date,
        "data_status": _data_status(trade_date, ""),
        "source": {
            "provider": "NSE_BHAVCOPY",
            "files": [path.name for path in files],
            "schema_variants": sorted({str(frame["schema_variant"].iloc[0]) for frame in frames}),
            "selection_policy": "NEAREST_EXPIRY_THEN_VOLUME_OI_TURNOVER",
            "most_active_policy": "VOLUME_THEN_OPEN_INTEREST_THEN_TURNOVER_THEN_EXPIRY",
            "oi_change_semantics": "SOURCE_REPORTED_DAILY_CHANGE",
        },
        "futures": records,
        "most_active_contracts": [
            {
                "underlying_id": row.get("underlying_id"),
                "symbol": row.get("underlying_symbol"),
                "contract_id": row.get("contract_id"),
                "expiry": row.get("expiry_date"),
                "volume": _round(row.get("volume"), 0),
                "open_interest": _round(row.get("open_interest"), 0),
            }
            for _, row in most_active.iterrows()
        ],
        "selection": {
            "nearest_expiry": "Earliest non-expired expiry per underlying, then deterministic liquidity tie-break.",
            "most_active": "Highest volume, then open interest, turnover, expiry and contract identifier.",
            "active_contract_filter": "expiry_date >= trade_date",
        },
        "options": {
            "stock_contract_count": len(stock_options),
            "index_contract_count": len(index_options),
            "stock_option_scope": "ALL_ACTIVE_EXPIRIES",
            "index_option_scope": "ALL_ACTIVE_EXPIRIES",
            "greeks": "NOT_IMPLEMENTED",
            "max_pain": "NOT_IMPLEMENTED",
        },
        "pcr": {
            "scope": "ALL_ACTIVE_EXPIRIES",
            "stock_options_oi": stock_pcr,
            "index_options_oi": index_pcr,
            "index_by_underlying": by_index,
            "signal": "UNINTERPRETED_DESCRIPTIVE_ONLY",
        },
        "features": {
            "participant_options": "NOT_SUPPORTED",
            "greeks": "NOT_IMPLEMENTED",
            "max_pain": "NOT_IMPLEMENTED",
        },
        "limitations": [
            "F&O values are descriptive EOD source data, not trade recommendations.",
            "Participant-wise options attribution is not available from ordinary bhavcopy.",
            "Five-session OI is withheld when the selected expiry is not continuous across the bounded files.",
        ],
    }
    _CACHE[cache_key] = result
    return copy.deepcopy(result)


def _data_status(as_of: str | None, reason: str) -> dict[str, Any]:
    return {
        "state": "AVAILABLE" if as_of else "UNAVAILABLE",
        "as_of": as_of,
        "source": ["NSE_BHAVCOPY"] if as_of else [],
        "last_successful_update": as_of,
        "limitations": [reason] if reason else [],
    }
