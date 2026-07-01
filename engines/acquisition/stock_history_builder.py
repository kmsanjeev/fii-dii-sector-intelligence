"""
Stock History Builder
Reads raw bhavcopy files (READ-ONLY) and builds per-symbol OHLCV parquet files.

Raw source (immutable):  data/NSE/bhavcopy/equity/**/*.csv  (7813 files, 1995-2026)
Output (cache/derived):  data/NSE/nsecache/stock_history/<SYMBOL>.parquet

Run modes:
  py -3.11 engines/acquisition/stock_history_builder.py          <- incremental (new dates only)
  py -3.11 engines/acquisition/stock_history_builder.py --full   <- full rebuild from scratch
"""

import argparse
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm as _tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("stock_history_builder")

BHAVCOPY_DIR = cfg.NSE_EQUITY_BHAVCOPY_DIR
OUTPUT_DIR   = cfg.STOCK_HISTORY_CACHE
MANIFEST     = OUTPUT_DIR / "manifest.json"

BATCH_SIZE = 300                                             # files per memory batch
WORKERS    = min(cfg.MAX_CONCURRENCY, os.cpu_count() or 4)  # thread workers for I/O

RENAME = {
    "TIMESTAMP":    "date",
    "TOTTRDQTY":    "volume",
    "TOTTRDVAL":    "turnover",
    "PREVCLOSE":    "prev_close",
    "TOTALTRADES":  "trades",
    "LAST":         "last_price",
}

KEEP = ["date", "symbol", "open", "high", "low", "close",
        "prev_close", "volume", "turnover", "trades", "isin"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_bhavcopy(path: Path) -> pd.DataFrame:
    try:
        if str(path).endswith(".gz"):
            df = pd.read_csv(path, compression="gzip", low_memory=False)
        else:
            df = pd.read_csv(path, low_memory=False)
        df.columns = df.columns.str.strip()
        # EQ series only (G-S-01)
        if "SERIES" in df.columns:
            df = df[df["SERIES"].str.strip().str.upper() == "EQ"].copy()
        elif "series" in df.columns:
            df = df[df["series"].str.strip().str.upper() == "EQ"].copy()
        if df.empty:
            return pd.DataFrame()
        df = df.rename(columns={k: v for k, v in RENAME.items() if k in df.columns})
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["date", "symbol"])
        df["symbol"] = df["symbol"].str.strip().str.upper()
        keep = [c for c in KEEP if c in df.columns]
        return df[keep]
    except Exception as exc:
        logger.warning("[Builder] Could not read %s: %s", path.name, exc)
        return pd.DataFrame()


def _load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except Exception:
            pass
    return {"last_processed_date": None, "symbol_count": 0}


def _save_manifest(last_date: str, symbol_count: int):
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "last_processed_date": last_date,
        "symbol_count": symbol_count,
    }, indent=2))
    shutil.move(str(tmp), str(MANIFEST))


def _write_symbol_parquet(symbol: str, df: pd.DataFrame):
    path = OUTPUT_DIR / f"{symbol}.parquet"
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    df = (df.drop_duplicates(subset=["date"])
            .sort_values("date")
            .reset_index(drop=True))
    tmp = path.with_suffix(".tmp")
    df.to_parquet(tmp, index=False)
    shutil.move(str(tmp), str(path))


# ── Main engine ───────────────────────────────────────────────────────────────

class StockHistoryBuilder:

    def __init__(self, full_rebuild: bool = False):
        self.full_rebuild = full_rebuild
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        logger.info("[StockHistoryBuilder] Starting (full=%s)", self.full_rebuild)

        all_files = sorted(BHAVCOPY_DIR.rglob("*.csv")) + sorted(BHAVCOPY_DIR.rglob("*.csv.gz"))
        if not all_files:
            logger.error("[Builder] No bhavcopy files found in %s", BHAVCOPY_DIR)
            print("ERROR: No bhavcopy files found in", BHAVCOPY_DIR)
            return False

        manifest = _load_manifest()
        last_date = None if self.full_rebuild else manifest.get("last_processed_date")

        if last_date:
            # Filter to only files that may contain newer data
            # Bhavcopy filenames often embed date; fall back to mtime
            cutoff = pd.Timestamp(last_date)
            pending = [f for f in all_files if pd.Timestamp(f.stat().st_mtime, unit="s") > cutoff]
            if not pending:
                print("Stock history cache is already up to date.")
                return True
            print(f"Incremental mode: {len(pending)} new files to process (after {last_date})")
        else:
            pending = all_files
            if self.full_rebuild and OUTPUT_DIR.exists():
                for p in OUTPUT_DIR.glob("*.parquet"):
                    p.unlink()
                print("Full rebuild: cleared existing cache")
            print(f"Full build: {len(pending)} bhavcopy files to process")

        # Process in batches to limit memory usage
        batches = [pending[i:i+BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]
        print(f"Workers    : {WORKERS}", flush=True)
        print(f"Batches    : {len(batches)}", flush=True)

        all_dates = []

        for batch_idx, batch in enumerate(batches):
            print(f"Batch {batch_idx + 1}/{len(batches)}  ({len(batch)} files) ...", flush=True)

            # Read phase — per-file tqdm bar drives the GUI ProgressBar component
            dfs = []
            with _tqdm(total=len(batch), desc="  Reading", ncols=100, leave=True, ascii=True) as pbar:
                with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                    futures = {ex.submit(_read_bhavcopy, f): f for f in batch}
                    for fut in as_completed(futures):
                        df = fut.result()
                        if not df.empty:
                            dfs.append(df)
                        pbar.update(1)

            if not dfs:
                continue

            batch_df = pd.concat(dfs, ignore_index=True)
            if batch_df.empty:
                continue

            all_dates.extend(batch_df["date"].dropna().tolist())

            # Write phase — per-symbol tqdm bar (4500+ symbols visible in GUI)
            groups = list(batch_df.groupby("symbol"))
            with _tqdm(total=len(groups), desc="  Writing", ncols=100, leave=True, ascii=True) as pbar:
                with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                    futures = [
                        ex.submit(_write_symbol_parquet, sym, grp.drop(columns=["symbol"]))
                        for sym, grp in groups
                    ]
                    for fut in as_completed(futures):
                        try:
                            fut.result()
                        except Exception as exc:
                            logger.warning("[Builder] Write error: %s", exc)
                        pbar.update(1)

            logger.info("[Builder] Batch %d/%d done", batch_idx + 1, len(batches))

        # Summary
        symbol_files = list(OUTPUT_DIR.glob("*.parquet"))
        symbol_count = len(symbol_files)
        last_processed = max(all_dates) if all_dates else (last_date or "")
        _save_manifest(last_processed, symbol_count)

        print(f"Stock history cache built: {symbol_count} symbols, last date {last_processed}")
        logger.info("[Builder] Complete: %d symbols, last_date=%s", symbol_count, last_processed)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Full rebuild from scratch")
    args = parser.parse_args()
    StockHistoryBuilder(full_rebuild=args.full).run()
