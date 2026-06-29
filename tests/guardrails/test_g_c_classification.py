"""
Guardrail Tests — Section 5: Classification (G-C-01 to G-C-05)
"""

import logging
from pathlib import Path

import pandas as pd
import pytest

from engines.common.guardrails import (
    apply_manual_overrides,
    fill_null_sectors,
    flag_low_confidence,
)

logger = logging.getLogger(__name__)


class TestFillNullSectors:
    """G-C-01: Every symbol must have a sector; nulls → UNCATEGORIZED."""

    def test_no_nulls_unchanged(self, sample_equity_master):
        """HAPPY PATH: No null sectors → DataFrame unchanged."""
        logger.debug("[G-C-01] test_no_nulls_unchanged")
        df = sample_equity_master.copy()
        df["sector_platform"] = df["sector_platform"].fillna("BANKING")
        result = fill_null_sectors(df)
        assert not result["sector_platform"].isnull().any()
        logger.debug("[G-C-01] PASS")

    def test_null_sector_becomes_uncategorized(self, sample_equity_master):
        """GUARD: Null sector → UNCATEGORIZED."""
        logger.debug("[G-C-01] test_null_sector_becomes_uncategorized")
        result = fill_null_sectors(sample_equity_master)
        # ADANIPORTS has null sector in fixture
        adani_sector = result.loc[result["symbol"] == "ADANIPORTS", "sector_platform"].iloc[0]
        assert adani_sector == "UNCATEGORIZED"
        logger.debug(f"[G-C-01] PASS — ADANIPORTS sector: {adani_sector}")

    def test_uncategorized_written_to_review_queue(self, sample_equity_master, tmp_dir):
        """G-C-01: UNCATEGORIZED symbols written to review queue."""
        logger.debug("[G-C-01] test_uncategorized_written_to_review_queue")
        queue = tmp_dir / "review_queue.csv"
        fill_null_sectors(sample_equity_master, queue_path=queue)
        assert queue.exists(), "Review queue should be created"
        queued = pd.read_csv(queue)
        assert any(queued["symbol"] == "ADANIPORTS")
        logger.debug(f"[G-C-01] PASS — {len(queued)} symbols in review queue")

    def test_null_count_logged_as_warning(self, sample_equity_master, caplog):
        """G-C-01: Number of null sectors logged as warning."""
        logger.debug("[G-C-01] test_null_count_logged_as_warning")
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            fill_null_sectors(sample_equity_master)
        assert any("UNCATEGORIZED" in r.message for r in caplog.records)
        logger.debug("[G-C-01] PASS — warning about null sectors emitted")

    def test_no_downstream_nulls_after_fill(self, sample_equity_master):
        """GUARD: After fill_null_sectors, zero nulls in sector column."""
        logger.debug("[G-C-01] test_no_downstream_nulls_after_fill")
        result = fill_null_sectors(sample_equity_master)
        assert result["sector_platform"].isnull().sum() == 0
        logger.debug("[G-C-01] PASS — zero nulls after fill")


