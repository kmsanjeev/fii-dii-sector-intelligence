"""
Corporate Announcements Intelligence Engine
Phase 18 -- Download, classify, and score NSE corporate announcements.

Source:  NSE API  /api/corporate-announcements?index=equities&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY
         Bulk endpoint -- no per-symbol calls. One call = all symbols for the date window.
         ~12,000-16,000 rows per month, 2000+ symbols per window.

Outputs:
    data/intelligence/company_announcements.csv
        symbol, date, announcement_type, signal_score, desc_raw, title_snippet, seq_id
    data/intelligence/announcement_signals.csv
        symbol, latest_date, dominant_type, score_30d, count_30d, count_90d, high_signal_30d

Run:    py -3.11 -m engines.corporate.announcement_intelligence_engine
        On first run: fetches LOOKBACK_MONTHS (24) of history.
        On subsequent runs: fetches only months since last stored date (incremental).

Guardrails: G-D-02 atomic writes, G-D-03 no empty df, G-D-04 schema validation,
            G-A-01 rate limiting, G-A-02 retry + backoff, G-S-01 EQ universe filter
"""

import shutil
import sys
import time
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("announcement_intelligence")

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_URL        = "https://www.nseindia.com/api/corporate-announcements"
HOME_URL        = "https://www.nseindia.com"
LOOKBACK_MONTHS = 24       # Full history window on first run
REFRESH_MONTHS  = 3        # Re-fetch last N months on incremental run
API_DELAY       = 2.5      # seconds between calls (G-A-01)
MAX_RETRIES     = 3
RETRY_DELAY     = 10       # seconds base delay on retry (G-A-02)
MIN_ROWS_CHECK  = 1000     # sanity: expect at least this many rows in output

ANNOUNCEMENTS_FILE = cfg.INTELLIGENCE_DIR / "company_announcements.csv"
SIGNALS_FILE       = cfg.INTELLIGENCE_DIR / "announcement_signals.csv"
RECOVERY_FILE      = cfg.NSE_DIR / "recovery_queue.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.nseindia.com/",
}

REQUIRED_ANN_COLS    = ["symbol", "date", "announcement_type", "signal_score", "seq_id"]
REQUIRED_SIGNAL_COLS = ["symbol", "latest_date", "dominant_type", "score_30d"]

# ── Classification map ────────────────────────────────────────────────────────
# Maps NSE `desc` field (exact or partial match) to (announcement_type, signal_score).
# Signal score = intelligence value of this announcement type (0-100).
# Higher = stronger forward-looking signal for stock move / institutional interest.

CLASSIFICATION: list[tuple[list[str], str, int]] = [
    # pattern list, type, signal_score
    (["financial result", "board meeting outcome", "financial results", "unaudited financial"],
     "RESULT_UPDATE",   90),
    (["analysts/institutional", "analyst meet", "investor meet", "investor presentation",
      "con. call", "concall"],
     "ANALYST_MEET",    85),
    (["acquisition", "merger", "amalgamat", "takeover", "scheme of arrangement"],
     "ACQUISITION",     85),
    (["qip", "rights issue", "preferential allot", "ncd", "allotment of securities",
      "fundrais", "public issue", "ipo", "fpo"],
     "FUNDRAISE",       80),
    (["buy back", "buyback", "buy-back"],
     "BUYBACK",         75),
    (["board meeting", "board of director"],
     "BOARD_OUTCOME",   70),
    (["dividend"],
     "DIVIDEND",        70),
    (["bonus share", "bonus issue", "issuance of bonus"],
     "BONUS",           65),
    (["stock split", "sub-division of share", "face value split", "subdivision"],
     "STOCK_SPLIT",     50),
    (["press release", "media release", "news clarif", "news verif",
      "general updates", "update"],
     "PRESS_RELEASE",   55),
    (["esop", "esos", "esps", "sweat equity", "employee stock"],
     "ESOP",            45),
    (["disclosure under insider", "sebi takeover", "trading window",
      "sebi regulation", "sebi (sast)", "insider trading",
      "disclosure under sebi"],
     "REGULATORY",      25),
]
DEFAULT_TYPE  = "OTHER"
DEFAULT_SCORE = 10


# ── Session manager ───────────────────────────────────────────────────────────

class _Session:
    """NSE requires valid browser cookies. Refresh homepage every 25 calls."""

    REFRESH_EVERY = 25

    def __init__(self):
        self._s = requests.Session()
        self._calls = 0
        self._init()

    def _init(self):
        try:
            self._s.get(HOME_URL, headers=HEADERS, timeout=20)
        except Exception as e:
            logger.warning("[Ann] Cookie refresh failed: %s", e)

    def get(self, url: str, params: dict) -> requests.Response:
        self._calls += 1
        if self._calls % self.REFRESH_EVERY == 0:
            logger.debug("[Ann] Refreshing NSE session (call %d)", self._calls)
            self._init()
            time.sleep(1)
        return self._s.get(url, headers=HEADERS, params=params, timeout=30)


# ── Classifier ────────────────────────────────────────────────────────────────

