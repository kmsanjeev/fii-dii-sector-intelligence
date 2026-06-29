# PLATFORM GUARDRAILS & EDGE CASE REGISTRY
## Capital Flow Intelligence Platform
### Version 1.0 — June 2026

---

## PURPOSE

This document defines all mandatory guardrails, defensive checks, and edge case
handling rules for the platform. Every engine must comply. This is not optional guidance —
these are engineering contracts.

---

## SECTION 1 — DATA INTEGRITY GUARDRAILS

### G-D-01 — Raw Data Immutability (ADR-001)
**Rule:** Files under `data/bhavcopy/` and `data/NSE/bhavcopy/` are NEVER modified after download.
**Enforcement:**
```python
def write_raw(df, path: Path):
    if path.exists():
        raise FileExistsError(f"Raw file already exists: {path}. Raw data is immutable.")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
```
**Edge case:** Corrupted file detected → rename to `.corrupted`, download fresh, log the event.

### G-D-02 — Atomic Writes
**Rule:** ALL file writes must use a temp-then-rename pattern. Never write directly to the final path.
**Enforcement:**
```python
import shutil, tempfile

def safe_write_csv(df: pd.DataFrame, target: Path):
    if df.empty:
        raise ValueError(f"Refusing to write empty DataFrame to {target}")
    tmp = target.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(target))
```
**Why:** Prevents partial files if the process crashes mid-write.

### G-D-03 — Empty DataFrame Guard
**Rule:** Never write an empty DataFrame to any output file.
```python
if df.empty:
    logger.warning(f"Skipping write — empty result for {context}")
    return  # do not raise, just skip
```

### G-D-04 — Schema Validation Before Write
**Rule:** Every engine must validate schema before saving output.
```python
def validate_schema(df: pd.DataFrame, required: list[str], context: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[{context}] Schema violation — missing columns: {missing}")
    null_keys = [c for c in required if df[c].isnull().any()]
    if null_keys:
        logger.warning(f"[{context}] Null values in key columns: {null_keys}")
```

### G-D-05 — Duplicate Date Guard
**Rule:** Never append duplicate dates to historical time series.
```python
def safe_append(existing: pd.DataFrame, new: pd.DataFrame, date_col="date") -> pd.DataFrame:
    existing_dates = set(pd.to_datetime(existing[date_col]).dt.date)
    fresh = new[~pd.to_datetime(new[date_col]).dt.date.isin(existing_dates)]
    if fresh.empty:
        return existing
    return pd.concat([existing, fresh]).sort_values(date_col).reset_index(drop=True)
```

### G-D-06 — Sorted Output Invariant
**Rule:** All time-series outputs must be sorted ascending by date before saving.
```python
df = df.sort_values("date").reset_index(drop=True)
```

### G-D-07 — File Size Sanity Check
**Rule:** After writing, verify file is not suspiciously small.
```python
MIN_SIZES = {"bhavcopy": 50_000, "equity_master": 10_000, "intelligence": 1_000}

def verify_file_size(path: Path, min_bytes: int):
    size = path.stat().st_size
    if size < min_bytes:
        raise RuntimeError(f"Output file suspiciously small: {path} ({size} bytes, min {min_bytes})")
```

---

## SECTION 2 — API / ACQUISITION GUARDRAILS

### G-A-01 — nselib Rate Limiting
**Rule:** Always wait `cfg.API_DELAY` (1.0s) between consecutive nselib calls.
```python
import time
for date in dates:
    data = nse_client.fetch(date)
    time.sleep(cfg.API_DELAY)
```

### G-A-02 — Retry with Exponential Backoff
**Rule:** All API calls must retry `cfg.MAX_RETRIES` (3) times with doubling delay.
```python
def fetch_with_retry(fn, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn(*args)
        except Exception as e:
            wait = cfg.RETRY_DELAY * (2 ** attempt)
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"All {max_retries} attempts failed")
```

