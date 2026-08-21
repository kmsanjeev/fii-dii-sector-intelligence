from __future__ import annotations

from datetime import datetime

from backend.services.intraday_foundation import (
    DhanIntradayProvider,
    InstrumentIdentity,
    IntradayParquetStore,
    aggregate_candles,
    build_status,
    normalize_dhan_candles,
    session_state,
    validate_candle,
)
from engines.providers.dhan_auth import DhanAuthManager


def _identity() -> InstrumentIdentity:
    return InstrumentIdentity(
        provider_security_id="1333",
        exchange="NSE",
        segment="NSE_EQ",
        instrument_class="EQUITY",
        symbol="RELIANCE",
        isin="INE002A01018",
        mapping_version="fixture-2026-08-20",
    )


def test_session_semantics_are_timezone_aware_and_bounded() -> None:
    assert session_state(datetime(2026, 8, 20, 9, 5, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata"))) == "PRE_OPEN"
    assert session_state(datetime(2026, 8, 20, 10, 0, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata"))) == "REGULAR_OPEN"
    assert session_state(datetime(2026, 8, 22, 10, 0, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata"))) == "WEEKEND"


def test_identity_preserves_provider_instrument_type() -> None:
    from backend.services.intraday_foundation import identity_from_provider_row

    identity = identity_from_provider_row(
        {
            "security_id": "9001",
            "exchange_segment": "NSE_FNO",
            "symbol": "NIFTY",
            "instrument": "FUTIDX",
            "expiry": "2026-09-24",
        }
    )
    assert identity.instrument_class == "FUTURE"
    assert identity.provider_instrument_type == "FUTIDX"


def test_dhan_parallel_arrays_normalize_without_zeroing_missing_values() -> None:
    rows = normalize_dhan_candles(
        {
            "timestamp": [1787213700, 1787213760],
            "open": [100, 101],
            "high": [102, 103],
            "low": [99, 100],
            "close": [101, 102],
            "volume": [10, 20],
            "oi": [],
        },
        _identity(),
        1,
        retrieved_at=datetime(2026, 8, 20, 14, 0, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata")),
    )
    assert len(rows) == 2
    assert rows[0]["timezone"] == "Asia/Kolkata"
    assert rows[0]["open_interest"] is None
    assert rows[0]["is_closed"] is True
    assert rows[0]["quality_flags"] == []


def test_aggregation_uses_last_oi_and_never_sums_it() -> None:
    raw = normalize_dhan_candles(
        {
            "timestamp": [1787213700, 1787213760, 1787213820, 1787213880, 1787213940],
            "open": [100, 101, 102, 101, 103],
            "high": [101, 103, 104, 104, 105],
            "low": [99, 100, 101, 100, 102],
            "close": [101, 102, 103, 103, 104],
            "volume": [10, 20, 30, 40, 50],
            "oi": [100, 101, 102, 103, 104],
        },
        _identity(),
        1,
        retrieved_at=datetime(2026, 8, 20, 14, 0, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata")),
    )
    bars = aggregate_candles(raw, 5)
    assert len(bars) == 1
    assert bars[0]["open"] == 100
    assert bars[0]["close"] == 104
    assert bars[0]["volume"] == 150
    assert bars[0]["open_interest"] == 104


def test_quality_rejects_invalid_ohlc_and_negative_values() -> None:
    assert "INVALID_OHLC" in validate_candle(
        {"instrument_id": _identity().as_dict(), "interval": 1, "bar_start": "x", "open": 10, "high": 5, "low": 9, "close": 10}
    )
    assert "NEGATIVE_VOLUME" in validate_candle(
        {"instrument_id": _identity().as_dict(), "interval": 1, "bar_start": "x", "open": 10, "high": 11, "low": 9, "close": 10, "volume": -1}
    )


def test_store_is_idempotent_and_deduplicates(tmp_path) -> None:
    rows = normalize_dhan_candles(
        {"timestamp": [1787213700], "open": [100], "high": [101], "low": [99], "close": [100], "volume": [10]},
        _identity(),
        1,
        retrieved_at=datetime(2026, 8, 20, 14, 0, tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Kolkata")),
    )
    store = IntradayParquetStore(tmp_path / "candles")
    assert store.write(rows) == 1
    assert store.write(rows) == 1
    assert len(store.read("1333", 1)) == 1


def test_missing_credentials_are_explicit_and_do_not_fallback(monkeypatch) -> None:
    class EmptyStore:
        def get(self, name):
            return None

    monkeypatch.setattr(DhanAuthManager, "has_credentials", lambda self: False)
    monkeypatch.delenv("DHAN_CLIENT_ID", raising=False)
    monkeypatch.delenv("DHAN_ACCESS_TOKEN", raising=False)
    status = build_status(DhanIntradayProvider(auth_manager=DhanAuthManager(store=EmptyStore())))
    assert status["source"]["authorization_state"] == "CREDENTIALS_UNAVAILABLE"
    assert status["data_status"]["state"] == "CREDENTIALS_UNAVAILABLE"
    assert "yfinance" in " ".join(status["source"]["limitations"])
