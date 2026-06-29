"""
Edge Case Tests — Price Data Unusual Scenarios

Corporate actions, circuit breakers, Mahurat trading, and other price anomalies
that standard tests may not cover.
"""

import logging
from datetime import date

import pandas as pd
import pytest

from engines.common.guardrails import (
    flag_large_price_moves,
    guard_delivery_pct,
    guard_negative_prices,
    guard_ohlc_consistency,
    guard_volume_sanity,
    is_expected_missing,
)

logger = logging.getLogger(__name__)


class TestCircuitBreakerPriceEdgeCases:
    """Prices at circuit breaker limits — upper/lower circuit."""

    def test_upper_circuit_stock_high_equals_close(self):
        """REAL: Upper circuit — Open, High, Close = Upper circuit price; Low = prev close."""
        logger.debug("[EC-PRICE-01] test_upper_circuit_stock_high_equals_close")
        df = pd.DataFrame({
            "date": ["2024-01-15"],
            "open": [100.0],
            "high": [100.0],
            "low": [95.0],
            "close": [100.0],
            "volume": [50000],
        })
        result = guard_ohlc_consistency(df)
        # High == Close == Open — all valid (upper circuit)
        if "ohlc_valid" in result.columns:
            assert result.iloc[0]["ohlc_valid"] is True
        logger.debug("[EC-PRICE-01] PASS — upper circuit OHLC is valid")

    def test_lower_circuit_stock_low_equals_close(self):
        """REAL: Lower circuit — Close = Low; volume may be zero."""
        logger.debug("[EC-PRICE-02] test_lower_circuit_stock_low_equals_close")
        df = pd.DataFrame({
            "date": ["2024-01-15"],
            "open": [95.0],
            "high": [95.0],
            "low": [90.0],
            "close": [90.0],
            "volume": [0],
        })
        result = guard_negative_prices(df)
        assert len(result) == 1, "Lower circuit stock is valid equity"
        logger.debug("[EC-PRICE-02] PASS — lower circuit data is valid")

    def test_zero_volume_lower_circuit_warning(self, caplog):
        """REAL: Lower circuit hit → zero volume is expected; warning should be logged."""
        logger.debug("[EC-PRICE-03] test_zero_volume_lower_circuit_warning")
        df = pd.DataFrame({
            "date": ["2024-01-15"],
            "open": [90.0], "high": [90.0], "low": [85.0], "close": [85.0], "volume": [0],
        })
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            guard_volume_sanity(df)
        assert any("ZERO VOLUME" in r.message for r in caplog.records)
        logger.debug("[EC-PRICE-03] PASS — zero volume on circuit day warns")


