"""
Stock History Builder
Reads corporate-action-adjusted bhavcopy files and builds per-symbol OHLCV parquet files.

Source (adjusted, derived):  data/NSE/adjusted_equity/**/*.csv   <- run price_adjustment_engine first
Output (cache):              data/NSE/nsecache/stock_history/<SYMBOL>.parquet

Run modes:
  py -3.11 engines/acquisition/stock_history_builder.py          <- incremental (new dates only)
  py -3.11 engines/acquisition/stock_history_builder.py --full   <- full rebuild from scratch
"""

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("stock_history_builder")

# Reads from ADJUSTED equity (corporate-action-adjusted prices), not raw bhavcopy.
# Run price_adjustment_engine.py --full first to populate adjusted_equity/.
BHAVCOPY_DIR = cfg.ADJUSTED_EQUITY_DIR
OUTPUT_DIR   = cfg.STOCK_HISTORY_CACHE
MANIFEST     = OUTPUT_DIR / "manifest.json"

BATCH_SIZE = 300                                             # files per memory batch
WORKERS    = min(cfg.MAX_CONCURRENCY, os.cpu_count() or 4)  # thread workers for I/O

RENAME = {
    # ── Legacy schema (≤2019) — sec_bhavdata_full format ─────────────────────
    # Columns: SYMBOL SERIES OPEN HIGH LOW CLOSE LAST PREVCLOSE
    #          TOTTRDQTY TOTTRDVAL TIMESTAMP TOTALTRADES ISIN
    "TIMESTAMP":     "date",
    "TOTTRDQTY":     "volume",
    "TOTTRDVAL":     "turnover",
    "PREVCLOSE":     "prev_close",
    "TOTALTRADES":   "trades",
    "LAST":          "last_price",
    # OPEN/HIGH/LOW/CLOSE are already lowercase-correct after df.columns.lower()
    # ── New NSE schema (2020+) — bhavcopy_YYYYMMDD format ────────────────────
    # Columns: SYMBOL SERIES DATE1 PREV_CLOSE OPEN_PRICE HIGH_PRICE LOW_PRICE
    #          LAST_PRICE CLOSE_PRICE AVG_PRICE TTL_TRD_QNTY TURNOVER_LACS
    #          NO_OF_TRADES DELIV_QTY DELIV_PER TRADE_DATE
    "TRADE_DATE":    "date",       # preferred — already YYYY-MM-DD
    "OPEN_PRICE":    "open",
    "HIGH_PRICE":    "high",
    "LOW_PRICE":     "low",
    "CLOSE_PRICE":   "close",
    "LAST_PRICE":    "last_price",
    "PREV_CLOSE":    "prev_close",
    "TTL_TRD_QNTY":  "volume",
    "TURNOVER_LACS": "turnover",
    "NO_OF_TRADES":  "trades",
}

KEEP = ["date", "symbol", "open", "high", "low", "close",
        "prev_close", "volume", "turnover", "trades", "isin"]


# ── Corporate-action lookup ───────────────────────────────────────────────────
# Loaded once at startup; provides ca_info string keyed by (symbol, date).

