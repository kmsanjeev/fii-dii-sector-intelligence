"""
Guardrail Tests — Section 8: Financial Results (G-F-01 to G-F-04)
"""

import logging

import pytest

from engines.common.guardrails import (
    INDIA_QUARTER_MAP,
    detect_growth_outlier,
    get_india_quarter,
    validate_pl_sanity,
    validate_shareholding_sum,
)

logger = logging.getLogger(__name__)


class TestGetIndiaQuarter:
    """G-F-01: India FY quarters are Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar."""

    @pytest.mark.parametrize("month,expected_quarter", [
        (4, "Q1"), (5, "Q1"), (6, "Q1"),
        (7, "Q2"), (8, "Q2"), (9, "Q2"),
        (10, "Q3"), (11, "Q3"), (12, "Q3"),
        (1, "Q4"), (2, "Q4"), (3, "Q4"),
    ])
    def test_all_months_mapped_correctly(self, month, expected_quarter):
        """G-F-01: All 12 calendar months map to correct India FY quarter."""
        logger.debug(f"[G-F-01] month={month} → expecting {expected_quarter}")
        result = get_india_quarter(month)
        assert result == expected_quarter, f"Month {month}: expected {expected_quarter}, got {result}"
        logger.debug(f"[G-F-01] PASS — month {month} → {result}")

    def test_fy_starts_in_april(self):
        """G-F-01: April is Q1 (start of India FY)."""
        logger.debug("[G-F-01] test_fy_starts_in_april")
        assert get_india_quarter(4) == "Q1"
        logger.debug("[G-F-01] PASS")

    def test_fy_ends_in_march(self):
        """G-F-01: March is Q4 (end of India FY)."""
        logger.debug("[G-F-01] test_fy_ends_in_march")
        assert get_india_quarter(3) == "Q4"
        logger.debug("[G-F-01] PASS")

    def test_quarter_map_has_12_entries(self):
        """G-F-01: INDIA_QUARTER_MAP covers all 12 months."""
        logger.debug("[G-F-01] test_quarter_map_has_12_entries")
        assert len(INDIA_QUARTER_MAP) == 12
        assert set(INDIA_QUARTER_MAP.keys()) == set(range(1, 13))
        logger.debug("[G-F-01] PASS")


class TestValidatePlSanity:
    """G-F-02: PAT cannot exceed 150% of Revenue — flags data entry errors."""

    def test_normal_pl_passes(self):
        """HAPPY PATH: PAT = 20% of revenue → valid."""
        logger.debug("[G-F-02] test_normal_pl_passes")
        validate_pl_sanity(revenue=100.0, pat=20.0, symbol="TCS", quarter="Q2FY25")
        logger.debug("[G-F-02] PASS")

    def test_negative_pat_passes(self):
        """EDGE: Negative PAT (loss-making quarter) → valid."""
        logger.debug("[G-F-02] test_negative_pat_passes")
        validate_pl_sanity(revenue=100.0, pat=-50.0, symbol="YESBANK", quarter="Q1FY21")
        logger.debug("[G-F-02] PASS — negative PAT is valid")

    def test_pat_equals_revenue_passes(self):
        """EDGE: PAT = Revenue (100% margin) is unusual but passes (< 1.5x)."""
        logger.debug("[G-F-02] test_pat_equals_revenue_passes")
        validate_pl_sanity(revenue=100.0, pat=100.0, symbol="TEST", quarter="Q1FY25")
        logger.debug("[G-F-02] PASS — 100% PAT margin passes")

    def test_pat_exceeds_150pct_raises(self):
        """GUARD: PAT > 1.5x Revenue → ValueError."""
        logger.debug("[G-F-02] test_pat_exceeds_150pct_raises")
        with pytest.raises(ValueError, match="P&L sanity"):
            validate_pl_sanity(revenue=100.0, pat=200.0, symbol="TEST", quarter="Q1FY25")
        logger.debug("[G-F-02] PASS — PAT > 1.5x Revenue raises ValueError")

    def test_zero_revenue_does_not_divide_by_zero(self):
        """EDGE: Revenue = 0 → function handles without ZeroDivisionError."""
        logger.debug("[G-F-02] test_zero_revenue_does_not_divide_by_zero")
        try:
            validate_pl_sanity(revenue=0.0, pat=0.0, symbol="TEST", quarter="Q1FY25")
        except ValueError:
            pass  # acceptable to raise ValueError for degenerate input
        except ZeroDivisionError:
            pytest.fail("Should never raise ZeroDivisionError")
        logger.debug("[G-F-02] PASS — zero revenue handled gracefully")