### G-A-03 — Recovery Queue
**Rule:** Failed downloads must be logged to a recovery queue, not silently skipped.
```python
# At end of any download loop
if failed_items:
    recovery_df = pd.DataFrame({"item": failed_items, "timestamp": datetime.now().isoformat()})
    recovery_path = cfg.NSE_DIR / "recovery_queue.csv"
    safe_append_to_csv(recovery_df, recovery_path)
    logger.error(f"{len(failed_items)} items failed — logged to {recovery_path}")
```

### G-A-04 — Market Hours Guard
**Rule:** No heavy batch downloads during market hours (09:15 – 15:30 IST).
```python
from datetime import datetime
import pytz
IST = pytz.timezone("Asia/Kolkata")

def is_market_hours() -> bool:
    now = datetime.now(IST)
    return now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)

if is_market_hours() and batch_size > 100:
    logger.warning("Deferring heavy download — market hours active")
    return
```

### G-A-05 — Stale Data Detection
**Rule:** Flag any intelligence output whose source data is > 5 trading days old.
```python
def check_data_freshness(last_date: str, trading_calendar, max_lag_days: int = 5):
    last = pd.to_datetime(last_date).date()
    today = date.today()
    lag = trading_calendar.trading_days_between(last, today)
    if lag > max_lag_days:
        logger.warning(f"STALE DATA: last update {last_date}, {lag} trading days ago")
        return False
    return True
```

### G-A-06 — Process Lock (Singleton Execution)
**Rule:** Prevent two instances of the same engine running simultaneously.
```python
import fcntl  # Unix; use portalocker on Windows

LOCK_FILE = cfg.LOG_DIR / f"{engine_name}.lock"

with open(LOCK_FILE, "w") as lock:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_engine()
    except BlockingIOError:
        logger.error(f"Engine {engine_name} already running. Aborting.")
        sys.exit(1)
```

---

## SECTION 3 — SYMBOL / UNIVERSE GUARDRAILS

### G-S-01 — EQ Series Filter
**Rule:** Only process EQ series stocks. Reject BE, IL, N1, SM, W, PP, etc.
```python
VALID_SERIES = {"EQ"}
df = df[df["series"].isin(VALID_SERIES)]
```
**Why:** Other series are odd-lot, institutional, illiquid, or settlement-specific instruments.

### G-S-02 — Listing Date Awareness (ADR-004)
**Rule:** Never process bhavcopy data before a stock's listing date.
```python
def get_valid_files(symbol: str, all_files: list, equity_master: pd.DataFrame) -> list:
    listing_date = pd.to_datetime(equity_master.loc[symbol, "listing_date"]).date()
    return [f for f in all_files if extract_date_from_filename(f) >= listing_date]
```

### G-S-03 — Delisted Symbol Handling
**Rule:** Delisted symbols keep their historical data. Processing stops at their last trading date.
```python
if equity_master.loc[symbol, "status"] == "DELISTED":
    last_date = equity_master.loc[symbol, "delisting_date"]
    files = [f for f in files if extract_date(f) <= pd.to_datetime(last_date).date()]
```

### G-S-04 — Universe Size Validation
**Rule:** If equity_master has < 1800 EQ symbols, something is wrong — raise alert.
```python
eq_symbols = equity_master[equity_master["series"] == "EQ"]
if len(eq_symbols) < 1800:
    raise RuntimeError(f"UNIVERSE ANOMALY: Only {len(eq_symbols)} EQ symbols. Expected 2000+")
```

### G-S-05 — ISIN Deduplication
**Rule:** One ISIN must map to exactly one canonical symbol. On merger/consolidation, use the survivor.
```python
duplicated_isin = equity_master[equity_master.duplicated("isin", keep=False)]
if not duplicated_isin.empty:
    logger.warning(f"Duplicate ISINs detected: {duplicated_isin['isin'].tolist()}")
    # Keep only the active symbol (status == 'ACTIVE') per ISIN
    equity_master = equity_master.sort_values("status").drop_duplicates("isin", keep="first")
```

