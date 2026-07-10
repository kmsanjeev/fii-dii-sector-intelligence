"""
Signal Efficacy Engine
Phase SA-1 -- Measures which signals ACTUALLY predict forward returns.

The institutional discipline this platform was missing: every factor gets a
report card -- Information Coefficient (Spearman rank correlation of the
factor value vs the forward return), top-minus-bottom decile spread, and
hit rate -- computed on point-in-time reconstructed history so there is no
look-ahead bias.

Method:
  - Monthly snapshot dates over the past LOOKBACK_MONTHS (first trading day
    of each month present in the data)
  - At each snapshot, for each symbol with enough history, compute the
    price-based factors AS THEY WOULD HAVE READ ON THAT DAY:
      ret_30d, ret_90d          momentum
      prox_52w_high             distance below 52-week high (breakout factor)
      dma_trend                 close vs 50-DMA (%)
      vol_surge                 20d avg volume vs prior 60d avg
  - Forward returns 30/60/90 trading days after the snapshot
  - Per factor x horizon: IC (mean cross-sectional Spearman), decile spread
    (mean top-decile forward return minus bottom-decile), hit rate of the
    top decile (share with positive forward return), n observations

Non-price factors (institutional deals, sector flows, shareholding) cannot
be reconstructed point-in-time from current files -- they are listed as
UNMEASURED until data/intelligence/history/scores_history.parquet (Phase
SA-1 D2) accumulates enough live snapshots. Honest > complete.

Reads (read-only, G-D-01):
  data/cache/stock_history/{SYMBOL}.parquet
  data/NSE/indices/nifty_500_constituents.csv   (evaluation universe)

Writes (atomic, G-D-02):
  data/intelligence/signal_efficacy.csv

Run:  py -3.11 -m engines.research.signal_efficacy_engine
"""

import shutil
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

NIFTY500_CSV = cfg.INDICES_DIR / "nifty_500_constituents.csv"
OUTPUT_CSV   = cfg.INTELLIGENCE_DIR / "signal_efficacy.csv"

LOOKBACK_MONTHS = 36
MIN_HISTORY     = 420          # trading days needed before a snapshot counts
HORIZONS        = [30, 60, 90] # forward trading days
MIN_CROSS_SECTION = 150        # min symbols per snapshot for a valid IC

FACTORS = ["ret_30d", "ret_90d", "prox_52w_high", "dma_trend", "vol_surge"]

# Signals that exist on the platform but cannot be reconstructed historically
UNMEASURED = [
    ("deal_score",        "needs scores_history.parquet -- measurable after ~6 months of snapshots"),
    ("sector_flow_score", "needs scores_history.parquet -- measurable after ~6 months of snapshots"),
    ("corporate_score",   "needs scores_history.parquet -- measurable after ~6 months of snapshots"),
    ("ml_bull_run_score", "needs scores_history.parquet -- measurable after ~6 months of snapshots"),
    ("holding_trends",    "quarterly cadence -- needs 8+ quarters of snapshots"),
]

COLS = [
    "factor", "horizon_days", "ic_mean", "ic_std", "ic_positive_pct",
    "decile_spread_pct", "top_decile_hit_rate_pct", "n_snapshots", "n_obs",
    "status", "note", "run_date",
]


