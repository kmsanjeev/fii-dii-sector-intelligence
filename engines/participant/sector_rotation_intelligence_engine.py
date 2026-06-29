"""
Sector Rotation Intelligence Engine
Phase 6C — Combine participant flow scores with price momentum signals
           to produce the final capital flow rotation intelligence

Reads:
  data/intelligence/sector_flow_scores.csv     (Phase 6B — participant flows per sector)
  data/intelligence/index_strength.csv         (Phase 3 — NSE index price momentum)
  data/intelligence/sector_rotation.csv        (Phase 3 — NSE index rotation ranks)

Outputs:
  data/intelligence/sector_rotation_intelligence.csv
    One row per sector (latest snapshot) with combined signal
    Cols: sector, FII_flow_score, DII_flow_score, PRO_flow_score, CLIENT_flow_score,
          Smart_Money_Score, Retail_Score, price_momentum_score, nse_index,
          flow_rank, price_rank, combined_score, combined_rank,
          rotation_signal, capital_flow_alignment, last_date

  data/intelligence/sector_rotation_history.csv
    Full time-series of combined scores (one row per date × sector)
    Used for trend detection and GUI charting
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

logger = get_logger("sector_rotation_intelligence")

INTELLIGENCE_DIR   = cfg.INTELLIGENCE_DIR
FLOW_SCORES_FILE   = INTELLIGENCE_DIR / "sector_flow_scores.csv"
INDEX_STRENGTH     = INTELLIGENCE_DIR / "index_strength.csv"
SECTOR_ROTATION    = INTELLIGENCE_DIR / "sector_rotation.csv"
SNAPSHOT_OUTPUT    = INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
HISTORY_OUTPUT     = INTELLIGENCE_DIR / "sector_rotation_history.csv"

# Weights for combined score
FLOW_WEIGHT  = 0.60   # participant flows are leading indicator
PRICE_WEIGHT = 0.40   # price momentum confirms

# Map NSE index names → platform sectors (best-fit mapping)
NSE_TO_PLATFORM = {
    "NIFTY BANK":                        "BANKING",
    "NIFTY PSU BANK":                    "BANKING",
    "NIFTY PRIVATE BANK":                "BANKING",
    "NIFTY FINANCIAL SERVICES":          "FINANCIAL_SERVICES",
    "NIFTY FINANCIAL SERVICES 25/50":    "FINANCIAL_SERVICES",
    "NIFTY FINANCIAL SERVICES EX-BANK":  "FINANCIAL_SERVICES",
    "NIFTY CAPITAL MARKETS":             "AMC",
    "NIFTY IT":                          "IT",
    "NIFTY MIDSMALL IT & TELECOM":       "IT",
    "NIFTY PHARMA":                      "PHARMA",
    "NIFTY HEALTHCARE INDEX":            "HEALTHCARE",
    "NIFTY MIDSMALL HEALTHCARE":         "HEALTHCARE",
    "NIFTY500 HEALTHCARE":               "HEALTHCARE",
    "NIFTY FMCG":                        "FMCG",
    "NIFTY NON-CYCLICAL CONSUMER":       "FMCG",
    "NIFTY AUTO":                        "AUTO",
    "NIFTY CONSUMER DURABLES":           "CAPITAL_GOODS",
    "NIFTY METAL":                       "METAL",
    "NIFTY COMMODITIES":                 "METAL",
    "NIFTY REALTY":                      "REALTY",
    "NIFTY REITS & REALTY":              "REALTY",
    "NIFTY ENERGY":                      "ENERGY",
    "NIFTY OIL & GAS":                   "ENERGY",
    "NIFTY INFRASTRUCTURE":              "INFRASTRUCTURE",
    "NIFTY MEDIA":                       "MEDIA",
    "NIFTY SERVICES SECTOR":             "FINANCIAL_SERVICES",
    "NIFTY CHEMICALS":                   "CHEMICALS",
    "NIFTY CEMENT":                      "CEMENT",
    "NIFTY PSE":                         "DIVERSIFIED",
    "NIFTY CPSE":                        "DIVERSIFIED",
    "NIFTY MNC":                         "DIVERSIFIED",
    "NIFTY MIDSMALL FINANCIAL SERVICES": "FINANCIAL_SERVICES",
}


def _rotation_signal(flow_score: float, price_score: float) -> str:
    """
    Classify sector into rotation quadrant:
      STRONG_ACCUMULATION : flow+  price+  (institutional buying + price confirming)
      EARLY_ROTATION      : flow+  price−  (institutional accumulating before price moves)
      PRICE_LED           : flow−  price+  (price moving but institutions not buying)
      DISTRIBUTION        : flow−  price−  (institutional selling + price declining)
      NEUTRAL             : near-zero on both axes
    """
    if pd.isna(flow_score) or pd.isna(price_score):
        return "NEUTRAL"
    flow_pos  = flow_score > 15
    flow_neg  = flow_score < -15
    price_pos = price_score > 0
    price_neg = price_score < 0

    if flow_pos and price_pos:
        return "STRONG_ACCUMULATION"
    if flow_pos and price_neg:
        return "EARLY_ROTATION"
    if flow_neg and price_neg:
        return "DISTRIBUTION"
    if flow_neg and price_pos:
        return "PRICE_LED"
    return "NEUTRAL"


def _alignment(flow_score: float, price_score: float) -> str:
    """Whether smart money and price are pointing in the same direction."""
    if pd.isna(flow_score) or pd.isna(price_score):
        return "UNKNOWN"
    if (flow_score > 0) == (price_score > 0):
        return "ALIGNED"
    return "DIVERGENT"


class SectorRotationIntelligenceEngine:
    """
    Phase 6C — produces the combined capital flow + price rotation signal per sector.

    Outputs two files:
      sector_rotation_intelligence.csv  — latest snapshot (always current)
      sector_rotation_history.csv       — full time-series (rebuilt on run)
    """

    def run(self) -> bool:
        logger.info("[SectorRotationIntelligence] Starting Phase 6C")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

        flow_scores = self._load_flow_scores()
        price_map   = self._build_price_map()

        if flow_scores.empty:
            logger.error("[6C] sector_flow_scores.csv is empty — run Phase 6B first")
            return False

        history  = self._compute_history(flow_scores, price_map)
        snapshot = self._build_snapshot(history)

        self._save_atomic(history,  HISTORY_OUTPUT)
        self._save_atomic(snapshot, SNAPSHOT_OUTPUT)
        self._print_summary(snapshot)
        return True

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_flow_scores(self) -> pd.DataFrame:
        if not FLOW_SCORES_FILE.exists():
            logger.warning("[6C] %s not found", FLOW_SCORES_FILE)
            return pd.DataFrame()
        df = pd.read_csv(FLOW_SCORES_FILE)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        score_cols = [c for c in df.columns if "flow_score" in c or "Smart_Money" in c or "Retail_Score" in c]
        for col in score_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        logger.info("[6C] Flow scores: %d rows, %s → %s",
                    len(df), df["date"].min(), df["date"].max())
        return df

    def _build_price_map(self) -> dict[str, float]:
        """Build sector → price_momentum_score from NSE index files."""
        price_map: dict[str, float] = {}

        # Primary: sector_rotation.csv has RANK and MOMENTUM_SCORE
        if SECTOR_ROTATION.exists():
            sr = pd.read_csv(SECTOR_ROTATION)
            for _, row in sr.iterrows():
                idx_name = str(row.get("INDEX_NAME", "")).strip().upper()
                platform = NSE_TO_PLATFORM.get(idx_name)
                if not platform:
                    continue
                score = float(row.get("MOMENTUM_SCORE", 0) or 0)
                # Keep highest score when multiple NSE indices map to same platform sector
                if platform not in price_map or score > price_map[platform]:
                    price_map[platform] = score
            logger.info("[6C] Price map built from sector_rotation.csv: %d sectors", len(price_map))

        # Supplement with index_strength.csv if any sector still missing
        if INDEX_STRENGTH.exists() and len(price_map) < 15:
            is_df = pd.read_csv(INDEX_STRENGTH)
            for _, row in is_df.iterrows():
                idx_name = str(row.get("INDEX_NAME", "")).strip().upper()
                platform = NSE_TO_PLATFORM.get(idx_name)
                if not platform or platform in price_map:
                    continue
                price_map[platform] = float(row.get("MOMENTUM_SCORE", 0) or 0)

        return price_map

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def _compute_history(self, flow_scores: pd.DataFrame,
                         price_map: dict[str, float]) -> pd.DataFrame:
        """
        Merge per-date flow scores with price momentum and compute combined signal.
        Price momentum is from a point-in-time snapshot — applied as a constant offset
        to the historical time-series (it refreshes when Phase 3 engines re-run).
        """
        df = flow_scores.copy()

        # Map sector → price momentum score (constant for now)
        df["price_momentum_score"] = df["sector"].map(price_map).fillna(0.0)

        # Best-fit NSE index name for reference
        reverse_map = {}
        for nse_idx, plat in NSE_TO_PLATFORM.items():
            reverse_map.setdefault(plat, nse_idx)  # first match
        df["nse_index"] = df["sector"].map(reverse_map).fillna("")

        # Combined score: flow-weighted + price-weighted
        # Normalise price_momentum_score to same ±100 scale as flow scores
        df["price_norm"] = df["price_momentum_score"].clip(-10, 10) / 10 * 100
        fii_score = pd.to_numeric(df.get("FII_flow_score", np.nan), errors="coerce")
        df["combined_score"] = (
            fii_score * FLOW_WEIGHT
            + df["price_norm"] * PRICE_WEIGHT
        ).round(2)

        # Rotation signal and alignment (using Smart Money score vs price)
        smart = pd.to_numeric(df.get("Smart_Money_Score", np.nan), errors="coerce")
        df["rotation_signal"]       = [_rotation_signal(s, p) for s, p in
                                        zip(smart, df["price_momentum_score"])]
        df["capital_flow_alignment"] = [_alignment(f, p) for f, p in
                                         zip(fii_score, df["price_momentum_score"])]

        # Per-date flow rank (1 = best FII flow on that day)
        df["flow_rank"] = (df.groupby("date")["combined_score"]
                           .rank(ascending=False, method="min")
                           .astype("Int64"))

        keep = ["date", "sector", "nse_index",
                "FII_flow_score", "DII_flow_score", "PRO_flow_score", "CLIENT_flow_score",
                "Smart_Money_Score", "Retail_Score",
                "price_momentum_score", "combined_score",
                "rotation_signal", "capital_flow_alignment", "flow_rank"]
        keep = [c for c in keep if c in df.columns]
        return df[keep].sort_values(["date", "flow_rank"]).reset_index(drop=True)

    def _build_snapshot(self, history: pd.DataFrame) -> pd.DataFrame:
        """Extract the latest date's row per sector, add price_rank and combined_rank."""
        latest_date = history["date"].max()
        snap = history[history["date"] == latest_date].copy()

        # Price rank based on price_momentum_score
        snap["price_rank"] = (snap["price_momentum_score"]
                              .rank(ascending=False, method="min")
                              .astype("Int64"))
        snap["combined_rank"] = snap["flow_rank"]
        snap["last_date"] = latest_date
        snap = snap.drop(columns=["flow_rank"], errors="ignore")
        snap = snap.sort_values("combined_rank").reset_index(drop=True)
        return snap

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[6C] Saved: %s (%d rows)", path.name, len(df))

    def _print_summary(self, snap: pd.DataFrame):
        print()
        print("=" * 72)
        print("SECTOR ROTATION INTELLIGENCE ENGINE — PHASE 6C COMPLETE")
        print("=" * 72)
        if snap.empty:
            print("  No data")
            return
        print(f"Snapshot date : {snap['last_date'].iloc[0]}")
        print(f"Sectors       : {len(snap)}")
        print()
        print(f"{'Rank':<5} {'Sector':<22} {'FII':>7} {'Smart':>7} {'Price':>7} "
              f"{'Combined':>9} {'Signal':<22} {'Align'}")
        print("-" * 90)
        for _, r in snap.iterrows():
            print(f"{int(r.get('combined_rank', 0)):<5} "
                  f"{r['sector']:<22} "
                  f"{r.get('FII_flow_score', 0):>+7.1f} "
                  f"{r.get('Smart_Money_Score', 0):>+7.1f} "
                  f"{r.get('price_momentum_score', 0):>+7.2f} "
                  f"{r.get('combined_score', 0):>+9.1f} "
                  f"{r.get('rotation_signal', 'N/A'):<22} "
                  f"{r.get('capital_flow_alignment', '')}")
        print("=" * 72)


if __name__ == "__main__":
    engine = SectorRotationIntelligenceEngine()
    engine.run()
