"""
Extended Financials Engine -- Phase 15B
Fetches additional P&L + Balance Sheet data from NSE XBRL filings.

Computes (one row per symbol, aggregated from available quarters):
  OPM%              Operating Profit Margin (EBITDA / Revenue)
  ROCE%             Return on Capital Employed (EBIT / Capital Employed)
  Book Value/share  Shareholders Equity per share (Total Equity / Shares)
  Sales Growth      Best-available revenue CAGR over available history

Strategy:
  Re-uses nselib.capital_market.get_func.get_financial_results_master() to get XBRL
  URLs for the same filing windows as Phase 15A, then extracts additional tags from
  each XML (PBT, FinanceCosts, Depreciation, TotalAssets, CurrentLiabilities, TotalEquity).

  Joins with existing quarterly_results.csv for revenue/eps data to avoid refetching P&L.

  Default: fetches balance sheet for 6 current windows (Q2FY24-Q3FY25).
  --backfill: adds 5 historical windows (Q4FY21-Q4FY22) for 3Y revenue CAGR.

Output: data/NSE/results/extended_financials.csv
  One row per symbol with: opm_pct, roce_pct, book_value_per_share, total_equity_cr,
  capital_employed_cr, sales_growth_cagr_pct, sales_growth_years, as_of_date

Guardrails:
  G-D-02: Atomic writes (tmp then rename)
  G-D-03: No empty DataFrame writes
  G-A-01: Rate limiting (cfg.API_DELAY between calls)
  G-A-02: Retry with exponential backoff
  G-A-03: Failed items -> recovery_queue.csv
"""

import sys
import time
import shutil
import math
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

RESULTS_DIR     = cfg.NSE_DIR / "results"
OUTPUT_PATH     = RESULTS_DIR / "extended_financials.csv"
RAW_CACHE_PATH  = RESULTS_DIR / "extended_quarterly_raw.csv"
QR_PATH         = RESULTS_DIR / "quarterly_results.csv"
RECOVERY_QUEUE  = cfg.NSE_DIR / "recovery_queue.csv"

# XBRL namespace (same as Phase 15A)
_NS = {
    "xbrli":      "http://www.xbrl.org/2003/instance",
    "in-bse-fin": "http://www.bseindia.com/xbrl/fin/2020-03-31/in-bse-fin",
}

_DEFAULT_SCALE = 1 / 1e7   # rupees -> crores

# Current filing windows (same set as Phase 15A, balance sheet focus)
FILING_WINDOWS_BS = [
    ("01-01-2025", "31-03-2025", "Q3FY25"),
    ("01-10-2024", "31-12-2024", "Q2FY25"),
    ("01-07-2024", "30-09-2024", "Q1FY25"),
    ("01-04-2024", "31-07-2024", "Q4FY24"),
    ("01-01-2024", "31-03-2024", "Q3FY24"),
    ("01-10-2023", "31-12-2023", "Q2FY24"),
]

