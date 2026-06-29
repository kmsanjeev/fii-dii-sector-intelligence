"""
Guardrail Tests — Section 9: Trading Calendar (G-TC-01 to G-TC-07)
"""

import logging
from datetime import date

import pytest

from engines.common.guardrails import (
    get_india_budget_risk_flag,
    is_expected_missing,
    is_fno_expiry,
)

logger = logging.getLogger(__name__)


class TestIsExpectedMissing:
    """G-TC-01/02: Weekend and NSE holiday files are expected missing (not errors)."""

    HOLIDAYS_2024 = [
        date(2024, 1, 22),   # Ram Mandir (adhoc)
        date(2024, 1, 26),   # Republic Day
        date(2024, 3, 25),   # Holi
        date(2024, 4, 14),   # Dr. Ambedkar Jayanti
        date(2024, 4, 17),   # Ram Navami
        date(2024, 5, 23),   # Buddha Purnima
        date(2024, 6, 17),   # Bakrid
        date(2024, 7, 17),   # Muharram
        date(2024, 8, 15),   # Independence Day
        date(2024, 10, 2),   # Gandhi Jayanti
        date(2024, 11, 15),  # Diwali Laxmi Puja
        date(2024, 11, 1),   # Diwali Balipratipada
        date(2024, 11, 15),  # Gurunanak Jayanti
    ]

    def test_saturday_is_expected_missing(self):
        """G-TC-01: Saturday → expected missing (NSE closed)."""
        logger.debug("[G-TC-01] test_saturday_is_expected_missing")
        saturday = date(2024, 1, 6)  # Saturday
        result = is_expected_missing(saturday, self.HOLIDAYS_2024)
        assert result is True
        logger.debug("[G-TC-01] PASS — Saturday is expected missing")

    def test_sunday_is_expected_missing(self):
        """G-TC-01: Sunday → expected missing."""
        logger.debug("[G-TC-01] test_sunday_is_expected_missing")
        sunday = date(2024, 1, 7)
        result = is_expected_missing(sunday, self.HOLIDAYS_2024)
        assert result is True
        logger.debug("[G-TC-01] PASS — Sunday is expected missing")

    def test_nse_holiday_is_expected_missing(self):
        """G-TC-02: NSE holiday → expected missing."""
        logger.debug("[G-TC-02] test_nse_holiday_is_expected_missing")
        republic_day = date(2024, 1, 26)
        result = is_expected_missing(republic_day, self.HOLIDAYS_2024)
        assert result is True
        logger.debug("[G-TC-02] PASS — Republic Day (Jan 26) is expected missing")

    def test_regular_weekday_is_not_expected_missing(self):
        """G-TC-01/02: Regular Monday → NOT expected missing (data must be present)."""
        logger.debug("[G-TC-01] test_regular_weekday_is_not_expected_missing")
        regular_monday = date(2024, 1, 15)  # Monday, not a holiday
        result = is_expected_missing(regular_monday, self.HOLIDAYS_2024)
        assert result is False
        logger.debug("[G-TC-01] PASS — Regular weekday NOT expected missing")

    def test_diwali_is_expected_missing(self):
        """G-TC-02: Diwali Laxmi Puja → expected missing."""
        logger.debug("[G-TC-02] test_diwali_is_expected_missing")
        diwali = date(2024, 11, 15)
        result = is_expected_missing(diwali, self.HOLIDAYS_2024)
        assert result is True
        logger.debug("[G-TC-02] PASS — Diwali is expected missing")

    def test_independence_day_is_expected_missing(self):
        """G-TC-02: Independence Day (Aug 15) → expected missing."""
        logger.debug("[G-TC-02] test_independence_day_is_expected_missing")
        independence_day = date(2024, 8, 15)
        result = is_expected_missing(independence_day, self.HOLIDAYS_2024)
        assert result is True
        logger.debug("[G-TC-02] PASS")

    def test_day_before_holiday_is_trading_day(self):
        """EDGE: Day before a holiday (non-holiday weekday) → NOT expected missing."""
        logger.debug("[G-TC-01] test_day_before_holiday_is_trading_day")
        day_before_republic_day = date(2024, 1, 25)  # Thursday
        result = is_expected_missing(day_before_republic_day, self.HOLIDAYS_2024)
        assert result is False
        logger.debug("[G-TC-01] PASS — day before holiday is a trading day")

    def test_empty_holiday_list_only_weekends_missing(self):
        """EDGE: Empty holiday list → only weekends are expected missing."""
        logger.debug("[G-TC-01] test_empty_holiday_list_only_weekends_missing")
        saturday = date(2024, 1, 6)
        tuesday = date(2024, 1, 9)
        assert is_expected_missing(saturday, []) is True
        assert is_expected_missing(tuesday, []) is False
        logger.debug("[G-TC-01] PASS")


