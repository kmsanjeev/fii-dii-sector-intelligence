"""
Platform Guardrails — Utility Functions
Implements all 55 rules from docs/governance/GUARDRAILS.md.
Every function logs its action at DEBUG level.
"""

import os
import re
import shutil
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import pytz

from engines.common.logger import get_logger

logger = get_logger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — DATA INTEGRITY (G-D-*)
# ─────────────────────────────────────────────────────────────────────────────

def write_raw(df: pd.DataFrame, path: Path) -> None:
    """G-D-01: Write raw file only if it does not already exist."""
    logger.debug(f"[G-D-01] write_raw called: target={path}")
    if path.exists():
        logger.error(f"[G-D-01] BLOCKED: Raw file already exists at {path}. Raw data is immutable.")
        raise FileExistsError(f"Raw file already exists: {path}. Raw data is immutable.")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.debug(f"[G-D-01] Raw file written: {path} ({path.stat().st_size} bytes)")


def safe_write_csv(df: pd.DataFrame, target: Path) -> None:
    """G-D-02 + G-D-03: Atomic write via .tmp rename; guard against empty DataFrames."""
    logger.debug(f"[G-D-02/03] safe_write_csv called: target={target}, rows={len(df)}")
    if df.empty:
        logger.warning(f"[G-D-03] Skipping write — empty DataFrame for {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    try:
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(target))
        logger.debug(f"[G-D-02] Atomic write complete: {target} ({target.stat().st_size} bytes)")
    except Exception as e:
        logger.error(f"[G-D-02] Write failed for {target}: {e}")
        if tmp.exists():
            tmp.unlink()
        raise


def validate_schema(df: pd.DataFrame, required: list, context: str = "") -> None:
    """G-D-04: Raise if any required column is missing; warn on null key fields."""
    logger.debug(f"[G-D-04] validate_schema: context={context}, required={required}, df_cols={list(df.columns)}")
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"[G-D-04] Schema violation in '{context}': missing columns {missing}")
        raise ValueError(f"[{context}] Schema violation — missing columns: {missing}")
    null_keys = [c for c in required if df[c].isnull().any()]
    if null_keys:
        counts = {c: int(df[c].isnull().sum()) for c in null_keys}
        logger.warning(f"[G-D-04] Null values in key columns in '{context}': {counts}")
    logger.debug(f"[G-D-04] Schema validation passed for '{context}'")