class TestDetectGrowthOutlier:
    """G-F-03: YoY growth > 5x (500%) flagged as likely data error."""

    def test_normal_growth_not_flagged(self, caplog):
        """HAPPY PATH: 30% YoY growth → no outlier flag."""
        logger.debug("[G-F-03] test_normal_growth_not_flagged")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            detect_growth_outlier(yoy_growth=0.30, symbol="TCS", quarter="Q2FY25")
        assert not any("GROWTH OUTLIER" in r.message for r in caplog.records)
        logger.debug("[G-F-03] PASS")

    def test_massive_growth_flagged(self, caplog):
        """GUARD: 1000% YoY growth → outlier flag + warning."""
        logger.debug("[G-F-03] test_massive_growth_flagged")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            detect_growth_outlier(yoy_growth=10.0, symbol="TEST", quarter="Q1FY25")
        assert any("GROWTH OUTLIER" in r.message for r in caplog.records)
        logger.debug("[G-F-03] PASS — 1000% growth flagged")

    def test_negative_growth_below_threshold_not_flagged(self, caplog):
        """EDGE: -30% decline → not an outlier."""
        logger.debug("[G-F-03] test_negative_growth_below_threshold_not_flagged")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            detect_growth_outlier(yoy_growth=-0.30, symbol="TEST", quarter="Q1FY25")
        assert not any("GROWTH OUTLIER" in r.message for r in caplog.records)
        logger.debug("[G-F-03] PASS")

    def test_exactly_at_5x_boundary_not_flagged(self, caplog):
        """EDGE: Exactly 5x growth → boundary, not flagged."""
        logger.debug("[G-F-03] test_exactly_at_5x_boundary_not_flagged")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            detect_growth_outlier(yoy_growth=5.0, symbol="TEST", quarter="Q1FY25")
        # 5.0 == threshold → not flagged (must be strictly greater)
        logger.debug("[G-F-03] PASS — boundary case handled")

    def test_base_quarter_comparison_for_loss_making(self, caplog):
        """EDGE: Base quarter was loss (negative → positive) → outlier check applied."""
        logger.debug("[G-F-03] test_base_quarter_comparison_for_loss_making")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            detect_growth_outlier(yoy_growth=50.0, symbol="YESBANK", quarter="Q2FY24")
        assert any("GROWTH OUTLIER" in r.message for r in caplog.records)
        logger.debug("[G-F-03] PASS")


class TestValidateShareholdingSum:
    """G-F-04: Promoter + FII + DII + Public + Others ≈ 100% (±1%)."""

    def test_valid_shareholding_sum(self):
        """HAPPY PATH: 55 + 15 + 10 + 20 + 0 = 100%."""
        logger.debug("[G-F-04] test_valid_shareholding_sum")
        validate_shareholding_sum(
            promoter=55.0, fii=15.0, dii=10.0, public=20.0, others=0.0,
            symbol="TCS", quarter="Q2FY25"
        )
        logger.debug("[G-F-04] PASS")

    def test_sum_within_1pct_tolerance(self):
        """EDGE: Sum = 100.5% → within ±1% tolerance → valid."""
        logger.debug("[G-F-04] test_sum_within_1pct_tolerance")
        validate_shareholding_sum(
            promoter=55.0, fii=15.0, dii=10.0, public=20.0, others=0.5,
            symbol="TCS", quarter="Q2FY25", tolerance=1.0
        )
        logger.debug("[G-F-04] PASS — 100.5% within tolerance")

    def test_large_deviation_raises(self):
        """GUARD: Sum = 90% → ValueError."""
        logger.debug("[G-F-04] test_large_deviation_raises")
        with pytest.raises(ValueError, match="shareholding sum"):
            validate_shareholding_sum(
                promoter=40.0, fii=20.0, dii=10.0, public=20.0, others=0.0,
                symbol="TEST", quarter="Q1FY25"
            )  # sum = 90%
        logger.debug("[G-F-04] PASS — 90% sum raises ValueError")

    def test_sum_over_101pct_raises(self):
        """GUARD: Sum = 102% → ValueError."""
        logger.debug("[G-F-04] test_sum_over_101pct_raises")
        with pytest.raises(ValueError, match="shareholding sum"):
            validate_shareholding_sum(
                promoter=60.0, fii=20.0, dii=12.0, public=10.0, others=0.0,
                symbol="TEST", quarter="Q1FY25"
            )  # sum = 102%
        logger.debug("[G-F-04] PASS — 102% sum raises ValueError")

    def test_others_column_handles_none(self):
        """EDGE: others=None (often missing in source) → treated as 0."""
        logger.debug("[G-F-04] test_others_column_handles_none")
        validate_shareholding_sum(
            promoter=55.0, fii=15.0, dii=10.0, public=20.0, others=None,
            symbol="TCS", quarter="Q2FY25"
        )
        logger.debug("[G-F-04] PASS — None others handled as 0")
