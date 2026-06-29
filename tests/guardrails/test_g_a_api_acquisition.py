"""
Guardrail Tests — Section 2: API / Acquisition (G-A-01 to G-A-06)
"""

import logging
import time
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest
import pytz

from engines.common.guardrails import (
    check_data_freshness,
    fetch_with_retry,
    is_market_hours,
    save_recovery_queue,
)

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


class TestFetchWithRetry:
    """G-A-02: Retry with exponential backoff on API failures."""

    def test_success_on_first_attempt(self):
        """HAPPY PATH: Function succeeds on first attempt — no retry needed."""
        logger.debug("[G-A-02] test_success_on_first_attempt")
        mock_fn = MagicMock(return_value={"data": "ok"})
        result = fetch_with_retry(mock_fn, "arg1", max_retries=3, base_delay=0.01)
        assert result == {"data": "ok"}
        assert mock_fn.call_count == 1
        logger.debug("[G-A-02] PASS — succeeded first try")

    def test_success_on_second_attempt(self):
        """RETRY: First attempt fails, second succeeds."""
        logger.debug("[G-A-02] test_success_on_second_attempt")
        mock_fn = MagicMock(side_effect=[RuntimeError("timeout"), {"data": "ok"}])
        result = fetch_with_retry(mock_fn, max_retries=3, base_delay=0.01)
        assert result == {"data": "ok"}
        assert mock_fn.call_count == 2
        logger.debug("[G-A-02] PASS — succeeded on attempt 2")

    def test_all_retries_exhausted_raises(self):
        """GUARD: All retries fail → RuntimeError raised."""
        logger.debug("[G-A-02] test_all_retries_exhausted_raises")
        mock_fn = MagicMock(side_effect=RuntimeError("server error"))
        with pytest.raises(RuntimeError, match="attempts failed"):
            fetch_with_retry(mock_fn, max_retries=3, base_delay=0.01)
        assert mock_fn.call_count == 3
        logger.debug("[G-A-02] PASS — RuntimeError after 3 exhausted retries")

    def test_exponential_backoff_delay(self):
        """G-A-02: Delay doubles on each retry (mocked sleep to verify)."""
        logger.debug("[G-A-02] test_exponential_backoff_delay")
        mock_fn = MagicMock(side_effect=[Exception("fail1"), Exception("fail2"), "ok"])
        delays = []
        original_sleep = time.sleep
        with patch("time.sleep", side_effect=lambda s: delays.append(s)):
            result = fetch_with_retry(mock_fn, max_retries=3, base_delay=1.0)
        assert result == "ok"
        assert len(delays) == 2
        assert delays[0] == 1.0, f"First retry delay should be 1.0s, got {delays[0]}"
        assert delays[1] == 2.0, f"Second retry delay should be 2.0s, got {delays[1]}"
        logger.debug(f"[G-A-02] PASS — delays: {delays}")


class TestSaveRecoveryQueue:
    """G-A-03: Failed downloads persist to recovery queue CSV."""

    def test_creates_recovery_queue(self, tmp_dir):
        """HAPPY PATH: Recovery queue created with failed items."""
        logger.debug("[G-A-03] test_creates_recovery_queue")
        queue = tmp_dir / "recovery_queue.csv"
        save_recovery_queue(["2024-01-10", "2024-01-11"], queue)
        assert queue.exists()
        df = pd.read_csv(queue)
        assert len(df) == 2
        assert set(df["item"]) == {"2024-01-10", "2024-01-11"}
        logger.debug("[G-A-03] PASS — queue created with 2 items")

    def test_appends_to_existing_queue(self, tmp_dir):
        """G-A-03: Subsequent failures append to (not overwrite) existing queue."""
        logger.debug("[G-A-03] test_appends_to_existing_queue")
        queue = tmp_dir / "recovery_queue.csv"
        save_recovery_queue(["2024-01-10"], queue)
        save_recovery_queue(["2024-01-11"], queue)
        df = pd.read_csv(queue)
        assert len(df) == 2
        logger.debug("[G-A-03] PASS — queue correctly appended")

    def test_empty_failed_list_no_write(self, tmp_dir):
        """EDGE: Empty failure list does not create or modify queue file."""
        logger.debug("[G-A-03] test_empty_failed_list_no_write")
        queue = tmp_dir / "recovery_queue.csv"
        save_recovery_queue([], queue)
        assert not queue.exists(), "Queue should not be created for empty failure list"
        logger.debug("[G-A-03] PASS — no file created for empty list")


