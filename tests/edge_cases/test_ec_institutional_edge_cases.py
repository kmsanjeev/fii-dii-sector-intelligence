"""
Edge Case Tests — Institutional Flow Data Unusual Scenarios

Tests for T+1 lag, pre-2016 OI gap, gross flow consistency, budget day effects,
and other institutional data edge cases specific to Indian market structure.
"""

import logging
from datetime import date

import pandas as pd
import pytest

from engines.common.guardrails import (
    check_institutional_oi_availability,
    check_t1_data_lag,
    get_india_budget_risk_flag,
    is_expected_missing,
    is_fno_expiry,
    validate_gross_flows,
)

logger = logging.getLogger(__name__)


class TestPre2016OiGapEdgeCases:
    """Institutional OI data not available before 2016 — critical for historical analysis."""

    def test_2015_data_not_available(self):
        """GUARD: 2015 OI data doesn't exist — guard must block queries."""
        logger.debug("[EC-INST-01] test_2015_data_not_available")
        assert check_institutional_oi_availability(2015) is False
        logger.debug("[EC-INST-01] PASS — 2015 OI blocked")

    def test_2016_transition_year_available(self):
        """EDGE: 2016 is the first year with OI data — must be available."""
        logger.debug("[EC-INST-02] test_2016_transition_year_available")
        assert check_institutional_oi_availability(2016) is True
        logger.debug("[EC-INST-02] PASS — 2016 OI available")

    def test_historical_analysis_range_pre_2016(self):
        """REAL CASE: Multi-year analysis starting from 2010 — years 2010-2015 blocked."""
        logger.debug("[EC-INST-03] test_historical_analysis_range_pre_2016")
        years = list(range(2010, 2020))
        pre_2016 = [y for y in years if not check_institutional_oi_availability(y)]
        post_2016 = [y for y in years if check_institutional_oi_availability(y)]
        assert pre_2016 == [2010, 2011, 2012, 2013, 2014, 2015]
        assert post_2016 == [2016, 2017, 2018, 2019]
        logger.debug(f"[EC-INST-03] PASS — blocked: {pre_2016}, available: {post_2016}")


class TestBudgetDayInstitutionalEdgeCases:
    """Budget day (Feb 1) causes extreme institutional flow volatility."""

    def test_budget_day_2024_flagged(self):
        """REAL: Feb 1 2024 Budget — flag must be raised."""
        logger.debug("[EC-INST-04] test_budget_day_2024_flagged")
        assert get_india_budget_risk_flag(date(2024, 2, 1)) is True
        logger.debug("[EC-INST-04] PASS — Budget Day 2024 flagged")

    def test_budget_day_2025_flagged(self):
        """REAL: Feb 1 2025 Budget — flag must be raised."""
        logger.debug("[EC-INST-05] test_budget_day_2025_flagged")
        assert get_india_budget_risk_flag(date(2025, 2, 1)) is True
        logger.debug("[EC-INST-05] PASS — Budget Day 2025 flagged")

    def test_interim_budget_election_year(self):
        """REAL: Election year interim budget (Feb 1 2024) — still Feb 1, still flagged."""
        logger.debug("[EC-INST-06] test_interim_budget_election_year")
        interim_budget = date(2024, 2, 1)
        assert get_india_budget_risk_flag(interim_budget) is True
        logger.debug("[EC-INST-06] PASS — interim budget still flagged")

    def test_budget_day_eve_not_flagged(self):
        """EDGE: Jan 31 (Budget eve) not flagged — only the actual day."""
        logger.debug("[EC-INST-07] test_budget_day_eve_not_flagged")
        assert get_india_budget_risk_flag(date(2024, 1, 31)) is False
        logger.debug("[EC-INST-07] PASS — budget eve not flagged")


class TestFnoExpiryInstitutionalEdgeCases:
    """F&O expiry days generate anomalous institutional flows."""

    def test_expiry_day_fii_flows_potentially_anomalous(self):
        """REAL: F&O expiry causes unwinding — flows on expiry should be noted."""
        logger.debug("[EC-INST-08] test_expiry_day_fii_flows_potentially_anomalous")
        expiry_jan_2024 = date(2024, 1, 25)  # Last Thursday Jan 2024
        assert is_fno_expiry(expiry_jan_2024) is True
        # Gross flows still required on expiry days
        df = pd.DataFrame({
            "date": ["2024-01-25"],
            "fii_buy": [15000.0],
            "fii_sell": [18000.0],
            "fii_net": [-3000.0],
        })
        validate_gross_flows(df, participant="fii")  # must not raise
        logger.debug("[EC-INST-08] PASS — expiry day flows are valid but may be anomalous")

    def test_leap_year_february_expiry(self):
        """EDGE: Leap year Feb 2024 — last Thursday is Feb 29."""
        logger.debug("[EC-INST-09] test_leap_year_february_expiry")
        feb_29_2024 = date(2024, 2, 29)
        assert is_fno_expiry(feb_29_2024) is True
        logger.debug("[EC-INST-09] PASS — Feb 29 (leap year) is F&O expiry")