class TestApplyManualOverrides:
    """G-C-02: Manual override CSV is always applied last and is immutable."""

    def test_override_applied_to_matching_symbol(self, tmp_dir, sample_equity_master):
        """GUARD: Override CSV entry applied to matching symbol."""
        logger.debug("[G-C-02] test_override_applied_to_matching_symbol")
        override_file = tmp_dir / "manual_override.csv"
        overrides = pd.DataFrame({
            "symbol": ["ADANIPORTS"],
            "sector_platform": ["LOGISTICS"],
            "theme_platform": ["INFRASTRUCTURE"],
        })
        overrides.to_csv(override_file, index=False)

        result = apply_manual_overrides(
            sample_equity_master, override_file, symbol_col="symbol",
            sector_col="sector_platform", theme_col="theme_platform"
        )
        row = result[result["symbol"] == "ADANIPORTS"].iloc[0]
        assert row["sector_platform"] == "LOGISTICS"
        assert row["theme_platform"] == "INFRASTRUCTURE"
        logger.debug(f"[G-C-02] PASS — ADANIPORTS overridden to LOGISTICS/INFRASTRUCTURE")

    def test_non_matching_symbol_unchanged(self, tmp_dir, sample_equity_master):
        """GUARD: Symbols not in override CSV are not modified."""
        logger.debug("[G-C-02] test_non_matching_symbol_unchanged")
        override_file = tmp_dir / "manual_override.csv"
        pd.DataFrame({"symbol": ["ADANIPORTS"], "sector_platform": ["LOGISTICS"],
                      "theme_platform": ["INFRASTRUCTURE"]}).to_csv(override_file, index=False)

        result = apply_manual_overrides(sample_equity_master, override_file)
        tcs_sector = result[result["symbol"] == "TCS"].iloc[0]["sector_platform"]
        assert tcs_sector == "IT"
        logger.debug("[G-C-02] PASS — TCS sector unchanged")

    def test_no_override_file_returns_unchanged(self, tmp_dir, sample_equity_master):
        """EDGE: Missing override file → DataFrame returned unchanged."""
        logger.debug("[G-C-02] test_no_override_file_returns_unchanged")
        non_existent = tmp_dir / "no_such_file.csv"
        result = apply_manual_overrides(sample_equity_master, non_existent)
        assert len(result) == len(sample_equity_master)
        logger.debug("[G-C-02] PASS — unchanged when no override file")

    def test_override_beats_engine_classification(self, tmp_dir):
        """G-C-02: Override value wins even if engine classified differently."""
        logger.debug("[G-C-02] test_override_beats_engine_classification")
        # Engine classified ADANIPORTS as AEROSPACE (wrong)
        df = pd.DataFrame({
            "symbol": ["ADANIPORTS"],
            "sector_platform": ["AEROSPACE"],   # wrong engine result
            "theme_platform": [None],
        })
        override_file = tmp_dir / "override.csv"
        pd.DataFrame({"symbol": ["ADANIPORTS"],
                      "sector_platform": ["LOGISTICS"],
                      "theme_platform": ["INFRASTRUCTURE"]}).to_csv(override_file, index=False)
        result = apply_manual_overrides(df, override_file)
        assert result.iloc[0]["sector_platform"] == "LOGISTICS"
        logger.debug("[G-C-02] PASS — override beats engine AEROSPACE→LOGISTICS")


class TestFlagLowConfidence:
    """G-C-03: Symbols with classification_confidence < 0.70 go to review queue."""

    def test_high_confidence_not_queued(self, tmp_dir, sample_equity_master):
        """HAPPY PATH: High-confidence symbols not added to review queue."""
        logger.debug("[G-C-03] test_high_confidence_not_queued")
        # Only TCS, INFY, RELIANCE, BANDHANBNK have conf ≥ 0.70 in fixture
        df = sample_equity_master[sample_equity_master["symbol"] != "ADANIPORTS"].copy()
        queue = tmp_dir / "review_queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert "ADANIPORTS" not in queued.get("symbol", pd.Series()).tolist()
        logger.debug("[G-C-03] PASS")

    def test_low_confidence_added_to_queue(self, tmp_dir, sample_equity_master):
        """GUARD: ADANIPORTS (confidence=0.40) → added to review queue."""
        logger.debug("[G-C-03] test_low_confidence_added_to_queue")
        queue = tmp_dir / "review_queue.csv"
        flag_low_confidence(sample_equity_master, threshold=0.70, queue_path=queue)
        assert queue.exists(), "Review queue should be created"
        queued = pd.read_csv(queue)
        assert any(queued["symbol"] == "ADANIPORTS")
        logger.debug(f"[G-C-03] PASS — ADANIPORTS (conf=0.40) in review queue")

    def test_boundary_exactly_at_threshold_not_queued(self, tmp_dir):
        """EDGE: Confidence exactly at threshold (0.70) → NOT queued."""
        logger.debug("[G-C-03] test_boundary_exactly_at_threshold_not_queued")
        df = pd.DataFrame({"symbol": ["X"], "classification_confidence": [0.70]})
        queue = tmp_dir / "queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert "X" not in queued.get("symbol", pd.Series()).tolist()
        logger.debug("[G-C-03] PASS — exactly at threshold not queued")

    def test_no_confidence_column_skips_gracefully(self, tmp_dir, sample_equity_master, caplog):
        """EDGE: No confidence column → function skips with warning."""
        logger.debug("[G-C-03] test_no_confidence_column_skips_gracefully")
        df = sample_equity_master.drop(columns=["classification_confidence"])
        queue = tmp_dir / "queue.csv"
        with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
            flag_low_confidence(df, threshold=0.70, queue_path=queue)
        assert any("No" in r.message and "confidence" in r.message for r in caplog.records)
        logger.debug("[G-C-03] PASS — graceful skip when column absent")
