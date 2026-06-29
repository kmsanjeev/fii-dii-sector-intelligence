"""
Guardrail Tests — Section 3: Symbol / Universe (G-S-01 to G-S-06)
"""

import logging
from datetime import date
from pathlib import Path

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


def _make_date(filename: str) -> date:
    """Extract date from filename like 'bhavcopy_20200115.csv'."""
    return date(int(filename[9:13]), int(filename[13:15]), int(filename[15:17]))


class TestFilterEqSeries:
    """G-S-01: Only process EQ series instruments."""

    def test_keeps_only_eq_series(self):
        """HAPPY PATH: Mixed series input → only EQ retained."""
        logger.debug("[G-S-01] test_keeps_only_eq_series")
        df = pd.DataFrame({
            "symbol": ["TCS", "TATASTEEL", "BAJFINANCE", "LIQUIDBEES"],
            "series": ["EQ", "BE", "EQ", "IL"],
        })
        result = filter_eq_series(df)
        assert list(result["symbol"]) == ["TCS", "BAJFINANCE"]
        logger.debug("[G-S-01] PASS — only EQ retained")

    def test_all_eq_unchanged(self):
        """HAPPY PATH: All-EQ input is returned unchanged."""
        logger.debug("[G-S-01] test_all_eq_unchanged")
        df = pd.DataFrame({"symbol": ["TCS", "INFY"], "series": ["EQ", "EQ"]})
        result = filter_eq_series(df)
        assert len(result) == 2
        logger.debug("[G-S-01] PASS")

    def test_no_eq_returns_empty_with_warning(self, caplog):
        """EDGE: No EQ instruments → empty result + warning logged."""
        logger.debug("[G-S-01] test_no_eq_returns_empty_with_warning")
        df = pd.DataFrame({"symbol": ["LIQUIDBEES"], "series": ["IL"]})
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            result = filter_eq_series(df)
        assert result.empty
        assert any("No EQ series" in r.message for r in caplog.records)
        logger.debug("[G-S-01] PASS — empty result and warning emitted")

    def test_dropped_count_logged(self, caplog):
        """G-S-01: Number of dropped non-EQ rows is logged as warning."""
        logger.debug("[G-S-01] test_dropped_count_logged")
        df = pd.DataFrame({
            "symbol": ["TCS", "X", "Y"],
            "series": ["EQ", "N1", "SM"],
        })
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            filter_eq_series(df)
        assert any("Dropped 2" in r.message for r in caplog.records)
        logger.debug("[G-S-01] PASS — correct dropped count in warning")


class TestFilterByListingDate:
    """G-S-02: Never process bhavcopy data before a stock's listing date."""

    def _files(self, years):
        return [f"bhavcopy_{y}0115.csv" for y in years]

    def test_pre_listing_files_excluded(self):
        """GUARD: Files before listing date are not returned."""
        logger.debug("[G-S-02] test_pre_listing_files_excluded")
        files = self._files([2018, 2019, 2020, 2021, 2022])
        listing = date(2020, 1, 1)
        result = filter_by_listing_date(files, listing, _make_date)
        years = [int(f[9:13]) for f in result]
        assert all(y >= 2020 for y in years), f"Pre-listing files included: {result}"
        assert 2018 not in years and 2019 not in years
        logger.debug(f"[G-S-02] PASS — {len(result)} files returned, all ≥ listing date")

    def test_listing_date_file_included(self):
        """EDGE: File exactly on listing date is included."""
        logger.debug("[G-S-02] test_listing_date_file_included")
        files = ["bhavcopy_20200115.csv"]
        listing = date(2020, 1, 15)
        result = filter_by_listing_date(files, listing, _make_date)
        assert len(result) == 1
        logger.debug("[G-S-02] PASS — listing date file included")

    def test_recently_listed_stock(self):
        """EDGE: Recently listed stock (2023) — only 2023+ files returned from 1995-2023 range."""
        logger.debug("[G-S-02] test_recently_listed_stock")
        all_years = list(range(1995, 2027))
        files = self._files(all_years)
        listing = date(2023, 6, 1)
        result = filter_by_listing_date(files, listing, _make_date)
        result_years = [int(f[9:13]) for f in result]
        assert all(y >= 2023 for y in result_years)
        logger.debug(f"[G-S-02] PASS — {len(result)} files returned for recently-listed stock")

    def test_old_listing_returns_all_files(self):
        """EDGE: 1995 listing date — all available files returned."""
        logger.debug("[G-S-02] test_old_listing_returns_all_files")
        files = self._files([1995, 2000, 2010, 2024])
        listing = date(1995, 1, 1)
        result = filter_by_listing_date(files, listing, _make_date)
        assert len(result) == 4
        logger.debug("[G-S-02] PASS")


class TestFilterDelisted:
    """G-S-03: Cut off data after delisting date for DELISTED symbols."""

    def _files(self, years):
        return [f"bhavcopy_{y}0115.csv" for y in years]

    def test_delisted_symbol_trimmed(self):
        """GUARD: Files after delisting date are removed."""
        logger.debug("[G-S-03] test_delisted_symbol_trimmed")
        files = self._files([2018, 2019, 2020, 2021, 2022])
        delist = date(2020, 12, 31)
        result = filter_delisted(files, delist, _make_date)
        years = [int(f[9:13]) for f in result]
        assert all(y <= 2020 for y in years)
        logger.debug(f"[G-S-03] PASS — {len(result)} files retained up to delisting")

    def test_active_symbol_no_cutoff(self):
        """HAPPY PATH: Active symbol (delisting_date=None) → no files removed."""
        logger.debug("[G-S-03] test_active_symbol_no_cutoff")
        files = self._files([2018, 2019, 2020, 2021])
        result = filter_delisted(files, None, _make_date)
        assert len(result) == 4
        logger.debug("[G-S-03] PASS")


