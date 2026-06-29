"""
Guardrail Tests — Section 7: Intelligence Scoring (G-I-01 to G-I-05)
"""

import logging
from datetime import date

import pandas as pd
import pytest

from engines.common.guardrails import (
    check_data_coverage,
    check_min_sessions,
    check_score_staleness,
    enforce_score_range,
)

logger = logging.getLogger(__name__)


class TestCheckMinSessions:
    """G-I-01: At least 5 trading sessions required for reliable scoring."""

    def test_adequate_sessions_returns_true(self):
        """HAPPY PATH: 252 sessions → sufficient for scoring."""
        logger.debug("[G-I-01] test_adequate_sessions_returns_true")
        data = pd.DataFrame({"date": [f"2024-01-{i:02d}" for i in range(1, 253)]})
        result = check_min_sessions(data, symbol="TCS", min_sessions=5)
        assert result is True
        logger.debug("[G-I-01] PASS — 252 sessions is adequate")

    def test_exactly_5_sessions_passes(self):
        """EDGE: Exactly 5 sessions → boundary, passes."""
        logger.debug("[G-I-01] test_exactly_5_sessions_passes")
        data = pd.DataFrame({"date": [f"2024-01-{i:02d}" for i in range(1, 6)]})
        result = check_min_sessions(data, symbol="NEW_STOCK", min_sessions=5)
        assert result is True
        logger.debug("[G-I-01] PASS — exactly 5 sessions passes")

    def test_fewer_than_5_sessions_returns_false(self):
        """GUARD: 3 sessions → insufficient, returns False."""
        logger.debug("[G-I-01] test_fewer_than_5_sessions_returns_false")
        data = pd.DataFrame({"date": ["2024-01-15", "2024-01-16", "2024-01-17"]})
        result = check_min_sessions(data, symbol="RECENT_IPO", min_sessions=5)
        assert result is False
        logger.debug("[G-I-01] PASS — 3 sessions is insufficient")

    def test_zero_sessions_returns_false(self):
        """EDGE: Empty DataFrame → 0 sessions → False."""
        logger.debug("[G-I-01] test_zero_sessions_returns_false")
        data = pd.DataFrame({"date": []})
        result = check_min_sessions(data, symbol="GHOST", min_sessions=5)
        assert result is False
        logger.debug("[G-I-01] PASS — 0 sessions returns False")

    def test_4_sessions_insufficient(self):
        """EDGE: 4 sessions (one below boundary) → insufficient."""
        logger.debug("[G-I-01] test_4_sessions_insufficient")
        data = pd.DataFrame({"date": ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18"]})
        result = check_min_sessions(data, symbol="NEWCO", min_sessions=5)
        assert result is False
        logger.debug("[G-I-01] PASS — 4 sessions returns False")

    def test_recently_listed_ipo_blocked(self):
        """REAL CASE: IPO with 2 days trading history → scoring blocked."""
        logger.debug("[G-I-01] test_recently_listed_ipo_blocked")
        data = pd.DataFrame({"date": ["2024-06-25", "2024-06-26"]})
        result = check_min_sessions(data, symbol="SME_IPO", min_sessions=5)
        assert result is False
        logger.debug("[G-I-01] PASS — IPO with 2 days blocked")


class TestCheckDataCoverage:
    """G-I-02: Minimum 80% data coverage required to generate scores."""

    def test_full_coverage_passes(self):
        """HAPPY PATH: 252 actual / 252 expected → 100% coverage."""
        logger.debug("[G-I-02] test_full_coverage_passes")
        result = check_data_coverage(actual=252, expected=252, symbol="TCS", min_coverage=0.80)
        assert result is True
        logger.debug("[G-I-02] PASS")

    def test_exactly_80pct_passes(self):
        """EDGE: Exactly 80% coverage → passes (boundary inclusive)."""
        logger.debug("[G-I-02] test_exactly_80pct_passes")
        result = check_data_coverage(actual=80, expected=100, symbol="TCS", min_coverage=0.80)
        assert result is True
        logger.debug("[G-I-02] PASS — 80% boundary is inclusive")

    def test_79pct_coverage_fails(self):
        """GUARD: 79% coverage → below minimum → returns False."""
        logger.debug("[G-I-02] test_79pct_coverage_fails")
        result = check_data_coverage(actual=79, expected=100, symbol="TCS", min_coverage=0.80)
        assert result is False
        logger.debug("[G-I-02] PASS — 79% is below minimum")

    def test_partial_coverage_with_real_numbers(self):
        """REAL CASE: 198/252 trading days present → 78.6% coverage → insufficient."""
        logger.debug("[G-I-02] test_partial_coverage_with_real_numbers")
        result = check_data_coverage(actual=198, expected=252, symbol="TCS", min_coverage=0.80)
        assert result is False
        logger.debug(f"[G-I-02] PASS — 198/252 = {198/252:.1%} < 80%")

    def test_custom_coverage_threshold(self):
        """CONFIG: Custom 90% threshold → 85% fails."""
        logger.debug("[G-I-02] test_custom_coverage_threshold")
        result = check_data_coverage(actual=85, expected=100, symbol="TCS", min_coverage=0.90)
        assert result is False
        logger.debug("[G-I-02] PASS — 85% fails at 90% threshold")


class TestEnforceScoreRange:
    """G-I-03: Scores must be in declared range; clip or raise on out-of-range."""

    def test_scores_within_range_unchanged(self):
        """HAPPY PATH: All scores in [0, 100] → unchanged."""
        logger.debug("[G-I-03] test_scores_within_range_unchanged")
        df = pd.DataFrame({"symbol": ["TCS", "INFY"], "bull_run_score": [75.0, 45.0]})
        result = enforce_score_range(df, "bull_run_score", min_val=0, max_val=100)
        assert result["bull_run_score"].tolist() == [75.0, 45.0]
        logger.debug("[G-I-03] PASS")

    def test_score_above_max_clipped(self):
        """GUARD: Score > 100 → clipped to 100."""
        logger.debug("[G-I-03] test_score_above_max_clipped")
        df = pd.DataFrame({"symbol": ["TCS"], "bull_run_score": [115.0]})
        result = enforce_score_range(df, "bull_run_score", min_val=0, max_val=100)
        assert result["bull_run_score"].iloc[0] == 100.0
        logger.debug("[G-I-03] PASS — 115 clipped to 100")

    def test_score_below_min_clipped(self):
        """GUARD: Score < 0 → clipped to 0."""
        logger.debug("[G-I-03] test_score_below_min_clipped")
        df = pd.DataFrame({"symbol": ["TCS"], "bull_run_score": [-5.0]})
        result = enforce_score_range(df, "bull_run_score", min_val=0, max_val=100)
        assert result["bull_run_score"].iloc[0] == 0.0
        logger.debug("[G-I-03] PASS — -5 clipped to 0")

    def test_boundary_values_retained(self):
        """EDGE: Scores at exactly 0 and 100 are not clipped."""
        logger.debug("[G-I-03] test_boundary_values_retained")
        df = pd.DataFrame({"symbol": ["A", "B"], "score": [0.0, 100.0]})
        result = enforce_score_range(df, "score", min_val=0, max_val=100)
        assert result["score"].tolist() == [0.0, 100.0]
        logger.debug("[G-I-03] PASS — boundary values 0 and 100 retained")

    def test_mixed_valid_invalid_scores(self):
        """EDGE: Mixed valid/invalid scores → only out-of-range clipped."""
        logger.debug("[G-I-03] test_mixed_valid_invalid_scores")
        df = pd.DataFrame({"symbol": ["A", "B", "C", "D"],
                           "score": [-10.0, 50.0, 85.0, 120.0]})
        result = enforce_score_range(df, "score", min_val=0, max_val=100)
        assert result["score"].tolist() == [0.0, 50.0, 85.0, 100.0]
        logger.debug("[G-I-03] PASS — out-of-range values clipped, valid values unchanged")


class TestCheckScoreStaleness:
    """G-I-05: Score must not be based on data older than 5 trading days."""

    def test_fresh_data_returns_true(self):
        """HAPPY PATH: 2 day lag → data is fresh."""
        logger.debug("[G-I-05] test_fresh_data_returns_true")
        result = check_score_staleness(source_lag_days=2, max_lag=5)
        assert result is True
        logger.debug("[G-I-05] PASS")

    def test_stale_data_returns_false(self):
        """GUARD: 8 day lag → score is stale."""
        logger.debug("[G-I-05] test_stale_data_returns_false")
        result = check_score_staleness(source_lag_days=8, max_lag=5)
        assert result is False
        logger.debug("[G-I-05] PASS")

    def test_exactly_at_max_lag_is_fresh(self):
        """EDGE: lag == max_lag (5 days) → still fresh."""
        logger.debug("[G-I-05] test_exactly_at_max_lag_is_fresh")
        result = check_score_staleness(source_lag_days=5, max_lag=5)
        assert result is True
        logger.debug("[G-I-05] PASS — 5 days at boundary is fresh")

    def test_zero_lag_is_fresh(self):
        """EDGE: 0 day lag → real-time data, definitely fresh."""
        logger.debug("[G-I-05] test_zero_lag_is_fresh")
        result = check_score_staleness(source_lag_days=0, max_lag=5)
        assert result is True
        logger.debug("[G-I-05] PASS")