# Historical windows added in --backfill mode (extended to 10Y: FY17-FY25)
FILING_WINDOWS_HIST = [
    # FY22 (already fetched in 3Y backfill — engine skips via done_labels cache)
    ("01-01-2022", "31-03-2022", "Q3FY22"),
    ("01-10-2021", "31-12-2021", "Q2FY22"),
    ("01-07-2021", "30-09-2021", "Q1FY22"),
    ("01-04-2021", "31-07-2021", "Q4FY21"),
    ("01-01-2021", "31-03-2021", "Q3FY21"),
    # FY21 early quarters (bridge gap)
    ("01-10-2020", "31-12-2020", "Q2FY21"),
    ("01-07-2020", "30-09-2020", "Q1FY21"),
    # FY22-FY23 gap (between HIST top and FILING_WINDOWS_BS bottom)
    ("01-04-2022", "30-06-2022", "Q4FY22"),
    ("01-07-2022", "30-09-2022", "Q1FY23"),
    ("01-10-2022", "31-12-2022", "Q2FY23"),
    ("01-01-2023", "31-03-2023", "Q3FY23"),
    ("01-04-2023", "30-06-2023", "Q4FY23"),
    ("01-07-2023", "30-09-2023", "Q1FY24"),
    # FY20
    ("01-04-2020", "30-06-2020", "Q4FY20"),
    ("01-01-2020", "31-03-2020", "Q3FY20"),
    ("01-10-2019", "31-12-2019", "Q2FY20"),
    ("01-07-2019", "30-09-2019", "Q1FY20"),
    # FY19
    ("01-04-2019", "30-06-2019", "Q4FY19"),
    ("01-01-2019", "31-03-2019", "Q3FY19"),
    ("01-10-2018", "31-12-2018", "Q2FY19"),
    ("01-07-2018", "30-09-2018", "Q1FY19"),
    # FY18
    ("01-04-2018", "30-06-2018", "Q4FY18"),
    ("01-01-2018", "31-03-2018", "Q3FY18"),
    ("01-10-2017", "31-12-2017", "Q2FY18"),
    ("01-07-2017", "30-09-2017", "Q1FY18"),
    # FY17 (XBRL mandated for top-500 from Apr 2016; coverage thins for smaller caps)
    ("01-04-2017", "30-06-2017", "Q4FY17"),
    ("01-01-2017", "31-03-2017", "Q3FY17"),
    ("01-10-2016", "31-12-2016", "Q2FY17"),
    ("01-07-2016", "30-09-2016", "Q1FY17"),
]

# Extended XBRL fields beyond Phase 15A.
# Each entry maps our column name to a list of tag candidates (first match wins).
_XBRL_BALANCE_SHEET = {
    # Additional P&L fields
    "pbt_raw":          ["ProfitBeforeTax",
                         "ProfitBeforeExceptionalExtraordinaryItemsAndTax"],
    "finance_costs_raw": ["FinanceCosts",
                          "FinanceCharges",
                          "InterestAndFinanceCharges"],
    "depreciation_raw": ["DepreciationDepletionAndAmortisationExpense",
                         "DepreciationAndAmortisation",
                         "Depreciation"],
    # Balance sheet
    "total_assets_raw":   ["TotalAssets"],
    "current_liab_raw":   ["TotalCurrentLiabilities",
                           "CurrentLiabilities"],
    "equity_capital_raw": ["EquityShareCapital",
                           "ShareCapital",
                           "PaidUpShareCapital"],
    "other_equity_raw":   ["OtherEquity",
                           "ReservesAndSurplus",
                           "Reserves"],
}

# Also fetch core P&L tags from same XML (to avoid relying on outer join for symbol lookup)
_XBRL_CORE = {
    "symbol":       "Symbol",
    "date_end":     "DateOfEndOfReportingPeriod",
    "date_start":   "DateOfStartOfReportingPeriod",
    "revenue_raw":  "RevenueFromOperations",
    "profit_raw":   "ProfitLossForPeriod",
    "eps":          "BasicEarningsLossPerShareFromContinuingOperations",
}


def _find_tag(root, candidates: list) -> Optional[str]:
    """Return the text of the first matching XBRL tag candidate."""
    for tag in candidates:
        elem = root.find(f".//in-bse-fin:{tag}", _NS)
        if elem is not None and elem.text:
            return elem.text.strip()
    return None