### G-S-06 — Exclude Non-Equity Instruments
**Rule:** Filter out ETFs, Index Funds, REITs, InvITs, SGBs from equity universe.
```python
EXCLUDE_KEYWORDS = ["ETF", "FUND", "REIT", "INVIT", "BEES", "GOLD", "SILVER", "SGB"]
mask = equity_master["company_name"].str.upper().str.contains("|".join(EXCLUDE_KEYWORDS), na=False)
equity_universe = equity_master[~mask & (equity_master["series"] == "EQ")]
```

---

## SECTION 4 — PRICE DATA GUARDRAILS

### G-P-01 — Negative Price Guard
**Rule:** Prices (Open, High, Low, Close) must all be > 0.
```python
price_cols = ["open", "high", "low", "close"]
invalid = df[(df[price_cols] <= 0).any(axis=1)]
if not invalid.empty:
    logger.error(f"NEGATIVE/ZERO PRICES detected for {len(invalid)} rows")
    df = df[(df[price_cols] > 0).all(axis=1)]
```

### G-P-02 — OHLC Consistency Check
**Rule:** High >= Open, High >= Close, High >= Low; Low <= Open, Low <= Close.
```python
ohlc_invalid = df[
    (df["high"] < df["low"]) |
    (df["high"] < df["close"]) |
    (df["high"] < df["open"]) |
    (df["low"] > df["close"]) |
    (df["low"] > df["open"])
]
if not ohlc_invalid.empty:
    logger.warning(f"OHLC inconsistency in {len(ohlc_invalid)} rows — flagging")
```

### G-P-03 — Volume Sanity Check
**Rule:** Volume = 0 on a trading day is suspicious. Log for review.
```python
zero_vol = df[df["volume"] == 0]
if not zero_vol.empty:
    logger.warning(f"Zero volume on {len(zero_vol)} days — possible circuit breaker or data gap")
```

### G-P-04 — Large Price Move Flag (Corporate Action Detector)
**Rule:** Single-session close change > 40% triggers a corporate action review flag.
```python
df["pct_change"] = df["close"].pct_change().abs()
large_moves = df[df["pct_change"] > 0.40]
if not large_moves.empty:
    logger.warning(f"Large price moves (>40%) detected — check for corporate actions: {large_moves.index.tolist()}")
```
**Why:** Bonus, split, rights issue all cause large overnight price adjustments.

### G-P-05 — Raw Prices Never Auto-Adjusted
**Rule:** Raw bhavcopy prices are stored as-is. Never apply split/bonus adjustments to raw data.
Price adjustment (for backtesting) is a separate derived layer only.

### G-P-06 — Delivery Percentage Range
**Rule:** Delivery % must be between 0 and 100.
```python
if "delivery_pct" in df.columns:
    df.loc[df["delivery_pct"] < 0, "delivery_pct"] = None
    df.loc[df["delivery_pct"] > 100, "delivery_pct"] = None
```

---

## SECTION 5 — CLASSIFICATION GUARDRAILS

### G-C-01 — No Null Sector Assignments
**Rule:** Every symbol must have a sector. Use `UNCATEGORIZED` as the final fallback — never null.
```python
df["sector_platform"] = df["sector_platform"].fillna("UNCATEGORIZED")
# Log all symbols that fell to UNCATEGORIZED for manual review
unclassified = df[df["sector_platform"] == "UNCATEGORIZED"]
if not unclassified.empty:
    logger.warning(f"{len(unclassified)} symbols unclassified: {unclassified['symbol'].tolist()}")
```

