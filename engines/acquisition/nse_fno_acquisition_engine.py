"""
NSE F&O Bhavcopy Acquisition Engine
Phase 1 — Download daily F&O bhavcopy from 2000 to today.

Data sources (priority order per G-A-01):
  1. NSE archive URL  — works for 2000-07-2024  (old format: INSTRUMENT, SYMBOL, EXPIRY_DT ...)
  2. nselib           — works for 2024-08-01+    (new format: TradDt, BizDt, Sgmt ...)

Both formats are stored as-is. Consuming engines must handle both schemas.

Modes:
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py             <- incremental
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py --full      <- full rebuild
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py --start-year 2010

Output: data/NSE/bhavcopy/fno/YYYY/fo_YYYYMMDD.csv

Guardrails: G-D-02 (atomic write), G-D-03 (no empty write),
            G-A-01 (rate limit), G-A-02 (retry+backoff), G-A-03 (recovery queue)
"""

import argparse
import io
import shutil
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from nselib.derivatives import fno_bhav_copy

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("nse_fno_acquisition")

# ── Paths ─────────────────────────────────────────────────────────────────────
FNO_ROOT      = cfg.NSE_FNO_BHAVCOPY_DIR
REGISTRY_FILE = FNO_ROOT / "fno_registry.csv"
COVERAGE_FILE = FNO_ROOT / "fno_coverage_report.csv"
RECOVERY_FILE = FNO_ROOT / "fno_recovery_queue.csv"

FNO_ROOT.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
# NSE archive has a rolling ~2-year window: dates older than 2 years are served
# as static ZIP files; more recent dates require nselib's live API.
# Computed at runtime so the engine stays correct as years pass.
ARCHIVE_HORIZON_DAYS = 730   # 2 years
_today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
ARCHIVE_CUTOFF = _today - timedelta(days=ARCHIVE_HORIZON_DAYS)

MONTHS = {
    1: "JAN", 2: "FEB",  3: "MAR", 4: "APR",
    5: "MAY", 6: "JUN",  7: "JUL", 8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer":         "https://www.nseindia.com/",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION_REFRESH_EVERY = 200   # re-hit nseindia.com every N downloads
_session: requests.Session | None = None
_session_call_count = 0


# ── Session management ────────────────────────────────────────────────────────

def _get_session() -> requests.Session:
    """Return a live requests session, refreshing cookies periodically."""
    global _session, _session_call_count
    if _session is None or _session_call_count >= SESSION_REFRESH_EVERY:
        s = requests.Session()
        try:
            s.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=15)
        except Exception:
            pass
        _session = s
        _session_call_count = 0
    _session_call_count += 1
    return _session


# ── File helpers ──────────────────────────────────────────────────────────────