class TestIsMarketHours:
    """G-A-04: Detect NSE market hours (09:15–15:30 IST, weekdays only)."""

    def test_during_market_hours_is_true(self):
        """Mocked time: 10:30 IST Monday → market is open."""
        logger.debug("[G-A-04] test_during_market_hours_is_true")
        with patch("engines.common.guardrails.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.weekday.return_value = 0  # Monday
            mock_now.replace.side_effect = lambda **kw: MagicMock(
                __le__=lambda s, o: True,
                __ge__=lambda s, o: True,
            )
            mock_now.hour = 10
            mock_now.minute = 30
            # Build a time that satisfies the market_open <= now <= market_close condition
            mock_dt.now.return_value = MagicMock(
                weekday=lambda: 0,
                replace=lambda **kw: datetime(2024, 1, 15, kw.get("hour", 10),
                                              kw.get("minute", 0), tzinfo=IST),
                hour=10, minute=30,
            )
            # Use direct datetime construction instead
        # Real test using actual IST datetime mocking
        fake_now = IST.localize(datetime(2024, 1, 15, 10, 30, 0))  # Monday 10:30 IST
        with patch("engines.common.guardrails.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            result = is_market_hours()
        assert result is True
        logger.debug("[G-A-04] PASS — market open at 10:30 Mon IST")

    def test_after_market_close_is_false(self):
        """Mocked time: 17:00 IST weekday → market is closed."""
        logger.debug("[G-A-04] test_after_market_close_is_false")
        fake_now = IST.localize(datetime(2024, 1, 15, 17, 0, 0))
        with patch("engines.common.guardrails.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            result = is_market_hours()
        assert result is False
        logger.debug("[G-A-04] PASS — market closed at 17:00 IST")

    def test_weekend_is_not_market_hours(self):
        """Mocked time: Saturday 10:30 IST → market is closed (weekend)."""
        logger.debug("[G-A-04] test_weekend_is_not_market_hours")
        fake_now = IST.localize(datetime(2024, 1, 20, 10, 30, 0))  # Saturday
        with patch("engines.common.guardrails.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            result = is_market_hours()
        assert result is False
        logger.debug("[G-A-04] PASS — Saturday correctly returns False")

    def test_before_market_open_is_false(self):
        """Mocked time: 09:00 IST weekday → before market open."""
        logger.debug("[G-A-04] test_before_market_open_is_false")
        fake_now = IST.localize(datetime(2024, 1, 15, 9, 0, 0))
        with patch("engines.common.guardrails.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            result = is_market_hours()
        assert result is False
        logger.debug("[G-A-04] PASS — before 09:15 correctly returns False")


class TestCheckDataFreshness:
    """G-A-05: Detect stale data (>5 trading days lag)."""

    def test_fresh_data_within_lag(self):
        """HAPPY PATH: 3 trading days lag → data is fresh."""
        logger.debug("[G-A-05] test_fresh_data_within_lag")
        result = check_data_freshness("2024-01-10", trading_days_since=3, max_lag=5)
        assert result is True
        logger.debug("[G-A-05] PASS — 3 days lag is fresh")

    def test_stale_data_exceeds_lag(self):
        """GUARD: 8 trading days lag → data is stale."""
        logger.debug("[G-A-05] test_stale_data_exceeds_lag")
        result = check_data_freshness("2024-01-01", trading_days_since=8, max_lag=5)
        assert result is False
        logger.debug("[G-A-05] PASS — 8 days lag is stale")

    def test_exactly_at_lag_boundary_is_fresh(self):
        """EDGE: Exactly at max_lag (5 days) → still fresh."""
        logger.debug("[G-A-05] test_exactly_at_lag_boundary_is_fresh")
        result = check_data_freshness("2024-01-08", trading_days_since=5, max_lag=5)
        assert result is True
        logger.debug("[G-A-05] PASS — boundary case: 5 days is still fresh")

    def test_one_over_lag_is_stale(self):
        """EDGE: One day over max_lag → stale."""
        logger.debug("[G-A-05] test_one_over_lag_is_stale")
        result = check_data_freshness("2024-01-07", trading_days_since=6, max_lag=5)
        assert result is False
        logger.debug("[G-A-05] PASS — 6 days lag is stale")

    def test_custom_max_lag(self):
        """CONFIG: Custom max_lag=10 — 8 days should be fresh."""
        logger.debug("[G-A-05] test_custom_max_lag")
        result = check_data_freshness("2024-01-01", trading_days_since=8, max_lag=10)
        assert result is True
        logger.debug("[G-A-05] PASS — custom lag respected")
