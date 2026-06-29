"""
Participant Flow Engine
Phase 5B — Rolling metrics and normalized flow scores per participant

Reads:
  data/historical/institutional/institutional_positioning_history.csv  (F&O)
  data/historical/institutional/cash_market_flows_history.csv          (cash)

Outputs:
  data/intelligence/participant_flow_scores.csv

Columns produced:
  date
  FII_OI_Net, DII_OI_Net, PRO_OI_Net, CLIENT_OI_Net
  FII_OI_Delta, DII_OI_Delta, PRO_OI_Delta, CLIENT_OI_Delta
  FII_OI_Delta_5D, FII_OI_Delta_20D, FII_OI_Delta_60D   (and same for DII/PRO/CLIENT)
  FII_Volume_Net, DII_Volume_Net, PRO_Volume_Net, CLIENT_Volume_Net
  FII_Volume_5D, FII_Volume_20D, FII_Volume_60D           (and same for DII/PRO/CLIENT)
  FPI_net_cr, MF_net_cr, INSURANCE_net_cr, RETAIL_net_cr  (cash flows)
  FPI_flow_5D, FPI_flow_20D, FPI_flow_60D                 (cash rolling)
  MF_flow_5D, MF_flow_20D, MF_flow_60D
  FII_flow_score, DII_flow_score, PRO_flow_score, CLIENT_flow_score   (z-score → -100..+100)
  FPI_flow_score, MF_flow_score
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

logger = get_logger("participant_flow")

HISTORICAL_DIR = ROOT / "data" / "historical" / "institutional"
FNO_HISTORY    = HISTORICAL_DIR / "institutional_positioning_history.csv"
CASH_HISTORY   = HISTORICAL_DIR / "cash_market_flows_history.csv"
INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
OUTPUT_FILE    = INTELLIGENCE_DIR / "participant_flow_scores.csv"

PARTICIPANTS      = ["FII", "DII", "PRO", "CLIENT"]
CASH_PARTICIPANTS = ["FPI", "MF", "INSURANCE", "RETAIL"]
WINDOWS           = [5, 20, 60]
Z_WINDOW          = 252   # 1-year lookback for z-score normalisation
SCORE_SCALE       = 100   # z-score clip at ±3 → scale to ±100


def _zscore_norm(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score clipped to [-3, +3] then scaled to [-SCORE_SCALE, +SCORE_SCALE]."""
    roll = series.rolling(window, min_periods=max(window // 2, 20))
    mu  = roll.mean()
    sigma = roll.std().replace(0, np.nan)
    z   = (series - mu) / sigma
    z   = z.clip(-3, 3)
    return (z / 3 * SCORE_SCALE).round(2)


class ParticipantFlowEngine:
    """
    Phase 5B — computes OI deltas, rolling sums, and normalized flow scores.

    All computations are in-memory on existing history files.
    Output is always a full rewrite of participant_flow_scores.csv (rebuild on run).
    """

    def run(self) -> bool:
        logger.info("[ParticipantFlow] Starting Phase 5B")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

        fno = self._load_fno()
        cash = self._load_cash()
        if fno.empty:
            logger.error("[5B] F&O history is empty — cannot compute scores")
            return False

        result = self._compute(fno, cash)
        self._save(result)
        self._print_summary(result)
        return True

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_fno(self) -> pd.DataFrame:
        if not FNO_HISTORY.exists():
            logger.warning("[5B] %s not found", FNO_HISTORY)
            return pd.DataFrame()
        df = pd.read_csv(FNO_HISTORY)
        # Support both 'Date' (existing schema) and 'date'
        if "Date" in df.columns:
            df = df.rename(columns={"Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)
        logger.info("[5B] F&O history: %d rows, %s → %s", len(df),
                    df["date"].min(), df["date"].max())
        return df

    def _load_cash(self) -> pd.DataFrame:
        if not CASH_HISTORY.exists():
            logger.warning("[5B] Cash history not found — cash scores will be empty")
            return pd.DataFrame()
        df = pd.read_csv(CASH_HISTORY)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)
        logger.info("[5B] Cash history: %d rows, %s → %s", len(df),
                    df["date"].min(), df["date"].max())
        return df

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def _compute(self, fno: pd.DataFrame, cash: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame({"date": fno["date"]})

        # ---- F&O OI net (raw) ----------------------------------------
        for p in PARTICIPANTS:
            col = f"{p}_OI_Net"
            if col in fno.columns:
                result[col] = pd.to_numeric(fno[col], errors="coerce")
            else:
                result[col] = np.nan

        # ---- OI delta (day-over-day change) ----------------------------
        for p in PARTICIPANTS:
            col = f"{p}_OI_Net"
            result[f"{p}_OI_Delta"] = result[col].diff().round(2)

        # ---- OI delta rolling sums -------------------------------------
        for p in PARTICIPANTS:
            delta_col = f"{p}_OI_Delta"
            for w in WINDOWS:
                result[f"{p}_OI_Delta_{w}D"] = (
                    result[delta_col].rolling(w, min_periods=1).sum().round(2)
                )

        # ---- Volume net (raw) ------------------------------------------
        for p in PARTICIPANTS:
            col = f"{p}_Volume_Net"
            if col in fno.columns:
                result[col] = pd.to_numeric(fno[col], errors="coerce")
            else:
                result[col] = np.nan

        # ---- Volume rolling sums ----------------------------------------
        for p in PARTICIPANTS:
            vol_col = f"{p}_Volume_Net"
            for w in WINDOWS:
                result[f"{p}_Volume_{w}D"] = (
                    result[vol_col].rolling(w, min_periods=1).sum().round(2)
                )

        # ---- FII Derivatives net ----------------------------------------
        if "FII_Derivatives_Net" in fno.columns:
            result["FII_Derivatives_Net"] = pd.to_numeric(fno["FII_Derivatives_Net"], errors="coerce")

        # ---- Merge cash flows -------------------------------------------
        if not cash.empty:
            for p in CASH_PARTICIPANTS:
                net_col = f"{p}_net_cr"
                if net_col in cash.columns:
                    cash_sub = cash[["date", net_col]].copy()
                    cash_sub[net_col] = pd.to_numeric(cash_sub[net_col], errors="coerce")
                    result = result.merge(cash_sub, on="date", how="left")
                    for w in WINDOWS:
                        result[f"{p}_flow_{w}D"] = (
                            result[net_col].rolling(w, min_periods=1).sum().round(2)
                        )
        else:
            for p in CASH_PARTICIPANTS:
                result[f"{p}_net_cr"] = np.nan
                for w in WINDOWS:
                    result[f"{p}_flow_{w}D"] = np.nan

        # ---- Normalized flow scores ------------------------------------
        # F&O participants: use 20D OI delta sum as the base signal
        for p in PARTICIPANTS:
            base = result[f"{p}_OI_Delta_20D"]
            result[f"{p}_flow_score"] = _zscore_norm(base, Z_WINDOW)

        # Cash participants: use 20D rolling net cr
        for p in CASH_PARTICIPANTS:
            base = result.get(f"{p}_flow_20D", pd.Series(np.nan, index=result.index))
            result[f"{p}_flow_score"] = _zscore_norm(base.fillna(0), Z_WINDOW)

        return result

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("G-D-03: refusing to write empty participant_flow_scores.csv")
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_FILE))
        logger.info("[5B] Saved: %s (%d rows, %d cols)", OUTPUT_FILE.name, len(df), len(df.columns))

    def _print_summary(self, df: pd.DataFrame):
        print()
        print("=" * 60)
        print("PARTICIPANT FLOW ENGINE — PHASE 5B COMPLETE")
        print("=" * 60)
        print(f"Date range  : {df['date'].min()} to {df['date'].max()}")
        print(f"Total rows  : {len(df)}")
        print(f"Columns     : {len(df.columns)}")
        for p in PARTICIPANTS:
            sc = df[f"{p}_flow_score"].dropna()
            if not sc.empty:
                print(f"  {p:8s} score: latest={sc.iloc[-1]:+.1f}  min={sc.min():+.1f}  max={sc.max():+.1f}")
        print("=" * 60)


if __name__ == "__main__":
    engine = ParticipantFlowEngine()
    engine.run()
