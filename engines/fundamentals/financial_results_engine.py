"""
Financial Results Engine -- Phase 15A
Fetches quarterly financial results from NSE XBRL filings for all EQ-series companies.

Strategy:
  The official NSE corporate financial-results endpoint returns the list of
  quarterly result filings submitted to NSE in that window.
  We use "filing season" windows (45-60 days after each quarter-end) which capture
  near-complete universe coverage (~3,500-3,900 companies per quarter).

  Each filing has an XBRL XML URL with detailed P&L data. We skip entries with
  invalid/missing XBRL ending in /xbrl/- and parse the rest concurrently.

Filing season windows (confirmed coverage via live tests):
  Jan-Mar 2025  -> Q3 FY25 (Oct-Dec 2024)  ~3,865 records, all valid XBRL
  Oct-Dec 2024  -> Q2 FY25 (Jul-Sep 2024)  ~3,738 records, all valid XBRL
  Jul-Sep 2024  -> Q1 FY25 (Apr-Jun 2024)  ~3,650 records, all valid XBRL
  Apr-Jul 2024  -> Q4 FY24 (Jan-Mar 2024)  ~4,474 records, all valid XBRL

Data source priority:
  1. NSE XBRL (official endpoint, identity-encoded transport) -- primary
  2. yfinance per-symbol quarterly_income_stmt -- last resort (capped)

Output: data/NSE/results/quarterly_results.csv
  Columns: symbol, date_start, date_end, quarter_label, window_label, filing_date,
           revenue_cr, net_profit_cr, eps, rounding, standalone_or_consolidated, source

Guardrails:
  - Atomic writes (G-D-02)
  - No empty DataFrame writes (G-D-03)
  - Rate limiting between NSE calls (G-A-01)
  - Failed entries -> recovery_queue.csv (G-A-03)
  - Incremental: rechecks recent windows and skips unchanged normalized output
"""

import hashlib
import json
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.nse_client import create_session
from engines.common.progress import progress

logger = get_logger(__name__)

RESULTS_DIR = cfg.NSE_DIR / "results"
OUTPUT_PATH = RESULTS_DIR / "quarterly_results.csv"
EQUITY_MASTER = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# Kept as a compatibility reference for callers that import this constant.
# Routine acquisition now derives recent filing windows from the current date.
FILING_WINDOWS = [
    ("01-01-2025", "31-03-2025", "Q3FY25"),
    ("01-10-2024", "31-12-2024", "Q2FY25"),
    ("01-07-2024", "30-09-2024", "Q1FY25"),
    ("01-04-2024", "31-07-2024", "Q4FY24"),
    ("01-01-2024", "31-03-2024", "Q3FY24"),
    ("01-10-2023", "31-12-2023", "Q2FY24"),
]

RESULTS_ORIGIN = "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"
RESULTS_API = "https://www.nseindia.com/api/corporates-financial-results"
_RECORD_KEY = [
    "symbol", "date_start", "date_end", "standalone_or_consolidated", "source", "filing_date",
]


def _generate_all_filing_windows() -> list[tuple[str, str, str]]:
    """Generate all filing-season windows from Q1FY18 (earliest reliable NSE XBRL) to today.

    NSE mandated XBRL filing for listed companies from 2017-18 onwards.
    Filing-season dates are the dates the results appear on NSE (not the financial period dates):
      Q1 (Apr-Jun) → filed Jul-Sep   same cal year
      Q2 (Jul-Sep) → filed Oct-Dec   same cal year
      Q3 (Oct-Dec) → filed Jan-Mar   next cal year
      Q4 (Jan-Mar) → filed Apr-Jul   next cal year (extended: annuals take longer)
    """
    today = datetime.now(timezone.utc).date()
    windows = []

    for fy in range(18, 100):           # FY18 = Apr2017-Mar2018, FY99 is far future
        base_cal = 2000 + fy - 1        # FY18 base calendar year = 2017
        quarters = [
            # (label, filing_from_m, filing_from_d, filing_to_m, filing_to_d, yr_offset)
            (f"Q1FY{fy:02d}", 7,  1,  9, 30, 0),
            (f"Q2FY{fy:02d}", 10, 1, 12, 31, 0),
            (f"Q3FY{fy:02d}", 1,  1,  3, 31, 1),
            (f"Q4FY{fy:02d}", 4,  1,  7, 31, 1),
        ]
        for label, fm, fd, tm, td, yr_off in quarters:
            filing_year = base_cal + yr_off
            try:
                window_end = date(filing_year, tm, td)
            except ValueError:
                continue
            if window_end > today:
                return windows          # stop once we pass today
            from_str = f"{fd:02d}-{fm:02d}-{filing_year}"
            to_str   = f"{td:02d}-{tm:02d}-{filing_year}"
            windows.append((from_str, to_str, label))

    return windows