class SignalEfficacyEngine:
    """Point-in-time factor report card: IC, decile spread, hit rate."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()

    # ── Entry ─────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[SignalEfficacy] Starting -- reconstructing %d months of factor history",
                    LOOKBACK_MONTHS)
        panel = self._build_panel()
        if panel is None or panel.empty:
            logger.warning("[SignalEfficacy] Aborted -- no usable panel")
            return False

        rows = self._evaluate(panel)
        for factor, note in UNMEASURED:
            for h in HORIZONS:
                rows.append({
                    "factor": factor, "horizon_days": h,
                    "ic_mean": None, "ic_std": None, "ic_positive_pct": None,
                    "decile_spread_pct": None, "top_decile_hit_rate_pct": None,
                    "n_snapshots": 0, "n_obs": 0,
                    "status": "UNMEASURED", "note": note, "run_date": self.run_date,
                })

        df = pd.DataFrame(rows, columns=COLS)
        if df.empty:                                            # G-D-03
            raise ValueError("Refusing to write empty efficacy frame")
        self._atomic_write(df, OUTPUT_CSV)
        measured = df[df["status"] == "MEASURED"]
        logger.info("[SignalEfficacy] Complete -- %d factor x horizon cells measured; "
                    "best IC: %s", len(measured),
                    measured.loc[measured["ic_mean"].idxmax()][["factor", "horizon_days", "ic_mean"]].tolist()
                    if not measured.empty else "n/a")
        return True

    # ── Panel construction (point-in-time, per symbol) ────────────────────────

    def _load_symbol(self, symbol: str) -> pd.DataFrame | None:
        pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
        if not pq.exists():
            return None
        try:
            df = pd.read_parquet(pq, columns=["date", "close", "high", "volume"])
        except Exception:
            return None
        df["date"]   = pd.to_datetime(df["date"], errors="coerce")
        df["close"]  = pd.to_numeric(df["close"], errors="coerce")
        df["high"]   = pd.to_numeric(df["high"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df = df.dropna(subset=["date", "close"])
        df = df[df["close"] > 0]                                # G-P-01
        return df.drop_duplicates(subset=["date"], keep="last") \
                 .sort_values("date").reset_index(drop=True) if len(df) else None

    def _build_panel(self) -> pd.DataFrame | None:
        if not NIFTY500_CSV.exists():
            return None
        universe = pd.read_csv(NIFTY500_CSV)["symbol"].str.strip().str.upper().tolist()

        records: list[dict] = []
        loaded = 0
        for sym in universe:
            df = self._load_symbol(sym)
            if df is None or len(df) < MIN_HISTORY:
                continue
            loaded += 1

            close  = df["close"].values
            high   = df["high"].values
            vol    = df["volume"].values
            dates  = df["date"]

            # Monthly snapshot indices: first trading day of each month
            months = dates.dt.to_period("M")
            snap_idx = np.where(months != months.shift(1))[0]

            n = len(df)
            dma50 = pd.Series(close).rolling(50).mean().values
            hi252 = pd.Series(high).rolling(252).max().values
            v20   = pd.Series(vol).rolling(20).mean().values
            v60p  = pd.Series(vol).shift(20).rolling(60).mean().values

            cutoff = dates.iloc[-1] - pd.DateOffset(months=LOOKBACK_MONTHS)
            for i in snap_idx:
                if i < 260 or dates.iloc[i] < cutoff:
                    continue
                if i + min(HORIZONS) >= n:
                    continue    # not enough forward data for even the shortest horizon
                rec = {
                    "date":   dates.iloc[i],
                    "symbol": sym,
                    "ret_30d":       close[i] / close[i - 21] - 1 if i >= 21 else np.nan,
                    "ret_90d":       close[i] / close[i - 63] - 1 if i >= 63 else np.nan,
                    "prox_52w_high": close[i] / hi252[i] - 1 if hi252[i] > 0 else np.nan,
                    "dma_trend":     close[i] / dma50[i] - 1 if dma50[i] > 0 else np.nan,
                    "vol_surge":     v20[i] / v60p[i] - 1 if v60p[i] and v60p[i] > 0 else np.nan,
                }
                for h in HORIZONS:
                    rec[f"fwd_{h}d"] = close[i + h] / close[i] - 1 if i + h < n else np.nan
                records.append(rec)

        logger.info("[SignalEfficacy] Panel: %d symbols loaded, %d snapshot rows",
                    loaded, len(records))
        return pd.DataFrame(records) if records else None

    # ── Evaluation: IC, decile spread, hit rate ───────────────────────────────

    def _evaluate(self, panel: pd.DataFrame) -> list[dict]:
        rows: list[dict] = []
        for factor in FACTORS:
            for h in HORIZONS:
                fwd = f"fwd_{h}d"
                ics: list[float] = []
                top_rets: list[float] = []
                bot_rets: list[float] = []
                top_hits: list[float] = []
                n_obs = 0

                for _, snap in panel.groupby("date"):
                    d = snap[[factor, fwd]].dropna()
                    if len(d) < MIN_CROSS_SECTION:
                        continue
                    ic = d[factor].corr(d[fwd], method="spearman")
                    if pd.isna(ic):
                        continue
                    ics.append(float(ic))
                    n_obs += len(d)
                    q_hi = d[factor].quantile(0.9)
                    q_lo = d[factor].quantile(0.1)
                    top = d[d[factor] >= q_hi][fwd]
                    bot = d[d[factor] <= q_lo][fwd]
                    if len(top) and len(bot):
                        top_rets.append(float(top.mean()))
                        bot_rets.append(float(bot.mean()))
                        top_hits.append(float((top > 0).mean()))

                if len(ics) < 6:
                    rows.append({
                        "factor": factor, "horizon_days": h,
                        "ic_mean": None, "ic_std": None, "ic_positive_pct": None,
                        "decile_spread_pct": None, "top_decile_hit_rate_pct": None,
                        "n_snapshots": len(ics), "n_obs": n_obs,
                        "status": "INSUFFICIENT", "note": "fewer than 6 valid snapshots",
                        "run_date": self.run_date,
                    })
                    continue

                ic_arr = np.array(ics)
                rows.append({
                    "factor":                  factor,
                    "horizon_days":            h,
                    "ic_mean":                 round(float(ic_arr.mean()), 4),
                    "ic_std":                  round(float(ic_arr.std()), 4),
                    "ic_positive_pct":         round(float((ic_arr > 0).mean() * 100), 1),
                    "decile_spread_pct":       round(float((np.mean(top_rets) - np.mean(bot_rets)) * 100), 2),
                    "top_decile_hit_rate_pct": round(float(np.mean(top_hits) * 100), 1),
                    "n_snapshots":             len(ics),
                    "n_obs":                   n_obs,
                    "status":                  "MEASURED",
                    "note":                    "",
                    "run_date":                self.run_date,
                })
        return rows

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    ok = SignalEfficacyEngine().run()
    sys.exit(0 if ok else 1)
