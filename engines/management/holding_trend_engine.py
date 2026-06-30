"""
Holding Trend Engine -- Phase 16A
Computes quarterly holding pattern trends for promoter, FII, DII, and public shareholders.

Data source: nselib shareholding_pattern (NSE filing data)
Output: data/NSE/shareholding/holding_trends.csv

Columns:
  symbol, period, promoter_pct, fii_pct, dii_pct, public_pct,
  promoter_delta, fii_delta, dii_delta, conviction_signal, as_of_date

Signals:
  STRONG_PROMOTER_BUY  : promoter_delta >= +1% in quarter
  FII_ACCUMULATION     : fii_delta >= +0.5%
  DII_ACCUMULATION     : dii_delta >= +0.5%
  PROMOTER_SELLING     : promoter_delta <= -1%
  DIVERGENCE           : FII buying + DII selling (or vice versa)

Guardrails:
  - G-D-02: atomic writes
  - G-D-03: no empty DataFrame writes
  - G-A-01: rate limiting between nselib calls
  - G-A-02: retry with exponential backoff
  - G-A-03: failed symbols -> recovery_queue.csv
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

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
OUTPUT_PATH = SHAREHOLDING_DIR / "holding_trends.csv"
EQUITY_MASTER = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
RECOVERY_QUEUE = cfg.NSE_DIR / "recovery_queue.csv"

# Thresholds for conviction signals
STRONG_PROMOTER_BUY  = 1.0   # pct
FII_ACCUM_THRESHOLD  = 0.5
DII_ACCUM_THRESHOLD  = 0.5
PROMOTER_SELL_THRESH = -1.0


class HoldingTrendEngine:
    """
    Fetches quarterly shareholding patterns and computes QoQ delta signals.
    Promoter increasing stake + FII accumulating = STRONG conviction.
    """

    def __init__(self, max_symbols: Optional[int] = None):
        SHAREHOLDING_DIR.mkdir(parents=True, exist_ok=True)
        self.max_symbols = max_symbols
        self.recovery: list[dict] = []

    def run(self) -> bool:
        logger.info("[HoldingTrend] Starting shareholding pattern analysis")

        symbols = self._load_symbols()
        if not symbols:
            logger.error("[HoldingTrend] No EQ symbols found")
            return False

        if self.max_symbols:
            symbols = symbols[:self.max_symbols]

        logger.info(f"[HoldingTrend] Processing {len(symbols)} symbols")
        existing = self._load_existing()
        processed = set(existing["symbol"].unique()) if not existing.empty else set()

        pending = [sym for sym in symbols if sym not in processed]
        n_workers = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(pending)))
        new_rows: list[dict] = []

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(self._fetch_symbol, sym): sym for sym in pending}
            for fut in progress(as_completed(futures), total=len(futures), desc="Shareholding fetch"):
                sym = futures[fut]
                try:
                    rows = fut.result()
                    if rows:
                        new_rows.extend(rows)
                    else:
                        self.recovery.append({"symbol": sym, "reason": "no_shareholding"})
                except Exception as e:
                    self.recovery.append({"symbol": sym, "reason": str(e)})

        if not new_rows and existing.empty:
            logger.warning("[HoldingTrend] No shareholding data fetched")
            return False

        combined = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
        combined = combined.drop_duplicates(subset=["symbol", "period"])
        combined = combined.sort_values(["symbol", "period"])

        # Compute QoQ deltas
        combined = self._compute_deltas(combined)
        combined = self._assign_signals(combined)

        self._save(combined)
        if self.recovery:
            self._save_recovery()

        logger.info(f"[HoldingTrend] Complete: {len(combined)} records")
        return True

    def _load_symbols(self) -> list[str]:
        if not EQUITY_MASTER.exists():
            return []
        em = pd.read_csv(EQUITY_MASTER)
        series_col = next((c for c in ["series", "SERIES"] if c in em.columns), None)
        if series_col:
            em = em[em[series_col] == "EQ"]
        sym_col = next((c for c in ["symbol", "SYMBOL"] if c in em.columns), None)
        return em[sym_col].dropna().unique().tolist() if sym_col else []

    def _fetch_symbol(self, symbol: str) -> list[dict]:
        for attempt in range(cfg.MAX_RETRIES):
            try:
                from nselib import capital_market as cm
                raw = cm.shareholding_patterns(symbol=symbol)
                time.sleep(max(0.2, cfg.API_DELAY / cfg.MAX_CONCURRENCY))
                if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
                    return []
                return self._parse(symbol, raw)
            except Exception as e:
                if attempt < cfg.MAX_RETRIES - 1:
                    time.sleep(cfg.RETRY_DELAY * (2 ** attempt))
                else:
                    logger.debug(f"[HoldingTrend] Failed {symbol}: {e}")
        return []

    def _parse(self, symbol: str, raw) -> list[dict]:
        try:
            if isinstance(raw, pd.DataFrame):
                df = raw
            elif isinstance(raw, list):
                df = pd.DataFrame(raw)
            else:
                return []

            rows = []
            for _, r in df.iterrows():
                period = str(r.get("period", r.get("quarter", r.get("date", "")))).strip()
                promoter = _safe_float(r.get("promoter", r.get("promoterHolding", r.get("Promoter", None))))
                fii      = _safe_float(r.get("fii", r.get("fiiHolding", r.get("FII", None))))
                dii      = _safe_float(r.get("dii", r.get("diiHolding", r.get("DII", None))))
                public   = _safe_float(r.get("public", r.get("publicHolding", r.get("Public", None))))

                rows.append({
                    "symbol": symbol,
                    "period": period,
                    "promoter_pct": promoter,
                    "fii_pct": fii,
                    "dii_pct": dii,
                    "public_pct": public,
                })
            return rows
        except Exception as e:
            logger.debug(f"[HoldingTrend] Parse error {symbol}: {e}")
            return []

    def _compute_deltas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute QoQ change in holding percentages."""
        df = df.sort_values(["symbol", "period"])
        for col in ["promoter_pct", "fii_pct", "dii_pct"]:
            delta_col = col.replace("_pct", "_delta")
            df[delta_col] = df.groupby("symbol")[col].diff()
        return df

    def _assign_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Assign conviction signal based on QoQ deltas."""
        def signal(row):
            p = row.get("promoter_delta")
            f = row.get("fii_delta")
            d = row.get("dii_delta")

            if p and p >= STRONG_PROMOTER_BUY and f and f >= FII_ACCUM_THRESHOLD:
                return "STRONG_PROMOTER_FII_BUY"
            if p and p >= STRONG_PROMOTER_BUY:
                return "STRONG_PROMOTER_BUY"
            if f and f >= FII_ACCUM_THRESHOLD and d and d >= DII_ACCUM_THRESHOLD:
                return "FII_DII_ACCUMULATION"
            if f and f >= FII_ACCUM_THRESHOLD:
                return "FII_ACCUMULATION"
            if d and d >= DII_ACCUM_THRESHOLD:
                return "DII_ACCUMULATION"
            if p and p <= PROMOTER_SELL_THRESH:
                return "PROMOTER_SELLING"
            if f and d and f >= FII_ACCUM_THRESHOLD and d <= -DII_ACCUM_THRESHOLD:
                return "FII_DII_DIVERGENCE"
            return "STABLE"

        df["conviction_signal"] = df.apply(signal, axis=1)
        df["as_of_date"] = pd.Timestamp.now().date().isoformat()
        return df

    def _load_existing(self) -> pd.DataFrame:
        if OUTPUT_PATH.exists():
            df = pd.read_csv(OUTPUT_PATH)
            return df if not df.empty else pd.DataFrame()
        return pd.DataFrame()

    def _save(self, df: pd.DataFrame):
        if df.empty:
            return
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[HoldingTrend] Saved {len(df)} records -> {OUTPUT_PATH}")

    def _save_recovery(self):
        rdf = pd.DataFrame(self.recovery)
        existing = pd.read_csv(RECOVERY_QUEUE) if RECOVERY_QUEUE.exists() else pd.DataFrame()
        combined = pd.concat([existing, rdf], ignore_index=True).drop_duplicates()
        tmp = RECOVERY_QUEUE.with_suffix(".tmp.csv")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))


def _safe_float(v) -> Optional[float]:
    try:
        return float(str(v).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    engine = HoldingTrendEngine(max_symbols=20)
    engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        n_sym = df["symbol"].nunique()
        print(f"Holding trends: {len(df)} records, {n_sym} symbols")
        strong = df[df["conviction_signal"] == "STRONG_PROMOTER_FII_BUY"]
        print(f"STRONG_PROMOTER_FII_BUY: {len(strong)} entries")
        if not strong.empty:
            print(strong[["symbol", "period", "promoter_delta", "fii_delta"]].head())