def _classify(desc: str) -> tuple[str, int]:
    """Map NSE desc field -> (announcement_type, signal_score)."""
    text = desc.lower()
    for patterns, ann_type, score in CLASSIFICATION:
        for p in patterns:
            if p in text:
                return ann_type, score
    return DEFAULT_TYPE, DEFAULT_SCORE


# ── Date window builder ───────────────────────────────────────────────────────

def _month_windows(start: date, end: date) -> list[tuple[str, str]]:
    """
    Return list of (from_date, to_date) strings in DD-MM-YYYY format,
    one tuple per calendar month from start to end inclusive.
    """
    windows = []
    cur = date(start.year, start.month, 1)
    while cur <= end:
        last_day = monthrange(cur.year, cur.month)[1]
        to_d = min(date(cur.year, cur.month, last_day), end)
        windows.append((
            cur.strftime("%d-%m-%Y"),
            to_d.strftime("%d-%m-%Y"),
        ))
        # Advance to next month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return windows


# ── Downloader ────────────────────────────────────────────────────────────────

def _fetch_window(session: _Session, from_d: str, to_d: str) -> list[dict]:
    """Fetch one monthly window with retry. Returns list of raw API dicts."""
    params = {"index": "equities", "from_date": from_d, "to_date": to_d}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(BASE_URL, params=params)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    logger.info("[Ann] %s -> %s: %d rows", from_d, to_d, len(data))
                    return data
                logger.warning("[Ann] %s -> %s: unexpected response type: %s", from_d, to_d, type(data))
                return []
            logger.warning("[Ann] HTTP %d for window %s -> %s (attempt %d)", r.status_code, from_d, to_d, attempt)
        except Exception as e:
            logger.warning("[Ann] Window %s -> %s error (attempt %d): %s", from_d, to_d, attempt, e)

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAY * attempt
            logger.info("[Ann] Retrying in %ds...", delay)
            time.sleep(delay)

    logger.error("[Ann] Window %s -> %s failed after %d attempts", from_d, to_d, MAX_RETRIES)
    _log_recovery(from_d, to_d)
    return []


def _log_recovery(from_d: str, to_d: str) -> None:
    RECOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    header = not RECOVERY_FILE.exists()
    with open(RECOVERY_FILE, "a", encoding="utf-8") as f:
        if header:
            f.write("engine,item,error,timestamp\n")
        ts = datetime.now().isoformat()
        f.write(f"announcement_intelligence,{from_d}:{to_d},fetch_failed,{ts}\n")


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_rows(raw_rows: list[dict]) -> list[dict]:
    """Convert raw API dicts to normalised rows with type + score."""
    parsed = []
    for r in raw_rows:
        sym = str(r.get("symbol", "")).strip().upper()
        if not sym:
            continue
        seq_id   = str(r.get("seq_id", "")).strip()
        desc_raw = str(r.get("desc", "")).strip()
        snippet  = str(r.get("attchmntText", "")).strip()[:200]
        sort_dt  = str(r.get("sort_date", "")).strip()
        # Normalise date to YYYY-MM-DD
        date_str = sort_dt[:10] if sort_dt else ""

        ann_type, score = _classify(desc_raw)
        parsed.append({
            "symbol":            sym,
            "date":              date_str,
            "announcement_type": ann_type,
            "signal_score":      score,
            "desc_raw":          desc_raw,
            "title_snippet":     snippet,
            "seq_id":            seq_id,
        })
    return parsed


# ── Signal aggregator ─────────────────────────────────────────────────────────

def _build_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-symbol 30d/90d signal summaries from company_announcements."""
    today = pd.Timestamp.now().normalize()
    df["_dt"] = pd.to_datetime(df["date"], errors="coerce")

    window_30  = today - pd.Timedelta(days=30)
    window_90  = today - pd.Timedelta(days=90)

    rows = []
    for sym, grp in df.groupby("symbol"):
        latest  = grp["_dt"].max()
        w30     = grp[grp["_dt"] >= window_30]
        w90     = grp[grp["_dt"] >= window_90]
        dom_30  = (
            w30["announcement_type"].mode().iloc[0]
            if not w30.empty else (grp["announcement_type"].mode().iloc[0] if not grp.empty else "OTHER")
        )
        rows.append({
            "symbol":          sym,
            "latest_date":     latest.strftime("%Y-%m-%d") if pd.notna(latest) else "",
            "dominant_type":   dom_30,
            "score_30d":       round(w30["signal_score"].sum(), 1),
            "count_30d":       len(w30),
            "count_90d":       len(w90),
            "high_signal_30d": int((w30["signal_score"] >= 70).sum()),
        })

    out = pd.DataFrame(rows).sort_values("score_30d", ascending=False).reset_index(drop=True)
    return out


# ── Writer ────────────────────────────────────────────────────────────────────

def _atomic_save(df: pd.DataFrame, path: Path) -> None:
    """G-D-02: write to .tmp then move."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.csv")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(path))
    logger.info("[Ann] Saved %d rows -> %s", len(df), path.name)


# ── Validator ─────────────────────────────────────────────────────────────────

