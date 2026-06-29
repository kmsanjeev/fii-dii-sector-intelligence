"""
Guardrail Tests — Section 1: Data Integrity (G-D-01 to G-D-07)
Every test logs at DEBUG level; results appear in tests/logs/pytest_debug.log.
"""

import logging
import shutil
from pathlib import Path

import pandas as pd
import pytest

from engines.common.guardrails import (
    safe_append,
    safe_write_csv,
    validate_schema,
    verify_file_size,
    write_raw,
)

logger = logging.getLogger(__name__)

# ─── G-D-01 write_raw ────────────────────────────────────────────────────────

class TestWriteRaw:
    """G-D-01: Raw data is immutable — never overwrite existing raw files."""

    def test_write_raw_new_file_succeeds(self, tmp_dir, sample_bhavcopy_df):
        """HAPPY PATH: Writing to a new path succeeds."""
        target = tmp_dir / "bhavcopy_20240115.csv"
        logger.debug(f"[G-D-01] test_write_raw_new_file_succeeds: target={target}")
        write_raw(sample_bhavcopy_df, target)
        assert target.exists(), "File should have been created"
        assert target.stat().st_size > 0, "File should not be empty"
        logger.debug(f"[G-D-01] PASS — file created at {target}")

    def test_write_raw_existing_file_raises(self, tmp_dir, sample_bhavcopy_df):
        """GUARD: Overwriting an existing raw file raises FileExistsError."""
        target = tmp_dir / "bhavcopy_20240115.csv"
        logger.debug(f"[G-D-01] test_write_raw_existing_file_raises: target={target}")
        write_raw(sample_bhavcopy_df, target)  # first write
        with pytest.raises(FileExistsError, match="immutable"):
            write_raw(sample_bhavcopy_df, target)  # second write must fail
        logger.debug("[G-D-01] PASS — FileExistsError correctly raised on overwrite attempt")

    def test_write_raw_creates_parent_dirs(self, tmp_dir, sample_bhavcopy_df):
        """EDGE: Parent directories are created automatically if missing."""
        target = tmp_dir / "nested" / "dir" / "bhavcopy.csv"
        logger.debug(f"[G-D-01] test_write_raw_creates_parent_dirs: target={target}")
        write_raw(sample_bhavcopy_df, target)
        assert target.exists()
        logger.debug("[G-D-01] PASS — nested parent dirs created")


# ─── G-D-02 + G-D-03 safe_write_csv ─────────────────────────────────────────

class TestSafeWriteCsv:
    """G-D-02: Atomic writes via .tmp rename. G-D-03: Guard against empty DataFrames."""

    def test_atomic_write_no_tmp_left(self, tmp_dir, sample_bhavcopy_df):
        """G-D-02: After successful write no .tmp file remains."""
        target = tmp_dir / "output.csv"
        logger.debug(f"[G-D-02] test_atomic_write_no_tmp_left: target={target}")
        safe_write_csv(sample_bhavcopy_df, target)
        assert target.exists(), "Final file should exist"
        assert not target.with_suffix(".tmp").exists(), ".tmp file should be cleaned up"
        logger.debug("[G-D-02] PASS — no .tmp residue")

    def test_atomic_write_content_correct(self, tmp_dir, sample_bhavcopy_df):
        """G-D-02: Written file content matches source DataFrame."""
        target = tmp_dir / "output.csv"
        logger.debug(f"[G-D-02] test_atomic_write_content_correct")
        safe_write_csv(sample_bhavcopy_df, target)
        result = pd.read_csv(target)
        assert list(result["symbol"]) == list(sample_bhavcopy_df["symbol"])
        logger.debug("[G-D-02] PASS — content round-trips correctly")

    def test_empty_dataframe_not_written(self, tmp_dir):
        """G-D-03: Empty DataFrame skips write without raising."""
        target = tmp_dir / "output.csv"
        logger.debug(f"[G-D-03] test_empty_dataframe_not_written")
        safe_write_csv(pd.DataFrame(), target)
        assert not target.exists(), "Empty DataFrame should not produce a file"
        logger.debug("[G-D-03] PASS — empty DataFrame correctly skipped")

    def test_non_empty_dataframe_is_written(self, tmp_dir, sample_bhavcopy_df):
        """G-D-03: Non-empty DataFrame is written normally."""
        target = tmp_dir / "output.csv"
        logger.debug(f"[G-D-03] test_non_empty_dataframe_is_written")
        safe_write_csv(sample_bhavcopy_df, target)
        assert target.exists()
        logger.debug("[G-D-03] PASS")

    def test_write_creates_parent_dir(self, tmp_dir, sample_bhavcopy_df):
        """G-D-02: Parent directory created if absent."""
        target = tmp_dir / "sub" / "output.csv"
        safe_write_csv(sample_bhavcopy_df, target)
        assert target.exists()
        logger.debug("[G-D-02] PASS — parent dir auto-created")


# ─── G-D-04 validate_schema ──────────────────────────────────────────────────

