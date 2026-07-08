"""
Phase FPI-B -- FPI Sector Signal Engine
Converts raw fortnightly AUC/net-investment data into rolling signals
for use in the sector rotation engine.

Reads:
  data/NSE/fpi/sector_fpi_fortnightly.csv  (Phase FPI output)

Outputs:
  data/NSE/fpi/fpi_sector_signals.csv
    Cols: sector_normalized, date, auc_equity_crore, net_inv_equity_crore,
          auc_pct_of_total, auc_z52, net_z52, qoq_auc_delta_pct,
          fpi_signal, signal_score

Signal legend:
  STRONG_ACCUMULATION  : high AUC and high net inflow (z>1.0 on both)
  ACCUMULATION         : positive net inflow, above-average AUC
  DISTRIBUTION         : significant net outflow (z<-1.0)
  STRONG_DISTRIBUTION  : heavy outflow + falling AUC
  NEUTRAL              : neither threshold crossed
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

logger = get_logger("fpi_sector_signal_engine")

INPUT_FILE  = cfg.FPI_DIR / "sector_fpi_fortnightly.csv"
OUTPUT_FILE = cfg.FPI_DIR / "fpi_sector_signals.csv"

# Rolling window: 26 fortnights = ~1 year
ROLLING_WINDOW = 26

# Sectors to exclude from signals (aggregate/non-actionable)
EXCLUDE_SECTORS = {"SKIP", "DIVERSIFIED", "OTHERS", ""}


def _signal_label(auc_z: float, net_z: float) -> str:
    if pd.isna(auc_z) or pd.isna(net_z):
        return "NEUTRAL"
    if auc_z > 1.0 and net_z > 1.0:
        return "STRONG_ACCUMULATION"
    if net_z > 0.5:
        return "ACCUMULATION"
    if auc_z < -1.0 and net_z < -1.0:
        return "STRONG_DISTRIBUTION"
    if net_z < -0.5:
        return "DISTRIBUTION"
    return "NEUTRAL"


def _signal_score(auc_z: float, net_z: float) -> float:
    """Continuous score: positive = accumulation, negative = distribution."""
    if pd.isna(auc_z) or pd.isna(net_z):
        return 0.0
    return round(float(auc_z * 0.5 + net_z * 0.5), 3)


class FPISectorSignalEngine:
    """Compute rolling Z-scores and signals from fortnightly FPI AUC data."""

    def run(self) -> bool:
        logger.info("[FPI-B] Starting signal engine")

        if not INPUT_FILE.exists():
            logger.error("[FPI-B] Input file not found: %s", INPUT_FILE)
            print("[FPI-B] ERROR: run sector_fpi_engine.py first")
            return False

        df = pd.read_csv(INPUT_FILE, parse_dates=["date"])
        logger.info("[FPI-B] Loaded %d rows, %d dates", len(df), df["date"].nunique())

        # Work only with mapped/actionable sectors
        df = df[~df["sector_normalized"].isin(EXCLUDE_SECTORS)].copy()
        df = df.dropna(subset=["auc_equity_crore"])

        if df.empty:
            logger.error("[FPI-B] No usable rows after filtering")
            return False

        # Aggregate multiple raw sectors that map to the same normalized sector
        # (e.g. 'Consumer Services' + 'Services' both -> SERVICES)
        agg_funcs = {
            "auc_equity_crore":    "sum",
            "net_inv_equity_crore": "sum",
            "source":              "first",
        }
        df = (
            df.groupby(["date", "sector_normalized"], as_index=False)
              .agg(agg_funcs)
        )

        # Compute total FPI equity AUC per date for share calculation
        total_per_date = (
            df.groupby("date")["auc_equity_crore"]
              .sum()
              .rename("total_auc")
        )
        df = df.join(total_per_date, on="date")
        df["auc_pct_of_total"] = (
            df["auc_equity_crore"] / df["total_auc"] * 100
        ).round(4)

        # Rolling Z-scores per sector (52-fortnight = 2-year lookback)
        df = df.sort_values(["sector_normalized", "date"])

        def _rolling_z(series: pd.Series, window: int = ROLLING_WINDOW) -> pd.Series:
            mu  = series.rolling(window, min_periods=6).mean()
            sig = series.rolling(window, min_periods=6).std()
            return ((series - mu) / sig.replace(0, np.nan)).round(3)

        df["auc_z52"] = df.groupby("sector_normalized")["auc_equity_crore"].transform(
            _rolling_z
        )
        df["net_z52"] = df.groupby("sector_normalized")["net_inv_equity_crore"].transform(
            _rolling_z
        )

        # QoQ AUC delta % (compare to same sector 6 fortnights ago = ~3 months)
        df["auc_lag6"] = df.groupby("sector_normalized")["auc_equity_crore"].shift(6)
        df["qoq_auc_delta_pct"] = (
            (df["auc_equity_crore"] - df["auc_lag6"]) / df["auc_lag6"].abs() * 100
        ).round(2)

        # Signal classification
        df["fpi_signal"]   = [
            _signal_label(a, n)
            for a, n in zip(df["auc_z52"], df["net_z52"])
        ]
        df["signal_score"] = [
            _signal_score(a, n)
            for a, n in zip(df["auc_z52"], df["net_z52"])
        ]

        # Select and order output columns
        keep = [
            "sector_normalized", "date", "source",
            "auc_equity_crore", "net_inv_equity_crore",
            "auc_pct_of_total", "auc_z52", "net_z52",
            "qoq_auc_delta_pct", "fpi_signal", "signal_score",
        ]
        keep = [c for c in keep if c in df.columns]
        out = df[keep].sort_values(["date", "sector_normalized"]).reset_index(drop=True)

        self._save_atomic(out)
        self._print_summary(out)
        return True

    def _save_atomic(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("G-D-03: refusing to write empty DataFrame")
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_FILE))
        logger.info("[FPI-B] Saved %d rows -> %s", len(df), OUTPUT_FILE)

    def _print_summary(self, df: pd.DataFrame):
        latest = df[df["date"] == df["date"].max()].copy()
        latest = latest.sort_values("signal_score", ascending=False)
        print()
        print("=" * 70)
        print("FPI SECTOR SIGNAL ENGINE -- LATEST SNAPSHOT")
        print("=" * 70)
        if latest.empty:
            print("  No data")
            return
        print(f"Latest date  : {latest['date'].iloc[0].date()}")
        print(f"Sectors      : {len(latest)}")
        print()
        print(f"{'Sector':<30} {'AUC (CR)':>12} {'AUC%':>6} {'Z52':>6} "
              f"{'NetZ':>6} {'QoQ%':>7} {'Signal'}")
        print("-" * 80)
        for _, r in latest.iterrows():
            print(
                f"{r['sector_normalized']:<30} "
                f"{r['auc_equity_crore']:>12,.0f} "
                f"{r.get('auc_pct_of_total', 0):>6.1f} "
                f"{r.get('auc_z52', 0):>+6.2f} "
                f"{r.get('net_z52', 0):>+6.2f} "
                f"{r.get('qoq_auc_delta_pct', 0):>+7.1f} "
                f"{r['fpi_signal']}"
            )
        print("=" * 70)


if __name__ == "__main__":
    engine = FPISectorSignalEngine()
    engine.run()
