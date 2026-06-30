"""
Price Momentum Engine
Phase 8A — Per-symbol price returns and volume trend across all lookback windows

Reads bhavcopy files (data/NSE/bhavcopy/equity/) for 5 reference dates:
  now, 30D ago, 60D ago, 90D ago, 365D ago

Computes per symbol:
  ret_30d, ret_60d, ret_90d, ret_365d      — price returns in %
  vol_ratio                                 — latest volume / 20D average volume
  sector_rel_30d                            — ret_30d minus sector median ret_30d
  price_score                               — 0-100 composite (percentile-ranked)

Outputs:
  data/intelligence/price_momentum.csv     (~2400 symbols, full rebuild on run)

Guardrails: G-S-01 (EQ only), G-D-02 (atomic), G-D-03 (no empty write),
            G-P-01 (no negative prices), G-I-04 (no fillna(0) on price data)
"""

import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("price_momentum")

BHAV_ROOT = cfg.NSE_EQUITY_BHAVCOPY_DIR
CLASSIFICATION   = cfg.DATA_DIR / "reference" / "company_classification_v4.csv"
INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
OUTPUT_FILE      = INTELLIGENCE_DIR / "price_momentum.csv"

# Trading-day lookbacks (approximate)
LOOKBACKS = {"30d": 22, "60d": 43, "90d": 65, "365d": 252}
VOLUME_WINDOW = 22   # 20 trading days for volume average