def _output_path(trade_date: datetime) -> Path:
    year_dir = FNO_ROOT / str(trade_date.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    return year_dir / f"fo_{trade_date.strftime('%Y%m%d')}.csv"


def _existing_dates() -> set:
    dates = set()
    for f in FNO_ROOT.rglob("fo_*.csv"):
        try:
            dates.add(datetime.strptime(f.stem.replace("fo_", ""), "%Y%m%d").date())
        except Exception:
            pass
    return dates


def _all_weekdays(start: datetime, end: datetime) -> list:
    days, cur = [], start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


# ── Downloaders ───────────────────────────────────────────────────────────────

def _download_via_archive(trade_date: datetime) -> pd.DataFrame:
    """NSE archive URL — works for dates up to ~Jul 2024."""
    mon  = MONTHS[trade_date.month]
    day  = trade_date.strftime("%d")
    year = trade_date.year
    url  = (
        f"https://archives.nseindia.com/content/historical/DERIVATIVES"
        f"/{year}/{mon}/fo{day}{mon}{year}bhav.csv.zip"
    )
    session = _get_session()
    r = session.get(url, headers=NSE_HEADERS, timeout=30)
    if r.status_code != 200:
        return pd.DataFrame()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with z.open(z.namelist()[0]) as f:
            return pd.read_csv(f)


def _download_via_nselib(trade_date: datetime) -> pd.DataFrame:
    """nselib — works for Aug 2024 onwards."""
    date_str = trade_date.strftime("%d-%m-%Y")
    df = fno_bhav_copy(date_str)
    return df if df is not None else pd.DataFrame()


def _download_one(trade_date: datetime, retries: int = 3) -> str:
    """Download one date. Returns DOWNLOADED / SKIPPED / FAILED."""
    out = _output_path(trade_date)
    if out.exists():
        return "SKIPPED"

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            # Source selection: archive first, nselib for recent dates
            if trade_date < ARCHIVE_CUTOFF:
                df = _download_via_archive(trade_date)
            else:
                df = _download_via_nselib(trade_date)
                # Fallback: some Aug-2024 dates might still be in archive
                if df.empty:
                    df = _download_via_archive(trade_date)

            if df is None or df.empty:
                return "FAILED"

            tmp = out.with_suffix(".tmp")
            df.to_csv(tmp, index=False)
            shutil.move(str(tmp), str(out))
            return "DOWNLOADED"

        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(cfg.RETRY_DELAY * attempt)

    logger.warning(f"{trade_date.date()} failed after {retries} attempts: {last_err}")
    return "FAILED"


# ── Reports ───────────────────────────────────────────────────────────────────

def _build_registry() -> pd.DataFrame:
    rows = []
    for f in sorted(FNO_ROOT.rglob("fo_*.csv")):
        try:
            d = datetime.strptime(f.stem.replace("fo_", ""), "%Y%m%d").date()
            rows.append({
                "TRADE_DATE":    d,
                "YEAR":          d.year,
                "FILE_NAME":     f.name,
                "FILE_SIZE_KB":  round(f.stat().st_size / 1024, 2),
                "STATUS":        "AVAILABLE",
            })
        except Exception:
            pass
    registry = pd.DataFrame(rows)
    registry.to_csv(REGISTRY_FILE, index=False)
    return registry


def _build_coverage(registry: pd.DataFrame):
    if registry.empty:
        pd.DataFrame().to_csv(COVERAGE_FILE, index=False)
        return
    rows = []
    for year in sorted(registry["YEAR"].unique()):
        grp = registry[registry["YEAR"] == year]
        rows.append({
            "YEAR":        year,
            "TOTAL_FILES": len(grp),
            "FIRST_DATE":  grp["TRADE_DATE"].min(),
            "LAST_DATE":   grp["TRADE_DATE"].max(),
        })
    pd.DataFrame(rows).to_csv(COVERAGE_FILE, index=False)


def _save_recovery(failed: list):
    if not failed:
        if RECOVERY_FILE.exists():
            RECOVERY_FILE.unlink()
        return
    pd.DataFrame({
        "TRADE_DATE": [d.date() for d in failed],
        "STATUS":     "FAILED",
    }).to_csv(RECOVERY_FILE, index=False)
    logger.warning(f"Recovery queue: {len(failed)} dates -> {RECOVERY_FILE.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NSE F&O Bhavcopy Acquisition Engine")
    parser.add_argument("--full",       action="store_true",
                        help="Force re-download all dates (ignore existing files)")
    parser.add_argument("--start-year", type=int, default=cfg.NSE_FNO_START_YEAR,
                        help=f"Backfill from this year (default: {cfg.NSE_FNO_START_YEAR})")
    args = parser.parse_args()

    start    = datetime(args.start_year, 1, 1)
    end      = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    all_days = _all_weekdays(start, end)

    if args.full:
        todo = all_days
    else:
        existing = _existing_dates()
        todo = [d for d in all_days if d.date() not in existing]

    total_all  = len(all_days)
    total_todo = len(todo)
    eta_min    = round(total_todo * cfg.API_DELAY / 60)

    print("=" * 60)
    print("NSE F&O BHAVCOPY ACQUISITION ENGINE")
    print("=" * 60)
    print(f"Start year : {args.start_year}")
    print(f"Total dates: {total_all:,}")
    print(f"Already OK : {total_all - total_todo:,}")
    print(f"To download: {total_todo:,}")
    print(f"Est. time  : ~{eta_min} min")
    print(f"Sources    : archive (before {ARCHIVE_CUTOFF.strftime('%Y-%m-%d')}) + nselib (recent 2 yrs)")
    print("=" * 60)

    if total_todo == 0:
        print("Nothing to download - already up to date.")
        _build_registry()
        return

    downloaded, skipped, failed_dates = 0, 0, []

    for trade_date in progress(todo, total=total_todo, desc="F&O dates"):
        status = _download_one(trade_date)
        if status == "DOWNLOADED":
            downloaded += 1
        elif status == "SKIPPED":
            skipped += 1
        else:
            failed_dates.append(trade_date)
        time.sleep(cfg.API_DELAY)

    _save_recovery(failed_dates)
    registry = _build_registry()
    _build_coverage(registry)

    print()
    print("=" * 60)
    print("NSE F&O ACQUISITION ENGINE - COMPLETE")
    print("=" * 60)
    print(f"Downloaded : {downloaded:,}")
    print(f"Skipped    : {skipped:,}")
    print(f"Failed     : {len(failed_dates):,}")
    print(f"Total files: {len(registry):,}")
    if not registry.empty:
        print(f"Coverage   : {registry['TRADE_DATE'].min()} to {registry['TRADE_DATE'].max()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
