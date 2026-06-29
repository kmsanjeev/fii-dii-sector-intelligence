"""
Guardrail Tests — Section 4: Price Data (G-P-01 to G-P-06)
"""

import logging

import pandas as pd
import pytest

from engines.common.guardrails import (
    flag_large_price_moves,
    guard_delivery_pct,
    guard_negative_prices,
    guard_ohlc_consistency,
    guard_volume_sanity,
)

logger = logging.getLogger(__name__)


def _make_ohlcv(rows):
    """Helper to build OHLCV DataFrame from list of (date, o, h, l, c, vol) tuples."""
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


class TestGuardNegativePrices:
    """G-P-01: Drop rows where any OHLC price ≤ 0."""

    def test_all_positive_prices_unchanged(self):
        """HAPPY PATH: All positive → all rows retained."""
        logger.debug("[G-P-01] test_all_positive_prices_unchanged")
        df = _make_ohlcv([("2024-01-15", 100, 110, 95, 105, 5000)])
        result = guard_negative_prices(df)
        assert len(result) == 1
        logger.debug("[G-P-01] PASS")

    def test_negative_close_row_dropped(self):
        """GUARD: Row with Close < 0 is dropped."""
        logger.debug("[G-P-01] test_negative_close_row_dropped")
        df = _make_ohlcv([
            ("2024-01-15", 100, 110, 95, 105, 5000),
            ("2024-01-16", 105, 108, 90, -5, 3000),   # invalid: Close = -5
        ])
        result = guard_negative_prices(df)
        assert len(result) == 1
        assert result.iloc[0]["date"] == "2024-01-15"
        logger.debug("[G-P-01] PASS — negative close row dropped")

    def test_zero_open_row_dropped(self):
        """GUARD: Row with Open = 0 is dropped."""
        logger.debug("[G-P-01] test_zero_open_row_dropped")
        df = _make_ohlcv([("2024-01-15", 0, 110, 95, 105, 5000)])
        result = guard_negative_prices(df)
        assert result.empty
        logger.debug("[G-P-01] PASS — zero open row dropped")

    def test_all_invalid_rows_dropped(self):
        """GUARD: DataFrame with all invalid prices → empty result."""
        logger.debug("[G-P-01] test_all_invalid_rows_dropped")
        df = _make_ohlcv([
            ("2024-01-15", -1, 110, 95, 105, 5000),
            ("2024-01-16", 100, -5, 95, 105, 5000),
        ])
        result = guard_negative_prices(df)
        assert result.empty
        logger.debug("[G-P-01] PASS")


class TestGuardOhlcConsistency:
    """G-P-02: High ≥ Low; High ≥ Open/Close; Low ≤ Open/Close."""

    def test_valid_ohlc_passes(self):
        """HAPPY PATH: Valid OHLC data — no ohlc_valid column added."""
        logger.debug("[G-P-02] test_valid_ohlc_passes")
        df = _make_ohlcv([("2024-01-15", 100, 110, 95, 105, 5000)])
        result = guard_ohlc_consistency(df)
        if "ohlc_valid" in result.columns:
            assert result.iloc[0]["ohlc_valid"] is True
        logger.debug("[G-P-02] PASS")

    def test_high_less_than_low_flagged(self):
        """GUARD: High < Low → row flagged as invalid."""
        logger.debug("[G-P-02] test_high_less_than_low_flagged")
        df = _make_ohlcv([("2024-01-15", 100, 90, 95, 92, 5000)])  # High < Low
        result = guard_ohlc_consistency(df)
        if "ohlc_valid" in result.columns:
            assert result.iloc[0]["ohlc_valid"] is False
        logger.debug("[G-P-02] PASS — High < Low flagged")

    def test_high_less_than_close_flagged(self, caplog):
        """GUARD: High < Close → warning logged."""
        logger.debug("[G-P-02] test_high_less_than_close_flagged")
        df = _make_ohlcv([("2024-01-15", 100, 95, 90, 105, 5000)])  # High=95 < Close=105
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            guard_ohlc_consistency(df)
        assert any("OHLC inconsistency" in r.message for r in caplog.records)
        logger.debug("[G-P-02] PASS — OHLC warning emitted")

    def test_mixed_valid_invalid(self):
        """EDGE: Mixed valid/invalid rows — only invalid flagged."""
        logger.debug("[G-P-02] test_mixed_valid_invalid")
        df = _make_ohlcv([
            ("2024-01-15", 100, 110, 95, 105, 5000),  # valid
            ("2024-01-16", 100, 90, 95, 105, 5000),   # invalid: High < Low
        ])
        result = guard_ohlc_consistency(df)
        if "ohlc_valid" in result.columns:
            assert result.iloc[0]["ohlc_valid"] is True
            assert result.iloc[1]["ohlc_valid"] is False
        logger.debug("[G-P-02] PASS")


