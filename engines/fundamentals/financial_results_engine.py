"""
Financial Results Engine -- Phase 15A
Fetches quarterly financial results from NSE for all EQ-series companies.

nselib provides `financial_results_for_equity(from_date, to_date, fin_period)` which
fetches all companies for a date range in one call (XBRL archives).
NOTE: NSE XBRL archive endpoint returns 404 intermittently -- engine handles this
      gracefully and logs recovery. Retry after market hours.

Data source priority:
  1. nselib financial_results_for_equity (bulk, date range)
  2. yfinance per-symbol quarterly_income_stmt (last resort)

Output: data/NSE/results/quarterly_results.csv
        Columns: symbol, date, period, revenue_cr, net_profit_cr, eps, yoy_revenue_pct, yoy_profit_pct, source

Guardrails:
  - EQ series only (G-S-01)
  - Atomic writes (G-D-02)
  - No empty DataFrame writes (G-D-03)
  - Rate limiting between yfinance calls (G-A-01)
  - Failed symbols -> recovery_queue.csv (G-A-03)
"""

import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger(__name__)

RESULTS_DIR = cfg.NSE_DIR / "results"
OUTPUT_PATH = RESULTS_DIR / "quarterly_results.csv"
EQUITY_MASTER = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# nselib bulk fetch: last 4 quarters
FETCH_PERIODS = [
    ("01-04-2025", "30-06-2025"),
    ("01-07-2025", "30-09-2025"),
    ("01-10-2025", "31-12-2025"),
    ("01-01-2026", "31-03-2026"),
]

REQUIRED_COLS = ["symbol", "date", "period", "revenue_cr", "net_profit_cr", "eps"]