def safe_append(
    existing: pd.DataFrame,
    new: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """G-D-05 + G-D-06: Append only new dates; return sorted result."""
    logger.debug(
        f"[G-D-05/06] safe_append: existing={len(existing)} rows, new={len(new)} rows, date_col={date_col}"
    )
    existing_dates = set(pd.to_datetime(existing[date_col]).dt.date)
    new_dates = pd.to_datetime(new[date_col]).dt.date
    fresh = new[~new_dates.isin(existing_dates)].copy()
    duplicates = len(new) - len(fresh)
    if duplicates:
        logger.warning(f"[G-D-05] Skipped {duplicates} duplicate date(s)")
    if fresh.empty:
        logger.debug("[G-D-05] No new rows to append — returning original")
        return existing
    result = pd.concat([existing, fresh], ignore_index=True).sort_values(date_col).reset_index(drop=True)
    logger.debug(f"[G-D-06] Result sorted by {date_col}: {len(result)} total rows")
    return result


def verify_file_size(path: Path, min_bytes: int) -> None:
    """G-D-07: Raise if written file is smaller than expected minimum."""
    logger.debug(f"[G-D-07] verify_file_size: path={path}, min_bytes={min_bytes}")
    actual = path.stat().st_size
    if actual < min_bytes:
        logger.error(f"[G-D-07] File too small: {path} ({actual} bytes < {min_bytes} minimum)")
        raise RuntimeError(f"Output file suspiciously small: {path} ({actual} bytes, min {min_bytes})")
    logger.debug(f"[G-D-07] File size OK: {path} ({actual} bytes ≥ {min_bytes})")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — API / ACQUISITION (G-A-*)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_with_retry(fn, *args, max_retries: int = 3, base_delay: float = 3.0):
    """G-A-02: Retry with exponential backoff."""
    logger.debug(f"[G-A-02] fetch_with_retry: fn={fn.__name__}, max_retries={max_retries}")
    for attempt in range(max_retries):
        try:
            result = fn(*args)
            logger.debug(f"[G-A-02] Success on attempt {attempt + 1}")
            return result
        except Exception as e:
            wait = base_delay * (2 ** attempt)
            logger.warning(f"[G-A-02] Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait}s")
            if attempt < max_retries - 1:
                time.sleep(wait)
    logger.error(f"[G-A-02] All {max_retries} attempts exhausted")
    raise RuntimeError(f"All {max_retries} retry attempts failed for {fn.__name__}")


def save_recovery_queue(failed_items: list, queue_path: Path) -> None:
    """G-A-03: Append failed items to persistent recovery queue."""
    logger.debug(f"[G-A-03] save_recovery_queue: {len(failed_items)} items → {queue_path}")
    if not failed_items:
        return
    new_rows = pd.DataFrame({
        "item": [str(i) for i in failed_items],
        "timestamp": datetime.now(IST).isoformat(),
    })
    if queue_path.exists():
        existing = pd.read_csv(queue_path)
        combined = pd.concat([existing, new_rows], ignore_index=True)
    else:
        combined = new_rows
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(queue_path, index=False)
    logger.warning(f"[G-A-03] Recovery queue updated: {len(failed_items)} new failures → {queue_path}")


def is_market_hours() -> bool:
    """G-A-04: True if current IST time is within NSE market hours (09:15–15:30 weekdays)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        logger.debug(f"[G-A-04] Weekend — market closed")
        return False
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    result = market_open <= now <= market_close
    logger.debug(f"[G-A-04] is_market_hours={result} at {now.strftime('%H:%M IST %A')}")
    return result


def check_data_freshness(last_date_str: str, trading_days_since: int, max_lag: int = 5) -> bool:
    """G-A-05: Return False (stale) if data is older than max_lag trading days."""
    logger.debug(f"[G-A-05] check_data_freshness: last={last_date_str}, lag={trading_days_since}, max={max_lag}")
    is_fresh = trading_days_since <= max_lag
    if not is_fresh:
        logger.warning(
            f"[G-A-05] STALE DATA: last update {last_date_str}, {trading_days_since} trading days ago "
            f"(max allowed: {max_lag})"
        )
    else:
        logger.debug(f"[G-A-05] Data is fresh: {trading_days_since} trading days old")
    return is_fresh


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SYMBOL / UNIVERSE (G-S-*)
# ─────────────────────────────────────────────────────────────────────────────

VALID_SERIES = {"EQ"}
EXCLUDE_KEYWORDS = ["ETF", "FUND", "REIT", "INVIT", "BEES", "GOLD", "SILVER", "SGB"]


def filter_eq_series(df: pd.DataFrame, series_col: str = "series") -> pd.DataFrame:
    """G-S-01: Keep only EQ series instruments."""
    logger.debug(f"[G-S-01] filter_eq_series: input={len(df)} rows")
    before = len(df)
    result = df[df[series_col].isin(VALID_SERIES)].copy()
    dropped = before - len(result)
    if dropped:
        logger.warning(f"[G-S-01] Dropped {dropped} non-EQ rows (series values: "
                       f"{df[~df[series_col].isin(VALID_SERIES)][series_col].unique().tolist()})")
    if result.empty:
        logger.warning("[G-S-01] No EQ series instruments found after filter")
    logger.debug(f"[G-S-01] After filter: {len(result)} rows")
    return result


def filter_by_listing_date(
    files: list,
    listing_date: date,
    date_extractor,
) -> list:
    """G-S-02 / ADR-004: Return only files on or after listing_date."""
    logger.debug(f"[G-S-02] filter_by_listing_date: {len(files)} files, listing_date={listing_date}")
    valid = [f for f in files if date_extractor(f) >= listing_date]
    skipped = len(files) - len(valid)
    if skipped:
        logger.debug(f"[G-S-02] Skipped {skipped} pre-listing files (listed: {listing_date})")
    return valid


def filter_delisted(
    files: list,
    delisting_date: Optional[date],
    date_extractor,
) -> list:
    """G-S-03: Cut off files after delisting date for DELISTED symbols."""
    if delisting_date is None:
        logger.debug("[G-S-03] Symbol is active — no delisting cutoff applied")
        return files
    logger.debug(f"[G-S-03] filter_delisted: {len(files)} files, delisting_date={delisting_date}")
    valid = [f for f in files if date_extractor(f) <= delisting_date]
    trimmed = len(files) - len(valid)
    if trimmed:
        logger.debug(f"[G-S-03] Trimmed {trimmed} post-delisting files")
    return valid


def validate_universe_size(equity_master: pd.DataFrame, min_symbols: int = 1800) -> None:
    """G-S-04: Raise if EQ symbol count is suspiciously low."""
    eq_count = len(equity_master[equity_master.get("series", pd.Series()).eq("EQ")
                                 if "series" in equity_master.columns else equity_master.index.notna()])
    logger.debug(f"[G-S-04] validate_universe_size: {eq_count} EQ symbols (min={min_symbols})")
    if eq_count < min_symbols:
        logger.error(f"[G-S-04] UNIVERSE ANOMALY: {eq_count} EQ symbols < {min_symbols} minimum")
        raise RuntimeError(f"Universe anomaly: {eq_count} EQ symbols. Expected {min_symbols}+")


def deduplicate_isin(df: pd.DataFrame, isin_col: str = "isin", status_col: str = "status") -> pd.DataFrame:
    """G-S-05: Keep only active symbol per ISIN when duplicates exist."""
    logger.debug(f"[G-S-05] deduplicate_isin: {len(df)} rows")
    dups = df[df.duplicated(isin_col, keep=False)]
    if dups.empty:
        logger.debug("[G-S-05] No duplicate ISINs found")
        return df
    logger.warning(f"[G-S-05] Duplicate ISINs detected: {dups[isin_col].unique().tolist()}")
    # Prefer ACTIVE over DELISTED; within same status keep first
    priority = {"ACTIVE": 0, "SUSPENDED": 1, "DELISTED": 2}
    df = df.copy()
    df["_sort_key"] = df[status_col].map(priority).fillna(99)
    result = df.sort_values("_sort_key").drop_duplicates(isin_col, keep="first").drop(columns=["_sort_key"])
    logger.debug(f"[G-S-05] After deduplication: {len(result)} rows")
    return result


def filter_non_equity_instruments(df: pd.DataFrame, name_col: str = "company_name") -> pd.DataFrame:
    """G-S-06: Exclude ETFs, REITs, InvITs, SGBs, Gold/Silver funds, etc."""
    logger.debug(f"[G-S-06] filter_non_equity_instruments: {len(df)} rows")
    pattern = "|".join(EXCLUDE_KEYWORDS)
    mask = df[name_col].str.upper().str.contains(pattern, na=False)
    excluded = df[mask]
    if not excluded.empty:
        logger.warning(f"[G-S-06] Excluded {len(excluded)} non-equity instruments: "
                       f"{excluded[name_col].tolist()}")
    result = df[~mask].copy()
    logger.debug(f"[G-S-06] After filter: {len(result)} rows")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — PRICE DATA (G-P-*)
# ─────────────────────────────────────────────────────────────────────────────

PRICE_COLS = ["open", "high", "low", "close"]


def guard_negative_prices(df: pd.DataFrame) -> pd.DataFrame:
    """G-P-01: Drop rows where any OHLC price is ≤ 0."""
    logger.debug(f"[G-P-01] guard_negative_prices: {len(df)} rows")
    cols = [c for c in PRICE_COLS if c in df.columns]
    invalid = df[(df[cols] <= 0).any(axis=1)]
    if not invalid.empty:
        logger.error(f"[G-P-01] NEGATIVE/ZERO PRICES: {len(invalid)} rows dropped — "
                     f"dates={invalid.get('date', invalid.index).tolist()}")
    result = df[(df[cols] > 0).all(axis=1)].copy()
    logger.debug(f"[G-P-01] After price guard: {len(result)} rows")
    return result


def guard_ohlc_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """G-P-02: Flag rows where High < Low, High < Close, or High < Open."""
    logger.debug(f"[G-P-02] guard_ohlc_consistency: {len(df)} rows")
    required = [c for c in ["open", "high", "low", "close"] if c in df.columns]
    if len(required) < 4:
        logger.warning(f"[G-P-02] Insufficient OHLC columns: {required}")
        return df
    invalid = df[
        (df["high"] < df["low"]) |
        (df["high"] < df["close"]) |
        (df["high"] < df["open"]) |
        (df["low"] > df["close"]) |
        (df["low"] > df["open"])
    ]
    if not invalid.empty:
        logger.warning(f"[G-P-02] OHLC inconsistency: {len(invalid)} rows — "
                       f"dates={invalid.get('date', invalid.index).tolist()}")
        df = df.copy()
        df["ohlc_valid"] = True
        df.loc[invalid.index, "ohlc_valid"] = False
    logger.debug(f"[G-P-02] OHLC check complete")
    return df


def guard_volume_sanity(df: pd.DataFrame, vol_col: str = "volume") -> pd.DataFrame:
    """G-P-03: Warn on zero-volume trading days."""
    logger.debug(f"[G-P-03] guard_volume_sanity: {len(df)} rows")
    if vol_col not in df.columns:
        logger.debug(f"[G-P-03] No '{vol_col}' column — skipping")
        return df
    zero_vol = df[df[vol_col] == 0]
    if not zero_vol.empty:
        logger.warning(f"[G-P-03] ZERO VOLUME on {len(zero_vol)} day(s) — "
                       f"possible circuit breaker: {zero_vol.get('date', zero_vol.index).tolist()}")
    return df


def flag_large_price_moves(
    df: pd.DataFrame,
    close_col: str = "close",
    threshold: float = 0.40,
) -> pd.DataFrame:
    """G-P-04: Flag single-session moves > threshold (default 40%) for corporate action review."""
    logger.debug(f"[G-P-04] flag_large_price_moves: threshold={threshold:.0%}, {len(df)} rows")
    df = df.copy()
    df["_pct_change"] = df[close_col].pct_change().abs()
    large = df[df["_pct_change"] > threshold]
    if not large.empty:
        logger.warning(
            f"[G-P-04] LARGE PRICE MOVE (>{threshold:.0%}): {len(large)} instance(s) — "
            f"check corporate actions: {large.get('date', large.index).tolist()}"
        )
        df["ca_review_flag"] = df["_pct_change"] > threshold
    df = df.drop(columns=["_pct_change"], errors="ignore")
    return df


def guard_delivery_pct(df: pd.DataFrame, col: str = "delivery_pct") -> pd.DataFrame:
    """G-P-06: Set delivery_pct to NaN if outside 0–100 range."""
    logger.debug(f"[G-P-06] guard_delivery_pct: {len(df)} rows")
    if col not in df.columns:
        return df
    df = df.copy()
    out_of_range = df[(df[col] < 0) | (df[col] > 100)]
    if not out_of_range.empty:
        logger.warning(f"[G-P-06] {len(out_of_range)} rows with invalid delivery_pct — setting to NaN")
        df.loc[(df[col] < 0) | (df[col] > 100), col] = None
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — CLASSIFICATION (G-C-*)
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_QUEUE_DEFAULT = Path("data/NSE/equity_master/fundamentals_review_queue.csv")


def fill_null_sectors(
    df: pd.DataFrame,
    sector_col: str = "sector_platform",
    queue_path: Optional[Path] = None,
) -> pd.DataFrame:
    """G-C-01: Replace null sectors with UNCATEGORIZED; log to review queue."""
    logger.debug(f"[G-C-01] fill_null_sectors: {len(df)} rows")
    df = df.copy()
    unclassified = df[df[sector_col].isnull()]
    if not unclassified.empty:
        count = len(unclassified)
        symbols = unclassified.get("symbol", unclassified.index).tolist()
        logger.warning(f"[G-C-01] {count} symbol(s) have null sector — set to UNCATEGORIZED: {symbols}")
        df[sector_col] = df[sector_col].fillna("UNCATEGORIZED")
        if queue_path:
            _append_to_review_queue(unclassified, queue_path)
    return df


def apply_manual_overrides(
    df: pd.DataFrame,
    override_path: Path,
    symbol_col: str = "symbol",
    sector_col: str = "sector_platform",
    theme_col: str = "theme_platform",
) -> pd.DataFrame:
    """G-C-02: Apply manual override CSV — these assignments are immutable."""
    logger.debug(f"[G-C-02] apply_manual_overrides: override_path={override_path}")
    if not override_path.exists():
        logger.debug(f"[G-C-02] No override file found at {override_path}")
        return df
    overrides = pd.read_csv(override_path)
    df = df.copy().set_index(symbol_col) if symbol_col in df.columns else df.copy()
    applied = 0
    for _, row in overrides.iterrows():
        sym = row.get(symbol_col)
        if sym in df.index:
            if sector_col in row and pd.notna(row[sector_col]):
                df.loc[sym, sector_col] = row[sector_col]
            if theme_col in row and pd.notna(row[theme_col]):
                df.loc[sym, theme_col] = row[theme_col]
            applied += 1
            logger.debug(f"[G-C-02] Override applied: {sym} → sector={row.get(sector_col)}, theme={row.get(theme_col)}")
    logger.info(f"[G-C-02] Manual overrides applied to {applied} symbol(s)")
    return df.reset_index()


def flag_low_confidence(
    df: pd.DataFrame,
    confidence_col: str = "classification_confidence",
    threshold: float = 0.70,
    queue_path: Optional[Path] = None,
) -> pd.DataFrame:
    """G-C-03: Move symbols with confidence < threshold to review queue."""
    logger.debug(f"[G-C-03] flag_low_confidence: threshold={threshold}, {len(df)} rows")
    if confidence_col not in df.columns:
        logger.warning(f"[G-C-03] No '{confidence_col}' column — skipping")
        return df
    low = df[df[confidence_col] < threshold]
    if not low.empty:
        logger.warning(f"[G-C-03] {len(low)} symbol(s) below confidence threshold {threshold}: "
                       f"{low.get('symbol', low.index).tolist()}")
        if queue_path:
            _append_to_review_queue(low, queue_path)
    return df


def _append_to_review_queue(df: pd.DataFrame, queue_path: Path) -> None:
    """Internal: append rows to the review queue CSV."""
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    header = not queue_path.exists()
    df.to_csv(queue_path, mode="a", header=header, index=False)
    logger.debug(f"[review_queue] Appended {len(df)} rows to {queue_path}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — CORPORATE ACTIONS (G-CA-*)
# ─────────────────────────────────────────────────────────────────────────────

def validate_split_ratio(ratio: float, symbol: str = "") -> None:
    """G-CA-02: Split ratio must be > 0 and ≠ 1.0."""
    logger.debug(f"[G-CA-02] validate_split_ratio: symbol={symbol}, ratio={ratio}")
    if ratio <= 0 or ratio == 1.0:
        logger.error(f"[G-CA-02] Invalid split ratio for {symbol}: {ratio}")
        raise ValueError(f"Invalid split ratio for {symbol}: {ratio}. Must be > 0 and ≠ 1.0")
    logger.debug(f"[G-CA-02] Split ratio valid: {ratio}")


def validate_dividend(amount: float, price: float, symbol: str = "") -> bool:
    """G-CA-03: Return True if ordinary; False if extraordinary (amount > price * 50%)."""
    logger.debug(f"[G-CA-03] validate_dividend: symbol={symbol}, amount={amount}, price={price}")
    threshold = price * 0.50
    is_extraordinary = amount > threshold
    if is_extraordinary:
        logger.warning(
            f"[G-CA-03] EXTRAORDINARY DIVIDEND: {symbol} — "
            f"dividend {amount} > 50% of price {price} (threshold {threshold:.2f})"
        )
    return not is_extraordinary


def log_corporate_action(
    symbol: str,
    ca_type: str,
    ex_date: str,
    detail: str,
    detected_by: str,
    log_path: Path,
) -> None:
    """G-CA-04: Log every corporate action event to ca_events.log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"{datetime.now(IST).isoformat()} | {symbol} | {ca_type} | "
        f"ex_date={ex_date} | {detail} | detected_by={detected_by}\n"
    )
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"[G-CA-04] CA event logged: {symbol} {ca_type} ex={ex_date}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — INTELLIGENCE SCORING (G-I-*)
# ─────────────────────────────────────────────────────────────────────────────

