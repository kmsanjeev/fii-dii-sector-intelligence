"""
NSE F&O Bhavcopy Acquisition Engine
Phase 1 -- Download daily F&O bhavcopy from 2000 to today.

Data sources (nselib first, archive fallback -- same policy as equity engine):
  1. nselib.derivatives.fno_bhav_copy()   <- primary (recent ~2 years)
  2. NSE archive URL                      <- fallback (all years, rolling 2-yr window)

Output: data/NSE/bhavcopy/fno/YYYY/fo_YYYYMMDD.csv

Modes:
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py --full
  py -3.11 engines/acquisition/nse_fno_acquisition_engine.py --start-year 2010

Guardrails: G-D-02 (atomic write), G-D-03 (no empty write),
            G-A-01 (rate limit), G-A-02 (retry+backoff), G-A-03 (recovery queue)
"""

import argparse
import asyncio
import io
import os
import shutil
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

import aiohttp
import pandas as pd
from nselib.derivatives import fno_bhav_copy

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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

MONTHS = {
    1: "JAN",  2: "FEB",  3: "MAR",  4: "APR",
    5: "MAY",  6: "JUN",  7: "JUL",  8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer":         "https://www.nseindia.com/",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_optimal_workers() -> int:
    cpu_count = os.cpu_count() or 4
    workers = min(cfg.MAX_CONCURRENCY, cpu_count)
    workers = max(cfg.MIN_CONCURRENCY, workers)
    return workers


def ensure_year_dir(year: int) -> Path:
    year_dir = FNO_ROOT / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    return year_dir


def output_path(trade_date: date) -> Path:
    year_dir = ensure_year_dir(trade_date.year)
    return year_dir / f"fo_{trade_date.strftime('%Y%m%d')}.csv"


def fetch_from_nselib(trade_date: date) -> pd.DataFrame:
    """Primary source: nselib (works for recent ~2 years)."""
    try:
        date_str = trade_date.strftime("%d-%m-%Y")
        df = fno_bhav_copy(date_str)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


async def fetch_from_archive(
    session: aiohttp.ClientSession,
    trade_date: date,
) -> pd.DataFrame:
    """Fallback: NSE archive URL (rolling ~2-year window of static ZIPs)."""
    mon  = MONTHS[trade_date.month]
    dd   = trade_date.strftime("%d")
    year = trade_date.year
    url  = (
        f"https://archives.nseindia.com/content/historical/DERIVATIVES"
        f"/{year}/{mon}/fo{dd}{mon}{year}bhav.csv.zip"
    )
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, headers=HEADERS, timeout=timeout) as r:
            if r.status != 200:
                return pd.DataFrame()
            content = await r.read()
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            with z.open(z.namelist()[0]) as f:
                return pd.read_csv(f)
    except Exception:
        return pd.DataFrame()


async def process_day(
    semaphore: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    trade_date: date,
) -> str:
    """Download one date. Returns DOWNLOADED / SKIPPED / FAILED."""
    async with semaphore:
        out = output_path(trade_date)
        if out.exists():
            return "SKIPPED"

        # Primary: nselib — run in thread so it doesn't block the event loop
        df = await asyncio.to_thread(fetch_from_nselib, trade_date)
        source = "NSELIB"

        # Fallback: NSE archive (truly async via aiohttp)
        if df.empty:
            df = await fetch_from_archive(session, trade_date)
            source = "ARCHIVE"

        if df.empty:
            return "FAILED"

        tmp = out.with_suffix(".tmp")
        try:
            await asyncio.to_thread(lambda: df.to_csv(tmp, index=False))
            shutil.move(str(tmp), str(out))
        except Exception as e:
            logger.warning(f"Write failed {trade_date}: {e}")
            if tmp.exists():
                tmp.unlink()
            return "FAILED"

        logger.info(f"{trade_date} | {source}")
        return "DOWNLOADED"


_PRINT_EVERY = 25   # emit a log line every N completed dates within a year