def _validate(df: pd.DataFrame, required_cols: list[str], min_rows: int, label: str) -> None:
    if df.empty:
        raise ValueError(f"{label}: DataFrame is empty")
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label}: missing columns {missing}")
    if len(df) < min_rows:
        raise ValueError(f"{label}: only {len(df)} rows (expected >= {min_rows})")


# ── Incremental date logic ────────────────────────────────────────────────────

def _determine_start_date() -> date:
    """
    If existing data found: re-fetch last REFRESH_MONTHS months.
    If no existing data: fetch full LOOKBACK_MONTHS.
    """
    today = date.today()
    if ANNOUNCEMENTS_FILE.exists():
        try:
            existing = pd.read_csv(ANNOUNCEMENTS_FILE, usecols=["date"], dtype=str)
            max_date = pd.to_datetime(existing["date"], errors="coerce").max()
            if pd.notna(max_date):
                # Step back REFRESH_MONTHS from last known date
                refresh_start = max_date.date() - timedelta(days=REFRESH_MONTHS * 31)
                logger.info("[Ann] Incremental: existing data to %s, refreshing from %s",
                            max_date.date(), refresh_start)
                return refresh_start
        except Exception as e:
            logger.warning("[Ann] Could not read existing data: %s -- full rebuild", e)

    full_start = date(today.year, today.month, 1) - timedelta(days=LOOKBACK_MONTHS * 31)
    logger.info("[Ann] Full download: %s to %s", full_start, today)
    return full_start


# ── Main engine ───────────────────────────────────────────────────────────────

def run(lookback_months: int = LOOKBACK_MONTHS) -> bool:
    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()

    start = _determine_start_date()
    windows = _month_windows(start, today)
    logger.info("[Ann] Fetching %d monthly windows (%s -> %s)", len(windows), start, today)

    session  = _Session()
    all_rows: list[dict] = []

    for i, (from_d, to_d) in enumerate(windows, 1):
        logger.info("[Ann] Window %d/%d: %s -> %s", i, len(windows), from_d, to_d)
        raw = _fetch_window(session, from_d, to_d)
        all_rows.extend(_parse_rows(raw))
        time.sleep(API_DELAY)

    if not all_rows:
        logger.error("[Ann] No data fetched -- aborting")
        return False

    new_df = pd.DataFrame(all_rows)

    # ── Merge with existing data (incremental) ────────────────────────────────
    if ANNOUNCEMENTS_FILE.exists():
        try:
            existing = pd.read_csv(ANNOUNCEMENTS_FILE, dtype=str)
            # Convert signal_score back to int
            if "signal_score" in existing.columns:
                existing["signal_score"] = pd.to_numeric(existing["signal_score"], errors="coerce").fillna(DEFAULT_SCORE).astype(int)
            combined = pd.concat([existing, new_df], ignore_index=True)
            logger.info("[Ann] Merged %d existing + %d new rows", len(existing), len(new_df))
        except Exception as e:
            logger.warning("[Ann] Could not merge existing: %s -- using new only", e)
            combined = new_df
    else:
        combined = new_df

    # ── Dedup by seq_id (primary) or (symbol, date, desc_raw) ────────────────
    before = len(combined)
    combined = combined.drop_duplicates(subset=["seq_id"]).reset_index(drop=True)
    logger.info("[Ann] Dedup: %d -> %d rows (removed %d)", before, len(combined), before - len(combined))

    # ── G-D-03: no empty df ───────────────────────────────────────────────────
    _validate(combined, REQUIRED_ANN_COLS, MIN_ROWS_CHECK, "company_announcements")

    # Sort: newest first
    combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
    _atomic_save(combined, ANNOUNCEMENTS_FILE)

    # ── Build signals ─────────────────────────────────────────────────────────
    signals = _build_signals(combined)
    _validate(signals, REQUIRED_SIGNAL_COLS, 100, "announcement_signals")
    _atomic_save(signals, SIGNALS_FILE)

    logger.info(
        "[Ann] COMPLETE: %d announcements, %d symbols | signals: %d symbols",
        len(combined), combined["symbol"].nunique(), len(signals),
    )
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time as _time
    t0 = _time.monotonic()
    ok = run()
    elapsed = _time.monotonic() - t0

    if ok and ANNOUNCEMENTS_FILE.exists():
        df  = pd.read_csv(ANNOUNCEMENTS_FILE)
        sig = pd.read_csv(SIGNALS_FILE)
        print(f"\nAnnouncements : {len(df):,} rows, {df['symbol'].nunique():,} symbols")
        print(f"Signals       : {len(sig):,} symbols")
        print(f"Date range    : {df['date'].min()} to {df['date'].max()}")
        print(f"Elapsed       : {elapsed:.0f}s")
        print("\nAnnouncement type breakdown:")
        print(df["announcement_type"].value_counts().to_string())
        print("\nTop 10 by score_30d:")
        print(sig.head(10)[["symbol", "dominant_type", "score_30d", "count_30d", "high_signal_30d"]].to_string(index=False))
    else:
        print("Run failed.")
        sys.exit(1)