def check_min_sessions(data: pd.DataFrame, symbol: str = "", min_sessions: int = 5) -> bool:
    """G-I-01: Return False if fewer than min_sessions rows are available."""
    n = len(data)
    logger.debug(f"[G-I-01] check_min_sessions: symbol={symbol}, n={n}, min={min_sessions}")
    if n < min_sessions:
        logger.warning(f"[G-I-01] Insufficient data for {symbol}: {n} sessions < {min_sessions} minimum")
        return False
    return True


def check_data_coverage(
    actual_count: int,
    expected_count: int,
    symbol: str = "",
    min_coverage: float = 0.80,
) -> str:
    """G-I-02: Return 'RELIABLE' or 'UNRELIABLE' based on coverage ratio."""
    logger.debug(f"[G-I-02] check_data_coverage: symbol={symbol}, actual={actual_count}, expected={expected_count}")
    if expected_count == 0:
        logger.warning(f"[G-I-02] Expected count is 0 for {symbol}")
        return "UNRELIABLE"
    coverage = actual_count / expected_count
    if coverage < min_coverage:
        logger.warning(
            f"[G-I-02] LOW COVERAGE for {symbol}: {actual_count}/{expected_count} "
            f"({coverage:.1%}) < {min_coverage:.0%} threshold → UNRELIABLE"
        )
        return "UNRELIABLE"
    logger.debug(f"[G-I-02] Coverage OK for {symbol}: {coverage:.1%}")
    return "RELIABLE"