def _load_bhav(path: Path) -> pd.DataFrame:
    """Load bhavcopy with dual-schema support. Returns (SYMBOL, close, volume) EQ only."""
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    df.columns = df.columns.str.strip()

    if "CLOSE_PRICE" in df.columns and "TTL_TRD_QNTY" in df.columns:
        close_col, vol_col = "CLOSE_PRICE", "TTL_TRD_QNTY"
    elif "CLOSE" in df.columns and "TOTTRDQTY" in df.columns:
        close_col, vol_col = "CLOSE", "TOTTRDQTY"
    else:
        return pd.DataFrame()

    df = df[df["SERIES"].astype(str).str.strip() == "EQ"][["SYMBOL", close_col, vol_col]].copy()
    df.columns = ["symbol", "close", "volume"]
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["close"]  = pd.to_numeric(df["close"],  errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = df[(df["close"] > 0) & (df["volume"] >= 0)]   # G-P-01
    return df.dropna(subset=["close"])


def _pct_rank(series: pd.Series) -> pd.Series:
    """Percentile rank: 0-100 across non-NaN values. NaN stays NaN."""
    n = series.notna().sum()
    if n == 0:
        return series
    return series.rank(pct=True, na_option="keep") * 100


class PriceMomentumEngine:
    """
    Phase 8A — full rebuild of per-symbol price momentum on each run.
    Takes ~5 seconds (5 bhavcopy file loads + 22 for volume).
    """

    def run(self) -> bool:
        logger.info("[PriceMomentum] Starting Phase 8A")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

        all_files = sorted(BHAV_ROOT.rglob("*.csv"))
        if len(all_files) < VOLUME_WINDOW + max(LOOKBACKS.values()):
            logger.error("[8A] Insufficient bhavcopy history")
            return False

        logger.info("[8A] Total bhavcopy files: %d, latest: %s",
                    len(all_files), all_files[-1].stem)

        # Load reference close prices
        df_now = _load_bhav(all_files[-1]).set_index("symbol")["close"].rename("close_now")
        reference: dict[str, pd.Series] = {}
        for label, n_back in LOOKBACKS.items():
            idx = max(-len(all_files), -n_back - 1)
            try:
                reference[label] = _load_bhav(all_files[idx]).set_index("symbol")["close"]
            except IndexError:
                reference[label] = pd.Series(dtype=float)

        # Load volume window
        vol_dfs = [_load_bhav(f)[["symbol", "volume"]].set_index("symbol")["volume"]
                   for f in all_files[-VOLUME_WINDOW:]]
        vol_stack = pd.concat(vol_dfs, axis=1)
        avg_vol   = vol_stack.mean(axis=1)
        cur_vol   = vol_dfs[-1]

        # Sector map
        sector_map = self._load_sector_map()

        # Build result DataFrame
        result = pd.DataFrame({"close_now": df_now})
        result.index.name = "symbol"

        for label, ref_series in reference.items():
            result[f"ret_{label}"] = (
                (df_now - ref_series) / ref_series * 100
            ).round(2)

        # Volume ratio
        result["vol_ratio"] = (cur_vol / avg_vol).round(3)
        result.loc[result["vol_ratio"] > 50, "vol_ratio"] = np.nan  # clip extreme outliers

        # Sector
        result["sector"] = result.index.map(sector_map).fillna("OTHER")

        # Sector-relative 30D return
        sector_median = (result.groupby("sector")["ret_30d"]
                         .transform("median"))
        result["sector_rel_30d"] = (result["ret_30d"] - sector_median).round(2)

        # Percentile-rank each metric
        result["ret_30d_pct"]     = _pct_rank(result["ret_30d"])
        result["ret_90d_pct"]     = _pct_rank(result["ret_90d"])
        result["ret_365d_pct"]    = _pct_rank(result["ret_365d"])
        result["vol_ratio_pct"]   = _pct_rank(result["vol_ratio"])
        result["sector_rel_pct"]  = _pct_rank(result["sector_rel_30d"])

        # Composite price momentum score (0-100)
        # Weights: 30D momentum 35%, 90D 25%, 365D 20%, sector-relative 15%, volume 5%
        result["price_score"] = (
            result["ret_30d_pct"].fillna(50)    * 0.35
            + result["ret_90d_pct"].fillna(50)  * 0.25
            + result["ret_365d_pct"].fillna(50) * 0.20
            + result["sector_rel_pct"].fillna(50) * 0.15
            + result["vol_ratio_pct"].fillna(50) * 0.05
        ).round(2)

        result = result.reset_index()
        result["as_of_date"] = pd.to_datetime(all_files[-1].stem.split("_")[1],
                                               format="%Y%m%d").strftime("%Y-%m-%d")

        if result.empty:
            raise ValueError("G-D-03: price momentum result is empty")

        self._save_atomic(result, OUTPUT_FILE)
        self._print_summary(result)
        return True

    def _load_sector_map(self) -> dict:
        if not CLASSIFICATION.exists():
            return {}
        df = pd.read_csv(CLASSIFICATION, usecols=["SYMBOL", "SECTOR"])
        df["SYMBOL"] = df["SYMBOL"].str.strip().str.upper()
        return dict(zip(df["SYMBOL"], df["SECTOR"]))

    def _save_atomic(self, df: pd.DataFrame, path: Path):
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[8A] Saved %s (%d rows, %d cols)", path.name, len(df), len(df.columns))

    def _print_summary(self, df: pd.DataFrame):
        print()
        print("=" * 65)
        print("PRICE MOMENTUM ENGINE - PHASE 8A COMPLETE")
        print("=" * 65)
        print(f"Symbols           : {len(df)}")
        print(f"As of date        : {df['as_of_date'].iloc[0]}")
        print(f"30D return range  : {df['ret_30d'].min():.1f}% to {df['ret_30d'].max():.1f}%")
        print(f"Symbols w/ 365D   : {df['ret_365d'].notna().sum()}")
        print(f"Price score range : {df['price_score'].min():.0f} to {df['price_score'].max():.0f}")
        print()
        print("Top 10 by price_score:")
        top = df.nlargest(10, "price_score")
        for _, r in top.iterrows():
            print(f"  {r['symbol']:15s}: score={r['price_score']:.0f}  "
                  f"30D={r.get('ret_30d', float('nan')):+.1f}%  "
                  f"90D={r.get('ret_90d', float('nan')):+.1f}%  "
                  f"sector={r['sector']}")
        print("=" * 65)


if __name__ == "__main__":
    engine = PriceMomentumEngine()
    engine.run()
