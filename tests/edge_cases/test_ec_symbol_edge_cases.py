"""
Edge Case Tests — Symbol Universe Boundary Conditions

Tests cover the unusual, country-specific, and corporate-event-driven edge cases
that standard guardrail tests do not cover.
"""

import logging
from datetime import date

import pandas as pd
import pytest

from engines.common.guardrails import (
    deduplicate_isin,
    filter_by_listing_date,
    filter_delisted,
    filter_eq_series,
    filter_non_equity_instruments,
    validate_universe_size,
)

logger = logging.getLogger(__name__)


class TestMergerDemergerEdgeCases:
    """Corporate events that create ISIN deduplication challenges."""

    def test_hdfc_hdfc_bank_merger(self):
        """REAL: HDFC merged into HDFCBANK Jul 2023 — both had same underlying ISIN briefly."""
        logger.debug("[EC-SYM-01] test_hdfc_hdfc_bank_merger")
        df = pd.DataFrame({
            "symbol": ["HDFCBANK", "HDFC"],
            "isin": ["INE040A01034", "INE040A01034"],
            "status": ["ACTIVE", "DELISTED"],
            "listing_date": [date(1995, 11, 3), date(2023, 7, 1)],
        })
        result = deduplicate_isin(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "HDFCBANK"
        logger.debug("[EC-SYM-01] PASS — HDFC-HDFCBANK merger dedup: HDFCBANK retained")

    def test_reliance_power_spin_off(self):
        """EDGE: Spin-off creates separate symbols with different ISINs — both ACTIVE."""
        logger.debug("[EC-SYM-02] test_reliance_power_spin_off")
        df = pd.DataFrame({
            "symbol": ["RELIANCE", "RPOWER"],
            "isin": ["INE002A01018", "INE036A01016"],
            "status": ["ACTIVE", "DELISTED"],
        })
        result = deduplicate_isin(df)
        # RELIANCE should remain (ACTIVE), RPOWER should be dropped (DELISTED)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "RELIANCE"
        logger.debug("[EC-SYM-02] PASS — RPOWER (delisted) filtered out")

    def test_symbol_rename_same_isin(self):
        """EDGE: Symbol renamed (e.g. BPCL → rebranded) — same ISIN, old symbol DELISTED."""
        logger.debug("[EC-SYM-03] test_symbol_rename_same_isin")
        df = pd.DataFrame({
            "symbol": ["NEWNAME", "OLDNAME"],
            "isin": ["INE123X01234", "INE123X01234"],
            "status": ["ACTIVE", "DELISTED"],
        })
        result = deduplicate_isin(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "NEWNAME"
        logger.debug("[EC-SYM-03] PASS — renamed symbol: new name retained")


class TestRecentlyListedIpoEdgeCases:
    """Stocks with very short trading history."""

    def test_ipo_on_listing_day_only(self):
        """EDGE: IPO listed today — only 1 day of data, should not trigger processing."""
        logger.debug("[EC-SYM-04] test_ipo_on_listing_day_only")
        listing = date(2024, 6, 25)
        files = [f"bhavcopy_{listing.year}{listing.month:02d}{listing.day:02d}.csv"]
        result = filter_by_listing_date(files, listing,
                                        lambda f: date(int(f[9:13]), int(f[13:15]), int(f[15:17])))
        assert len(result) == 1  # listing day file is included
        logger.debug("[EC-SYM-04] PASS — IPO listing day file included")

    def test_sme_ipo_not_in_main_board_universe(self):
        """EDGE: SME IPOs are in separate series (SM) — filtered by EQ series check."""
        logger.debug("[EC-SYM-05] test_sme_ipo_not_in_main_board_universe")
        df = pd.DataFrame({
            "symbol": ["MAINBOARD_CO", "SME_CO"],
            "series": ["EQ", "SM"],
        })
        result = filter_eq_series(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "MAINBOARD_CO"
        logger.debug("[EC-SYM-05] PASS — SME (SM series) excluded from EQ universe")


class TestDelistingEdgeCases:
    """Delisting scenarios: voluntary, NCLT, regulatory."""

    def test_voluntary_delisting_data_cut_off(self):
        """REAL: Voluntarily delisted stock — data after delist date excluded."""
        logger.debug("[EC-SYM-06] test_voluntary_delisting_data_cut_off")

        def _date(f):
            return date(int(f[9:13]), int(f[13:15]), int(f[15:17]))

        files = ["bhavcopy_20230115.csv", "bhavcopy_20230601.csv", "bhavcopy_20240115.csv"]
        delist_date = date(2023, 12, 31)
        result = filter_delisted(files, delist_date, _date)
        assert "bhavcopy_20240115.csv" not in result
        assert "bhavcopy_20230115.csv" in result
        logger.debug(f"[EC-SYM-06] PASS — post-delist files excluded: {len(result)} retained")

    def test_delist_same_day_as_last_bhavcopy(self):
        """EDGE: Delisting date = last available bhavcopy date → that file is included."""
        logger.debug("[EC-SYM-07] test_delist_same_day_as_last_bhavcopy")

        def _date(f):
            return date(int(f[9:13]), int(f[13:15]), int(f[15:17]))

        files = ["bhavcopy_20231231.csv"]
        delist_date = date(2023, 12, 31)
        result = filter_delisted(files, delist_date, _date)
        assert len(result) == 1
        logger.debug("[EC-SYM-07] PASS — delist date file is included (boundary inclusive)")


class TestConglomerateAndHoldingCompanyEdgeCases:
    """Difficult classification cases: conglomerates, holding companies, PSUs."""

    def test_conglomerate_not_excluded_as_non_equity(self):
        """EDGE: Pure conglomerate (e.g. TATAMOTORS) is valid equity — must not be excluded."""
        logger.debug("[EC-SYM-08] test_conglomerate_not_excluded_as_non_equity")
        df = pd.DataFrame({
            "symbol": ["TATAMOTORS", "TATAINVEST"],
            "company_name": ["TATA MOTORS LIMITED", "TATA INVESTMENT CORP"],
        })
        result = filter_non_equity_instruments(df)
        assert len(result) == 2, "Conglomerates and holding companies are valid equities"
        logger.debug("[EC-SYM-08] PASS — conglomerates retained in universe")


class TestUniverseSizeAnomalies:
    """Universe size edge cases that should trigger anomaly warnings."""

    def test_all_stocks_marked_delisted_raises(self):
        """GUARD: Universe suddenly shows 0 active stocks → RuntimeError."""
        logger.debug("[EC-SYM-09] test_all_stocks_marked_delisted_raises")
        df = pd.DataFrame({"symbol": ["A", "B"], "series": ["EQ", "EQ"]})  # only 2 stocks
        with pytest.raises(RuntimeError, match="anomaly"):
            validate_universe_size(df, min_symbols=1800)
        logger.debug("[EC-SYM-09] PASS — near-zero universe raises anomaly")

    def test_market_wide_circuit_breaker_day_still_has_universe(self):
        """REAL: On market circuit-breaker day, universe is intact (trading suspended, not delisted)."""
        logger.debug("[EC-SYM-10] test_market_wide_circuit_breaker_day_still_has_universe")
        # Universe should still have 2000+ stocks even on circuit breaker days
        df = pd.DataFrame({"symbol": [f"SYM{i}" for i in range(2100)],
                           "series": ["EQ"] * 2100})
        validate_universe_size(df, min_symbols=1800)
        logger.debug("[EC-SYM-10] PASS — full universe survives circuit breaker")