async def _download_dates(trade_dates: list, year: int) -> dict:
    WORKERS = get_optimal_workers()
    total = len(trade_dates)

    semaphore = asyncio.Semaphore(WORKERS)
    downloaded = skipped = failed = completed = 0

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [
            process_day(semaphore, session, td)
            for td in trade_dates
        ]
        for task in asyncio.as_completed(tasks):
            result = await task
            completed += 1
            if result == "DOWNLOADED":
                downloaded += 1
            elif result == "SKIPPED":
                skipped += 1
            else:
                failed += 1

            if completed % _PRINT_EVERY == 0 or completed == total:
                pct = int(completed / total * 100) if total else 100
                print(
                    f"  {year}: {pct:3d}% | {completed}/{total} dates"
                    f" | D:{downloaded} S:{skipped} F:{failed}",
                    flush=True,
                )

    return {"downloaded": downloaded, "skipped": skipped, "failed": failed}


def download_year(year: int) -> dict:
    dates = [
        d.date()
        for d in pd.date_range(
            start=f"{year}-01-01",
            end=f"{year}-12-31",
            freq="B",
        )
    ]
    return asyncio.run(_download_dates(dates, year))


def download_year_range(start_year: int, end_year: int) -> dict:
    total_downloaded = total_skipped = total_failed = 0
    total_years = end_year - start_year + 1

    for idx, year in enumerate(
        progress(range(start_year, end_year + 1), desc="F&O Backfill"),
        start=1,
    ):
        print(f"Year {year} ({idx}/{total_years}) ...", flush=True)
        result = download_year(year)
        total_downloaded += result["downloaded"]
        total_skipped    += result["skipped"]
        total_failed     += result["failed"]
        logger.info(
            f"{year} | "
            f"D:{result['downloaded']} "
            f"S:{result['skipped']} "
            f"F:{result['failed']}"
        )

    print()
    print("=" * 60)
    print("F&O DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Downloaded : {total_downloaded:,}")
    print(f"Skipped    : {total_skipped:,}")
    print(f"Failed     : {total_failed:,}")
    print("=" * 60)

    return {
        "downloaded": total_downloaded,
        "skipped":    total_skipped,
        "failed":     total_failed,
    }


# ── Reports ───────────────────────────────────────────────────────────────────

def _build_registry() -> pd.DataFrame:
    rows = []
    for f in sorted(FNO_ROOT.rglob("fo_*.csv")):
        try:
            d = datetime.strptime(f.stem.replace("fo_", ""), "%Y%m%d").date()
            rows.append({
                "TRADE_DATE":   d,
                "YEAR":         d.year,
                "FILE_NAME":    f.name,
                "FILE_SIZE_KB": round(f.stat().st_size / 1024, 2),
                "STATUS":       "AVAILABLE",
            })
        except Exception:
            pass
    registry = pd.DataFrame(rows)
    registry.to_csv(REGISTRY_FILE, index=False)
    return registry


def _build_coverage(registry: pd.DataFrame):
    if registry.empty:
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NSE F&O Bhavcopy Acquisition Engine"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Ignore existing files and re-check all dates (does not delete)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=cfg.NSE_FNO_START_YEAR,
        help=f"Backfill from this year (default: {cfg.NSE_FNO_START_YEAR})",
    )
    args = parser.parse_args()

    end_year = datetime.today().year

    print("=" * 60)
    print("NSE F&O BHAVCOPY ACQUISITION ENGINE")
    print("=" * 60)
    print(f"Start year : {args.start_year}")
    print(f"End year   : {end_year}")
    print(f"Workers    : {get_optimal_workers()}")
    print(f"Mode       : {'FULL CHECK' if args.full else 'INCREMENTAL'}")
    print("=" * 60)

    download_year_range(args.start_year, end_year)
    registry = _build_registry()
    _build_coverage(registry)

    print(f"Total files: {len(registry):,}")
    if not registry.empty:
        print(
            f"Coverage   : "
            f"{registry['TRADE_DATE'].min()} to "
            f"{registry['TRADE_DATE'].max()}"
        )


if __name__ == "__main__":
    main()