### G-C-02 — Manual Override Immutability
**Rule:** If a symbol appears in `data/reference/mapping/manual_classification_override.csv`,
its sector and theme assignments are FROZEN. No engine may override them.
```python
OVERRIDE_FILE = cfg.REFERENCE_DIR / "mapping" / "manual_classification_override.csv"

def apply_overrides(df: pd.DataFrame) -> pd.DataFrame:
    if OVERRIDE_FILE.exists():
        overrides = pd.read_csv(OVERRIDE_FILE).set_index("symbol")
        for symbol, row in overrides.iterrows():
            if symbol in df.index:
                df.loc[symbol, "sector_platform"] = row["sector_platform"]
                df.loc[symbol, "theme_platform"] = row["theme_platform"]
    return df
```

### G-C-03 — Classification Confidence Score
**Rule:** Every classification must carry a confidence score (0.0–1.0).
Symbols with confidence < 0.70 go to `fundamentals_review_queue.csv`.
```python
# After classification
low_confidence = df[df["classification_confidence"] < 0.70]
if not low_confidence.empty:
    low_confidence.to_csv(cfg.EQUITY_MASTER_DIR / "fundamentals_review_queue.csv", index=False)
```

### G-C-04 — Classification Priority Hierarchy
**Enforce this exact order — never skip a level:**
1. Manual override (G-C-02)
2. NSE Industry Master (exact match)
3. NSE Index membership (sector index → sector)
4. Business profile keyword matching
5. Screener.in sector (validation only, not primary)
6. UNCATEGORIZED (fallback, goes to review queue)

### G-C-05 — Conglomerate Handling
**Rule:** For conglomerates, use the PRIMARY revenue segment as the sector.
Never classify by holding company structure.
Known conglomerates requiring manual override: ITC, RELIANCE, BAJAJFINSV, L&T.

---

## SECTION 6 — CORPORATE ACTIONS GUARDRAILS

### G-CA-01 — Ex-Date vs Record Date
**Rule:** Use EX-DATE for price adjustment calculations (this is when the price adjusts).
Never use record date for price-side adjustments.

### G-CA-02 — Split Ratio Validation
**Rule:** Split ratio must be > 0 and ≠ 1.0. A 1:1 split is invalid.
```python
if corporate_action["type"] == "SPLIT":
    ratio = corporate_action["ratio"]
    assert ratio > 0 and ratio != 1.0, f"Invalid split ratio: {ratio}"
```

### G-CA-03 — Dividend Sanity Check
**Rule:** If dividend_amount > stock_price * 0.5, flag as extraordinary.
```python
if dividend_amount > stock_price * 0.5:
    logger.warning(f"EXTRAORDINARY DIVIDEND: {symbol} — dividend {dividend_amount} vs price {stock_price}")
```

### G-CA-04 — Corporate Action Impact Log
**Rule:** Every detected corporate action must be logged to `data/NSE/corporate_actions/ca_events.log`
with: symbol, ca_type, ex_date, ratio/amount, detected_by.

---

## SECTION 7 — INTELLIGENCE SCORING GUARDRAILS

### G-I-01 — Minimum Data Window
**Rule:** Do not compute scores with fewer than 5 trading days of data.
```python
MIN_SESSIONS = 5
if len(df) < MIN_SESSIONS:
    logger.warning(f"Insufficient data for {symbol}: {len(df)} sessions < {MIN_SESSIONS} minimum")
    return None  # return None, not 0
```

### G-I-02 — Missing Data Threshold
**Rule:** If > 20% of expected data points are missing, mark score as UNRELIABLE.
```python
expected = trading_calendar.count_trading_days(start_date, end_date)
actual = len(df.dropna())
if actual < expected * 0.80:
    score_metadata["reliability"] = "UNRELIABLE"
    logger.warning(f"Low data coverage: {actual}/{expected} points for {symbol}")
```

### G-I-03 — Score Range Enforcement
**Rule:** Scores must always be within their declared range. Clip on output.
```python
# For 0-100 scores:
df["score"] = df["score"].clip(0, 100)
# For -1 to +1 scores:
df["signal"] = df["signal"].clip(-1, 1)
```

### G-I-04 — NaN Propagation Prevention
**Rule:** Never use `fillna(0)` on price/volume/flow data — it creates false signals.
Use `fillna(method="ffill")` only where business logic supports forward-filling.
If data is genuinely missing, leave as NaN and exclude from scoring.