def enforce_score_range(
    df: pd.DataFrame,
    score_col: str,
    min_val: float,
    max_val: float,
) -> pd.DataFrame:
    """G-I-03: Clip score column to [min_val, max_val]."""
    logger.debug(f"[G-I-03] enforce_score_range: col={score_col}, range=[{min_val}, {max_val}]")
    if score_col not in df.columns:
        logger.warning(f"[G-I-03] Column '{score_col}' not found")
        return df
    df = df.copy()
    before_min = (df[score_col] < min_val).sum()
    before_max = (df[score_col] > max_val).sum()
    df[score_col] = df[score_col].clip(min_val, max_val)
    if before_min or before_max:
        logger.warning(f"[G-I-03] Clipped {before_min} below-min and {before_max} above-max values in '{score_col}'")
    return df


def check_score_staleness(source_lag_days: int, max_lag: int = 5) -> bool:
    """G-I-05: Return True (stale) if source data is older than max_lag trading days."""
    is_stale = source_lag_days > max_lag
    if is_stale:
        logger.warning(f"[G-I-05] STALE SCORE: source data {source_lag_days} trading days old (max {max_lag})")
    else:
        logger.debug(f"[G-I-05] Score freshness OK: {source_lag_days} days lag")
    return is_stale


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — FINANCIAL RESULTS (G-F-*)
# ─────────────────────────────────────────────────────────────────────────────