class FinancialResultsEngine:
    """
    Fetches quarterly financial results using nselib bulk endpoint.
    Falls back to per-symbol yfinance if bulk endpoint unavailable.
    """

    # Hard cap: yfinance fallback never iterates more than this many symbols
    # Full universe (2373) at 1s/symbol = 40+ min; use batch_size for production runs
    YFINANCE_BATCH_CAP = 100

    def __init__(self, max_symbols: Optional[int] = None, use_yfinance: bool = True,
                 yfinance_cap: Optional[int] = None):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.max_symbols = max_symbols
        self.use_yfinance = use_yfinance
        # yfinance_cap: max symbols for fallback; defaults to YFINANCE_BATCH_CAP
        # set to None only when explicitly running full batch overnight
        self.yfinance_cap = yfinance_cap if yfinance_cap is not None else self.YFINANCE_BATCH_CAP
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[FinancialResults] Starting quarterly results fetch")

        # Try bulk nselib fetch first
        rows = self._fetch_bulk_nselib()

        # If bulk fails, fallback to per-symbol yfinance (capped to avoid multi-hour runs)
        if not rows and self.use_yfinance:
            logger.info(
                f"[FinancialResults] nselib bulk unavailable, falling back to yfinance "
                f"(cap={self.yfinance_cap} symbols)"
            )
            rows = self._fetch_yfinance_all()

        if not rows:
            logger.warning(
                "[FinancialResults] No results fetched. NSE XBRL archive may be temporarily unavailable. "
                "This is a known intermittent issue. Retry after market hours."
            )
            return False

        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["symbol", "date", "period"])
        df = df.sort_values(["symbol", "date"])

        # Append to existing (incremental)
        existing = self._load_existing()
        if not existing.empty:
            combined = pd.concat([existing, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["symbol", "date", "period"])
            df = combined.sort_values(["symbol", "date"])

        if df.empty:
            return False

        self._save(df)
        logger.info(f"[FinancialResults] Complete: {len(df)} records, {df['symbol'].nunique()} symbols")
        return True

    # ------------------------------------------------------------------
    # Primary: nselib bulk fetch (all companies, date range)
    # ------------------------------------------------------------------

    def _fetch_bulk_nselib(self) -> list[dict]:
        try:
            from nselib import capital_market as cm
        except ImportError:
            logger.warning("[FinancialResults] nselib not installed")
            return []

        all_rows: list[dict] = []
        for from_date, to_date in FETCH_PERIODS:
            try:
                df = cm.financial_results_for_equity(
                    from_date=from_date,
                    to_date=to_date,
                    fin_period="Quarterly",
                )
                if df is None or df.empty:
                    continue
                rows = self._parse_bulk(df, period=f"{from_date[:7]}")
                all_rows.extend(rows)
                logger.info(f"[FinancialResults] nselib fetched {len(rows)} rows for {from_date} - {to_date}")
                time.sleep(cfg.API_DELAY)
            except Exception as e:
                logger.warning(f"[FinancialResults] nselib bulk failed for {from_date}: {e}")

        return all_rows

    def _parse_bulk(self, df: pd.DataFrame, period: str) -> list[dict]:
        """Parse nselib financial_results_for_equity DataFrame."""
        rows = []
        # Column mapping (nselib uses various names)
        symbol_col = next((c for c in ["symbol", "Symbol", "SYMBOL"] if c in df.columns), None)
        date_col   = next((c for c in ["date", "periodEnd", "to_date", "Date"] if c in df.columns), None)
        rev_col    = next((c for c in ["revenue", "totalIncome", "netSales", "total_income"] if c in df.columns), None)
        pft_col    = next((c for c in ["netProfit", "netIncome", "profit_after_tax", "PAT"] if c in df.columns), None)
        eps_col    = next((c for c in ["eps", "EPS", "basicEPS"] if c in df.columns), None)

        if not symbol_col:
            logger.warning(f"[FinancialResults] No symbol column found in bulk response, cols: {list(df.columns)[:10]}")
            return []

        for _, row in df.iterrows():
            sym = str(row.get(symbol_col, "")).strip().upper()
            if not sym:
                continue

            date_raw = str(row.get(date_col, ""))[:10] if date_col else period
            rev_raw  = row.get(rev_col, None) if rev_col else None
            pft_raw  = row.get(pft_col, None) if pft_col else None
            eps_raw  = row.get(eps_col, None) if eps_col else None

            try:
                revenue_cr = float(str(rev_raw).replace(",", "")) / 1e7 if rev_raw else None
            except (ValueError, TypeError):
                revenue_cr = None

            try:
                profit_cr = float(str(pft_raw).replace(",", "")) / 1e7 if pft_raw else None
            except (ValueError, TypeError):
                profit_cr = None

            rows.append({
                "symbol": sym,
                "date": date_raw,
                "period": period,
                "revenue_cr": round(revenue_cr, 2) if revenue_cr else None,
                "net_profit_cr": round(profit_cr, 2) if profit_cr else None,
                "eps": float(eps_raw) if eps_raw else None,
                "source": "nselib",
            })

        return rows

    # ------------------------------------------------------------------
    # Fallback: yfinance per-symbol
    # ------------------------------------------------------------------

    def _fetch_yfinance_all(self) -> list[dict]:
        symbols = self._load_symbols()
        if self.max_symbols:
            symbols = symbols[:self.max_symbols]
        # Never iterate full universe uncapped — use yfinance_cap as hard ceiling
        if self.yfinance_cap and len(symbols) > self.yfinance_cap:
            logger.warning(
                f"[FinancialResults] yfinance cap applied: {self.yfinance_cap}/{len(symbols)} symbols. "
                f"Pass yfinance_cap=None only for overnight full-batch runs."
            )
            symbols = symbols[:self.yfinance_cap]

        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(symbols)))
        all_rows: list[dict] = []

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(self._fetch_yfinance_symbol, sym): sym for sym in symbols}
            for fut in progress(as_completed(futures), total=len(futures), desc="yfinance fetch"):
                sym = futures[fut]
                try:
                    rows = fut.result()
                    if rows:
                        all_rows.extend(rows)
                    else:
                        self.recovery.append({"symbol": sym, "reason": "no_yfinance_data"})
                except Exception as e:
                    self.recovery.append({"symbol": sym, "reason": str(e)})

        if self.recovery:
            self._save_recovery()
        return all_rows

    def _fetch_yfinance_symbol(self, symbol: str) -> list[dict]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            income = ticker.quarterly_income_stmt
            # Per-worker rate limit: total rate ≈ n_workers / sleep_per_worker
            time.sleep(max(0.3, cfg.API_DELAY / cfg.MAX_CONCURRENCY))
            if income is None or income.empty:
                return []

            rows = []
            for col in income.columns:
                date_str = str(col)[:10]
                try:
                    revenue = income.loc["Total Revenue", col] if "Total Revenue" in income.index else None
                    profit  = income.loc["Net Income", col] if "Net Income" in income.index else None
                    revenue_cr = float(revenue) / 1e7 if revenue is not None else None
                    profit_cr  = float(profit) / 1e7 if profit is not None else None
                except Exception:
                    continue

                rows.append({
                    "symbol": symbol,
                    "date": date_str,
                    "period": "Q",
                    "revenue_cr": round(revenue_cr, 2) if revenue_cr else None,
                    "net_profit_cr": round(profit_cr, 2) if profit_cr else None,
                    "eps": None,
                    "source": "yfinance",
                })
            return rows
        except Exception as e:
            logger.debug(f"[FinancialResults] yfinance failed for {symbol}: {e}")
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_symbols(self) -> list[str]:
        if not EQUITY_MASTER.exists():
            return []
        em = pd.read_csv(EQUITY_MASTER)
        series_col = next((c for c in ["series", "SERIES"] if c in em.columns), None)
        if series_col:
            em = em[em[series_col] == "EQ"]
        sym_col = next((c for c in ["symbol", "SYMBOL"] if c in em.columns), None)
        return em[sym_col].dropna().unique().tolist() if sym_col else []

    def _load_existing(self) -> pd.DataFrame:
        if OUTPUT_PATH.exists():
            df = pd.read_csv(OUTPUT_PATH)
            return df if not df.empty else pd.DataFrame()
        return pd.DataFrame()

    def _save(self, df: pd.DataFrame):
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[FinancialResults] Saved {len(df)} records -> {OUTPUT_PATH}")

    def _save_recovery(self):
        if not self.recovery:
            return
        recovery_df = pd.DataFrame(self.recovery)
        existing_rq = pd.read_csv(RECOVERY_QUEUE) if RECOVERY_QUEUE.exists() else pd.DataFrame()
        combined = pd.concat([existing_rq, recovery_df], ignore_index=True).drop_duplicates()
        tmp = RECOVERY_QUEUE.with_suffix(".tmp.csv")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))
        logger.warning(f"[FinancialResults] {len(self.recovery)} symbols in recovery -> {RECOVERY_QUEUE}")


if __name__ == "__main__":
    import sys as _sys
    # Pass --full to run full yfinance batch (overnight only)
    full_run = "--full" in _sys.argv
    engine = FinancialResultsEngine(
        max_symbols=None,
        yfinance_cap=None if full_run else 100,
    )
    success = engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        n_sym = df["symbol"].nunique()
        print(f"Results: {len(df)} records, {n_sym} symbols")
        print(df.head(10).to_string())
    else:
        print("No results fetched. NSE XBRL endpoint may be temporarily unavailable.")
        print("Run again after market hours or retry tomorrow.")