class TestGrossFlowConsistencyEdgeCases:
    """Gross flow edge cases — NaN values, extreme flows, settlement issues."""

    def test_all_four_participants_validated(self):
        """G-ID-05: All 4 participants (FII, DII, PRO, CLIENT) must store gross flows."""
        logger.debug("[EC-INST-10] test_all_four_participants_validated")
        for participant in ["fii", "dii", "pro", "client"]:
            df = pd.DataFrame({
                "date": ["2024-01-15"],
                f"{participant}_buy": [5000.0],
                f"{participant}_sell": [3000.0],
                f"{participant}_net": [2000.0],
            })
            validate_gross_flows(df, participant=participant)
        logger.debug("[EC-INST-10] PASS — all 4 participants validated")

    def test_only_net_flow_stored_raises(self):
        """GUARD: Storing only NET flow without BUY+SELL violates ADR-006."""
        logger.debug("[EC-INST-11] test_only_net_flow_stored_raises")
        df = pd.DataFrame({
            "date": ["2024-01-15"],
            "fii_net": [2000.0],  # missing fii_buy and fii_sell
        })
        with pytest.raises(ValueError):
            validate_gross_flows(df, participant="fii")
        logger.debug("[EC-INST-11] PASS — missing BUY/SELL raises ValueError")

    def test_extreme_fii_buying_day(self):
        """REAL: Extreme FII buying day (e.g. post-budget relief rally) — valid gross flows."""
        logger.debug("[EC-INST-12] test_extreme_fii_buying_day")
        df = pd.DataFrame({
            "date": ["2024-07-24"],
            "fii_buy": [25000.0],   # ₹25,000 Cr buy
            "fii_sell": [8000.0],   # ₹8,000 Cr sell
            "fii_net": [17000.0],   # ₹17,000 Cr net buy
        })
        validate_gross_flows(df, participant="fii")
        logger.debug("[EC-INST-12] PASS — extreme buying day validated correctly")

    def test_extreme_fii_selling_day(self):
        """REAL: FII panic selling day (COVID March 2020) — large negative NET is valid."""
        logger.debug("[EC-INST-13] test_extreme_fii_selling_day")
        df = pd.DataFrame({
            "date": ["2020-03-23"],
            "fii_buy": [5000.0],
            "fii_sell": [28000.0],
            "fii_net": [-23000.0],  # COVID panic selling
        })
        validate_gross_flows(df, participant="fii")
        logger.debug("[EC-INST-13] PASS — extreme negative NET is valid")

    def test_holiday_day_data_not_required(self):
        """EDGE: NSE holiday → institutional flow data is naturally absent (not an error)."""
        logger.debug("[EC-INST-14] test_holiday_day_data_not_required")
        # Republic Day 2024 — no FII/DII data published
        republic_day = date(2024, 1, 26)
        holidays = [republic_day]
        assert is_expected_missing(republic_day, holidays) is True
        logger.debug("[EC-INST-14] PASS — holiday day data absence is expected")


class TestT1LagEdgeCases:
    """T+1 data availability edge cases."""

    def test_weekend_data_lag_longer(self):
        """EDGE: Friday's data available Saturday (T+1), but T+1 is Saturday — need Monday."""
        logger.debug("[EC-INST-15] test_weekend_data_lag_longer")
        # Friday historical date — data should be available
        friday = date(2024, 1, 12)
        result = check_t1_data_lag(friday, cutoff_hour=18)
        assert result is True  # historical date always available
        logger.debug("[EC-INST-15] PASS — historical Friday data available")

    def test_historical_dates_always_available(self):
        """G-ID-01: Historical data (before today) is always available."""
        logger.debug("[EC-INST-16] test_historical_dates_always_available")
        historical_dates = [
            date(2020, 3, 23),   # COVID crash
            date(2024, 2, 1),    # Budget Day
            date(2023, 7, 3),    # HDFC-HDFCBANK merger
        ]
        for d in historical_dates:
            result = check_t1_data_lag(d, cutoff_hour=18)
            assert result is True, f"{d} should be available as historical date"
        logger.debug("[EC-INST-16] PASS — all historical dates available")
