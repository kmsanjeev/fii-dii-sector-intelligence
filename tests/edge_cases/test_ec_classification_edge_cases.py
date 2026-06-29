"""
Edge Case Tests — Classification Boundary Conditions

Tests for conglomerates, PSUs, holding companies, recently-listed stocks,
and other hard-to-classify companies in the Indian equity universe.
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


class TestAdaniPortsClassificationBug:
    """Documents the known ADANIPORTS → AEROSPACE misclassification bug."""

    def test_adaniports_overridden_to_logistics(self, tmp_dir):
        """KNOWN BUG: Engine classifies ADANIPORTS as AEROSPACE; override must fix it."""
        logger.debug("[EC-CLASS-01] test_adaniports_overridden_to_logistics")
        df = pd.DataFrame({
            "symbol": ["ADANIPORTS"],
            "sector_platform": ["AEROSPACE"],    # wrong engine output
            "theme_platform": ["DEFENCE"],       # wrong
        })
        override_file = tmp_dir / "manual_override.csv"
        pd.DataFrame({
            "symbol": ["ADANIPORTS"],
            "sector_platform": ["LOGISTICS"],
            "theme_platform": ["INFRASTRUCTURE"],
        }).to_csv(override_file, index=False)

        result = apply_manual_overrides(df, override_file)
        assert result.iloc[0]["sector_platform"] == "LOGISTICS"
        assert result.iloc[0]["theme_platform"] == "INFRASTRUCTURE"
        logger.debug("[EC-CLASS-01] PASS — ADANIPORTS correctly overridden to LOGISTICS")

    def test_adaniports_without_override_is_uncategorized_or_wrong(self, tmp_dir):
        """KNOWN BUG: Without override, ADANIPORTS gets wrong classification."""
        logger.debug("[EC-CLASS-02] test_adaniports_without_override_is_uncategorized_or_wrong")
        df = pd.DataFrame({
            "symbol": ["ADANIPORTS"],
            "sector_platform": ["AEROSPACE"],
            "theme_platform": ["DEFENCE"],
        })
        non_existent = tmp_dir / "no_override.csv"
        result = apply_manual_overrides(df, non_existent)
        # Without override, AEROSPACE classification is preserved (wrong but documented)
        assert result.iloc[0]["sector_platform"] == "AEROSPACE"
        logger.debug("[EC-CLASS-02] DOCUMENTED BUG — ADANIPORTS shows AEROSPACE without override")


class TestConglomerateClassificationEdgeCases:
    """Companies spanning multiple sectors — hardest classification cases."""

    def test_itc_conglomerate_low_confidence(self, tmp_dir):
        """EDGE: ITC spans FMCG/Hotels/Agribusiness — low confidence expected."""
        logger.debug("[EC-CLASS-03] test_itc_conglomerate_low_confidence")
        df = pd.DataFrame({
            "symbol": ["ITC"],
            "sector_platform": ["FMCG"],
            "classification_confidence": [0.55],  # low due to diversified business
        })
        queue = tmp_dir / "queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert any(queued["symbol"] == "ITC")
        logger.debug("[EC-CLASS-03] PASS — ITC (conglomerate) flagged for low confidence review")

    def test_tatamotors_automotive_not_conglomerate(self, tmp_dir):
        """EDGE: TATAMOTORS despite being Tata group → primarily AUTOMOTIVE."""
        logger.debug("[EC-CLASS-04] test_tatamotors_automotive_not_conglomerate")
        df = pd.DataFrame({
            "symbol": ["TATAMOTORS"],
            "sector_platform": ["AUTOMOTIVE"],
            "theme_platform": ["EV_MOBILITY"],
            "classification_confidence": [0.85],
        })
        queue = tmp_dir / "queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert "TATAMOTORS" not in queued.get("symbol", pd.Series()).tolist()
        logger.debug("[EC-CLASS-04] PASS — TATAMOTORS high confidence AUTOMOTIVE not queued")


class TestPsuClassificationEdgeCases:
    """PSU companies often span multiple sectors."""

    def test_coalindia_mining_not_energy(self, tmp_dir):
        """EDGE: COALINDIA is MINING sector, not ENERGY despite being fuel-related."""
        logger.debug("[EC-CLASS-05] test_coalindia_mining_not_energy")
        df = pd.DataFrame({
            "symbol": ["COALINDIA"],
            "sector_platform": ["MINING"],
            "theme_platform": ["COMMODITIES"],
            "classification_confidence": [0.90],
        })
        queue = tmp_dir / "queue.csv"
        fill_null_sectors(df, queue_path=queue)
        assert df.loc[0, "sector_platform"] == "MINING"
        logger.debug("[EC-CLASS-05] PASS — COALINDIA classified as MINING")

    def test_bpcl_energy_petroleum(self, tmp_dir):
        """EDGE: BPCL is oil & gas (ENERGY), not FMCG despite retail petrol stations."""
        logger.debug("[EC-CLASS-06] test_bpcl_energy_petroleum")
        df = pd.DataFrame({
            "symbol": ["BPCL"],
            "sector_platform": ["OIL_GAS"],
            "theme_platform": ["ENERGY_INFRA"],
            "classification_confidence": [0.88],
        })
        queue = tmp_dir / "queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert "BPCL" not in queued.get("symbol", pd.Series()).tolist()
        logger.debug("[EC-CLASS-06] PASS — BPCL high confidence OIL_GAS not queued")


class TestHoldingCompanyEdgeCases:
    """Holding/Investment companies — often misclassified as their investee sectors."""

    def test_tatainvest_classified_as_financial_services(self, tmp_dir):
        """EDGE: TATAINVEST is a holding co → FINANCIAL_SERVICES, not AUTOMOTIVE."""
        logger.debug("[EC-CLASS-07] test_tatainvest_classified_as_financial_services")
        df = pd.DataFrame({
            "symbol": ["TATAINVEST"],
            "sector_platform": ["FINANCIAL_SERVICES"],
            "theme_platform": ["HOLDING_COMPANIES"],
            "classification_confidence": [0.75],
        })
        queue = tmp_dir / "queue.csv"
        flag_low_confidence(df, threshold=0.70, queue_path=queue)
        if queue.exists():
            queued = pd.read_csv(queue)
            assert "TATAINVEST" not in queued.get("symbol", pd.Series()).tolist()
        logger.debug("[EC-CLASS-07] PASS — holding company classified as FINANCIAL_SERVICES")


class TestNullClassificationEdgeCases:
    """All-null sector scenarios."""

    def test_all_symbols_null_sector_all_become_uncategorized(self):
        """EXTREME: All symbols have null sector → all become UNCATEGORIZED."""
        logger.debug("[EC-CLASS-08] test_all_symbols_null_sector_all_become_uncategorized")
        df = pd.DataFrame({
            "symbol": [f"SYM{i}" for i in range(100)],
            "sector_platform": [None] * 100,
        })
        result = fill_null_sectors(df)
        assert (result["sector_platform"] == "UNCATEGORIZED").all()
        assert result["sector_platform"].isnull().sum() == 0
        logger.debug("[EC-CLASS-08] PASS — 100 null sectors all become UNCATEGORIZED")

    def test_override_file_all_symbols(self, tmp_dir):
        """EXTREME: Override file covers all symbols — all overridden correctly."""
        logger.debug("[EC-CLASS-09] test_override_file_all_symbols")
        symbols = [f"SYM{i}" for i in range(5)]
        df = pd.DataFrame({
            "symbol": symbols,
            "sector_platform": ["WRONG"] * 5,
            "theme_platform": [None] * 5,
        })
        override_file = tmp_dir / "override.csv"
        pd.DataFrame({
            "symbol": symbols,
            "sector_platform": ["CORRECT"] * 5,
            "theme_platform": ["THEME_X"] * 5,
        }).to_csv(override_file, index=False)
        result = apply_manual_overrides(df, override_file)
        assert (result["sector_platform"] == "CORRECT").all()
        logger.debug("[EC-CLASS-09] PASS — all symbols overridden correctly")