# India FY: Q1=Apr-Jun(4-6), Q2=Jul-Sep(7-9), Q3=Oct-Dec(10-12), Q4=Jan-Mar(1-3)
INDIA_QUARTER_MAP = {1: "Q4", 2: "Q4", 3: "Q4", 4: "Q1", 5: "Q1", 6: "Q1",
                     7: "Q2", 8: "Q2", 9: "Q2", 10: "Q3", 11: "Q3", 12: "Q3"}


def get_india_quarter(month: int) -> str:
    """Return India FY quarter name for given month number."""
    q = INDIA_QUARTER_MAP.get(month)
    logger.debug(f"[G-F-01] get_india_quarter: month={month} → {q}")
    return q


def validate_pl_sanity(revenue: float, pat: float, symbol: str = "", quarter: str = "") -> None:
    """G-F-02: Flag impossible P&L combinations."""
    logger.debug(f"[G-F-02] validate_pl_sanity: symbol={symbol}, quarter={quarter}, revenue={revenue}, pat={pat}")
    if revenue <= 0:
        logger.warning(f"[G-F-02] Non-positive Revenue for {symbol} {quarter}: {revenue}")
    if pat > revenue * 1.5:
        logger.error(f"[G-F-02] PAT exceeds Revenue for {symbol} {quarter}: PAT={pat}, Revenue={revenue}")
        raise ValueError(f"PAT ({pat}) > Revenue ({revenue}) for {symbol} {quarter} — likely data error")


