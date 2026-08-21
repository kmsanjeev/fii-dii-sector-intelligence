"""Governed Intraday Market-data foundation.

This module deliberately stops at source acquisition, normalization, quality,
storage and bounded read contracts.  It does not calculate signals, create
trade setups, or call any broker execution API.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import pandas as pd

from engines.common import config as cfg

CONTRACT_VERSION = "intraday-market-data-1.0"
PROVIDER_ID = "dhanhq"
TIMEZONE = ZoneInfo("Asia/Kolkata")
SUPPORTED_INTERVALS = frozenset({1, 5, 15, 25, 60})
SESSION_OPEN = time(9, 15)
SESSION_CLOSE = time(15, 30)
PRE_OPEN_START = time(9, 0)

DATA_ROOT = cfg.DATA_DIR / "intraday"
STORE_ROOT = DATA_ROOT / "candles"
MANIFEST_PATH = DATA_ROOT / "manifest.json"


class IntradaySourceError(RuntimeError):
    """Typed source or entitlement failure."""


@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    provider_security_id: str
    exchange: str
    segment: str
    instrument_class: str
    symbol: str
    provider_instrument_type: str | None = None
    isin: str | None = None
    underlying: str | None = None
    expiry: str | None = None
    strike: float | None = None
    option_type: str | None = None
    mapping_source: str = "dhan-security-master"
    mapping_version: str = "UNRECORDED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_security_id": self.provider_security_id,
            "exchange": self.exchange,
            "segment": self.segment,
            "instrument_class": self.instrument_class,
            "provider_instrument_type": self.provider_instrument_type,
            "symbol": self.symbol,
            "isin": self.isin,
            "underlying": self.underlying,
            "expiry": self.expiry,
            "strike": self.strike,
            "option_type": self.option_type,
            "mapping_source": self.mapping_source,
            "mapping_version": self.mapping_version,
        }


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def identity_from_provider_row(row: dict[str, Any]) -> InstrumentIdentity:
    """Build an exact identity from a provider master row; never fuzzy-match."""
    provider_id = _text(row.get("security_id") or row.get("SEM_SMST_SECURITY_ID"))
    segment = _text(row.get("exchange_segment") or row.get("SEM_SEGMENT"))
    symbol = _text(
        row.get("symbol")
        or row.get("trading_symbol")
        or row.get("SEM_TRADING_SYMBOL")
        or row.get("SM_SYMBOL_NAME")
    )
    if not provider_id or not segment or not symbol:
        raise ValueError("provider row lacks exact security_id, segment or symbol")

    raw_instrument = _text(row.get("instrument") or row.get("SEM_INSTRUMENT_NAME")).upper()
    if "OPTION" in raw_instrument or raw_instrument in {"OPTIDX", "OPTSTK"}:
        instrument_class = "OPTION"
    elif "FUT" in raw_instrument or raw_instrument in {"FUTIDX", "FUTSTK"}:
        instrument_class = "FUTURE"
    elif "INDEX" in raw_instrument or segment == "IDX_I":
        instrument_class = "INDEX"
    else:
        instrument_class = "EQUITY"

    return InstrumentIdentity(
        provider_security_id=provider_id,
        exchange=_text(row.get("exchange") or row.get("EXCH_ID")),
        segment=segment,
        instrument_class=instrument_class,
        provider_instrument_type=raw_instrument or None,
        symbol=symbol.upper(),
        isin=_text(row.get("isin") or row.get("ISIN")) or None,
        underlying=_text(row.get("underlying") or row.get("UNDERLYING_SYMBOL")) or None,
        expiry=_text(row.get("expiry") or row.get("SEM_EXPIRY_DATE")) or None,
        strike=_float_or_none(row.get("strike") or row.get("SEM_STRIKE_PRICE")),
        option_type=_text(row.get("option_type") or row.get("SEM_OPTION_TYPE")) or None,
        mapping_version=_text(row.get("mapping_version")) or "UNRECORDED",
    )


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            numeric = float(value)
            # Dhan historical responses use Unix seconds.
            parsed = datetime.fromtimestamp(numeric, tz=ZoneInfo("UTC"))
        except (TypeError, ValueError, OverflowError):
            parsed = pd.Timestamp(value).to_pydatetime()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TIMEZONE)
    return parsed.astimezone(TIMEZONE)


def session_state(at: datetime | None = None, *, holiday: bool = False, special: bool = False) -> str:
    at = (at or datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    if holiday:
        return "HOLIDAY"
    if at.weekday() >= 5:
        return "WEEKEND"
    if special:
        return "SPECIAL_SESSION"
    if at.time() < PRE_OPEN_START:
        return "UNKNOWN"
    if at.time() < SESSION_OPEN:
        return "PRE_OPEN"
    if at.time() <= SESSION_CLOSE:
        return "REGULAR_OPEN"
    return "POST_CLOSE"


def is_regular_session_timestamp(at: datetime) -> bool:
    return session_state(at) == "REGULAR_OPEN"


def _bar_closed(bar_end: datetime, *, retrieved_at: datetime | None = None) -> bool:
    now = (retrieved_at or datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    return bar_end <= now or bar_end.date() < now.date()


def validate_candle(candle: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    required = ("instrument_id", "interval", "bar_start", "open", "high", "low", "close")
    if any(key not in candle for key in required):
        return ["MISSING_REQUIRED_FIELD"]
    try:
        open_, high, low, close = (float(candle[key]) for key in ("open", "high", "low", "close"))
    except (TypeError, ValueError):
        return ["NON_NUMERIC_PRICE"]
    if min(open_, high, low, close) <= 0:
        flags.append("NON_POSITIVE_PRICE")
    if high < max(open_, close, low) or low > min(open_, close, high):
        flags.append("INVALID_OHLC")
    if candle.get("volume") is not None:
        try:
            if float(candle["volume"]) < 0:
                flags.append("NEGATIVE_VOLUME")
        except (TypeError, ValueError):
            flags.append("NON_NUMERIC_VOLUME")
    if candle.get("open_interest") is not None:
        try:
            if float(candle["open_interest"]) < 0:
                flags.append("NEGATIVE_OI")
        except (TypeError, ValueError):
            flags.append("NON_NUMERIC_OI")
    return flags


def normalize_dhan_candles(
    payload: dict[str, Any],
    identity: InstrumentIdentity,
    interval: int,
    *,
    retrieved_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Normalize Dhan parallel arrays without converting missing values to zero."""
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    arrays = {key: payload.get(key) or [] for key in ("open", "high", "low", "close", "volume", "timestamp", "oi")}
    size = len(arrays["timestamp"])
    if not size or any(len(values) not in {0, size} for values in arrays.values()):
        raise ValueError("provider candle arrays are not aligned")
    retrieved = (retrieved_at or datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    out: list[dict[str, Any]] = []
    for index in range(size):
        start = _timestamp(arrays["timestamp"][index])
        end = start + timedelta(minutes=interval)
        row = {
            "instrument_id": identity.as_dict(),
            "trade_date": start.date().isoformat(),
            "interval": interval,
            "bar_start": start.isoformat(),
            "bar_end": end.isoformat(),
            "timezone": "Asia/Kolkata",
            "open": arrays["open"][index],
            "high": arrays["high"][index],
            "low": arrays["low"][index],
            "close": arrays["close"][index],
            "volume": arrays["volume"][index] if arrays["volume"] else None,
            "open_interest": arrays["oi"][index] if arrays["oi"] else None,
            "is_closed": _bar_closed(end, retrieved_at=retrieved),
            "candle_state": "CLOSED" if _bar_closed(end, retrieved_at=retrieved) else "OPEN_PARTIAL",
            "source": PROVIDER_ID,
            "source_record_context": {"provider": PROVIDER_ID, "interval": interval},
            "retrieved_at": retrieved.isoformat(),
            "data_status": "AVAILABLE",
        }
        row["quality_flags"] = validate_candle(row)
        out.append(row)
    return out


def aggregate_candles(candles: list[dict[str, Any]], target_interval: int) -> list[dict[str, Any]]:
    """Aggregate same-session bars; OI is last-value, never summed."""
    if target_interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"unsupported interval: {target_interval}")
    if not candles:
        return []
    buckets: dict[tuple[str, datetime], list[dict[str, Any]]] = {}
    for candle in candles:
        start = _timestamp(candle["bar_start"])
        if session_state(start) != "REGULAR_OPEN":
            continue
        session_open = datetime.combine(start.date(), SESSION_OPEN, tzinfo=TIMEZONE)
        offset = int((start - session_open).total_seconds() // 60)
        bucket_start = session_open + timedelta(minutes=(offset // target_interval) * target_interval)
        buckets.setdefault((candle["instrument_id"]["provider_security_id"], bucket_start), []).append(candle)

    result: list[dict[str, Any]] = []
    for (_, bucket_start), rows in sorted(buckets.items(), key=lambda item: item[0][1]):
        rows = sorted(rows, key=lambda row: _timestamp(row["bar_start"]))
        first, last = rows[0], rows[-1]
        row = dict(first)
        row.update(
            {
                "interval": target_interval,
                "bar_start": bucket_start.isoformat(),
                "bar_end": (bucket_start + timedelta(minutes=target_interval)).isoformat(),
                "open": first["open"],
                "high": max(float(item["high"]) for item in rows),
                "low": min(float(item["low"]) for item in rows),
                "close": last["close"],
                "volume": (
                    sum(float(item["volume"]) for item in rows if item.get("volume") is not None)
                    if any(item.get("volume") is not None for item in rows)
                    else None
                ),
                "open_interest": last.get("open_interest"),
                "is_closed": all(bool(item.get("is_closed")) for item in rows),
                "candle_state": "CLOSED" if all(bool(item.get("is_closed")) for item in rows) else "OPEN_PARTIAL",
                "quality_flags": [],
            }
        )
        row["quality_flags"] = validate_candle(row)
        result.append(row)
    return result


class IntradayProvider(Protocol):
    def status(self) -> dict[str, Any]: ...

    def historical_candles(self, identity: InstrumentIdentity, interval: int, start: str, end: str, oi: bool = False) -> list[dict[str, Any]]: ...

    def quote(self, identities: list[InstrumentIdentity]) -> dict[str, Any]: ...

    def option_chain(self, underlying: InstrumentIdentity, expiry: str) -> dict[str, Any]: ...


class DhanIntradayProvider:
    """Dhan market-data seam; account credentials are never logged or returned."""

    def __init__(self, *, client_id: str | None = None, access_token: str | None = None, client: Any = None):
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN")
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.access_token)

    def status(self) -> dict[str, Any]:
        if not self.configured:
            state = "CREDENTIALS_UNAVAILABLE"
            entitlement = "UNVERIFIED"
        else:
            state = "AUTHORIZED_WITH_LIMITS"
            entitlement = "REQUIRES_PROVIDER_VALIDATION"
        return {
            "provider": PROVIDER_ID,
            "provider_version": "dhanhq-2.2.0",
            "source_authority": "OFFICIAL_DHAN_API",
            "authorization_state": state,
            "entitlement_state": entitlement,
            "historical": {"available_intervals": [1, 5, 15, 25, 60], "range": "PROVIDER_DOCUMENTED_LAST_5_YEARS_UNTESTED"},
            "live": {"available": "PROVIDER_DOCUMENTED_UNTESTED", "connection": "NOT_STARTED"},
            "options": {"available": "PROVIDER_DOCUMENTED_UNTESTED", "rate_limit": "ONE_UNIQUE_REQUEST_PER_3_SECONDS"},
            "limitations": [
                "Data API entitlement and account access are not verified in this runtime.",
                "No provider fallback to yfinance is permitted for governed intraday reads.",
            ],
        }

    def _require_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.configured:
            raise IntradaySourceError("CREDENTIALS_UNAVAILABLE")
        try:
            from dhanhq import dhanhq as DhanHQ
            self._client = DhanHQ(str(self.client_id), str(self.access_token))
            return self._client
        except Exception as exc:
            raise IntradaySourceError(f"SOURCE_UNAVAILABLE:{type(exc).__name__}") from exc

    def historical_candles(self, identity: InstrumentIdentity, interval: int, start: str, end: str, oi: bool = False) -> list[dict[str, Any]]:
        if interval not in SUPPORTED_INTERVALS:
            raise ValueError(f"unsupported interval: {interval}")
        payload = self._require_client().intraday_minute_data(
            identity.provider_security_id,
            identity.segment,
            identity.provider_instrument_type or identity.instrument_class,
            start,
            end,
            interval,
            oi,
        )
        if not isinstance(payload, dict):
            raise IntradaySourceError("MALFORMED_PROVIDER_RESPONSE")
        return normalize_dhan_candles(payload, identity, interval)

    def quote(self, identities: list[InstrumentIdentity]) -> dict[str, Any]:
        if not identities:
            return {"status": "EMPTY_REQUEST", "data": {}}
        securities: dict[str, list[str]] = {}
        for identity in identities[:1000]:
            securities.setdefault(identity.segment, []).append(identity.provider_security_id)
        payload = self._require_client().quote_data(securities)
        if not isinstance(payload, dict):
            raise IntradaySourceError("MALFORMED_PROVIDER_RESPONSE")
        return {"status": "AVAILABLE", "source": PROVIDER_ID, "data": payload}

    def option_chain(self, underlying: InstrumentIdentity, expiry: str) -> dict[str, Any]:
        payload = self._require_client().option_chain(int(underlying.provider_security_id), underlying.segment, expiry)
        if not isinstance(payload, dict):
            raise IntradaySourceError("MALFORMED_PROVIDER_RESPONSE")
        return {"status": "AVAILABLE", "source": PROVIDER_ID, "expiry": expiry, "data": payload}


def build_status(provider: IntradayProvider | None = None) -> dict[str, Any]:
    provider = provider or DhanIntradayProvider()
    provider_status = provider.status()
    configured = provider_status.get("authorization_state") not in {"CREDENTIALS_UNAVAILABLE", "SOURCE_UNAVAILABLE"}
    return {
        "contract_version": CONTRACT_VERSION,
        "instrument": {"state": "IDENTITY_REVIEW_REQUIRED", "provider_master": "Dhan official instrument list", "fuzzy_matching": False},
        "session": {"timezone": "Asia/Kolkata", "states": ["PRE_OPEN", "REGULAR_OPEN", "REGULAR_CLOSED", "POST_CLOSE", "HOLIDAY", "WEEKEND", "SPECIAL_SESSION", "UNKNOWN"]},
        "source": provider_status,
        "entitlement_state": provider_status.get("entitlement_state"),
        "data_status": {
            "state": "AVAILABLE_WITH_CONDITIONS" if configured else provider_status.get("authorization_state", "SOURCE_UNAVAILABLE"),
            "as_of": None,
            "source": [PROVIDER_ID],
            "last_successful_update": None,
            "limitations": provider_status.get("limitations", []),
        },
        "historical": {"supported_intervals": sorted(SUPPORTED_INTERVALS), "candles": [], "coverage": "NOT_VALIDATED"},
        "live": {"available": False, "connection": "NOT_CONFIGURED", "quote": None, "freshness": "UNKNOWN"},
        "derivatives": {"live_oi": "PROVIDER_DOCUMENTED_UNTESTED"},
        "options": {"chain_available": "PROVIDER_DOCUMENTED_UNTESTED", "snapshot": None},
        "quality": {"rules": ["OHLC", "volume", "OI", "duplicate", "ordering", "session", "identity"]},
        "provenance": {"owner": "FII-DII-Sector-Intelligence", "provider": PROVIDER_ID, "fallback": "NONE"},
        "limitations": ["This foundation contains no strategy, signal, recommendation, prediction or execution fields."],
    }


class IntradayParquetStore:
    """Small partitioned Parquet store with deterministic key de-duplication."""

    def __init__(self, root: Path = STORE_ROOT):
        self.root = Path(root)

    @staticmethod
    def _key(row: dict[str, Any]) -> tuple[str, int, str]:
        return (row["instrument_id"]["provider_security_id"], int(row["interval"]), row["bar_start"])

    def write(self, rows: list[dict[str, Any]]) -> int:
        grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for row in rows:
            flags = validate_candle(row)
            if flags:
                continue
            grouped.setdefault((row["trade_date"], int(row["interval"])), []).append(row)
        written = 0
        for (trade_date, interval), items in grouped.items():
            partition = self.root / f"date={trade_date}" / f"interval={interval}"
            partition.mkdir(parents=True, exist_ok=True)
            path = partition / "candles.parquet"
            existing: list[dict[str, Any]] = []
            if path.exists():
                existing = pd.read_parquet(path).to_dict(orient="records")
                for row in existing:
                    if isinstance(row.get("instrument_id"), str):
                        row["instrument_id"] = json.loads(row["instrument_id"])
                    if isinstance(row.get("quality_flags"), str):
                        row["quality_flags"] = json.loads(row["quality_flags"])
            merged = {self._key(row): row for row in [*existing, *items]}
            frame_rows: list[dict[str, Any]] = []
            for row in sorted(merged.values(), key=lambda item: self._key(item)):
                flat = dict(row)
                flat["instrument_id"] = json.dumps(flat["instrument_id"], sort_keys=True)
                flat["quality_flags"] = json.dumps(flat.get("quality_flags", []), sort_keys=True)
                frame_rows.append(flat)
            temp = path.with_suffix(".tmp.parquet")
            pd.DataFrame(frame_rows).to_parquet(temp, index=False)
            temp.replace(path)
            written += len(items)
        return written

    def read(self, provider_security_id: str, interval: int, start: str | None = None, end: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not self.root.exists():
            return rows
        for path in self.root.glob(f"date=*/interval={int(interval)}/candles.parquet"):
            frame = pd.read_parquet(path)
            for row in frame.to_dict(orient="records"):
                if json.loads(row["instrument_id"])["provider_security_id"] != provider_security_id:
                    continue
                if start and row["bar_start"] < start:
                    continue
                if end and row["bar_start"] >= end:
                    continue
                row["instrument_id"] = json.loads(row["instrument_id"])
                row["quality_flags"] = json.loads(row["quality_flags"])
                rows.append(row)
        return sorted(rows, key=lambda row: row["bar_start"])[-limit:]