class TestValidateSchema:
    """G-D-04: Schema validation before every write."""

    def test_all_required_columns_present_passes(self, sample_bhavcopy_df):
        """HAPPY PATH: All required columns present — no exception."""
        logger.debug("[G-D-04] test_all_required_columns_present_passes")
        validate_schema(sample_bhavcopy_df, ["symbol", "series", "close", "volume"], "bhavcopy")
        logger.debug("[G-D-04] PASS")

    def test_missing_column_raises_value_error(self, sample_bhavcopy_df):
        """GUARD: Missing required column raises ValueError."""
        logger.debug("[G-D-04] test_missing_column_raises_value_error")
        with pytest.raises(ValueError, match="Schema violation"):
            validate_schema(sample_bhavcopy_df, ["symbol", "isin"], "bhavcopy")
        logger.debug("[G-D-04] PASS — ValueError raised for missing column")

    def test_null_key_field_logs_warning(self, sample_equity_master, caplog):
        """WARN: Null values in key columns generate a warning (but do not raise)."""
        logger.debug("[G-D-04] test_null_key_field_logs_warning")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            validate_schema(sample_equity_master, ["symbol", "sector_platform"], "equity_master")
        assert any("Null values" in r.message for r in caplog.records), \
            "Should warn about null sector_platform values"
        logger.debug("[G-D-04] PASS — null warning emitted")

    def test_multiple_missing_columns_listed(self, sample_bhavcopy_df):
        """GUARD: All missing columns listed in error message."""
        logger.debug("[G-D-04] test_multiple_missing_columns_listed")
        with pytest.raises(ValueError) as exc:
            validate_schema(sample_bhavcopy_df, ["symbol", "isin", "listing_date"], "test")
        assert "isin" in str(exc.value)
        assert "listing_date" in str(exc.value)
        logger.debug("[G-D-04] PASS — multiple missing columns reported")


# ─── G-D-05 + G-D-06 safe_append ────────────────────────────────────────────

class TestSafeAppend:
    """G-D-05: Dedup by date before append. G-D-06: Output always sorted by date."""

    def test_new_dates_appended(self):
        """HAPPY PATH: New dates are correctly appended."""
        logger.debug("[G-D-05] test_new_dates_appended")
        existing = pd.DataFrame({"date": ["2024-01-10", "2024-01-11"], "value": [1, 2]})
        new = pd.DataFrame({"date": ["2024-01-12", "2024-01-13"], "value": [3, 4]})
        result = safe_append(existing, new)
        assert len(result) == 4
        logger.debug(f"[G-D-05] PASS — 4 rows after append")

    def test_duplicate_dates_not_appended(self):
        """G-D-05: Duplicate dates are silently dropped."""
        logger.debug("[G-D-05] test_duplicate_dates_not_appended")
        existing = pd.DataFrame({"date": ["2024-01-10", "2024-01-11"], "value": [1, 2]})
        new = pd.DataFrame({"date": ["2024-01-11", "2024-01-12"], "value": [99, 3]})
        result = safe_append(existing, new)
        assert len(result) == 3
        # Existing value for 2024-01-11 (2) should be preserved, not overwritten by 99
        val_11 = result.loc[result["date"] == "2024-01-11", "value"].iloc[0]
        assert val_11 == 2, "Existing value should not be overwritten by duplicate"
        logger.debug("[G-D-05] PASS — duplicate date rejected, existing value preserved")

    def test_all_duplicates_returns_original_unchanged(self):
        """G-D-05: All-duplicate new batch returns original unchanged."""
        logger.debug("[G-D-05] test_all_duplicates_returns_original_unchanged")
        existing = pd.DataFrame({"date": ["2024-01-10", "2024-01-11"], "value": [1, 2]})
        new = pd.DataFrame({"date": ["2024-01-10", "2024-01-11"], "value": [99, 99]})
        result = safe_append(existing, new)
        assert len(result) == 2
        logger.debug("[G-D-05] PASS")

    def test_result_sorted_by_date(self):
        """G-D-06: Result is always sorted ascending by date."""
        logger.debug("[G-D-06] test_result_sorted_by_date")
        existing = pd.DataFrame({"date": ["2024-01-13"], "value": [3]})
        new = pd.DataFrame({"date": ["2024-01-10", "2024-01-15"], "value": [1, 5]})
        result = safe_append(existing, new)
        dates = list(result["date"])
        assert dates == sorted(dates), f"Result not sorted: {dates}"
        logger.debug(f"[G-D-06] PASS — sorted: {dates}")

    def test_unsorted_existing_becomes_sorted(self):
        """G-D-06: Even unsorted existing data is sorted in the result."""
        logger.debug("[G-D-06] test_unsorted_existing_becomes_sorted")
        existing = pd.DataFrame({"date": ["2024-01-15", "2024-01-10"], "value": [5, 1]})
        new = pd.DataFrame({"date": ["2024-01-12"], "value": [3]})
        result = safe_append(existing, new)
        dates = list(result["date"])
        assert dates == sorted(dates)
        logger.debug("[G-D-06] PASS")


# ─── G-D-07 verify_file_size ─────────────────────────────────────────────────

class TestVerifyFileSize:
    """G-D-07: Raise RuntimeError if written file is smaller than expected minimum."""

    def test_large_enough_file_passes(self, tmp_dir, sample_bhavcopy_df):
        """HAPPY PATH: File above min size passes verification."""
        target = tmp_dir / "output.csv"
        logger.debug(f"[G-D-07] test_large_enough_file_passes")
        safe_write_csv(sample_bhavcopy_df, target)
        verify_file_size(target, min_bytes=10)  # should be much larger than 10 bytes
        logger.debug("[G-D-07] PASS")

    def test_small_file_raises_runtime_error(self, tmp_dir):
        """GUARD: File smaller than min_bytes raises RuntimeError."""
        logger.debug(f"[G-D-07] test_small_file_raises_runtime_error")
        target = tmp_dir / "tiny.csv"
        target.write_text("a,b\n1,2\n")  # tiny file
        with pytest.raises(RuntimeError, match="suspiciously small"):
            verify_file_size(target, min_bytes=1_000_000)
        logger.debug("[G-D-07] PASS — RuntimeError raised for small file")