def _to_cr(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return round(float(str(val).replace(",", "")) * _DEFAULT_SCALE, 4)
    except (ValueError, TypeError):
        return None


def _to_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        v = float(str(val).replace(",", ""))
        return None if math.isnan(v) else v
    except (ValueError, TypeError):
        return None


class ExtendedFinancialsEngine:
    """
    Phase 15B: fetch balance sheet XBRL fields and compute OPM, ROCE, Book Value, Sales Growth.
    """

    def __init__(
        self,
        backfill: bool = False,
        max_windows: Optional[int] = None,
        use_cached_raw: bool = True,
        use_yfinance_bs: bool = True,
    ):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.backfill        = backfill
        self.max_windows     = max_windows
        self.use_cached_raw  = use_cached_raw
        self.use_yfinance_bs = use_yfinance_bs
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[ExtendedFinancials] Phase 15B start")

        # Determine which windows to fetch (skip already-cached if use_cached_raw)
        raw_df = self._load_raw_cache() if (self.use_cached_raw and RAW_CACHE_PATH.exists()) else pd.DataFrame()
        done_labels: set = set(raw_df["window_label"].dropna().unique()) if not raw_df.empty else set()

        windows = FILING_WINDOWS_BS + (FILING_WINDOWS_HIST if self.backfill else [])
        if self.max_windows:
            windows = windows[: self.max_windows]

        # Fetch per-window and save incrementally (safe against mid-run interruption)
        any_new = False
        for window in windows:
            label = window[2]
            if label in done_labels:
                logger.info(f"[ExtendedFinancials] Skipping {label} (cached)")
                continue
            rows = self._fetch_xbrl_windows([window], skip_labels=set())
            if not rows:
                continue
            any_new = True
            new_df = pd.DataFrame(rows)
            raw_df = pd.concat([raw_df, new_df], ignore_index=True) if not raw_df.empty else new_df
            raw_df = raw_df.drop_duplicates(subset=["symbol", "date_end", "window_label"])
            # Save after each window (incremental)
            tmp = RAW_CACHE_PATH.with_suffix(".tmp")
            raw_df.to_csv(tmp, index=False)
            shutil.move(str(tmp), str(RAW_CACHE_PATH))
            done_labels.add(label)
            logger.info(f"[ExtendedFinancials] {label} saved. Cache: {len(raw_df)} rows, {raw_df['symbol'].nunique()} symbols")

        if not any_new:
            logger.info("[ExtendedFinancials] No new balance sheet data fetched; using cached raw")

        if raw_df.empty:
            logger.warning("[ExtendedFinancials] No raw data available — aborting")
            return False

        # Load existing quarterly_results.csv (for eps + revenue history)
        qr_df = self._load_qr()

        # Aggregate per symbol
        out_rows = self._aggregate(raw_df, qr_df)
        if not out_rows:
            logger.warning("[ExtendedFinancials] Aggregation produced no rows")
            return False

        out_df = pd.DataFrame(out_rows).sort_values("symbol")
        if out_df.empty:
            return False

        # Phase 15B-YF: augment with yfinance balance sheet for ROCE + Book Value
        if self.use_yfinance_bs:
            out_df = self._augment_yfinance_bs(out_df)

        # Atomic save
        tmp = OUTPUT_PATH.with_suffix(".tmp")
        out_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))

        if self.recovery:
            self._save_recovery()

        logger.info(
            f"[ExtendedFinancials] Complete: {len(out_df)} symbols -> {OUTPUT_PATH}"
        )
        return True

    # -------------------------------------------------------------------------
    # XBRL fetch
    # -------------------------------------------------------------------------

    def _fetch_xbrl_windows(self, windows: list, skip_labels: set) -> list:
        try:
            from nselib.capital_market.get_func import get_financial_results_master
        except ImportError:
            logger.error("[ExtendedFinancials] nselib not installed")
            return []

        all_rows: list = []

        for from_date, to_date, label in windows:
            if label in skip_labels:
                logger.info(f"[ExtendedFinancials] Skipping {label} (cached)")
                continue

            logger.info(f"[ExtendedFinancials] Fetching {label} ({from_date} to {to_date})")
            for attempt in range(3):
                try:
                    master_df, headers, ns, _ = get_financial_results_master(
                        from_date=from_date,
                        to_date=to_date,
                        fin_period="Quarterly",
                    )
                    time.sleep(cfg.API_DELAY)
                    break
                except Exception as e:
                    wait = cfg.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"[ExtendedFinancials] Master fetch {label} attempt {attempt+1}: {e}")
                    if attempt < 2:
                        time.sleep(wait)
                    else:
                        master_df = None

            if master_df is None or master_df.empty:
                logger.warning(f"[ExtendedFinancials] No master list for {label}")
                continue

            # Skip invalid XBRL
            valid = master_df[~master_df["xbrl"].str.endswith("/xbrl/-", na=True)].copy()
            logger.info(f"[ExtendedFinancials] {label}: {len(valid)} valid XBRL filings")

            if valid.empty:
                continue

            rows = self._parse_xbrl_batch(valid, headers, label)
            all_rows.extend(rows)
            logger.info(f"[ExtendedFinancials] {label}: {len(rows)} extended rows parsed")

        return all_rows

    def _parse_xbrl_batch(self, df, headers, window_label: str) -> list:
        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(df)))
        rows: list = []

        filing_dates = df["filingDate"].to_dict() if "filingDate" in df.columns else {}
        symbols_map  = df["symbol"].to_dict()     if "symbol"     in df.columns else {}

        def _fetch_one(idx, xbrl_url):
            for attempt in range(3):
                try:
                    resp = requests.get(xbrl_url, headers=headers, timeout=cfg.API_TIMEOUT)
                    if resp.status_code != 200:
                        return None
                    root = ET.fromstring(resp.content)

                    extracted: dict = {"window_label": window_label}

                    # Core fields (symbol, dates, basic P&L)
                    for col, tag in _XBRL_CORE.items():
                        elem = root.find(f".//in-bse-fin:{tag}", _NS)
                        extracted[col] = elem.text.strip() if elem is not None and elem.text else None

                    # Extended fields (balance sheet + additional P&L)
                    for col, candidates in _XBRL_BALANCE_SHEET.items():
                        extracted[col] = _find_tag(root, candidates)

                    if not extracted.get("symbol") and idx in symbols_map:
                        extracted["symbol"] = symbols_map[idx]
                    extracted["filing_date"] = str(filing_dates.get(idx, ""))[:10]

                    return extracted
                except ET.ParseError:
                    return None
                except Exception as e:
                    wait = 2 ** attempt
                    if attempt < 2:
                        time.sleep(wait)
                    else:
                        logger.debug(f"[ExtendedFinancials] XBRL fail {xbrl_url[:60]}: {e}")
                        return None
            return None

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            future_map = {
                ex.submit(_fetch_one, idx, row["xbrl"]): row.get("symbol", str(idx))
                for idx, row in df.iterrows()
            }
            for fut in progress(as_completed(future_map), total=len(future_map), desc=f"BS {window_label}"):
                sym = future_map[fut]
                try:
                    raw = fut.result()
                    if raw is None:
                        self.recovery.append({"symbol": sym, "reason": "xbrl_fetch_failed", "window": window_label})
                        continue
                    row = self._normalize_row(raw, window_label)
                    if row:
                        rows.append(row)
                    else:
                        self.recovery.append({"symbol": sym, "reason": "normalize_empty", "window": window_label})
                except Exception as e:
                    self.recovery.append({"symbol": sym, "reason": str(e)[:120], "window": window_label})

        return rows

    def _normalize_row(self, raw: dict, window_label: str) -> Optional[dict]:
        sym = str(raw.get("symbol") or "").strip().upper()
        if not sym:
            return None
        date_end = str(raw.get("date_end") or "")[:10]
        if not date_end:
            return None

        return {
            "symbol":           sym,
            "date_end":         date_end,
            "date_start":       str(raw.get("date_start") or "")[:10],
            "window_label":     window_label,
            "filing_date":      str(raw.get("filing_date") or "")[:10],
            # Basic P&L (redundant with quarterly_results.csv but useful for joining)
            "revenue_cr":       _to_cr(raw.get("revenue_raw")),
            "net_profit_cr":    _to_cr(raw.get("profit_raw")),
            "eps":              _to_float(raw.get("eps")),
            # Extended P&L
            "pbt_cr":           _to_cr(raw.get("pbt_raw")),
            "finance_costs_cr": _to_cr(raw.get("finance_costs_raw")),
            "depreciation_cr":  _to_cr(raw.get("depreciation_raw")),
            # Balance sheet
            "total_assets_cr":      _to_cr(raw.get("total_assets_raw")),
            "current_liab_cr":      _to_cr(raw.get("current_liab_raw")),
            "equity_capital_cr":    _to_cr(raw.get("equity_capital_raw")),
            "other_equity_cr":      _to_cr(raw.get("other_equity_raw")),
        }

    # -------------------------------------------------------------------------
    # Aggregation
    # -------------------------------------------------------------------------

    def _aggregate(self, raw_df: pd.DataFrame, qr_df: Optional[pd.DataFrame]) -> list:
        raw_df["_date"] = pd.to_datetime(raw_df["date_end"], errors="coerce")
        symbols = sorted(raw_df["symbol"].dropna().unique())
        logger.info(f"[ExtendedFinancials] Aggregating {len(symbols)} symbols")

        rows = []
        for sym in symbols:
            sym_raw = raw_df[raw_df["symbol"] == sym].sort_values("_date")
            sym_qr  = (qr_df[qr_df["symbol"].str.upper() == sym].copy()
                       if qr_df is not None and "symbol" in qr_df.columns
                       else pd.DataFrame())

            row = self._compute_symbol(sym, sym_raw, sym_qr)
            if row:
                rows.append(row)

        return rows

    def _compute_symbol(self, sym: str, sym_raw: pd.DataFrame, sym_qr: pd.DataFrame) -> Optional[dict]:
        if sym_raw.empty:
            return None

        out: dict = {
            "symbol":                sym,
            "opm_pct":               None,
            "roce_pct":              None,
            "book_value_per_share":  None,
            "total_equity_cr":       None,
            "equity_share_capital_cr": None,
            "capital_employed_cr":   None,
            "ebitda_cr_latest":      None,
            "ebit_cr_latest":        None,
            "sales_growth_cagr_pct": None,
            "sales_growth_years":    None,
            "as_of_date":            str(sym_raw["_date"].max())[:10],
            "data_quarters":         len(sym_raw),
        }

        latest = sym_raw.iloc[-1]

        # ── Balance Sheet (latest available) ──────────────────────────────────
        # Use the most recent row that has balance sheet data
        bs_rows = sym_raw.dropna(subset=["total_assets_cr"])
        if not bs_rows.empty:
            bs = bs_rows.iloc[-1]
            total_assets = _to_float(bs.get("total_assets_cr"))
            current_liab  = _to_float(bs.get("current_liab_cr"))
            equity_cap    = _to_float(bs.get("equity_capital_cr"))
            other_equity  = _to_float(bs.get("other_equity_cr"))

            if total_assets and current_liab is not None:
                cap_employed = total_assets - current_liab
                out["capital_employed_cr"] = round(cap_employed, 2) if cap_employed > 0 else None

            total_equity = None
            if equity_cap is not None and other_equity is not None:
                total_equity = equity_cap + other_equity
            elif other_equity is not None:
                total_equity = other_equity

            if total_equity is not None:
                out["total_equity_cr"]       = round(total_equity, 2)
                out["equity_share_capital_cr"] = round(equity_cap, 2) if equity_cap else None

        # ── OPM (Operating Profit Margin) ─────────────────────────────────────
        # Use latest quarter with PBT + FinanceCosts + Depreciation all available
        pl_rows = sym_raw.dropna(subset=["pbt_cr", "revenue_cr"])
        if not pl_rows.empty:
            for _, r in pl_rows.sort_values("_date", ascending=False).iterrows():
                pbt     = _to_float(r.get("pbt_cr"))
                fc      = _to_float(r.get("finance_costs_cr"))
                dep     = _to_float(r.get("depreciation_cr"))
                rev     = _to_float(r.get("revenue_cr"))
                if pbt is None or rev is None or rev <= 0:
                    continue
                # EBITDA = PBT + FinanceCosts + Depreciation
                ebitda = pbt + (fc or 0.0) + (dep or 0.0)
                out["ebitda_cr_latest"] = round(ebitda, 4)
                out["opm_pct"] = round(ebitda / rev * 100, 2)
                # EBIT = PBT + FinanceCosts (annualized by multiplying quarterly figure by 4)
                ebit = pbt + (fc or 0.0)
                out["ebit_cr_latest"] = round(ebit, 4)
                break

        # ── ROCE ─────────────────────────────────────────────────────────────
        if out["ebit_cr_latest"] is not None and out["capital_employed_cr"]:
            cap_emp = out["capital_employed_cr"]
            if cap_emp > 0:
                # Annualise quarterly EBIT (×4) / Capital Employed
                roce = out["ebit_cr_latest"] * 4 / cap_emp * 100
                out["roce_pct"] = round(roce, 2)

        # ── Book Value per Share ───────────────────────────────────────────────
        total_equity_cr = out.get("total_equity_cr")
        if total_equity_cr is not None and total_equity_cr > 0:
            # Get shares outstanding from eps in raw data (latest with eps + net_profit_cr)
            shares_cr = self._estimate_shares_cr(sym_raw, sym_qr)
            if shares_cr and shares_cr > 0:
                bvps = total_equity_cr * 1e7 / (shares_cr * 1e7)  # = total_equity_cr / shares_cr
                out["book_value_per_share"] = round(bvps, 2)

        # ── Sales Growth CAGR ─────────────────────────────────────────────────
        growth_result = self._compute_sales_growth(sym_raw, sym_qr)
        if growth_result:
            out["sales_growth_cagr_pct"] = growth_result["cagr_pct"]
            out["sales_growth_years"]    = growth_result["years"]

        return out

    def _augment_yfinance_bs(self, out_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fetch quarterly balance sheet from yfinance for each symbol and compute:
        - total_equity_cr        (Common Stock Equity)
        - capital_employed_cr    (Total Assets - Current Liabilities)
        - shares_outstanding_cr  (Ordinary Shares Number in crores)
        - book_value_per_share   (total_equity_cr / shares_outstanding_cr)
        - roce_pct               (ebit_cr_latest * 4 / capital_employed_cr * 100)
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("[ExtendedFinancials] yfinance not installed; skipping BS augment")
            return out_df

        symbols = out_df["symbol"].tolist()
        n_workers = min(cfg.MAX_CONCURRENCY, 6)
        logger.info(f"[ExtendedFinancials] yfinance BS augment: {len(symbols)} symbols, {n_workers} workers")

        bs_cache: dict = {}

        def _fetch_bs(sym: str) -> Optional[dict]:
            try:
                time.sleep(max(0.3, cfg.API_DELAY / n_workers))
                t = yf.Ticker(f"{sym}.NS")
                bs = t.quarterly_balance_sheet
                if bs is None or bs.empty:
                    return None
                # Use most recent column with data
                for col in bs.columns:
                    equity = None
                    try:
                        equity = float(bs.loc["Common Stock Equity", col])
                        if equity != equity:  # NaN
                            equity = None
                    except Exception:
                        pass

                    assets, cur_liab, shares = None, None, None
                    try:
                        assets = float(bs.loc["Total Assets", col])
                        if assets != assets:
                            assets = None
                    except Exception:
                        pass
                    try:
                        cur_liab = float(bs.loc["Current Liabilities", col])
                        if cur_liab != cur_liab:
                            cur_liab = None
                    except Exception:
                        pass
                    try:
                        shares = float(bs.loc["Ordinary Shares Number", col])
                        if shares != shares:
                            shares = None
                    except Exception:
                        pass

                    if equity is not None:
                        result = {
                            "equity_cr": round(equity / 1e7, 2),
                            "assets_cr": round(assets / 1e7, 2) if assets else None,
                            "cur_liab_cr": round(cur_liab / 1e7, 2) if cur_liab else None,
                            "shares_cr": round(shares / 1e7, 4) if shares else None,
                        }
                        if assets and cur_liab:
                            result["cap_employed_cr"] = round((assets - cur_liab) / 1e7, 2)
                        return result
                return None
            except Exception as e:
                logger.debug(f"[ExtendedFinancials] yf BS fail {sym}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(_fetch_bs, sym): sym for sym in symbols}
            for fut in progress(as_completed(futures), total=len(futures), desc="YF BS"):
                sym = futures[fut]
                try:
                    result = fut.result()
                    if result:
                        bs_cache[sym] = result
                except Exception:
                    pass

        logger.info(f"[ExtendedFinancials] yfinance BS: {len(bs_cache)}/{len(symbols)} symbols with balance sheet")

        # Merge into out_df
        def _enrich(row):
            sym = row["symbol"]
            bs = bs_cache.get(sym)
            if not bs:
                return row
            eq = bs.get("equity_cr")
            sh = bs.get("shares_cr")
            cap_emp = bs.get("cap_employed_cr")
            if eq is not None and eq > 0:
                row["total_equity_cr"] = eq
                if sh and sh > 0:
                    row["book_value_per_share"] = round(eq / sh, 2)
                elif row.get("shares_outstanding_cr") and float(row["shares_outstanding_cr"] or 0) > 0:
                    row["book_value_per_share"] = round(eq / float(row["shares_outstanding_cr"]), 2)
            if cap_emp and cap_emp > 0:
                row["capital_employed_cr"] = cap_emp
                ebit = row.get("ebit_cr_latest")
                if ebit and float(ebit or 0) != 0:
                    row["roce_pct"] = round(float(ebit) * 4 / cap_emp * 100, 2)
            return row

        out_df = out_df.apply(_enrich, axis=1)
        return out_df

    def _estimate_shares_cr(self, sym_raw: pd.DataFrame, sym_qr: pd.DataFrame) -> Optional[float]:
        """Estimate shares outstanding (in crores) from eps + net_profit_cr."""
        for df in [sym_raw, sym_qr]:
            if df.empty:
                continue
            sort_col = "_date" if "_date" in df.columns else df.columns[0]
            df_sorted = df.sort_values(sort_col, ascending=False)
            for _, r in df_sorted.iterrows():
                eps = _to_float(r.get("eps"))
                pat = _to_float(r.get("net_profit_cr"))
                if eps and pat and eps != 0 and pat != 0:
                    shares_cr = abs(pat * 1e7 / eps) / 1e7
                    if 0.001 < shares_cr < 10000:  # sanity range (0.001Cr to 10000Cr shares)
                        return shares_cr
        return None

    def _compute_sales_growth(self, sym_raw: pd.DataFrame, sym_qr: pd.DataFrame) -> Optional[dict]:
        """Compute best-available revenue CAGR across all available quarterly data."""
        # Build combined revenue series (prefer sym_qr which has more history)
        rev_data: list[tuple] = []  # (date, revenue_cr)

        for df in [sym_qr, sym_raw]:
            if df.empty:
                continue
            date_col = "_date" if "_date" in df.columns else None
            if date_col is None:
                for _, r in df.iterrows():
                    dt = pd.to_datetime(r.get("date_end"), errors="coerce")
                    rev = _to_float(r.get("revenue_cr"))
                    if pd.notna(dt) and rev and rev > 0:
                        rev_data.append((dt, rev))
            else:
                for _, r in df.iterrows():
                    dt = r.get("_date")
                    rev = _to_float(r.get("revenue_cr"))
                    if pd.notna(dt) and rev and rev > 0:
                        rev_data.append((dt, rev))

        if not rev_data:
            return None

        # Deduplicate by date (take max revenue if duplicates)
        rev_map: dict = {}
        for dt, rev in rev_data:
            key = str(dt)[:10]
            if key not in rev_map or rev > rev_map[key][1]:
                rev_map[key] = (dt, rev)

        sorted_rev = sorted(rev_map.values(), key=lambda x: x[0])
        if len(sorted_rev) < 2:
            return None

        oldest_dt, oldest_rev = sorted_rev[0]
        latest_dt, latest_rev = sorted_rev[-1]

        years = (latest_dt - oldest_dt).days / 365.25
        if years < 0.5 or oldest_rev <= 0 or latest_rev <= 0:
            return None

        # CAGR: (latest / oldest) ^ (1/years) - 1
        cagr = ((latest_rev / oldest_rev) ** (1.0 / years) - 1.0) * 100
        # Cap at reasonable range to avoid extreme CAGR from very small base
        cagr = max(-99.0, min(999.0, cagr))

        return {"cagr_pct": round(cagr, 2), "years": round(years, 1)}

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _load_raw_cache(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(RAW_CACHE_PATH, low_memory=False)
            df["_date"] = pd.to_datetime(df["date_end"], errors="coerce")
            logger.info(f"[ExtendedFinancials] Loaded raw cache: {len(df)} rows")
            return df
        except Exception as e:
            logger.warning(f"[ExtendedFinancials] Could not load raw cache: {e}")
            return pd.DataFrame()

    def _load_qr(self) -> Optional[pd.DataFrame]:
        if not QR_PATH.exists():
            logger.warning(f"[ExtendedFinancials] quarterly_results.csv not found at {QR_PATH}")
            return None
        try:
            df = pd.read_csv(QR_PATH, low_memory=False)
            df["symbol"] = df["symbol"].str.upper().str.strip()
            df["_date"]  = pd.to_datetime(df.get("date_end", df.get("period_end_date")), errors="coerce")
            logger.info(f"[ExtendedFinancials] Loaded quarterly_results: {len(df)} rows")
            return df
        except Exception as e:
            logger.warning(f"[ExtendedFinancials] Could not load quarterly_results: {e}")
            return None

    def _save_recovery(self):
        rec_df = pd.DataFrame(self.recovery)
        existing = pd.DataFrame()
        if RECOVERY_QUEUE.exists():
            try:
                existing = pd.read_csv(RECOVERY_QUEUE, low_memory=False)
            except Exception:
                pass
        combined = pd.concat([existing, rec_df], ignore_index=True) if not existing.empty else rec_df
        tmp = RECOVERY_QUEUE.with_suffix(".tmp")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))
        logger.info(f"[ExtendedFinancials] {len(self.recovery)} recovery items saved")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Phase 15B Extended Financials Engine")
    ap.add_argument("--backfill",      action="store_true", help="Fetch historical windows for 3Y growth")
    ap.add_argument("--windows",       type=int, default=None, help="Limit number of windows to fetch")
    ap.add_argument("--no-cache",        action="store_true", help="Ignore cached raw data (re-fetch everything)")
    ap.add_argument("--agg-only",        action="store_true", help="Skip XBRL fetch; re-aggregate from cached raw")
    ap.add_argument("--no-yfinance-bs",  action="store_true", help="Skip yfinance balance sheet augmentation")
    args = ap.parse_args()

    engine = ExtendedFinancialsEngine(
        backfill=args.backfill,
        max_windows=args.windows,
        use_cached_raw=not args.no_cache,
        use_yfinance_bs=not args.no_yfinance_bs,
    )

    if args.agg_only:
        # Re-aggregate from existing raw cache, then optionally augment with yfinance BS
        raw_df = engine._load_raw_cache()
        qr_df  = engine._load_qr()
        if raw_df.empty:
            print("[ERROR] No raw cache found. Run without --agg-only first.")
            sys.exit(1)
        rows = engine._aggregate(raw_df, qr_df)
        if not rows:
            print("[ERROR] Aggregation produced no rows")
            sys.exit(1)
        out_df = pd.DataFrame(rows).sort_values("symbol")
        if engine.use_yfinance_bs:
            out_df = engine._augment_yfinance_bs(out_df)
        tmp = OUTPUT_PATH.with_suffix(".tmp")
        out_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        print(f"[OK] {len(out_df)} symbols -> {OUTPUT_PATH}")
        return

    ok = engine.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