def _load_ca_lookup() -> dict[str, dict[str, str]]:
    """Returns {SYMBOL: {YYYY-MM-DD: ca_info_string}}"""
    ca_file = cfg.EQUITY_MASTER_DIR / "nse_corporate_actions_derived.csv"
    if not ca_file.exists():
        logger.warning("[Builder] CA derived file not found — ca_info column will be empty")
        return {}
    try:
        ca = pd.read_csv(ca_file, low_memory=False)
        ca = ca.dropna(subset=["symbol", "exDate"])
        lookup: dict[str, dict[str, str]] = {}
        for _, row in ca.iterrows():
            sym = str(row["symbol"]).strip().upper()
            try:
                dt = pd.to_datetime(row["exDate"], dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                continue
            subject = str(row.get("subject", "")).strip()
            adj_type = str(row.get("adjustment_type", "")).strip()
            label = subject if subject and subject != "nan" else adj_type
            if label and label != "nan":
                lookup.setdefault(sym, {})[dt] = label
        logger.info("[Builder] CA lookup loaded: %d symbols", len(lookup))
        return lookup
    except Exception as exc:
        logger.warning("[Builder] Could not load CA lookup: %s", exc)
        return {}

CA_LOOKUP: dict[str, dict[str, str]] = _load_ca_lookup()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _date_from_filename(path: Path) -> str | None:
    """Extract 'YYYY-MM-DD' from bhavcopy_YYYYMMDD.csv[.gz].
    Returns None if the name doesn't follow the standard pattern.
    This is used for accurate incremental filtering — mtime is wrong
    because all files were downloaded recently and have 2026 mtime.
    """
    name = path.name
    if name.endswith(".gz"):
        name = name[:-3]
    stem = Path(name).stem          # strips .csv
    if stem.startswith("bhavcopy_"):
        date_part = stem[len("bhavcopy_"):]
        if len(date_part) == 8 and date_part.isdigit():
            return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
    return None


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
        # Prefer TRADE_DATE (YYYY-MM-DD) over TIMESTAMP (DD-MON-YYYY).
        # Adjusted files have both; renaming both to "date" creates a duplicate
        # column that breaks pd.to_datetime().dt.strftime() with a silent error.
        if "TRADE_DATE" in df.columns and "TIMESTAMP" in df.columns:
            df = df.drop(columns=["TIMESTAMP"])
        df = df.rename(columns={k: v for k, v in RENAME.items() if k in df.columns})
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"], dayfirst=False, errors="coerce").dt.strftime("%Y-%m-%d")
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


def _write_symbol_parquet(symbol: str, new_df: pd.DataFrame):
    """Append new_df to existing symbol parquet. New data is deduplicated by date."""
    path = OUTPUT_DIR / f"{symbol}.parquet"
    if path.exists():
        existing = pd.read_parquet(path)
        # Drop stale ca_info before concat so it gets recalculated cleanly
        existing = existing.drop(columns=["ca_info"], errors="ignore")
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined = (combined
                .drop_duplicates(subset=["date"], keep="last")
                .sort_values("date")
                .reset_index(drop=True))
    # Attach corporate action info as the final column
    ca_dates = CA_LOOKUP.get(symbol.upper(), {})
    combined["ca_info"] = combined["date"].map(lambda d: ca_dates.get(str(d), ""))
    tmp = path.with_suffix(".tmp")
    combined.to_parquet(tmp, index=False)
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

        manifest  = _load_manifest()
        last_date = None if self.full_rebuild else manifest.get("last_processed_date")

        if last_date:
            # Filter by DATA DATE embedded in filename (bhavcopy_YYYYMMDD.csv).
            # DO NOT use mtime — all files were downloaded recently so their mtime
            # is always newer than any last_processed_date, causing every run to
            # process all 1400+ files instead of only the new ones.
            pending = []
            for f in all_files:
                file_date = _date_from_filename(f)
                if file_date is not None:
                    if file_date > last_date:
                        pending.append(f)
                else:
                    # Non-standard filename: fall back to mtime as last resort
                    if pd.Timestamp(f.stat().st_mtime, unit="s") > pd.Timestamp(last_date):
                        pending.append(f)

            if not pending:
                print(f"Stock history cache is up to date (last date: {last_date}).")
                return True
            print(f"Incremental mode : {len(pending)} new files to process (after {last_date})", flush=True)
        else:
            pending = all_files
            if self.full_rebuild and OUTPUT_DIR.exists():
                for p in OUTPUT_DIR.glob("*.parquet"):
                    p.unlink()
                print("Full rebuild: cleared existing cache", flush=True)
            print(f"Full build       : {len(pending)} bhavcopy files to process", flush=True)

        print(f"Workers          : {WORKERS}", flush=True)

        # ── Phase 1: Read all pending files, accumulate per-symbol ────────────
        # We read in batches for memory safety but accumulate across ALL batches.
        # This means each symbol parquet is written exactly ONCE in Phase 2,
        # not once per batch (old behaviour caused N_batches × N_symbols writes).

        batches = [pending[i:i+BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]
        print(f"Read batches     : {len(batches)}", flush=True)

        symbol_frames: dict[str, list] = defaultdict(list)
        all_dates: list[str] = []

        for batch_idx, batch in enumerate(batches):
            print(f"Reading batch {batch_idx + 1}/{len(batches)}  ({len(batch)} files) ...", flush=True)

            dfs: list[pd.DataFrame] = []
            with progress(total=len(batch), desc="  Reading") as pbar:
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

            for sym, grp in batch_df.groupby("symbol"):
                symbol_frames[sym].append(grp.drop(columns=["symbol"]).copy())

        if not symbol_frames:
            print("No new data found in pending files.", flush=True)
            return True

        # ── Phase 2: Write each symbol exactly once ───────────────────────────
        # Merge all batches into one DataFrame per symbol before writing.
        # This is the key fix: old code wrote once per batch per symbol.

        print(f"Writing {len(symbol_frames)} symbols (one pass) ...", flush=True)

        def _merge_and_write(sym: str, frames: list) -> None:
            new_df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
            _write_symbol_parquet(sym, new_df)

        items = list(symbol_frames.items())
        with progress(total=len(items), desc="  Writing") as pbar:
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futures = [ex.submit(_merge_and_write, sym, frames) for sym, frames in items]
                for fut in as_completed(futures):
                    try:
                        fut.result()
                    except Exception as exc:
                        logger.warning("[Builder] Write error: %s", exc)
                    pbar.update(1)

        # ── Manifest ──────────────────────────────────────────────────────────
        symbol_count   = len(list(OUTPUT_DIR.glob("*.parquet")))
        last_processed = max(all_dates) if all_dates else (last_date or "")
        _save_manifest(last_processed, symbol_count)

        print(f"Done: {symbol_count} symbols | last date: {last_processed}", flush=True)
        logger.info("[Builder] Complete: %d symbols, last_date=%s", symbol_count, last_processed)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Full rebuild from scratch")
    args = parser.parse_args()
    StockHistoryBuilder(full_rebuild=args.full).run()
