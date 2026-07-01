"""
Symbol Change History Engine
Phase 17 -- Download and normalise NSE symbol change history.

Source:  https://nsearchives.nseindia.com/content/equities/symbolchange.csv
         (no auth required, ~1038 records, no header row)
Output:  data/NSE/equity_master/symbol_change_history.csv

Columns in output:
    company_name, old_symbol, new_symbol, change_date (YYYY-MM-DD)

Guardrails: G-D-02 (atomic writes), G-D-03 (no empty df), G-D-04 (schema),
            G-A-01 (rate limit), G-A-02 (3 retries), G-P-01 (no nulls in keys)
"""

import shutil
import sys
import time
from pathlib import Path
from io import StringIO

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("symbol_change_engine")

# ── Constants ─────────────────────────────────────────────────────────────────

SOURCE_URL  = "https://nsearchives.nseindia.com/content/equities/symbolchange.csv"
OUTPUT_FILE = cfg.EQUITY_MASTER_DIR / "symbol_change_history.csv"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    ),
    "Accept":          "text/csv,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.nseindia.com/",
}

REQUIRED_COLS = ["company_name", "old_symbol", "new_symbol", "change_date"]


# ── Downloader ─────────────────────────────────────────────────────────────────

def _fetch_raw() -> str:
    """Download the CSV with retry + backoff. Returns raw text."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("[SymbolChange] Downloading symbolchange.csv (attempt %d)", attempt)
            resp = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            logger.info("[SymbolChange] Downloaded %d bytes", len(resp.content))
            return resp.text
        except Exception as e:
            logger.warning("[SymbolChange] Attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    raise RuntimeError(f"Failed to download {SOURCE_URL} after {MAX_RETRIES} attempts")


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse(raw: str) -> pd.DataFrame:
    """
    Parse the headerless 4-column CSV.
    Columns (positional): company_name, old_symbol, new_symbol, change_date
    """
    df = pd.read_csv(
        StringIO(raw),
        header=None,
        names=["company_name", "old_symbol", "new_symbol", "change_date"],
        dtype=str,
        encoding_errors="replace",
    )

    # Strip whitespace from all string columns
    for col in df.columns:
        df[col] = df[col].str.strip()

    # Drop rows with null/empty key fields
    before = len(df)
    df = df.dropna(subset=["old_symbol", "new_symbol", "change_date"])
    df = df[df["old_symbol"].str.len() > 0]
    df = df[df["new_symbol"].str.len() > 0]
    dropped = before - len(df)
    if dropped:
        logger.warning("[SymbolChange] Dropped %d rows with missing key fields", dropped)

    # Normalise symbols to uppercase
    df["old_symbol"] = df["old_symbol"].str.upper()
    df["new_symbol"] = df["new_symbol"].str.upper()

    # Parse date: NSE uses dd-MMM-YYYY (e.g. "23-JAN-2023")
    df["change_date"] = pd.to_datetime(
        df["change_date"], format="%d-%b-%Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # Drop rows where date failed to parse
    bad_dates = df["change_date"].isna().sum()
    if bad_dates:
        logger.warning("[SymbolChange] Dropped %d rows with unparseable dates", bad_dates)
        df = df.dropna(subset=["change_date"])

    # Sort oldest change first, then alphabetically by new_symbol for stable output
    df = df.sort_values(["change_date", "new_symbol"]).reset_index(drop=True)

    return df


# ── Validator ─────────────────────────────────────────────────────────────────

def _validate(df: pd.DataFrame) -> None:
    """G-D-03: no empty df. G-D-04: required columns present."""
    if df.empty:
        raise ValueError("Parsed DataFrame is empty -- aborting write")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if len(df) < 500:
        raise ValueError(f"Only {len(df)} rows -- expected 900+. Data may be corrupt.")


# ── Writer ────────────────────────────────────────────────────────────────────

def _save(df: pd.DataFrame) -> None:
    """G-D-02: atomic write via .tmp then shutil.move."""
    cfg.EQUITY_MASTER_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_FILE.with_suffix(".tmp.csv")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT_FILE))
    logger.info("[SymbolChange] Saved %d records -> %s", len(df), OUTPUT_FILE)


# ── Public API ────────────────────────────────────────────────────────────────

def run() -> pd.DataFrame:
    raw  = _fetch_raw()
    df   = _parse(raw)
    _validate(df)
    _save(df)
    return df


def load() -> pd.DataFrame:
    """Load the cached output. Downloads if missing."""
    if OUTPUT_FILE.exists():
        return pd.read_csv(OUTPUT_FILE, dtype=str)
    logger.warning("[SymbolChange] Cache missing -- running download")
    return run()


def resolve_current_symbol(symbol: str) -> str:
    """
    Given any historical or current symbol, return the latest known symbol.
    Follows the rename chain until no further rename is found.
    Returns the input symbol unchanged if no rename history exists.
    """
    df = load()
    lookup = dict(zip(df["old_symbol"].str.upper(), df["new_symbol"].str.upper()))
    current = symbol.upper()
    seen = set()
    while current in lookup and current not in seen:
        seen.add(current)
        current = lookup[current]
    return current


def get_all_aliases(symbol: str) -> list[str]:
    """
    Return all historical symbols that eventually map to the given current symbol.
    Useful for merging bhavcopy history across rename events.
    """
    df = load()
    lookup = dict(zip(df["old_symbol"].str.upper(), df["new_symbol"].str.upper()))
    target = symbol.upper()

    # Build reverse map: new_symbol -> [old_symbols]
    reverse: dict[str, list[str]] = {}
    for old, new in lookup.items():
        reverse.setdefault(new, []).append(old)

    aliases: list[str] = []
    queue = [target]
    visited = set()
    while queue:
        sym = queue.pop()
        if sym in visited:
            continue
        visited.add(sym)
        for old in reverse.get(sym, []):
            aliases.append(old)
            queue.append(old)

    return sorted(set(aliases))


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = run()
    print(f"Symbol change history: {len(df)} records")
    print(df.head(10).to_string(index=False))
    print("...")
    print(df.tail(5).to_string(index=False))

    # Demo: resolve IIFLWAM -> 360ONE
    for sym in ["IIFLWAM", "BIRLA3M", "RELIANCE", "360ONE"]:
        current = resolve_current_symbol(sym)
        aliases = get_all_aliases(current)
        print(f"  {sym:20s} -> current: {current:20s}  aliases: {aliases}")