def detect_growth_outlier(yoy_growth: float, symbol: str = "", quarter: str = "", threshold: float = 5.0) -> bool:
    """G-F-03: Return True if |YoY growth| > threshold (default 500%)."""
    is_outlier = abs(yoy_growth) > threshold
    logger.debug(f"[G-F-03] detect_growth_outlier: symbol={symbol}, yoy={yoy_growth:.0%}, outlier={is_outlier}")
    if is_outlier:
        logger.warning(f"[G-F-03] GROWTH OUTLIER: {symbol} {quarter} YoY={yoy_growth:.0%} — verify data")
    return is_outlier


def validate_shareholding_sum(
    promoter: float,
    fii: float,
    dii: float,
    public: float,
    others: float,
    symbol: str = "",
    quarter: str = "",
    tolerance: float = 1.0,
) -> bool:
    """G-F-04: Return True if holdings sum within 100% ± tolerance."""
    total = promoter + fii + dii + public + others
    logger.debug(f"[G-F-04] validate_shareholding_sum: symbol={symbol}, total={total:.2f}%")
    if not (100.0 - tolerance <= total <= 100.0 + tolerance):
        logger.error(f"[G-F-04] Shareholding sum anomaly: {symbol} {quarter} total={total:.2f}%")
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — TRADING CALENDAR (G-TC-*)
# ─────────────────────────────────────────────────────────────────────────────

