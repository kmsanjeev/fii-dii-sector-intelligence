"""
Announcement Fetcher -- Phase 16B
Fetches NSE board meeting announcements and classifies them by outcome type.

Data source: nselib corporate actions / announcements
Output: data/NSE/shareholding/board_announcements.csv

Announcement types tracked:
  DIVIDEND         : dividend declared
  BUYBACK          : share buyback announced
  BONUS            : bonus share issue
  STOCK_SPLIT      : stock split
  AGM_EGM          : AGM/EGM called
  BOARD_MEETING    : board meeting for results
  ACQUISITION      : acquisition / merger announced
  FUNDRAISE        : QIP, rights issue, NCD
  EARNINGS_BEAT    : implied from results announcement context (via management_sentiment)

Guardrails:
  - G-D-02: atomic writes
  - G-A-01: rate limiting
  - G-A-03: recovery queue
"""

import time
import shutil
import re
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
OUTPUT_PATH = SHAREHOLDING_DIR / "board_announcements.csv"
EQUITY_MASTER = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# Keyword patterns for announcement classification
ANNOUNCEMENT_PATTERNS = {
    "DIVIDEND":      [r"dividend", r"interim.div", r"final.div"],
    "BUYBACK":       [r"buy.?back", r"repurchase"],
    "BONUS":         [r"bonus.share", r"bonus.issue"],
    "STOCK_SPLIT":   [r"stock.split", r"sub.?division"],
    "AGM_EGM":       [r"\bagm\b", r"\begm\b", r"annual.general", r"extraordinary.general"],
    "BOARD_MEETING": [r"board.meeting", r"board.of.director", r"board.meeting.for.result"],
    "ACQUISITION":   [r"acqui", r"merger", r"takeover", r"amalgamat"],
    "FUNDRAISE":     [r"\bqip\b", r"rights.issue", r"\bncd\b", r"preferential.allot"],
}


class AnnouncementFetcher:
    """
    Fetches board meeting outcomes and classifies them by type.
    Used to enrich management_sentiment_engine with structural signals.
    """

    def __init__(self, max_symbols: Optional[int] = None, lookback_days: int = 90):
        SHAREHOLDING_DIR.mkdir(parents=True, exist_ok=True)
        self.max_symbols = max_symbols
        self.lookback_days = lookback_days
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[AnnouncementFetcher] Starting board announcement fetch")

        symbols = self._load_symbols()
        if not symbols:
            return False

        if self.max_symbols:
            symbols = symbols[:self.max_symbols]

        all_rows: list[dict] = []
        for i, symbol in enumerate(symbols):
            rows = self._fetch_symbol(symbol)
            all_rows.extend(rows)
            if not rows:
                self.recovery.append({"symbol": symbol, "reason": "no_announcements"})

            if i % 100 == 0 and i > 0:
                logger.info(f"[AnnouncementFetcher] {i}/{len(symbols)}")
            time.sleep(cfg.API_DELAY)

        if not all_rows:
            logger.warning("[AnnouncementFetcher] No announcements fetched")
            return False

        df = pd.DataFrame(all_rows)
        df = df.drop_duplicates(subset=["symbol", "date", "announcement_type"])
        df = df.sort_values(["symbol", "date"], ascending=[True, False])

        self._save(df)
        if self.recovery:
            self._save_recovery()

        logger.info(f"[AnnouncementFetcher] Complete: {len(df)} announcements")
        return True

    def _load_symbols(self) -> list[str]:
        if not EQUITY_MASTER.exists():
            return []
        em = pd.read_csv(EQUITY_MASTER)
        series_col = next((c for c in ["series", "SERIES"] if c in em.columns), None)
        if series_col:
            em = em[em[series_col] == "EQ"]
        sym_col = next((c for c in ["symbol", "SYMBOL"] if c in em.columns), None)
        return em[sym_col].dropna().unique().tolist() if sym_col else []

    def _fetch_symbol(self, symbol: str) -> list[dict]:
        for attempt in range(cfg.MAX_RETRIES):
            try:
                from nselib import capital_market as cm
                # Try board meetings endpoint
                raw = cm.board_meeting_detail(symbol=symbol)
                if raw is not None and not (isinstance(raw, pd.DataFrame) and raw.empty):
                    return self._parse(symbol, raw)
                return []
            except AttributeError:
                # nselib may not have board_meeting_detail
                try:
                    from nselib import capital_market as cm
                    raw = cm.corporate_actions(symbol=symbol)
                    if raw is not None and not (isinstance(raw, pd.DataFrame) and raw.empty):
                        return self._parse(symbol, raw)
                    return []
                except Exception as e:
                    logger.debug(f"[AnnouncementFetcher] nselib corp actions failed {symbol}: {e}")
                    return []
            except Exception as e:
                if attempt < cfg.MAX_RETRIES - 1:
                    time.sleep(cfg.RETRY_DELAY * (2 ** attempt))
                else:
                    logger.debug(f"[AnnouncementFetcher] Failed {symbol}: {e}")
        return []

    def _parse(self, symbol: str, raw) -> list[dict]:
        try:
            df = raw if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw if isinstance(raw, list) else [raw])
            if df.empty:
                return []

            rows = []
            text_cols = [c for c in df.columns if any(kw in c.lower() for kw in
                         ["subject", "purpose", "description", "text", "detail"])]

            for _, r in df.iterrows():
                text = " ".join(str(r.get(c, "")) for c in text_cols).lower()
                date_raw = r.get("date", r.get("record_date", r.get("exDate", "")))

                ann_type = _classify(text)
                rows.append({
                    "symbol": symbol,
                    "date": str(date_raw)[:10],
                    "announcement_type": ann_type,
                    "text_snippet": text[:200],
                })
            return rows
        except Exception as e:
            logger.debug(f"[AnnouncementFetcher] Parse error {symbol}: {e}")
            return []

    def _save(self, df: pd.DataFrame):
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[AnnouncementFetcher] Saved {len(df)} rows -> {OUTPUT_PATH}")

    def _save_recovery(self):
        rdf = pd.DataFrame(self.recovery)
        existing = pd.read_csv(RECOVERY_QUEUE) if RECOVERY_QUEUE.exists() else pd.DataFrame()
        combined = pd.concat([existing, rdf], ignore_index=True).drop_duplicates()
        tmp = RECOVERY_QUEUE.with_suffix(".tmp.csv")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))


def _classify(text: str) -> str:
    for ann_type, patterns in ANNOUNCEMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return ann_type
    return "OTHER"


if __name__ == "__main__":
    engine = AnnouncementFetcher(max_symbols=20)
    engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        print(f"Announcements: {len(df)} records")
        print(df["announcement_type"].value_counts())