### G-I-05 — Score Staleness Flag
**Rule:** If an intelligence score's source data is > 5 trading days old, add `is_stale: True` to output.
```python
score_output["is_stale"] = lag_days > 5
```

---

## SECTION 8 — FINANCIAL RESULTS GUARDRAILS (Phase 4+)

### G-F-01 — Quarter Sequence Validation
**Rule:** Results for a company must be quarterly (Q1, Q2, Q3, Q4).
Flag if any quarter is missing in a 4-quarter window.
Indian financial year: Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar.

### G-F-02 — P&L Sanity Checks
```python
# PAT > Revenue is impossible (ignoring extraordinary items)
if result["pat"] > result["revenue"] * 1.5:
    logger.error(f"PAT exceeds Revenue for {symbol} {quarter} — likely data error")

# Negative Revenue is invalid for most sectors
if result["revenue"] <= 0:
    logger.warning(f"Non-positive Revenue for {symbol} {quarter}")
```

### G-F-03 — Growth Outlier Detection
**Rule:** YoY revenue/PAT growth > 500% in a single quarter — flag for manual review.
```python
if abs(yoy_growth) > 5.0:
    logger.warning(f"GROWTH OUTLIER: {symbol} {quarter} YoY={yoy_growth:.0%} — verify data")
```

### G-F-04 — Shareholding Sum Check
**Rule:** Promoter% + FII% + DII% + Public% + Others% must sum to ~100% (allow ±1% rounding).
```python
total = promoter + fii + dii + public + others
if not (99.0 <= total <= 101.0):
    logger.error(f"Shareholding sum anomaly: {symbol} {quarter} total={total:.2f}%")
```

---

## SECTION 9 — TRADING CALENDAR EDGE CASES

### G-TC-01 — Weekend Handling
NSE does not trade Saturday/Sunday. These are NOT missing dates.
```python
def is_expected_missing(date) -> bool:
    return date.weekday() >= 5  # Saturday=5, Sunday=6
```

### G-TC-02 — National Holiday vs NSE Holiday
Both count as non-trading days. Use the NSE holiday master file, not just national holidays.
Source: `data/reference/nse_holidays.csv` (authoritative).

### G-TC-03 — Market Circuit Breaker Halt
A partial-day halt still produces bhavcopy data — do not treat it as a missing date.

### G-TC-04 — Budget Day
Union Budget day (typically Feb 1) often has unusual price action.
The day is a full trading day. Do not skip. Flag any analysis during budget week.

### G-TC-05 — Mahurat Trading (Diwali)
NSE conducts a 1-hour special session on Diwali evening.
This produces a very small bhavcopy file. Process it normally but be aware of low volume.

### G-TC-06 — F&O Expiry Days
Last Thursday of the month has F&O expiry — expect higher volume and volatility.
Do not treat this as anomalous. Flag in reports but process normally.

### G-TC-07 — Index Rebalancing Dates
NSE semi-annually rebalances Nifty 50, 100, 200, 500, and sector indices.
Track constituent changes in `data/NSE/indices/` — historical membership matters for backtesting.

---

## SECTION 10 — INSTITUTIONAL DATA EDGE CASES

### G-ID-01 — T+1 Data Lag
NSE institutional data (FII/DII cash flow) is sometimes published with T+1 delay.
Do not treat today's data as missing if it's not available by market close.
Wait until 18:00 IST before marking today as missing.

### G-ID-02 — PRO/CLIENT Data Availability
PRO and CLIENT participant data is only available for F&O segment.
There is no PRO/CLIENT breakdown for cash market.
Do not attempt to derive cash-market PRO/CLIENT from F&O data.

### G-ID-03 — FII Derivatives Data Separate Channel
FII derivatives statistics are on a different NSE report than participant OI.
These must be downloaded and stored separately (config: separate path).

