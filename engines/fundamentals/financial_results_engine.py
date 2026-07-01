"""
Financial Results Engine -- Phase 15A
Fetches quarterly financial results from NSE XBRL filings for all EQ-series companies.

Strategy:
  nselib.capital_market.get_func.get_financial_results_master(from_date, to_date)
  returns the list of all quarterly result filings submitted to NSE in that window.
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
  1. NSE XBRL (via nselib get_financial_results_master) -- primary
  2. yfinance per-symbol quarterly_income_stmt -- last resort (capped)

Output: data/NSE/results/quarterly_results.csv
  Columns: symbol, date_start, date_end, quarter_label, window_label, filing_date,
           revenue_cr, net_profit_cr, eps, rounding, standalone_or_consolidated, source

Guardrails:
  - Atomic writes (G-D-02)
  - No empty DataFrame writes (G-D-03)
  - Rate limiting between NSE calls (G-A-01)
  - Failed entries -> recovery_queue.csv (G-A-03)
  - Incremental: skips already-fetched window labels
"""

import sys
import time
import shutil
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger(__name__)

RESULTS_DIR = cfg.NSE_DIR / "results"
OUTPUT_PATH = RESULTS_DIR / "quarterly_results.csv"
EQUITY_MASTER = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# Filing season windows: (from_date, to_date, label)
# These are FILING dates (when results appear on NSE), NOT the financial period dates.
# Each window captures ~3,500-3,900 quarterly filings from nearly the full EQ universe.
FILING_WINDOWS = [
    ("01-01-2025", "31-03-2025", "Q3FY25"),   # Oct-Dec 2024 quarter results
    ("01-10-2024", "31-12-2024", "Q2FY25"),   # Jul-Sep 2024 quarter results
    ("01-07-2024", "30-09-2024", "Q1FY25"),   # Apr-Jun 2024 quarter results
    ("01-04-2024", "31-07-2024", "Q4FY24"),   # Jan-Mar 2024 quarter (extended window)
    ("01-01-2024", "31-03-2024", "Q3FY24"),   # Oct-Dec 2023 quarter results
    ("01-10-2023", "31-12-2023", "Q2FY24"),   # Jul-Sep 2023 quarter results
]

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
        max_windows: Optional[int] = None,
        use_yfinance: bool = True,
        yfinance_cap: int = YFINANCE_BATCH_CAP,
    ):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.max_windows = max_windows
        self.use_yfinance = use_yfinance
        self.yfinance_cap = yfinance_cap
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[FinancialResults] Starting quarterly results fetch")

        existing = self._load_existing()
        done_labels: set = set()
        if not existing.empty and "window_label" in existing.columns:
            done_labels = set(existing["window_label"].dropna().unique())
        if done_labels:
            logger.info(f"[FinancialResults] Already stored: {done_labels}")

        rows = self._fetch_bulk_nselib(skip_labels=done_labels)

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

        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["symbol", "date_start", "date_end", "source"])
        df = df.sort_values(["symbol", "date_end"])

        if not existing.empty:
            combined = pd.concat([existing, df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["symbol", "date_start", "date_end", "source"]
            )
            df = combined.sort_values(["symbol", "date_end"])

        if df.empty:
            return False

        self._save(df)
        logger.info(
            f"[FinancialResults] Complete: {len(df)} records, {df['symbol'].nunique()} symbols"
        )
        return True

    # ------------------------------------------------------------------
    # Primary: NSE XBRL bulk fetch via nselib get_financial_results_master
    # ------------------------------------------------------------------

    def _fetch_bulk_nselib(self, skip_labels: set) -> list:
        try:
            from nselib.capital_market.get_func import get_financial_results_master
        except ImportError:
            logger.warning("[FinancialResults] nselib not installed")
            return []

        windows = FILING_WINDOWS
        if self.max_windows:
            windows = windows[: self.max_windows]

        all_rows: list = []

        for from_date, to_date, label in windows:
            if label in skip_labels:
                logger.info(f"[FinancialResults] Skipping {label} (already stored)")
                continue

            logger.info(
                f"[FinancialResults] Fetching master list: {label} ({from_date} to {to_date})"
            )
            try:
                master_df, headers, ns, _ = get_financial_results_master(
                    from_date=from_date,
                    to_date=to_date,
                    fin_period="Quarterly",
                )
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

                extracted["filing_date"] = str(filing_dates.get(idx, ""))[:10]

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
            "filing_date":                str(raw.get("filing_date") or "")[:10],
            "revenue_cr":                 _to_cr(raw.get("revenue_raw")),
            "net_profit_cr":              _to_cr(raw.get("profit_raw")),
            "eps":                        _to_float(raw.get("eps")),
            "rounding":                   str(raw.get("rounding") or ""),
            "standalone_or_consolidated": str(raw.get("nature") or ""),
            "source":                     "nselib_xbrl",
        }

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
    import sys as _sys

    # Flags:
    #   --full       : fetch all 6 historical windows (~18 months, up to 2 hours)
    #   --windows N  : fetch N most recent windows only
    full_run  = "--full" in _sys.argv
    n_windows = None
    if "--windows" in _sys.argv:
        idx = _sys.argv.index("--windows")
        if idx + 1 < len(_sys.argv):
            n_windows = int(_sys.argv[idx + 1])
    if not full_run and n_windows is None:
        n_windows = 2   # default: 2 most recent quarters (~30-45 min)

    engine = FinancialResultsEngine(
        max_windows=n_windows,
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