def _recent_filing_windows(count: int = 2) -> list[tuple[str, str, str]]:
    """Return the most recent completed filing windows, newest first."""
    windows = _generate_all_filing_windows()
    return list(reversed(windows[-max(1, count):]))


def _parse_filing_date(value) -> str:
    """Normalize NSE filing timestamps without truncating the year."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc).date().isoformat()
        except (ValueError, TypeError):
            continue
    return ""

# XBRL namespace map
_NS = {
    "xbrli":      "http://www.xbrl.org/2003/instance",
    "in-bse-fin": "http://www.bseindia.com/xbrl/fin/2020-03-31/in-bse-fin",
}

# Maps our column names to XBRL tag names
_XBRL_FIELDS = {
    "symbol":        "Symbol",
    "date_start":    "DateOfStartOfReportingPeriod",
    "date_end":      "DateOfEndOfReportingPeriod",
    "revenue_raw":   "RevenueFromOperations",
    "profit_raw":    "ProfitLossForPeriod",
    "eps":           "BasicEarningsLossPerShareFromContinuingOperations",
    "rounding":      "LevelOfRoundingUsedInFinancialStatements",
    "nature":        "NatureOfReportStandaloneConsolidated",
    "quarter_label": "ReportingQuarter",
}

# NSE XBRL stores absolute rupees; divide by 1e7 to convert to crores (1 crore = 1e7 rupees)
_DEFAULT_SCALE = 1 / 1e7

YFINANCE_BATCH_CAP = 100


class FinancialResultsEngine:
    """
    Fetches quarterly P&L results from NSE XBRL filings for all listed companies.
    Uses filing-season windows to capture near-complete quarterly coverage (~3,500+ companies).
    Falls back to per-symbol yfinance if NSE XBRL is unavailable (capped).
    """

    def __init__(
        self,
        max_windows: int | None = None,
        backfill: bool = False,
        use_yfinance: bool = True,
        yfinance_cap: int = YFINANCE_BATCH_CAP,
    ):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.max_windows = max_windows
        self.backfill = backfill
        self.use_yfinance = use_yfinance
        self.yfinance_cap = yfinance_cap
        self.recovery: list[dict] = []
        self._nse_session = None

    def run(self) -> bool:
        logger.info("[FinancialResults] Starting quarterly results fetch")

        existing = self._load_existing()
        # A window label is not a completeness proof: one yfinance row or one
        # issuer filing must not suppress missing filings for every other
        # issuer in that window. The source master is therefore rechecked for
        # each recent window and exact records are deduplicated at merge time.
        rows = self._fetch_bulk_nselib(skip_labels=set())

        if not rows and self.use_yfinance:
            logger.info(
                f"[FinancialResults] XBRL unavailable, falling back to yfinance "
                f"(cap={self.yfinance_cap} symbols)"
            )
            rows = self._fetch_yfinance_all()

        if not rows:
            logger.warning(
                "[FinancialResults] No new results fetched. "
                "NSE XBRL archives may be temporarily unavailable. Retry after market hours."
            )
            return False

        existing_signature = self._canonical_signature(existing)
        df = self._deduplicate(pd.DataFrame(rows))

        if not existing.empty:
            combined = pd.concat([existing, df], ignore_index=True)
            df = self._deduplicate(combined)

        if df.empty:
            return False

        if existing_signature == self._canonical_signature(df):
            logger.info("[FinancialResults] No normalized changes; existing file retained")
            return True

        self._save(df)
        logger.info(
            f"[FinancialResults] Complete: {len(df)} records, {df['symbol'].nunique()} symbols"
        )
        return True

    # ------------------------------------------------------------------
    # Primary: NSE XBRL bulk fetch via nselib get_financial_results_master
    # ------------------------------------------------------------------

    def _fetch_bulk_nselib(self, skip_labels: set) -> list:
        if self.backfill:
            # Dynamic: all quarters from Q1FY18 to today, oldest first (incremental)
            windows = _generate_all_filing_windows()
        else:
            windows = _recent_filing_windows(self.max_windows or 2)
        if self.backfill and self.max_windows:
            windows = windows[: self.max_windows]

        all_rows: list = []

        for from_date, to_date, label in windows:
            logger.info(
                f"[FinancialResults] Fetching master list: {label} ({from_date} to {to_date})"
            )
            try:
                master_df, headers, _ns = self._fetch_master(from_date, to_date)
                time.sleep(cfg.API_DELAY)
            except Exception as e:
                logger.warning(f"[FinancialResults] Master list failed for {label}: {e}")
                continue

            if master_df is None or master_df.empty:
                logger.warning(f"[FinancialResults] Empty master list for {label}")
                continue

            # Skip entries with invalid XBRL (URL ends in /xbrl/-)
            valid = master_df[
                ~master_df["xbrl"].str.endswith("/xbrl/-", na=True)
            ].copy()
            logger.info(
                f"[FinancialResults] {label}: {len(master_df)} filings, "
                f"{len(valid)} with valid XBRL"
            )

            if valid.empty:
                continue

            rows = self._parse_xbrl_batch(valid, headers, label)
            all_rows.extend(rows)
            logger.info(f"[FinancialResults] {label}: parsed {len(rows)} P&L records")

        if self.recovery:
            self._save_recovery()

        return all_rows

    def _fetch_master(self, from_date: str, to_date: str):
        """Fetch the official NSE results master with bounded identity encoding."""
        if self._nse_session is None:
            self._nse_session = create_session(RESULTS_ORIGIN)
        url = (
            f"{RESULTS_API}?index=equities&from_date={from_date}"
            f"&to_date={to_date}&period=Quarterly"
        )
        headers = {
            "Accept": "application/json,text/plain,*/*",
            "Accept-Encoding": "identity",
            "Referer": "https://www.nseindia.com/",
        }
        last_error = None
        for attempt in range(cfg.MAX_RETRIES):
            try:
                response = self._nse_session.get(url, headers=headers, timeout=cfg.API_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                frame = pd.DataFrame(data)
                if not frame.empty:
                    frame.columns = [str(name).replace(" ", "") for name in frame.columns]
                xbrl_headers = {
                    "User-Agent": headers.get("User-Agent", "Mozilla/5.0"),
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                    "Referer": "https://www.nseindia.com/",
                }
                return frame, xbrl_headers, _NS
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                wait = cfg.RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    "[FinancialResults] Master fetch attempt %s failed for %s: %s. Retrying in %.1fs",
                    attempt + 1, from_date, exc, wait,
                )
                if attempt + 1 < cfg.MAX_RETRIES:
                    time.sleep(wait)
        raise RuntimeError(f"NSE financial-results master unavailable: {last_error}")

    def _parse_xbrl_batch(self, df, headers, window_label):
        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(df)))
        rows = []

        filing_dates = df["filingDate"].to_dict() if "filingDate" in df.columns else {}
        symbols_map  = df["symbol"].to_dict()     if "symbol"     in df.columns else {}

        def _fetch_one(idx, xbrl_url):
            try:
                resp = requests.get(xbrl_url, headers=headers, timeout=cfg.API_TIMEOUT)
                if resp.status_code != 200:
                    return None
                root = ET.fromstring(resp.content)

                extracted = {"window_label": window_label}
                for our_key, xbrl_tag in _XBRL_FIELDS.items():
                    elem = root.find(f".//in-bse-fin:{xbrl_tag}", _NS)
                    extracted[our_key] = elem.text if elem is not None else None

                extracted["filing_date"] = _parse_filing_date(filing_dates.get(idx, ""))

                if not extracted.get("symbol") and idx in symbols_map:
                    extracted["symbol"] = symbols_map[idx]

                return extracted
            except Exception as e:
                logger.debug(f"[FinancialResults] XBRL parse failed {xbrl_url[:60]}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            future_map = {
                ex.submit(_fetch_one, idx, row["xbrl"]): row.get("symbol", str(idx))
                for idx, row in df.iterrows()
            }
            for fut in progress(
                as_completed(future_map),
                total=len(future_map),
                desc=f"XBRL {window_label}",
            ):
                sym = future_map[fut]
                try:
                    raw = fut.result()
                    if raw is None:
                        self.recovery.append({"symbol": sym, "reason": "xbrl_fetch_failed"})
                        continue
                    row = self._normalize_xbrl_row(raw)
                    if row:
                        rows.append(row)
                    else:
                        self.recovery.append({"symbol": sym, "reason": "xbrl_parse_empty"})
                except Exception as e:
                    self.recovery.append({"symbol": sym, "reason": str(e)[:120]})

        return rows

    def _normalize_xbrl_row(self, raw):
        sym = str(raw.get("symbol") or "").strip().upper()
        if not sym:
            return None

        date_start = str(raw.get("date_start") or "")[:10]
        date_end   = str(raw.get("date_end")   or "")[:10]
        if not date_end:
            return None

        def _to_cr(val):
            if val is None:
                return None
            try:
                return round(float(str(val).replace(",", "")) * _DEFAULT_SCALE, 4)
            except (ValueError, TypeError):
                return None

        def _to_float(val):
            if val is None:
                return None
            try:
                return float(str(val).replace(",", ""))
            except (ValueError, TypeError):
                return None

        return {
            "symbol":                     sym,
            "date_start":                 date_start,
            "date_end":                   date_end,
            "quarter_label":              str(raw.get("quarter_label") or ""),
            "window_label":               str(raw.get("window_label") or ""),
            "filing_date":                _parse_filing_date(raw.get("filing_date")),
            "revenue_cr":                 _to_cr(raw.get("revenue_raw")),
            "net_profit_cr":              _to_cr(raw.get("profit_raw")),
            "eps":                        _to_float(raw.get("eps")),
            "rounding":                   str(raw.get("rounding") or ""),
            "standalone_or_consolidated": str(raw.get("nature") or ""),
            "source":                     "nselib_xbrl",
        }

    @staticmethod
    def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate exact filing versions while retaining restatement candidates."""
        if df.empty:
            return df
        for column in _RECORD_KEY:
            if column not in df.columns:
                df[column] = ""
        return (
            df.fillna("")
            .sort_values(_RECORD_KEY, kind="mergesort")
            .drop_duplicates(subset=_RECORD_KEY, keep="last")
            .sort_values(["symbol", "date_end", "filing_date", "standalone_or_consolidated"], kind="mergesort")
            .reset_index(drop=True)
        )

    # ------------------------------------------------------------------
    # Fallback: yfinance per-symbol
    # ------------------------------------------------------------------

    def _fetch_yfinance_all(self):
        symbols = self._load_symbols()
        if self.yfinance_cap and len(symbols) > self.yfinance_cap:
            logger.warning(
                f"[FinancialResults] yfinance cap: {self.yfinance_cap}/{len(symbols)} symbols."
            )
            symbols = symbols[: self.yfinance_cap]

        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(symbols)))
        all_rows = []

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(self._fetch_yfinance_symbol, sym): sym for sym in symbols
            }
            for fut in progress(
                as_completed(futures), total=len(futures), desc="yfinance fetch"
            ):
                sym = futures[fut]
                try:
                    rows = fut.result()
                    if rows:
                        all_rows.extend(rows)
                    else:
                        self.recovery.append({"symbol": sym, "reason": "no_yfinance_data"})
                except Exception as e:
                    self.recovery.append({"symbol": sym, "reason": str(e)})

        return all_rows

    def _fetch_yfinance_symbol(self, symbol):
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.NS")
            time.sleep(max(0.5, cfg.API_DELAY / cfg.MAX_CONCURRENCY))
            income = ticker.quarterly_income_stmt
            if income is None or income.empty:
                return []

            rows = []
            for col in income.columns:
                date_end = str(col)[:10]
                try:
                    revenue = (
                        income.loc["Total Revenue", col]
                        if "Total Revenue" in income.index else None
                    )
                    profit = (
                        income.loc["Net Income", col]
                        if "Net Income" in income.index else None
                    )
                    revenue_cr = float(revenue) / 1e7 if revenue is not None else None
                    profit_cr  = float(profit) / 1e7 if profit is not None else None
                except Exception:
                    continue

                rows.append({
                    "symbol":                     symbol,
                    "date_start":                 "",
                    "date_end":                   date_end,
                    "quarter_label":              "Q",
                    "window_label":               "yfinance",
                    "filing_date":                "",
                    "revenue_cr":                 round(revenue_cr, 4) if revenue_cr else None,
                    "net_profit_cr":              round(profit_cr, 4) if profit_cr else None,
                    "eps":                        None,
                    "rounding":                   "",
                    "standalone_or_consolidated": "",
                    "source":                     "yfinance",
                })
            return rows
        except Exception as e:
            logger.debug(f"[FinancialResults] yfinance failed for {symbol}: {e}")
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_symbols(self):
        if not EQUITY_MASTER.exists():
            return []
        em = pd.read_csv(EQUITY_MASTER)
        series_col = next((c for c in ["series", "SERIES"] if c in em.columns), None)
        if series_col:
            em = em[em[series_col] == "EQ"]
        sym_col = next((c for c in ["symbol", "SYMBOL"] if c in em.columns), None)
        return em[sym_col].dropna().unique().tolist() if sym_col else []

    def _load_existing(self):
        if OUTPUT_PATH.exists():
            try:
                df = pd.read_csv(OUTPUT_PATH)
                return df if not df.empty else pd.DataFrame()
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    @staticmethod
    def _canonical_signature(df: pd.DataFrame) -> str:
        """Return a stable signature for logical normalized rows."""
        if df.empty:
            return ""
        normalized = df.copy().fillna("")
        columns = sorted(normalized.columns)
        normalized = normalized.loc[:, columns].astype(str)
        normalized = normalized.sort_values(columns, kind="mergesort").reset_index(drop=True)
        payload = normalized.to_csv(index=False, lineterminator="\n").encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _save(self, df):
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[FinancialResults] Saved {len(df)} records -> {OUTPUT_PATH}")

    def _save_recovery(self):
        if not self.recovery:
            return
        recovery_df = pd.DataFrame(self.recovery)
        existing_rq = (
            pd.read_csv(RECOVERY_QUEUE) if RECOVERY_QUEUE.exists() else pd.DataFrame()
        )
        combined = (
            pd.concat([existing_rq, recovery_df], ignore_index=True).drop_duplicates()
        )
        tmp = RECOVERY_QUEUE.with_suffix(".tmp.csv")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))
        logger.warning(
            f"[FinancialResults] {len(self.recovery)} failed entries -> {RECOVERY_QUEUE}"
        )