### G-ID-04 — Pre-2016 Institutional Data Gap
Institutional OI/Volume participant breakdown is only available from ~2016.
Do not attempt to backfill pre-2016 participant data.
FII/DII cash market flow may be available earlier — treat as separate dataset.

### G-ID-05 — Gross Flow Preservation (ADR-006)
**Rule:** Always store Buy, Sell, AND Net separately. Never store only Net.
```python
# WRONG — loses information
institutional_df["fii_net"] = fii_buy - fii_sell

# CORRECT — preserves all flows
institutional_df["fii_buy"] = fii_buy
institutional_df["fii_sell"] = fii_sell
institutional_df["fii_net"] = fii_buy - fii_sell
```

---

## SECTION 11 — ENVIRONMENT / SYSTEM GUARDRAILS

### G-SYS-01 — Environment Variable Guard
**Rule:** Check all required env vars at startup — fail fast with clear message.
```python
REQUIRED_ENV = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GOOGLE_CREDENTIALS"]

def validate_environment():
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Missing required env vars: {missing}. Check .env file.")
```

### G-SYS-02 — Git Security Guard
`.gitignore` must exclude:
- All CSV/Parquet files under `data/` (financial data not to be pushed to git)
- `.env`, `*.env`, `credentials.json`
- `logs/` contents
- `__pycache__/`, `*.pyc`

### G-SYS-03 — Credentials Never in Source
**Rule:** TELEGRAM_BOT_TOKEN, GOOGLE_CREDENTIALS, NSE API keys — never in any `.py` or `.md` file.
Always read from `os.getenv()`.

### G-SYS-04 — Log Rotation
**Rule:** Log files must not grow unboundedly. Use rotating file handler.
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    LOG_DIR / f"{name}.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5
)
```

### G-SYS-05 — Disk Space Pre-Check
**Rule:** Before any large batch download, verify sufficient disk space.
```python
import shutil
free_gb = shutil.disk_usage(cfg.DATA_DIR).free / (1024 ** 3)
if free_gb < 1.0:
    raise RuntimeError(f"Insufficient disk space: {free_gb:.2f} GB free. Need at least 1 GB.")
```

---

## SECTION 12 — PERFORMANCE GUARDRAILS

### G-PERF-01 — No Full-Universe In-Memory Loads
**Rule:** Never load all 4500+ stock histories into memory simultaneously.
Batch in groups of 100-200 symbols maximum.

### G-PERF-02 — Listing-Date-Aware File Filtering
**Rule:** Always filter file list by listing date BEFORE any file reads.
Saves 90%+ of I/O for recently-listed stocks.

### G-PERF-03 — Market Hours Processing Limit
**Rule:** During 09:15-15:30 IST, limit batch sizes to < 50 symbols per operation.
Heavy workloads (full rebuild, integrity scans) are only allowed after hours or weekends.

### G-PERF-04 — DataFrame Copy Awareness
**Rule:** Use `df.copy()` explicitly when creating modified subsets to avoid SettingWithCopyWarning.
```python
# WRONG
subset = df[df["sector"] == "IT"]
subset["score"] = 100  # may modify original

# CORRECT
subset = df[df["sector"] == "IT"].copy()
subset["score"] = 100
```

---

## GUARDRAIL COMPLIANCE CHECKLIST (per engine)

Before marking any engine as complete, verify:
- [ ] Schema validation on all writes
- [ ] Atomic writes (tmp → rename)
- [ ] Empty DataFrame guard
- [ ] Series filter (EQ only)
- [ ] Listing-date-aware processing
- [ ] Market hours guard (if applicable)
- [ ] Retry with backoff on API calls
- [ ] Recovery queue for failures
- [ ] Stale data detection
- [ ] Score range enforcement (if scoring)
- [ ] NaN propagation prevention
- [ ] No hardcoded paths (all use cfg.*)
- [ ] Log all warnings/errors
- [ ] Environment variable guard at startup

---

END OF GUARDRAILS DOCUMENT
