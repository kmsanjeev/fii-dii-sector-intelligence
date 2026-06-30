"""
Announcement Fetcher -- Phase 16B
Fetches NSE corporate action announcements and classifies them by type.

Data source: nselib corporate_actions_for_equity (bulk date-range, all companies)
Output: data/NSE/shareholding/board_announcements.csv

Announcement types tracked:
  DIVIDEND, BUYBACK, BONUS, STOCK_SPLIT, AGM_EGM, BOARD_MEETING, ACQUISITION, FUNDRAISE

Guardrails:
  - G-D-02: atomic writes
  - G-A-01: rate limiting
"""

import re
import shutil
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
OUTPUT_PATH = SHAREHOLDING_DIR / "board_announcements.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# Fetch last 6 months (nselib bulk endpoint)
FETCH_PERIOD = "6M"

ANNOUNCEMENT_PATTERNS = {
    "DIVIDEND":      [r"dividend", r"interim.div", r"final.div"],
    "BUYBACK":       [r"buy.?back", r"repurchase"],
    "BONUS":         [r"bonus.share", r"bonus.issue", r"\bbonus\b"],
    "STOCK_SPLIT":   [r"stock.split", r"sub.?division", r"face.value.split"],
    "AGM_EGM":       [r"\bagm\b", r"\begm\b", r"annual.general", r"extraordinary.general"],
    "BOARD_MEETING": [r"board.meeting", r"board.of.director"],
    "ACQUISITION":   [r"acqui", r"merger", r"takeover", r"amalgamat"],
    "FUNDRAISE":     [r"\bqip\b", r"rights", r"\bncd\b", r"preferential.allot"],
}


class AnnouncementFetcher:
    """
    Fetches corporate actions bulk from nselib and classifies by announcement type.
    """

    def __init__(self, max_symbols: Optional[int] = None, lookback_days: int = 180):
        SHAREHOLDING_DIR.mkdir(parents=True, exist_ok=True)
        self.max_symbols = max_symbols
        self.lookback_days = lookback_days
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[AnnouncementFetcher] Starting announcement fetch via nselib bulk")

        all_rows = self._fetch_bulk()
        if not all_rows:
            logger.warning("[AnnouncementFetcher] No announcements fetched from nselib")
            return False

        df = pd.DataFrame(all_rows)

        # Filter to EQ series only (G-S-01)
        if "series" in df.columns:
            df = df[df["series"] == "EQ"]

        # Optionally limit symbols
        if self.max_symbols:
            symbols = df["symbol"].unique()[:self.max_symbols]
            df = df[df["symbol"].isin(symbols)]

        df = df.drop_duplicates(subset=["symbol", "date", "announcement_type"])
        df = df.sort_values(["symbol", "date"], ascending=[True, False])

        if df.empty:
            return False

        self._save(df)
        logger.info(f"[AnnouncementFetcher] Complete: {len(df)} announcements, "
                    f"{df['symbol'].nunique()} symbols")
        return True

    def _fetch_bulk(self) -> list[dict]:
        """Bulk fetch: one call returns all companies' corporate actions."""
        try:
            from nselib import capital_market as cm
            raw = cm.corporate_actions_for_equity(period=FETCH_PERIOD)
            if raw is None or raw.empty:
                return []
            logger.info(f"[AnnouncementFetcher] nselib returned {len(raw)} rows")
            return self._parse_bulk(raw)
        except Exception as e:
            logger.warning(f"[AnnouncementFetcher] nselib bulk fetch failed: {e}")
            return []

    def _parse_bulk(self, df: pd.DataFrame) -> list[dict]:
        """
        Parse nselib corporate_actions_for_equity DataFrame.
        Expected columns: symbol, series, subject, exDate, recDate, comp
        """
        rows = []
        for _, r in df.iterrows():
            sym = str(r.get("symbol", "")).strip().upper()
            if not sym:
                continue

            subject = str(r.get("subject", "")).strip()
            series = str(r.get("series", "EQ")).strip()
            date_raw = r.get("recDate") or r.get("exDate") or r.get("caBroadcastDate") or ""
            date_str = _normalize_date(str(date_raw)) if date_raw else ""
            ann_type = _classify(subject)

            rows.append({
                "symbol": sym,
                "series": series,
                "date": date_str,
                "announcement_type": ann_type,
                "text_snippet": subject[:200],
            })
        return rows

    def _save(self, df: pd.DataFrame):
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[AnnouncementFetcher] Saved {len(df)} rows -> {OUTPUT_PATH}")


def _classify(text: str) -> str:
    text = text.lower()
    for ann_type, patterns in ANNOUNCEMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return ann_type
    return "OTHER"


def _normalize_date(date_str: str) -> str:
    """Convert dd-Mon-yyyy or dd-mm-yyyy to yyyy-mm-dd."""
    import re as re_mod
    # Already ISO format
    if re_mod.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    # dd-Mon-yyyy (e.g. 02-Jan-2026)
    months = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
              "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
              "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    m = re_mod.match(r"(\d{2})-([A-Za-z]{3})-(\d{4})", date_str)
    if m:
        d, mon, y = m.groups()
        mon_num = months.get(mon.capitalize(), "01")
        return f"{y}-{mon_num}-{d}"
    return date_str[:10]


if __name__ == "__main__":
    engine = AnnouncementFetcher()
    engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        print(f"Announcements: {len(df)} records, {df['symbol'].nunique()} symbols")
        print(df["announcement_type"].value_counts())
        print(df.head(10)[["symbol", "date", "announcement_type", "text_snippet"]].to_string())