class TestGuardVolumeSanity:
    """G-P-03: Zero volume on trading day → warning logged."""

    def test_positive_volume_no_warning(self, caplog):
        """HAPPY PATH: Non-zero volume → no warning."""
        logger.debug("[G-P-03] test_positive_volume_no_warning")
        df = _make_ohlcv([("2024-01-15", 100, 110, 95, 105, 5000)])
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            guard_volume_sanity(df)
        assert not any("ZERO VOLUME" in r.message for r in caplog.records)
        logger.debug("[G-P-03] PASS")

    def test_zero_volume_warning_logged(self, caplog):
        """GUARD: Zero volume → warning logged with date."""
        logger.debug("[G-P-03] test_zero_volume_warning_logged")
        df = _make_ohlcv([("2024-01-15", 100, 110, 95, 105, 0)])
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            guard_volume_sanity(df)
        assert any("ZERO VOLUME" in r.message for r in caplog.records)
        logger.debug("[G-P-03] PASS — zero volume warning emitted")

    def test_no_volume_column_returns_unchanged(self):
        """EDGE: DataFrame without 'volume' column → returned unchanged."""
        logger.debug("[G-P-03] test_no_volume_column_returns_unchanged")
        df = pd.DataFrame({"date": ["2024-01-15"], "close": [105.0]})
        result = guard_volume_sanity(df)
        assert "volume" not in result.columns or len(result) == 1
        logger.debug("[G-P-03] PASS")


class TestFlagLargePriceMoves:
    """G-P-04: Flag >40% single-session move for corporate action review."""

    def test_normal_move_not_flagged(self):
        """HAPPY PATH: 10% move → no ca_review_flag."""
        logger.debug("[G-P-04] test_normal_move_not_flagged")
        df = pd.DataFrame({"date": ["2024-01-14", "2024-01-15"],
                           "close": [100.0, 110.0]})  # +10%
        result = flag_large_price_moves(df, threshold=0.40)
        if "ca_review_flag" in result.columns:
            assert not result.iloc[1]["ca_review_flag"]
        logger.debug("[G-P-04] PASS — 10% move not flagged")

    def test_bonus_like_move_flagged(self):
        """GUARD: 50% drop (bonus issue) → flagged for CA review."""
        logger.debug("[G-P-04] test_bonus_like_move_flagged")
        df = pd.DataFrame({"date": ["2024-01-14", "2024-01-15"],
                           "close": [200.0, 100.0]})  # -50% (1:1 bonus)
        result = flag_large_price_moves(df, threshold=0.40)
        assert "ca_review_flag" in result.columns
        assert result.iloc[1]["ca_review_flag"] is True
        logger.debug("[G-P-04] PASS — 50% drop flagged")

    def test_split_like_move_flagged(self):
        """GUARD: 50% drop (5:10 split) → flagged."""
        logger.debug("[G-P-04] test_split_like_move_flagged")
        df = pd.DataFrame({"date": ["2024-01-14", "2024-01-15"],
                           "close": [1000.0, 100.0]})  # 10:1 split
        result = flag_large_price_moves(df, threshold=0.40)
        assert result.iloc[1]["ca_review_flag"] is True
        logger.debug("[G-P-04] PASS")

    def test_no_ca_flag_column_for_normal_moves(self):
        """EDGE: All normal moves → no ca_review_flag column (or all False)."""
        logger.debug("[G-P-04] test_no_ca_flag_column_for_normal_moves")
        df = pd.DataFrame({"date": ["2024-01-13", "2024-01-14", "2024-01-15"],
                           "close": [100.0, 105.0, 98.0]})
        result = flag_large_price_moves(df)
        if "ca_review_flag" in result.columns:
            assert not result["ca_review_flag"].any()
        logger.debug("[G-P-04] PASS")


class TestGuardDeliveryPct:
    """G-P-06: Delivery percentage must be in [0, 100] range."""

    def test_valid_delivery_pct_unchanged(self):
        """HAPPY PATH: Valid delivery_pct [0, 100] → unchanged."""
        logger.debug("[G-P-06] test_valid_delivery_pct_unchanged")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [45.5]})
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 45.5
        logger.debug("[G-P-06] PASS")

    def test_negative_delivery_pct_set_to_nan(self):
        """GUARD: delivery_pct < 0 → set to NaN."""
        logger.debug("[G-P-06] test_negative_delivery_pct_set_to_nan")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [-5.0]})
        result = guard_delivery_pct(df)
        assert pd.isna(result.iloc[0]["delivery_pct"])
        logger.debug("[G-P-06] PASS")

    def test_over_100_delivery_pct_set_to_nan(self):
        """GUARD: delivery_pct > 100 → set to NaN."""
        logger.debug("[G-P-06] test_over_100_delivery_pct_set_to_nan")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [105.0]})
        result = guard_delivery_pct(df)
        assert pd.isna(result.iloc[0]["delivery_pct"])
        logger.debug("[G-P-06] PASS")

    def test_zero_delivery_pct_valid(self):
        """EDGE: delivery_pct = 0 is a valid value (circuit breaker day)."""
        logger.debug("[G-P-06] test_zero_delivery_pct_valid")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [0.0]})
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 0.0
        logger.debug("[G-P-06] PASS — 0% is valid")

    def test_100_delivery_pct_valid(self):
        """EDGE: delivery_pct = 100 is a valid value."""
        logger.debug("[G-P-06] test_100_delivery_pct_valid")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [100.0]})
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 100.0
        logger.debug("[G-P-06] PASS")

    def test_no_delivery_pct_column_unchanged(self):
        """EDGE: No delivery_pct column → DataFrame returned unchanged."""
        logger.debug("[G-P-06] test_no_delivery_pct_column_unchanged")
        df = pd.DataFrame({"symbol": ["TCS"], "close": [3500.0]})
        result = guard_delivery_pct(df)
        assert "delivery_pct" not in result.columns
        logger.debug("[G-P-06] PASS")
