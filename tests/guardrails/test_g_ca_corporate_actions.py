"""
Guardrail Tests — Section 6: Corporate Actions (G-CA-01 to G-CA-04)
"""

import logging
from pathlib import Path

import pytest

from engines.common.guardrails import (
    log_corporate_action,
    validate_dividend,
    validate_split_ratio,
)

logger = logging.getLogger(__name__)


class TestValidateSplitRatio:
    """G-CA-02: Split ratio must be > 0 and ≠ 1.0."""

    def test_valid_2to1_split(self):
        """HAPPY PATH: 2:1 split ratio → valid."""
        logger.debug("[G-CA-02] test_valid_2to1_split")
        validate_split_ratio(2.0, symbol="TCS")  # must not raise
        logger.debug("[G-CA-02] PASS — 2.0 ratio is valid")

    def test_valid_5to1_split(self):
        """HAPPY PATH: 5:1 split ratio → valid."""
        logger.debug("[G-CA-02] test_valid_5to1_split")
        validate_split_ratio(5.0, symbol="RELIANCE")
        logger.debug("[G-CA-02] PASS")

    def test_valid_fractional_split(self):
        """HAPPY PATH: 0.5 ratio (2-for-1 reverse split direction) → valid."""
        logger.debug("[G-CA-02] test_valid_fractional_split")
        validate_split_ratio(0.5, symbol="TCS")
        logger.debug("[G-CA-02] PASS — 0.5 ratio valid")

    def test_ratio_zero_raises(self):
        """GUARD: Ratio = 0 → raises ValueError."""
        logger.debug("[G-CA-02] test_ratio_zero_raises")
        with pytest.raises(ValueError, match="Invalid split ratio"):
            validate_split_ratio(0.0, symbol="TCS")
        logger.debug("[G-CA-02] PASS — ratio=0 raises ValueError")

    def test_ratio_one_raises(self):
        """GUARD: Ratio = 1.0 (no-op split) → raises ValueError."""
        logger.debug("[G-CA-02] test_ratio_one_raises")
        with pytest.raises(ValueError, match="Invalid split ratio"):
            validate_split_ratio(1.0, symbol="TCS")
        logger.debug("[G-CA-02] PASS — ratio=1.0 raises ValueError")

    def test_negative_ratio_raises(self):
        """GUARD: Negative ratio → raises ValueError."""
        logger.debug("[G-CA-02] test_negative_ratio_raises")
        with pytest.raises(ValueError, match="Invalid split ratio"):
            validate_split_ratio(-2.0, symbol="TCS")
        logger.debug("[G-CA-02] PASS — negative ratio raises ValueError")


class TestValidateDividend:
    """G-CA-03: Dividend > 50% of stock price → flagged as extraordinary."""

    def test_ordinary_dividend_passes(self):
        """HAPPY PATH: Small dividend relative to price → ordinary, returns True."""
        logger.debug("[G-CA-03] test_ordinary_dividend_passes")
        result = validate_dividend(amount=5.0, price=500.0, symbol="TCS")
        assert result is True
        logger.debug("[G-CA-03] PASS — ordinary dividend (1% of price)")

    def test_extraordinary_dividend_flagged(self, caplog):
        """GUARD: Dividend = 60% of price → extraordinary, returns False + warning."""
        logger.debug("[G-CA-03] test_extraordinary_dividend_flagged")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            result = validate_dividend(amount=60.0, price=100.0, symbol="TESTCO")
        assert result is False
        assert any("EXTRAORDINARY DIVIDEND" in r.message for r in caplog.records)
        logger.debug("[G-CA-03] PASS — extraordinary dividend flagged")

    def test_exactly_at_50pct_boundary(self):
        """EDGE: Dividend exactly = 50% of price → ordinary (boundary is exclusive)."""
        logger.debug("[G-CA-03] test_exactly_at_50pct_boundary")
        result = validate_dividend(amount=50.0, price=100.0, symbol="TESTCO")
        assert result is True  # 50 > 50? No, so it's ordinary
        logger.debug("[G-CA-03] PASS — boundary case: 50% is ordinary")

    def test_one_over_50pct_is_extraordinary(self):
        """EDGE: Dividend = 50.01% of price → extraordinary."""
        logger.debug("[G-CA-03] test_one_over_50pct_is_extraordinary")
        result = validate_dividend(amount=50.01, price=100.0, symbol="TESTCO")
        assert result is False
        logger.debug("[G-CA-03] PASS")

    def test_high_yield_stock_dividend(self):
        """REAL: Dividend of ₹20 on ₹200 stock (10%) → ordinary."""
        logger.debug("[G-CA-03] test_high_yield_stock_dividend")
        result = validate_dividend(amount=20.0, price=200.0, symbol="COALINDIA")
        assert result is True
        logger.debug("[G-CA-03] PASS")


class TestLogCorporateAction:
    """G-CA-04: Every CA event logged to ca_events.log with required fields."""

    def test_ca_event_log_created(self, tmp_dir):
        """HAPPY PATH: CA event creates log file with all required fields."""
        logger.debug("[G-CA-04] test_ca_event_log_created")
        log_path = tmp_dir / "ca_events.log"
        log_corporate_action(
            symbol="TCS",
            ca_type="SPLIT",
            ex_date="2024-01-15",
            detail="ratio=5:1",
            detected_by="nse_corporate_actions_engine",
            log_path=log_path,
        )
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "TCS" in content
        assert "SPLIT" in content
        assert "2024-01-15" in content
        assert "ratio=5:1" in content
        assert "nse_corporate_actions_engine" in content
        logger.debug(f"[G-CA-04] PASS — log created: {log_path}")

    def test_multiple_events_appended(self, tmp_dir):
        """G-CA-04: Multiple CA events append to same log file."""
        logger.debug("[G-CA-04] test_multiple_events_appended")
        log_path = tmp_dir / "ca_events.log"
        log_corporate_action("TCS", "SPLIT", "2024-01-15", "5:1", "engine", log_path)
        log_corporate_action("INFY", "BONUS", "2024-02-20", "1:1", "engine", log_path)
        log_corporate_action("RELIANCE", "DIVIDEND", "2024-03-10", "₹10/share", "engine", log_path)
        content = log_path.read_text(encoding="utf-8")
        assert content.count("\n") == 3
        logger.debug("[G-CA-04] PASS — 3 events in log file")

    def test_log_creates_parent_dir(self, tmp_dir):
        """EDGE: Parent directory created if absent."""
        logger.debug("[G-CA-04] test_log_creates_parent_dir")
        log_path = tmp_dir / "nested" / "ca_events.log"
        log_corporate_action("TCS", "SPLIT", "2024-01-15", "5:1", "engine", log_path)
        assert log_path.exists()
        logger.debug("[G-CA-04] PASS — parent dir created")

    def test_different_ca_types_all_logged(self, tmp_dir):
        """G-CA-04: All CA types are correctly logged."""
        logger.debug("[G-CA-04] test_different_ca_types_all_logged")
        log_path = tmp_dir / "ca_events.log"
        for ca_type in ["SPLIT", "BONUS", "DIVIDEND", "RIGHTS_ISSUE", "BUYBACK"]:
            log_corporate_action("SYM", ca_type, "2024-01-15", "detail", "engine", log_path)
        content = log_path.read_text(encoding="utf-8")
        for ca_type in ["SPLIT", "BONUS", "DIVIDEND", "RIGHTS_ISSUE", "BUYBACK"]:
            assert ca_type in content, f"CA type {ca_type} not found in log"
        logger.debug("[G-CA-04] PASS — all CA types logged")