def is_expected_missing(check_date: date, holidays: set) -> bool:
    """G-TC-01/02: True if date is weekend or NSE holiday (expected non-trading day)."""
    if check_date.weekday() >= 5:
        logger.debug(f"[G-TC-01] {check_date} is weekend — expected missing")
        return True
    if check_date in holidays:
        logger.debug(f"[G-TC-02] {check_date} is NSE holiday — expected missing")
        return True
    logger.debug(f"[G-TC-01/02] {check_date} is expected trading day")
    return False


def get_india_budget_risk_flag(check_date: date) -> bool:
    """G-TC-04: Return True if date is Feb 1 (India Union Budget day)."""
    is_budget = check_date.month == 2 and check_date.day == 1
    if is_budget:
        logger.warning(f"[G-TC-04] BUDGET DAY: {check_date} — expect unusual market conditions")
    return is_budget


def is_fno_expiry(check_date: date) -> bool:
    """G-TC-06: Return True if check_date is last Thursday of its month."""
    if check_date.weekday() != 3:
        return False
    # Check if next Thursday is in a different month
    next_thu = date(check_date.year, check_date.month, check_date.day + 7 if check_date.day + 7 <= 31 else 1)
    try:
        next_thu = date(check_date.year, check_date.month, check_date.day + 7)
        is_last = next_thu.month != check_date.month
    except ValueError:
        is_last = True
    if is_last:
        logger.debug(f"[G-TC-06] F&O EXPIRY: {check_date} — higher volume expected, not anomalous")
    return is_last


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10 — INSTITUTIONAL DATA (G-ID-*)
# ─────────────────────────────────────────────────────────────────────────────

INSTITUTIONAL_OI_START_YEAR = 2016


def check_institutional_oi_availability(year: int) -> bool:
    """G-ID-04: Return False for years before institutional OI data is available."""
    available = year >= INSTITUTIONAL_OI_START_YEAR
    if not available:
        logger.warning(f"[G-ID-04] Institutional OI/Volume data not available before {INSTITUTIONAL_OI_START_YEAR}. "
                       f"Year {year} requested.")
    return available


def validate_gross_flows(df: pd.DataFrame, participant: str = "fii") -> None:
    """G-ID-05 / ADR-006: Ensure BUY, SELL, and NET columns are all present."""
    p = participant.lower()
    required = [f"{p}_buy", f"{p}_sell", f"{p}_net"]
    logger.debug(f"[G-ID-05] validate_gross_flows: checking {required}")
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"[G-ID-05] ADR-006 VIOLATION: Gross flows missing: {missing}. "
                     f"Store BUY + SELL + NET separately — never only NET.")
        raise ValueError(f"Gross flow columns missing: {missing}. ADR-006 requires BUY, SELL, and NET.")
    # Verify NET = BUY - SELL
    computed_net = df[f"{p}_buy"] - df[f"{p}_sell"]
    mismatch = (computed_net - df[f"{p}_net"]).abs() > 0.01
    if mismatch.any():
        count = int(mismatch.sum())
        logger.warning(f"[G-ID-05] {count} row(s) where {p}_net ≠ {p}_buy - {p}_sell")
    logger.debug(f"[G-ID-05] Gross flow validation passed for {participant}")