if __name__ == "__main__":
    import argparse as _ap
    _parser = _ap.ArgumentParser(description="Financial Results Engine -- Phase 15A")
    _parser.add_argument("--windows", type=int, default=None,
                         help="Fetch N most recent filing windows (default: 2)")
    _parser.add_argument("--backfill", action="store_true",
                         help="Fetch ALL quarters from Q1FY18 to present (incremental)")
    _parser.add_argument("--full", action="store_true",
                         help="Alias for --backfill (backwards compat)")
    _args = _parser.parse_args()

    backfill  = _args.backfill or _args.full
    n_windows = _args.windows
    if not backfill and n_windows is None:
        n_windows = 2   # default: 2 most recent quarters

    engine = FinancialResultsEngine(
        max_windows=n_windows,
        backfill=backfill,
        use_yfinance=False,
        yfinance_cap=YFINANCE_BATCH_CAP,
    )
    success = engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        n_sym = df["symbol"].nunique()
        print(f"Results: {len(df)} records, {n_sym} symbols")
        if not df.empty:
            print(
                df[["symbol", "date_end", "revenue_cr", "net_profit_cr", "eps", "source"]]
                .head(10)
                .to_string()
            )
    else:
        print("No results fetched. NSE XBRL endpoint may be temporarily unavailable.")
        print("Retry: py -3.11 engines/fundamentals/financial_results_engine.py --full")
