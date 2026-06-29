"""
Shared pytest fixtures and logging configuration for all test suites.
Every test session writes a full DEBUG log to tests/logs/pytest_debug.log.
"""

import logging
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

# ─── Log directory setup ──────────────────────────────────────────────────────
TESTS_DIR = Path(__file__).parent
LOG_DIR = TESTS_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def pytest_configure(config):
    """Ensure log directory exists before any test runs."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# ─── Session-level fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_logger():
    """Return a DEBUG-level logger that writes to tests/logs/test_session.log."""
    logger = logging.getLogger("test_session")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_DIR / "test_session.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        ))
        logger.addHandler(fh)
    return logger


@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def nse_holidays():
    """Minimal NSE holiday set for 2024 (for testing calendar logic)."""
    return {
        date(2024, 1, 26),   # Republic Day
        date(2024, 3, 25),   # Holi
        date(2024, 3, 29),   # Good Friday
        date(2024, 4, 14),   # Ambedkar Jayanti (observed)
        date(2024, 4, 17),   # Ram Navami
        date(2024, 5, 23),   # Budh Purnima
        date(2024, 6, 17),   # Bakri Eid
        date(2024, 7, 17),   # Muharram
        date(2024, 8, 15),   # Independence Day
        date(2024, 10, 2),   # Gandhi Jayanti
        date(2024, 11, 1),   # Diwali Laxmi Pujan
        date(2024, 11, 15),  # Gurunanak Jayanti
        date(2024, 12, 25),  # Christmas
    }


# ─── Function-level fixtures ──────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    """Provide a temporary directory that is cleaned up after each test."""
    d = Path(tempfile.mkdtemp(prefix="cfip_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_bhavcopy_df():
    """Minimal valid bhavcopy DataFrame (EQ series, positive OHLCV)."""
    return pd.DataFrame({
        "symbol": ["TCS", "INFY", "RELIANCE"],
        "series": ["EQ", "EQ", "EQ"],
        "date": ["2024-01-15", "2024-01-15", "2024-01-15"],
        "open": [3500.0, 1400.0, 2400.0],
        "high": [3550.0, 1450.0, 2450.0],
        "low": [3480.0, 1390.0, 2380.0],
        "close": [3530.0, 1430.0, 2420.0],
        "volume": [500000, 750000, 1200000],
        "delivery_pct": [45.0, 52.0, 38.0],
    })


@pytest.fixture
def sample_equity_master():
    """Minimal equity master with 5 EQ symbols."""
    return pd.DataFrame({
        "symbol": ["TCS", "INFY", "RELIANCE", "ADANIPORTS", "BANDHANBNK"],
        "isin": ["INE467B01029", "INE009A01021", "INE002A01018", "INE742F01042", "INE545U01014"],
        "company_name": ["TATA CONSULTANCY SVCS", "INFOSYS", "RELIANCE INDUSTRIES",
                         "ADANI PORTS AND SEZ", "BANDHAN BANK"],
        "series": ["EQ", "EQ", "EQ", "EQ", "EQ"],
        "status": ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE"],
        "listing_date": ["2004-08-25", "1999-02-11", "1977-11-28", "2008-11-27", "2018-03-27"],
        "sector_platform": ["IT", "IT", "ENERGY", None, "BANKING"],
        "theme_platform": ["DIGITAL_INDIA", "DIGITAL_INDIA", "ENERGY", None, "FINANCIALISATION"],
        "classification_confidence": [0.95, 0.95, 0.90, 0.40, 0.85],
    })


@pytest.fixture
def sample_institutional_df():
    """Minimal institutional positioning DataFrame with gross flows."""
    return pd.DataFrame({
        "date": ["2024-01-15", "2024-01-16", "2024-01-17"],
        "fii_buy":  [15000.0, 12000.0, 18000.0],
        "fii_sell": [10000.0, 14000.0, 11000.0],
        "fii_net":  [5000.0, -2000.0, 7000.0],
        "dii_buy":  [8000.0, 11000.0, 9000.0],
        "dii_sell": [6000.0, 7000.0, 10000.0],
        "dii_net":  [2000.0, 4000.0, -1000.0],
    })


@pytest.fixture
def sample_results_df():
    """Minimal financial results DataFrame."""
    return pd.DataFrame({
        "symbol": ["TCS", "TCS", "TCS", "TCS"],
        "quarter": ["Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25"],
        "quarter_end_month": [6, 9, 12, 3],
        "revenue": [62613.0, 63974.0, 63973.0, 65406.0],
        "ebitda": [15842.0, 16396.0, 16348.0, 16855.0],
        "pat": [12040.0, 12447.0, 12380.0, 12750.0],
        "eps": [33.10, 34.27, 34.08, 35.10],
    })


@pytest.fixture(autouse=True)
def log_test_boundaries(request, test_logger):
    """Auto-log test start/end with test name for every test function."""
    test_logger.debug(f"{'='*60}")
    test_logger.debug(f"TEST START: {request.node.nodeid}")
    yield
    test_logger.debug(f"TEST END:   {request.node.nodeid}")
    test_logger.debug(f"{'='*60}")


# ─── Mock env fixture ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Inject required platform env vars for tests that need them."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1234567890:AAAA-test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456789")
    monkeypatch.setenv("GOOGLE_CREDENTIALS", '{"type":"service_account"}')
    yield


@pytest.fixture
def missing_env(monkeypatch):
    """Remove required env vars to test guard failures."""
    for var in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GOOGLE_CREDENTIALS"]:
        monkeypatch.delenv(var, raising=False)
    yield