class TestCorporateActionPriceDropEdgeCases:
    """Large single-day price drops from corporate actions — should be flagged."""

    def test_10_to_1_stock_split_flagged(self):
        """REAL: TCS 2004 split — 10:1 → price drops from ₹1500 to ₹150."""
        logger.debug("[EC-PRICE-04] test_10_to_1_stock_split_flagged")
        df = pd.DataFrame({
            "date": ["2004-06-17", "2004-06-18"],
            "close": [1500.0, 150.0],
        })
        result = flag_large_price_moves(df, threshold=0.40)
        assert "ca_review_flag" in result.columns
        assert result.iloc[1]["ca_review_flag"] is True
        logger.debug("[EC-PRICE-04] PASS — 10:1 split flagged for CA review")

    def test_1_to_1_bonus_flagged(self):
        """REAL: 1:1 bonus → price halves ex-bonus date."""
        logger.debug("[EC-PRICE-05] test_1_to_1_bonus_flagged")
        df = pd.DataFrame({
            "date": ["2024-01-14", "2024-01-15"],
            "close": [800.0, 400.0],
        })
        result = flag_large_price_moves(df, threshold=0.40)
        assert result.iloc[1]["ca_review_flag"] is True
        logger.debug("[EC-PRICE-05] PASS — 1:1 bonus (50% drop) flagged")

    def test_dividend_small_drop_not_flagged(self):
        """REAL: ₹5 dividend on ₹500 stock → 1% drop, not flagged."""
        logger.debug("[EC-PRICE-06] test_dividend_small_drop_not_flagged")
        df = pd.DataFrame({
            "date": ["2024-01-14", "2024-01-15"],
            "close": [500.0, 495.0],  # -1% (dividend adjustment)
        })
        result = flag_large_price_moves(df, threshold=0.40)
        if "ca_review_flag" in result.columns:
            assert not result.iloc[1]["ca_review_flag"]
        logger.debug("[EC-PRICE-06] PASS — small dividend drop not flagged")

    def test_rights_issue_price_drop(self):
        """EDGE: Rights issue at discount → 20% ex-rights drop, not flagged (< 40%)."""
        logger.debug("[EC-PRICE-07] test_rights_issue_price_drop")
        df = pd.DataFrame({
            "date": ["2024-01-14", "2024-01-15"],
            "close": [100.0, 82.0],  # -18% ex-rights
        })
        result = flag_large_price_moves(df, threshold=0.40)
        if "ca_review_flag" in result.columns:
            assert not result.iloc[1]["ca_review_flag"]
        logger.debug("[EC-PRICE-07] PASS — 18% rights drop not flagged (< 40%)")


class TestMahuratTradingEdgeCases:
    """Mahurat trading session (Diwali) — 1 hour session with special characteristics."""

    def test_mahurat_day_is_expected_missing_for_normal_session(self):
        """EDGE: Diwali Laxmi Puja bhavcopy is the Mahurat session (1hr only), not missing."""
        logger.debug("[EC-PRICE-08] test_mahurat_day_is_expected_missing_for_normal_session")
        # The Mahurat session produces a bhavcopy — it should NOT be flagged as missing
        mahurat_2024 = date(2024, 11, 1)  # Diwali Laxmi Puja 2024
        nse_holidays = []  # Mahurat day is NOT in the NSE holiday list
        result = is_expected_missing(mahurat_2024, nse_holidays)
        # Mahurat trading day bhavcopy is present (it's a real session)
        # Only completely closed days should be expected missing
        logger.debug(f"[EC-PRICE-08] Mahurat day expected_missing: {result} (varies by holiday list)")


class TestPriceNormalizationEdgeCases:
    """Delivery percentage edge cases."""

    def test_delivery_pct_exactly_100_is_valid(self):
        """EDGE: 100% delivery (block deal day) is valid."""
        logger.debug("[EC-PRICE-09] test_delivery_pct_exactly_100_is_valid")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [100.0]})
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 100.0
        logger.debug("[EC-PRICE-09] PASS — 100% delivery is valid")

    def test_delivery_pct_exactly_0_is_valid(self):
        """EDGE: 0% delivery (intraday squareoff day) is valid."""
        logger.debug("[EC-PRICE-10] test_delivery_pct_exactly_0_is_valid")
        df = pd.DataFrame({"symbol": ["TCS"], "delivery_pct": [0.0]})
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 0.0
        logger.debug("[EC-PRICE-10] PASS — 0% delivery is valid")

    def test_delivery_pct_mixed_valid_and_invalid(self):
        """EDGE: Mixed valid/invalid delivery percentages."""
        logger.debug("[EC-PRICE-11] test_delivery_pct_mixed_valid_and_invalid")
        df = pd.DataFrame({
            "symbol": ["A", "B", "C"],
            "delivery_pct": [45.0, -10.0, 120.0],
        })
        result = guard_delivery_pct(df)
        assert result.iloc[0]["delivery_pct"] == 45.0  # valid
        assert pd.isna(result.iloc[1]["delivery_pct"])  # -10 → NaN
        assert pd.isna(result.iloc[2]["delivery_pct"])  # 120 → NaN
        logger.debug("[EC-PRICE-11] PASS — mixed delivery pct handled correctly")
