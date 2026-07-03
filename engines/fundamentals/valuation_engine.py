"""
Valuation Engine -- Phase 15B
Computes P/E, P/B, ROE, and valuation scores from financial results + price data.

Reads:
  data/NSE/results/quarterly_results.csv   <- from financial_results_engine.py
  data/intelligence/bull_run_probability.csv <- price_score, sector
  cache/stock_history/<SYMBOL>.csv         <- latest close price

Output: data/NSE/results/valuation_scores.csv
Columns: symbol, pe_ratio, pb_ratio, roe_pct, valuation_score, valuation_label, as_of_date

Guardrails:
  - G-D-02: atomic writes
  - G-D-03: no empty DataFrame writes
  - G-I-04: never fillna(0) on financial ratios -- propagate None
  - G-P-01: no negative prices (filter before computing ratios)
"""

import shutil
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger(__name__)

RESULTS_PATH  = cfg.NSE_DIR / "results" / "quarterly_results.csv"
SCORES_PATH   = cfg.NSE_DIR / "results" / "valuation_scores.csv"
BULL_RUN_PATH = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
STOCK_CACHE   = cfg.STOCK_HISTORY_CACHE

SCORE_CLIP_LOW  = 0.0
SCORE_CLIP_HIGH = 100.0


class ValuationEngine:
    """
    Scores stocks on valuation metrics: P/E, P/B, ROE.
    Lower P/E + higher ROE = better valuation score.
    """

    def run(self) -> bool:
        logger.info("[ValuationEngine] Starting valuation scoring")

        if not RESULTS_PATH.exists():
            logger.error(f"[ValuationEngine] quarterly_results.csv not found: {RESULTS_PATH}")
            return False

        results = pd.read_csv(RESULTS_PATH)
        if results.empty:
            logger.error("[ValuationEngine] quarterly_results.csv is empty")
            return False

        # Latest quarter per symbol
        ttm = self._compute_ttm(results)

        # Get latest close prices from stock history cache
        prices = self._load_prices(ttm["symbol"].tolist())

        # Merge
        df = ttm.merge(prices, on="symbol", how="left")

        # Load bull_run for sector context
        if BULL_RUN_PATH.exists():
            br = pd.read_csv(BULL_RUN_PATH, usecols=["symbol", "sector"])
            df = df.merge(br, on="symbol", how="left")

        # Compute ratios
        df = self._compute_ratios(df)
        df = self._score(df)

        if df.empty:
            logger.error("[ValuationEngine] No valuation data computed")
            return False

        self._save(df)
        logger.info(f"[ValuationEngine] Scored {len(df)} symbols")
        return True

    def _compute_ttm(self, results: pd.DataFrame) -> pd.DataFrame:
        """Compute trailing 12-month (TTM) revenue and profit per symbol.

        Consolidated preference: when a symbol has both Consolidated and Standalone
        filings, use only Consolidated rows (they include subsidiaries and give the
        true group-level picture, e.g. RELIANCE includes Jio + Retail).
        """
        date_col = "date_end" if "date_end" in results.columns else "date"
        results = results.sort_values(["symbol", date_col])
        ttm_rows = []
        groups = list(results.groupby("symbol"))
        nat_col = "standalone_or_consolidated" if "standalone_or_consolidated" in results.columns else None

        for symbol, grp in progress(groups, desc="Computing TTM"):
            # Prefer Consolidated when available
            if nat_col:
                cons = grp[grp[nat_col].str.upper().str.contains("CONSOL", na=False)]
                base = cons if not cons.empty else grp
            else:
                base = grp

            last4 = base.tail(4)
            num_qtrs = len(last4)
            revenue_ttm = last4["revenue_cr"].sum() if "revenue_cr" in last4.columns else None
            profit_ttm  = last4["net_profit_cr"].sum() if "net_profit_cr" in last4.columns else None
            as_of = last4[date_col].max()

            # Latest single-quarter EPS + profit for share-count derivation in P/E
            latest_row = last4.iloc[-1]
            eps_q   = latest_row.get("eps") if "eps" in last4.columns else None
            prof_q  = latest_row.get("net_profit_cr") if "net_profit_cr" in last4.columns else None
            eps_q   = float(eps_q)  if eps_q  is not None and not _isnan(eps_q)  else None
            prof_q  = float(prof_q) if prof_q is not None and not _isnan(prof_q) else None

            # YoY growth (if 8 quarters available in the same cohort)
            if len(base) >= 8:
                prev4 = base.iloc[-8:-4]
                rev_prev = prev4["revenue_cr"].sum()
                pft_prev  = prev4["net_profit_cr"].sum()
                yoy_rev = ((revenue_ttm - rev_prev) / abs(rev_prev) * 100) if rev_prev and rev_prev != 0 else None
                yoy_pft = ((profit_ttm - pft_prev) / abs(pft_prev) * 100) if pft_prev and pft_prev != 0 else None
            else:
                yoy_rev = yoy_pft = None

            ttm_rows.append({
                "symbol":          symbol,
                "revenue_ttm_cr":  round(revenue_ttm, 2) if revenue_ttm else None,
                "profit_ttm_cr":   round(profit_ttm, 2)  if profit_ttm  else None,
                "eps_q":           eps_q,
                "profit_cr_q":     round(prof_q, 2) if prof_q else None,
                "num_quarters":    num_qtrs,
                "yoy_revenue_pct": round(yoy_rev, 2) if yoy_rev else None,
                "yoy_profit_pct":  round(yoy_pft, 2) if yoy_pft else None,
                "as_of_date":      as_of,
            })

        return pd.DataFrame(ttm_rows)

    def _load_prices(self, symbols: list[str]) -> pd.DataFrame:
        """Load latest close price from stock history cache using parallel file reads."""
        def _read_one(symbol: str) -> dict:
            cache_file = STOCK_CACHE / f"{symbol}.parquet"
            if not cache_file.exists():
                cache_file = STOCK_CACHE / f"{symbol}.csv"
                if not cache_file.exists():
                    return {"symbol": symbol, "latest_close": None}
            try:
                if cache_file.suffix == ".parquet":
                    df = pd.read_parquet(cache_file, columns=["close"])
                else:
                    df = pd.read_csv(cache_file)
                close_col = "close" if "close" in df.columns else "Close"
                if close_col not in df.columns or df.empty:
                    return {"symbol": symbol, "latest_close": None}
                latest_close = df[close_col].iloc[-1]
                if latest_close <= 0:  # G-P-01
                    return {"symbol": symbol, "latest_close": None}
                return {"symbol": symbol, "latest_close": float(latest_close)}
            except Exception:
                return {"symbol": symbol, "latest_close": None}

        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(symbols)))
        rows = [None] * len(symbols)

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(_read_one, sym): i for i, sym in enumerate(symbols)}
            for fut in progress(as_completed(futures), total=len(futures), desc="Loading prices"):
                rows[futures[fut]] = fut.result()

        return pd.DataFrame(rows)

    def _compute_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute P/E, P/B (placeholder), net margin from available data.

        P/E derivation:
          1. Derive shares from latest single-quarter EPS + profit
             shares_cr = profit_cr_q / eps_q
          2. Annualize TTM profit to full 4 quarters when fewer are available
             annualized_profit_cr = profit_ttm_cr * (4 / num_quarters)
          3. P/E = close * shares_cr / annualized_profit_cr
             (equivalent to market_cap / annualized_annual_profit)
        This avoids the single-quarter EPS bug (e.g. RELIANCE showed 200x because
        it used Q3FY25 standalone EPS=6.44 directly, which is not annualized).
        """
        pe_list, margin_list = [], []

        for _, row in df.iterrows():
            close      = row.get("latest_close")
            eps_q      = row.get("eps_q")
            prof_q     = row.get("profit_cr_q")
            profit_ttm = row.get("profit_ttm_cr")
            num_qtrs   = int(row.get("num_quarters") or 4)
            revenue    = row.get("revenue_ttm_cr")

            # P/E — annualized market-cap / profit approach
            pe = None
            if (close and eps_q and prof_q and profit_ttm
                    and eps_q > 0 and prof_q > 0 and profit_ttm > 0):
                shares_cr = prof_q / eps_q                            # crores of shares
                ann_profit = profit_ttm * (4.0 / max(num_qtrs, 1))   # extrapolate to 4Q
                if shares_cr > 0 and ann_profit > 0:
                    pe = round((close * shares_cr) / ann_profit, 2)

            # Net profit margin (proxy for profitability; true ROE needs balance sheet)
            margin = None
            if profit_ttm and revenue and revenue > 0:
                margin = round((profit_ttm / revenue) * 100, 2)

            pe_list.append(pe)
            margin_list.append(margin)

        df["pe_ratio"] = pe_list
        df["roe_pct"]  = margin_list   # labelled roe_pct for API compat; actually net margin
        df["pb_ratio"] = None          # requires book value (balance sheet)
        return df

    def _score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valuation score (0-100):
          Low P/E (good) + High ROE (good) + High revenue growth
        Normalized within universe.
        """
        # P/E score: lower is better; clip extreme values
        pe_valid = df["pe_ratio"].dropna()
        if not pe_valid.empty:
            pe_50 = pe_valid.quantile(0.50)
            pe_90 = pe_valid.quantile(0.90)
            df["pe_score"] = df["pe_ratio"].apply(
                lambda v: max(0, min(100, 100 * (1 - (v / pe_90)))) if v and v > 0 else 50
            )
        else:
            df["pe_score"] = 50

        # ROE score: higher is better; 25% ROE = 100, negative = 0
        df["roe_score"] = df["roe_pct"].apply(
            lambda v: max(0, min(100, (v / 25.0) * 100)) if v else 50
        )

        # YoY profit growth score
        df["growth_score"] = df["yoy_profit_pct"].apply(
            lambda v: max(0, min(100, 50 + v)) if v else 50
        )

        # Weighted composite
        df["valuation_score"] = (
            0.40 * df["pe_score"] +
            0.40 * df["roe_score"] +
            0.20 * df["growth_score"]
        ).clip(SCORE_CLIP_LOW, SCORE_CLIP_HIGH).round(2)

        # Label
        df["valuation_label"] = df["valuation_score"].apply(_label)

        return df[["symbol", "sector", "pe_ratio", "pb_ratio", "roe_pct",
                   "pe_score", "roe_score", "growth_score", "valuation_score",
                   "valuation_label", "revenue_ttm_cr", "profit_ttm_cr",
                   "yoy_revenue_pct", "yoy_profit_pct", "as_of_date"]]

    def _save(self, df: pd.DataFrame):
        tmp = SCORES_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(SCORES_PATH))
        logger.info(f"[ValuationEngine] Saved -> {SCORES_PATH}")


def _label(score: float) -> str:
    if score >= 75:
        return "CHEAP_QUALITY"
    if score >= 55:
        return "FAIR_VALUE"
    if score >= 35:
        return "MODERATE"
    return "EXPENSIVE_OR_WEAK"


def _isnan(v) -> bool:
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    engine = ValuationEngine()
    engine.run()
    if SCORES_PATH.exists():
        df = pd.read_csv(SCORES_PATH)
        print(f"Valuation scores: {len(df)} symbols")
        if not df.empty:
            print(df.nlargest(10, "valuation_score")[
                ["symbol", "pe_ratio", "roe_pct", "valuation_score", "valuation_label"]
            ].to_string())
