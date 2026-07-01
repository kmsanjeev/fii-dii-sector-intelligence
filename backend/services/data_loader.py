"""
Data Loader — Phase 10
Loads all intelligence CSVs into memory at startup.
Auto-reloads every 60 minutes via background thread.
Thread-safe reads via a shared state dict + lock.
"""

import threading
import time
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RELOAD_INTERVAL_S = 3600  # 60 minutes

# ── Source files ──────────────────────────────────────────────────────────────

SOURCES = {
    "participant_intel":    cfg.INTELLIGENCE_DIR / "participant_intelligence.csv",
    "participant_flows":    cfg.INTELLIGENCE_DIR / "participant_flow_scores.csv",
    "sector_rotation":      cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv",
    "sector_flows":         cfg.INTELLIGENCE_DIR / "sector_flow_scores.csv",
    "bull_run":             cfg.INTELLIGENCE_DIR / "bull_run_probability.csv",
    "bull_run_watchlist":   cfg.INTELLIGENCE_DIR / "bull_run_watchlist.csv",
    "deal_signals":         cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv",
    "event_calendar":       cfg.INTELLIGENCE_DIR / "event_calendar.csv",
    "upcoming_catalysts":   cfg.INTELLIGENCE_DIR / "upcoming_catalysts.csv",
    "corporate_confidence": cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv",
    "price_momentum":       cfg.INTELLIGENCE_DIR / "price_momentum.csv",
    # Phase 15 — Fundamentals
    "valuation_scores":     cfg.NSE_DIR / "results" / "valuation_scores.csv",
    "shareholding":         cfg.NSE_DIR / "shareholding" / "quarterly_shp.csv",
}

_lock = threading.Lock()
_data: dict[str, Optional[pd.DataFrame]] = {k: None for k in SOURCES}
_loaded_at: dict[str, Optional[str]] = {k: None for k in SOURCES}


def _load_all():
    loaded = 0
    for key, path in SOURCES.items():
        if not path.exists():
            logger.warning(f"[DataLoader] Missing: {path.name}")
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
            with _lock:
                _data[key] = df
                _loaded_at[key] = pd.Timestamp.now().isoformat()
            loaded += 1
            logger.debug(f"[DataLoader] Loaded {path.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"[DataLoader] Failed to load {path.name}: {e}")

    logger.info(f"[DataLoader] Loaded {loaded}/{len(SOURCES)} intelligence files")


def _reload_loop():
    while True:
        time.sleep(RELOAD_INTERVAL_S)
        logger.info("[DataLoader] Auto-reload triggered")
        _load_all()


def startup():
    """Load all data at app startup and launch background reload thread."""
    _load_all()
    t = threading.Thread(target=_reload_loop, daemon=True)
    t.start()
    logger.info("[DataLoader] Background reload thread started (60 min interval)")


def get(key: str) -> Optional[pd.DataFrame]:
    """Thread-safe getter for a loaded DataFrame. Returns None if not available."""
    with _lock:
        return _data.get(key)


def freshness() -> dict:
    """Return load timestamps for all datasets."""
    with _lock:
        return {k: v for k, v in _loaded_at.items()}