def check_t1_data_lag(data_date: date, cutoff_hour: int = 18) -> bool:
    """G-ID-01: Return True if it's safe to flag today's data as missing (after 18:00 IST)."""
    now = datetime.now(IST)
    today = now.date()
    if data_date < today and now.hour >= cutoff_hour:
        logger.warning(f"[G-ID-01] T+1 LAG: Data for {data_date} missing after {cutoff_hour}:00 IST — flag as missing")
        return True
    logger.debug(f"[G-ID-01] T+1 lag check: data_date={data_date}, now={now.strftime('%H:%M IST')} — OK or too early")
    return False


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11 — SYSTEM (G-SYS-*)
# ─────────────────────────────────────────────────────────────────────────────

def validate_environment(required_vars: list) -> None:
    """G-SYS-01: Raise early with clear message if required env vars are missing."""
    logger.debug(f"[G-SYS-01] validate_environment: checking {required_vars}")
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"[G-SYS-01] Missing environment variables: {missing}")
        raise EnvironmentError(f"Missing required env vars: {missing}. Check .env file or environment setup.")
    logger.debug(f"[G-SYS-01] All required env vars present: {required_vars}")


def scan_hardcoded_credentials(source_dir: Path) -> list:
    """G-SYS-03: Scan .py files for hardcoded credential patterns. Return list of (file, line) hits."""
    PATTERNS = [
        r"(?i)(password|token|secret|api_key|credential)\s*=\s*['\"][\w\-\.]{8,}['\"]",
        r"(?i)bot_token\s*=\s*['\"][\d:a-zA-Z\-_]{20,}['\"]",
    ]
    logger.debug(f"[G-SYS-03] Scanning for hardcoded credentials in {source_dir}")
    hits = []
    for py_file in source_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(content.splitlines(), start=1):
                for pat in PATTERNS:
                    if re.search(pat, line):
                        hits.append((str(py_file), i, line.strip()))
                        logger.warning(f"[G-SYS-03] Possible credential at {py_file}:{i}: {line.strip()[:80]}")
        except Exception as e:
            logger.debug(f"[G-SYS-03] Could not read {py_file}: {e}")
    if not hits:
        logger.debug("[G-SYS-03] No hardcoded credentials detected")
    return hits


def check_disk_space(data_dir: Path, min_gb: float = 1.0) -> None:
    """G-SYS-05: Raise if available disk space is below minimum."""
    logger.debug(f"[G-SYS-05] check_disk_space: dir={data_dir}, min={min_gb}GB")
    free_gb = shutil.disk_usage(str(data_dir)).free / (1024 ** 3)
    if free_gb < min_gb:
        logger.error(f"[G-SYS-05] INSUFFICIENT DISK SPACE: {free_gb:.2f} GB free < {min_gb} GB minimum")
        raise RuntimeError(f"Insufficient disk space: {free_gb:.2f} GB free. Need at least {min_gb} GB.")
    logger.debug(f"[G-SYS-05] Disk space OK: {free_gb:.2f} GB free")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12 — PERFORMANCE (G-PERF-*)
# ─────────────────────────────────────────────────────────────────────────────

def chunk_symbol_list(symbols: list, chunk_size: int = 100) -> list:
    """G-PERF-01: Split large symbol lists into chunks to avoid full-universe in-memory loads."""
    logger.debug(f"[G-PERF-01] chunk_symbol_list: {len(symbols)} symbols → chunks of {chunk_size}")
    chunks = [symbols[i:i + chunk_size] for i in range(0, len(symbols), chunk_size)]
    logger.debug(f"[G-PERF-01] Created {len(chunks)} chunk(s)")
    return chunks


def warn_market_hours_batch(batch_size: int, limit: int = 50) -> bool:
    """G-PERF-03: Return True (blocked) if market is open and batch exceeds limit."""
    if is_market_hours() and batch_size > limit:
        logger.warning(
            f"[G-PERF-03] MARKET HOURS BATCH LIMIT: requested {batch_size} > {limit} allowed during market hours"
        )
        return True
    return False