class TestGetIndiaBudgetRiskFlag:
    """G-TC-04: Feb 1 is Budget Day — high volatility, scores may be unreliable."""

    def test_feb_1_is_budget_day(self):
        """G-TC-04: February 1 of any year → budget risk flag True."""
        logger.debug("[G-TC-04] test_feb_1_is_budget_day")
        assert get_india_budget_risk_flag(date(2024, 2, 1)) is True
        assert get_india_budget_risk_flag(date(2025, 2, 1)) is True
        assert get_india_budget_risk_flag(date(2023, 2, 1)) is True
        logger.debug("[G-TC-04] PASS — Feb 1 is budget risk day")

    def test_other_dates_are_not_budget_day(self):
        """G-TC-04: Non-Feb-1 dates → budget risk flag False."""
        logger.debug("[G-TC-04] test_other_dates_are_not_budget_day")
        assert get_india_budget_risk_flag(date(2024, 2, 2)) is False
        assert get_india_budget_risk_flag(date(2024, 1, 31)) is False
        assert get_india_budget_risk_flag(date(2024, 7, 5)) is False
        logger.debug("[G-TC-04] PASS")

    def test_interim_budget_feb1_also_flagged(self):
        """EDGE: Interim budget years (election year) — still Feb 1."""
        logger.debug("[G-TC-04] test_interim_budget_feb1_also_flagged")
        assert get_india_budget_risk_flag(date(2024, 2, 1)) is True  # election year
        logger.debug("[G-TC-04] PASS — interim budget also flagged")


class TestIsFnoExpiry:
    """G-TC-06: Last Thursday of each month is F&O expiry day."""

    @pytest.mark.parametrize("expiry_date", [
        date(2024, 1, 25),   # Last Thu Jan 2024
        date(2024, 2, 29),   # Last Thu Feb 2024 (leap year)
        date(2024, 3, 28),   # Last Thu Mar 2024
        date(2024, 4, 25),   # Last Thu Apr 2024
        date(2024, 5, 30),   # Last Thu May 2024
        date(2024, 6, 27),   # Last Thu Jun 2024
        date(2024, 7, 25),   # Last Thu Jul 2024
        date(2024, 8, 29),   # Last Thu Aug 2024
        date(2024, 9, 26),   # Last Thu Sep 2024
        date(2024, 10, 31),  # Last Thu Oct 2024
        date(2024, 11, 28),  # Last Thu Nov 2024
        date(2024, 12, 26),  # Last Thu Dec 2024
    ])
    def test_last_thursday_is_fno_expiry(self, expiry_date):
        """G-TC-06: Each month's last Thursday is F&O expiry."""
        logger.debug(f"[G-TC-06] testing {expiry_date}")
        result = is_fno_expiry(expiry_date)
        assert result is True, f"{expiry_date} should be F&O expiry"
        logger.debug(f"[G-TC-06] PASS — {expiry_date} is F&O expiry")

    def test_non_thursday_is_not_fno_expiry(self):
        """G-TC-06: Wednesday is not F&O expiry."""
        logger.debug("[G-TC-06] test_non_thursday_is_not_fno_expiry")
        wednesday = date(2024, 1, 24)
        assert is_fno_expiry(wednesday) is False
        logger.debug("[G-TC-06] PASS")

    def test_non_last_thursday_is_not_fno_expiry(self):
        """G-TC-06: First Thursday of month is not expiry."""
        logger.debug("[G-TC-06] test_non_last_thursday_is_not_fno_expiry")
        first_thursday_jan2024 = date(2024, 1, 4)
        assert is_fno_expiry(first_thursday_jan2024) is False
        logger.debug("[G-TC-06] PASS")

    def test_second_thursday_is_not_fno_expiry(self):
        """G-TC-06: Second Thursday of month is not expiry."""
        logger.debug("[G-TC-06] test_second_thursday_is_not_fno_expiry")
        second_thursday = date(2024, 1, 11)
        assert is_fno_expiry(second_thursday) is False
        logger.debug("[G-TC-06] PASS")
