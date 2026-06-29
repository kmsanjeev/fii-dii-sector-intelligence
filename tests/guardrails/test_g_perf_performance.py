"""
Guardrail Tests — Section 12: Performance (G-PERF-01 to G-PERF-04)
"""

import logging
from unittest.mock import patch

import pytest

from engines.common.guardrails import (
    chunk_symbol_list,
    warn_market_hours_batch,
)

logger = logging.getLogger(__name__)


class TestChunkSymbolList:
    """G-PERF-01: Process symbols in chunks of ≤100 to avoid memory spikes."""

    def test_single_chunk_when_small_list(self):
        """HAPPY PATH: 50 symbols → 1 chunk."""
        logger.debug("[G-PERF-01] test_single_chunk_when_small_list")
        symbols = [f"SYM{i}" for i in range(50)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        assert len(chunks) == 1
        assert len(chunks[0]) == 50
        logger.debug("[G-PERF-01] PASS — 50 symbols in 1 chunk")

    def test_exactly_chunk_size(self):
        """EDGE: Exactly 100 symbols → 1 chunk of 100."""
        logger.debug("[G-PERF-01] test_exactly_chunk_size")
        symbols = [f"SYM{i}" for i in range(100)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        assert len(chunks) == 1
        assert len(chunks[0]) == 100
        logger.debug("[G-PERF-01] PASS — 100 symbols in 1 chunk")

    def test_multiple_full_chunks(self):
        """HAPPY PATH: 300 symbols → 3 chunks of 100."""
        logger.debug("[G-PERF-01] test_multiple_full_chunks")
        symbols = [f"SYM{i}" for i in range(300)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        assert len(chunks) == 3
        assert all(len(c) == 100 for c in chunks)
        logger.debug("[G-PERF-01] PASS — 300 symbols in 3 chunks of 100")

    def test_last_chunk_has_remainder(self):
        """EDGE: 250 symbols → 2 full chunks + 1 partial chunk of 50."""
        logger.debug("[G-PERF-01] test_last_chunk_has_remainder")
        symbols = [f"SYM{i}" for i in range(250)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        assert len(chunks) == 3
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50
        logger.debug("[G-PERF-01] PASS — 250 symbols: 2×100 + 1×50")

    def test_all_symbols_preserved(self):
        """INTEGRITY: All symbols appear exactly once across all chunks."""
        logger.debug("[G-PERF-01] test_all_symbols_preserved")
        symbols = [f"SYM{i}" for i in range(213)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        flat = [sym for chunk in chunks for sym in chunk]
        assert len(flat) == 213, "Total symbols should equal input"
        assert sorted(flat) == sorted(symbols), "No symbols should be dropped or duplicated"
        logger.debug("[G-PERF-01] PASS — all 213 symbols preserved across chunks")

    def test_empty_list_returns_no_chunks(self):
        """EDGE: Empty input → no chunks generated."""
        logger.debug("[G-PERF-01] test_empty_list_returns_no_chunks")
        chunks = list(chunk_symbol_list([], chunk_size=100))
        assert chunks == []
        logger.debug("[G-PERF-01] PASS — empty input yields no chunks")

    def test_full_2123_symbol_universe(self):
        """REAL CASE: 2123 NSE EQ symbols → 22 chunks (21 of 100 + 1 of 23)."""
        logger.debug("[G-PERF-01] test_full_2123_symbol_universe")
        symbols = [f"SYM{i}" for i in range(2123)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=100))
        assert len(chunks) == 22, f"Expected 22 chunks, got {len(chunks)}"
        assert len(chunks[-1]) == 23
        logger.debug("[G-PERF-01] PASS — 2123 symbols: 21×100 + 1×23")

    def test_custom_chunk_size(self):
        """CONFIG: Custom chunk_size=50 splits correctly."""
        logger.debug("[G-PERF-01] test_custom_chunk_size")
        symbols = [f"SYM{i}" for i in range(150)]
        chunks = list(chunk_symbol_list(symbols, chunk_size=50))
        assert len(chunks) == 3
        assert all(len(c) == 50 for c in chunks)
        logger.debug("[G-PERF-01] PASS — chunk_size=50 works correctly")


class TestWarnMarketHoursBatch:
    """G-PERF-03: Warn when large batch (>50 symbols) called during market hours."""

    def test_small_batch_during_market_hours_no_warning(self, caplog):
        """HAPPY PATH: 10 symbols during market hours → no warning."""
        logger.debug("[G-PERF-03] test_small_batch_during_market_hours_no_warning")
        with patch("engines.common.guardrails.is_market_hours", return_value=True):
            with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
                warn_market_hours_batch(batch_size=10, limit=50)
        assert not any("market hours" in r.message.lower() for r in caplog.records)
        logger.debug("[G-PERF-03] PASS — small batch during market hours: no warning")

    def test_large_batch_during_market_hours_warns(self, caplog):
        """GUARD: 200 symbols during market hours → performance warning."""
        logger.debug("[G-PERF-03] test_large_batch_during_market_hours_warns")
        with patch("engines.common.guardrails.is_market_hours", return_value=True):
            with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
                warn_market_hours_batch(batch_size=200, limit=50)
        assert any("market hours" in r.message.lower() for r in caplog.records)
        logger.debug("[G-PERF-03] PASS — large batch during market hours warns")

    def test_large_batch_outside_market_hours_no_warning(self, caplog):
        """HAPPY PATH: 200 symbols after market close → no warning."""
        logger.debug("[G-PERF-03] test_large_batch_outside_market_hours_no_warning")
        with patch("engines.common.guardrails.is_market_hours", return_value=False):
            with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
                warn_market_hours_batch(batch_size=200, limit=50)
        assert not any("market hours" in r.message.lower() for r in caplog.records)
        logger.debug("[G-PERF-03] PASS — large batch after close: no warning")

    def test_exactly_at_limit_no_warning(self, caplog):
        """EDGE: batch_size == limit → no warning (boundary is exclusive)."""
        logger.debug("[G-PERF-03] test_exactly_at_limit_no_warning")
        with patch("engines.common.guardrails.is_market_hours", return_value=True):
            with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
                warn_market_hours_batch(batch_size=50, limit=50)
        assert not any("market hours" in r.message.lower() for r in caplog.records)
        logger.debug("[G-PERF-03] PASS — exactly at limit: no warning")

    def test_one_over_limit_warns(self, caplog):
        """EDGE: batch_size == limit + 1 → warning emitted."""
        logger.debug("[G-PERF-03] test_one_over_limit_warns")
        with patch("engines.common.guardrails.is_market_hours", return_value=True):
            with caplog.at_level(logging.WARNING, logger="engines.common.guardrails"):
                warn_market_hours_batch(batch_size=51, limit=50)
        assert any("market hours" in r.message.lower() for r in caplog.records)
        logger.debug("[G-PERF-03] PASS — one-over-limit warns")