class TestValidateUniverseSize:
    """G-S-04: Raise if equity universe is suspiciously small."""

    def test_adequate_universe_passes(self):
        """HAPPY PATH: 2123 EQ symbols → no exception."""
        logger.debug("[G-S-04] test_adequate_universe_passes")
        df = pd.DataFrame({"symbol": [f"SYM{i}" for i in range(2123)],
                           "series": ["EQ"] * 2123})
        validate_universe_size(df, min_symbols=1800)
        logger.debug("[G-S-04] PASS")

    def test_undersized_universe_raises(self):
        """GUARD: Only 500 symbols → RuntimeError."""
        logger.debug("[G-S-04] test_undersized_universe_raises")
        df = pd.DataFrame({"symbol": [f"SYM{i}" for i in range(500)],
                           "series": ["EQ"] * 500})
        with pytest.raises(RuntimeError, match="anomaly"):
            validate_universe_size(df, min_symbols=1800)
        logger.debug("[G-S-04] PASS — RuntimeError for undersized universe")


class TestDeduplicateIsin:
    """G-S-05: One canonical symbol per ISIN — prefer ACTIVE over DELISTED."""

    def test_no_duplicates_unchanged(self):
        """HAPPY PATH: No duplicate ISINs → DataFrame unchanged."""
        logger.debug("[G-S-05] test_no_duplicates_unchanged")
        df = pd.DataFrame({
            "symbol": ["TCS", "INFY"],
            "isin": ["INE467B01029", "INE009A01021"],
            "status": ["ACTIVE", "ACTIVE"],
        })
        result = deduplicate_isin(df)
        assert len(result) == 2
        logger.debug("[G-S-05] PASS")

    def test_active_kept_over_delisted(self):
        """G-S-05: When same ISIN has ACTIVE and DELISTED, keep ACTIVE."""
        logger.debug("[G-S-05] test_active_kept_over_delisted")
        df = pd.DataFrame({
            "symbol": ["HDFCBANK", "HDFC"],
            "isin": ["INE040A01034", "INE040A01034"],
            "status": ["ACTIVE", "DELISTED"],
        })
        result = deduplicate_isin(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "HDFCBANK"
        assert result.iloc[0]["status"] == "ACTIVE"
        logger.debug("[G-S-05] PASS — ACTIVE symbol retained")

    def test_multiple_isin_dupes(self):
        """G-S-05: Multiple duplicate ISINs all resolved to unique rows."""
        logger.debug("[G-S-05] test_multiple_isin_dupes")
        df = pd.DataFrame({
            "symbol": ["A", "B", "C", "D"],
            "isin": ["ISIN1", "ISIN1", "ISIN2", "ISIN2"],
            "status": ["DELISTED", "ACTIVE", "ACTIVE", "DELISTED"],
        })
        result = deduplicate_isin(df)
        assert len(result) == 2
        assert set(result["symbol"]) == {"B", "C"}
        logger.debug("[G-S-05] PASS — 2 unique ISINs after dedup")


class TestFilterNonEquityInstruments:
    """G-S-06: Exclude ETFs, REITs, InvITs, Gold/Silver funds from equity universe."""

    def test_etf_excluded(self):
        """G-S-06: ETF by name is excluded."""
        logger.debug("[G-S-06] test_etf_excluded")
        df = pd.DataFrame({"symbol": ["NIFTYBEES", "TCS"],
                           "company_name": ["NIPPON INDIA ETF NIFTY BEES", "TATA CONSULTANCY"]})
        result = filter_non_equity_instruments(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "TCS"
        logger.debug("[G-S-06] PASS — ETF excluded")

    def test_reit_excluded(self):
        """G-S-06: REIT is excluded."""
        logger.debug("[G-S-06] test_reit_excluded")
        df = pd.DataFrame({"symbol": ["EMBASSYOFFICE", "INFY"],
                           "company_name": ["EMBASSY OFFICE PARKS REIT", "INFOSYS"]})
        result = filter_non_equity_instruments(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "INFY"
        logger.debug("[G-S-06] PASS — REIT excluded")

    def test_gold_fund_excluded(self):
        """G-S-06: Gold fund is excluded."""
        logger.debug("[G-S-06] test_gold_fund_excluded")
        df = pd.DataFrame({"symbol": ["GOLDBEES", "RELIANCE"],
                           "company_name": ["NIPPON INDIA GOLD BEES", "RELIANCE INDUSTRIES"]})
        result = filter_non_equity_instruments(df)
        assert len(result) == 1
        logger.debug("[G-S-06] PASS — gold fund excluded")

    def test_regular_stock_retained(self):
        """HAPPY PATH: Regular company name passes through filter."""
        logger.debug("[G-S-06] test_regular_stock_retained")
        df = pd.DataFrame({"symbol": ["RELIANCE", "TCS", "BAJFINANCE"],
                           "company_name": ["RELIANCE INDUSTRIES", "TATA CONSULTANCY",
                                            "BAJAJ FINANCE"]})
        result = filter_non_equity_instruments(df)
        assert len(result) == 3
        logger.debug("[G-S-06] PASS — all regular stocks retained")

    def test_invit_excluded(self):
        """G-S-06: InvIT is excluded."""
        logger.debug("[G-S-06] test_invit_excluded")
        df = pd.DataFrame({"symbol": ["POWERGRID-INV", "POWERGRID"],
                           "company_name": ["POWERGRID INFRASTRUCTURE INVIT",
                                            "POWER GRID CORPORATION"]})
        result = filter_non_equity_instruments(df)
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "POWERGRID"
        logger.debug("[G-S-06] PASS — InvIT excluded, regular stock retained")
