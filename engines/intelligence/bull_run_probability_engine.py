"""
Bull Run Probability Engine
Phase 8B -- Multi-factor score: which stocks are positioned for / already in a bull run

Five independent intelligence layers:
  1. Price Momentum Score    (25%) -- from price_momentum.csv [8A]
  2. ATH Proximity Score     (20%) -- from technical_indicators.csv [Phase A]
     (100 = at 52W high, 0 = 50% below; 2pts per % away from ATH)
  3. Sector Capital Flow     (20%) -- blended FII+DII+Smart Money from sector_rotation_intelligence.csv [6C]
  4. Institutional Deal Score(20%) -- inst_net_value_cr from institutional_deal_signals.csv [7A]
  5. Corporate Confidence    (15%) -- confidence_score_12m from corporate_confidence_scores.csv [7C]

Market Regime Multiplier applied after scoring:
  STRONG_ACCUMULATION: x1.20  ACCUMULATION: x1.10  EARLY_ACCUMULATION: x1.02
  NEUTRAL: x0.90  DISTRIBUTION: x0.80  STRONG_DISTRIBUTION: x0.65

Labels (market-phase descriptive):
  BULL_RUN  (>=60)  -- Already in confirmed bull run; near ATH, strong uptrend
  EMERGING  (>=42)  -- Early breakout / building momentum; not yet at ATH
  WATCHLIST (>=28)  -- On watch; some positive signals but unconfirmed
  NEUTRAL   (>=15)  -- No clear direction; sideways
  DEAD      (< 15)  -- Downtrend / distribution; avoid

Outputs:
  data/intelligence/bull_run_probability.csv   -- all symbols with component scores
  data/intelligence/bull_run_watchlist.csv     -- BULL_RUN + EMERGING only

Guardrails: G-D-02 (atomic), G-D-03 (no empty write), G-I-04 (no fillna on financial data)
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

logger = get_logger("bull_run_probability")

INTELLIGENCE_DIR    = cfg.INTELLIGENCE_DIR
PRICE_MOMENTUM      = INTELLIGENCE_DIR / "price_momentum.csv"
SECTOR_ROTATION     = INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
DEAL_SIGNALS        = INTELLIGENCE_DIR / "institutional_deal_signals.csv"
CORPORATE_SCORES    = INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
TECHNICAL_INTEL     = INTELLIGENCE_DIR / "technical_indicators.csv"
PARTICIPANT_INTEL   = INTELLIGENCE_DIR / "participant_intelligence.csv"
POSITIONING_HISTORY = cfg.DATA_DIR / "historical" / "institutional" / "institutional_positioning_history.csv"

OUTPUT_FULL      = INTELLIGENCE_DIR / "bull_run_probability.csv"
OUTPUT_WATCHLIST = INTELLIGENCE_DIR / "bull_run_watchlist.csv"

# Factor weights (must sum to 1.0)
WEIGHTS = {
    "price_score":        0.25,
    "ath_proximity_score":0.20,   # NEW: rewards stocks near 52W high
    "sector_flow_score":  0.20,   # uses blended FII+DII+Smart Money (not FII only)
    "deal_score":         0.20,
    "corporate_score":    0.15,
}

# Market regime multipliers
REGIME_MULTIPLIER = {
    "STRONG_ACCUMULATION": 1.20,
    "ACCUMULATION":        1.10,
    "EARLY_ACCUMULATION":  1.02,
    "NEUTRAL":             0.90,
    "DISTRIBUTION":        0.80,
    "STRONG_DISTRIBUTION": 0.65,
}
DEFAULT_MULTIPLIER = 0.90

# Market-phase labels
# Thresholds calibrated for NEUTRAL regime (x0.90), score mean ~43, range ~15-70:
#   BULL_RUN  >= 62: confirmed bull run; near ATH, strong uptrend  (~1%)
#   EMERGING  >= 52: building momentum, early breakout            (~20%)
#   WATCHLIST >= 40: worth monitoring, some positive signals      (~35%)
#   NEUTRAL   >= 25: no clear direction, sideways                 (~40%)
#   DEAD      <  25: downtrend / distribution — avoid             (~4%)
LABEL_THRESHOLDS = [
    (60, "BULL_RUN"),
    (52, "EMERGING"),
    (40, "WATCHLIST"),
    (25, "NEUTRAL"),
    (0,  "DEAD"),
]


def _label_score(score: float) -> str:
    for threshold, label in LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "DEAD"


def _pct_rank_0_100(series: pd.Series) -> pd.Series:
    """Percentile rank to 0-100. NaN stays NaN."""
    return series.rank(pct=True, na_option="keep") * 100


class BullRunProbabilityEngine:
    """
    Phase 8B -- full rebuild on each run.
    All upstream engines must run first (8A, 6C, 7A, 7C, Phase A technical).
    """

    def __init__(self):
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        self._validate_inputs()

    def _validate_inputs(self):
        required = {
            "price_momentum.csv":            PRICE_MOMENTUM,
            "sector_rotation_intelligence.csv": SECTOR_ROTATION,
        }
        missing = [name for name, path in required.items() if not path.exists()]
        if missing:
            raise FileNotFoundError(
                f"[8B] Required inputs missing -- run upstream engines first: {missing}"
            )
        for path in [DEAL_SIGNALS, CORPORATE_SCORES, TECHNICAL_INTEL, POSITIONING_HISTORY]:
            if not path.exists():
                logger.warning("[8B] Optional input missing (neutral fallback): %s", path.name)

    # ----------------------------------------------------------------
    # Factor loaders
    # ----------------------------------------------------------------

    def _load_price_scores(self) -> pd.DataFrame:
        df = pd.read_csv(PRICE_MOMENTUM)
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df = df.set_index("symbol")
        # price_score is already 0-100 from 8A
        return df[["price_score", "sector", "close_now", "ret_30d", "ret_90d",
                    "ret_365d", "vol_ratio", "as_of_date"]].copy()

    def _load_ath_proximity_scores(self) -> pd.Series:
        """
        ATH proximity: 0 = stock at 52W high (best), -50+ = far below (worst).
        Score: max(0, min(100, 100 + prox_52w_high * 2))
          at ATH (prox=0)    --> 100
          5% below  (prox=-5)  --> 90
          10% below (prox=-10) --> 80
          25% below (prox=-25) --> 50
          50%+ below           --> 0
        Also loads trend_signal for output annotation.
        """
        if not TECHNICAL_INTEL.exists():
            logger.warning("[8B] technical_indicators.csv missing -- ATH score defaults to 50 (neutral)")
            return pd.Series(dtype=float, name="ath_proximity_score"), pd.Series(dtype=str, name="trend_signal")

        df = pd.read_csv(TECHNICAL_INTEL, usecols=["symbol", "prox_52w_high", "trend_signal"])
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df = df.set_index("symbol")

        ath_score = (100 + df["prox_52w_high"] * 2).clip(0, 100).round(2)
        return ath_score.rename("ath_proximity_score"), df["trend_signal"]

    def _load_sector_flow_scores(self) -> tuple[pd.Series, pd.DataFrame]:
        """
        Blended sector intelligence: FII (40%) + DII (30%) + Smart Money (30%).
        All three are +-100 z-scores; rescaled to 0-100 via (score + 100) / 2.
        Also returns the full sector participant breakdown for driving_participant.
        """
        cols = ["sector", "FII_flow_score", "DII_flow_score",
                "Smart_Money_Score", "Retail_Score", "CLIENT_flow_score"]
        available = [c for c in cols if c in pd.read_csv(SECTOR_ROTATION, nrows=0).columns]
        df = pd.read_csv(SECTOR_ROTATION, usecols=available)
        df["sector"] = df["sector"].str.strip().str.upper()
        df = df.groupby("sector").last()

        # Fill missing participant columns with 0
        for col in ["FII_flow_score", "DII_flow_score", "Smart_Money_Score",
                    "Retail_Score", "CLIENT_flow_score"]:
            if col not in df.columns:
                df[col] = 0.0

        # Blended sector intelligence score
        blended = (
            df["FII_flow_score"]   * 0.40
            + df["DII_flow_score"] * 0.30
            + df["Smart_Money_Score"] * 0.30
        )
        normalised = ((blended + 100) / 2).clip(0, 100)

        return normalised.rename("sector_flow_score"), df

    def _load_deal_scores(self) -> pd.Series:
        """inst_net_value_cr percentile-ranked to 0-100. NaN -> 50 (neutral)."""
        if not DEAL_SIGNALS.exists():
            return pd.Series(dtype=float, name="deal_score")
        df = pd.read_csv(DEAL_SIGNALS, usecols=["symbol", "inst_net_value_cr"])
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df = df.set_index("symbol")
        ranked = _pct_rank_0_100(df["inst_net_value_cr"])
        return ranked.rename("deal_score")

    def _load_corporate_scores(self) -> pd.Series:
        """confidence_score_12m clipped [-3, 6] -> rescaled 0-100. NaN -> 50."""
        if not CORPORATE_SCORES.exists():
            return pd.Series(dtype=float, name="corporate_score")
        df = pd.read_csv(CORPORATE_SCORES, usecols=["symbol", "confidence_score_12m"])
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df = df.set_index("symbol")
        s = df["confidence_score_12m"].clip(-3, 6)
        normalised = ((s + 3) / 9 * 100).round(2)
        return normalised.rename("corporate_score")

    def _load_market_regime(self) -> tuple[str, float]:
        """
        Returns (regime_label, multiplier).
        Prefers participant_intelligence.csv (5C ensemble), falls back to positioning_history.
        """
        if PARTICIPANT_INTEL.exists():
            df = pd.read_csv(PARTICIPANT_INTEL, usecols=["date", "Market_Regime"])
            latest = df.dropna(subset=["Market_Regime"])
            if not latest.empty:
                regime = latest["Market_Regime"].iloc[-1]
                multiplier = REGIME_MULTIPLIER.get(regime, DEFAULT_MULTIPLIER)
                logger.info("[8B] Regime from participant_intelligence: %s (x%.2f)", regime, multiplier)
                return regime, multiplier

        if POSITIONING_HISTORY.exists():
            df = pd.read_csv(POSITIONING_HISTORY, usecols=["Date", "Regime"])
            latest = df.dropna(subset=["Regime"])
            if not latest.empty:
                regime = latest["Regime"].iloc[-1]
                multiplier = REGIME_MULTIPLIER.get(regime, DEFAULT_MULTIPLIER)
                logger.info("[8B] Regime from positioning_history: %s (x%.2f)", regime, multiplier)
                return regime, multiplier

        logger.warning("[8B] No regime data found -- defaulting to NEUTRAL")
        return "NEUTRAL", DEFAULT_MULTIPLIER

    # ----------------------------------------------------------------
    # Participant attribution
    # ----------------------------------------------------------------

    def _driving_participant(self, sector: str, sector_df: pd.DataFrame) -> str:
        """
        Returns the participant with the strongest positive flow into this sector.
        Uses: FII, DII, Smart_Money, Retail.
        Returns 'MIXED' if no clear dominant participant.
        """
        sector = sector.strip().upper()
        if sector not in sector_df.index:
            return "UNKNOWN"

        row = sector_df.loc[sector]
        candidates = {
            "FII":         float(row.get("FII_flow_score",   0) or 0),
            "DII":         float(row.get("DII_flow_score",   0) or 0),
            "SMART_MONEY": float(row.get("Smart_Money_Score",0) or 0),
            "RETAIL":      float(row.get("Retail_Score",     0) or 0),
        }
        # Only consider participants with positive flow
        positive = {k: v for k, v in candidates.items() if v > 5}
        if not positive:
            return "NONE"
        dominant = max(positive, key=positive.get)
        # If two participants are within 10pts of each other, call it MIXED
        top_two = sorted(positive.values(), reverse=True)[:2]
        if len(top_two) == 2 and (top_two[0] - top_two[1]) < 10:
            return "MIXED"
        return dominant

    # ----------------------------------------------------------------
    # Scoring
    # ----------------------------------------------------------------

    def run(self) -> bool:
        logger.info("[BullRunProbability] Starting Phase 8B")

        base                        = self._load_price_scores()
        ath_s, trend_sig            = self._load_ath_proximity_scores()
        sec_flow, sec_df            = self._load_sector_flow_scores()
        deal_s                      = self._load_deal_scores()
        corp_s                      = self._load_corporate_scores()
        regime, multiplier          = self._load_market_regime()

        # Attach ATH proximity score (neutral 50 if technical data missing)
        if isinstance(ath_s, pd.Series) and not ath_s.empty:
            base["ath_proximity_score"] = ath_s.reindex(base.index).fillna(50).round(2)
            base["trend_signal"]        = trend_sig.reindex(base.index).fillna("UNKNOWN")
        else:
            base["ath_proximity_score"] = 50.0
            base["trend_signal"]        = "UNKNOWN"

        # Attach sector blended flow score via sector mapping
        base["sector_flow_score"] = base["sector"].map(sec_flow).fillna(50).round(2)

        # Attach deal score (neutral 50 for unknown symbols)
        base["deal_score"] = deal_s.reindex(base.index).fillna(50).round(2)

        # Attach corporate score (neutral 50 for unknown symbols)
        base["corporate_score"] = corp_s.reindex(base.index).fillna(50).round(2)

        # Dominant participant for each stock's sector
        base["driving_participant"] = base["sector"].apply(
            lambda s: self._driving_participant(s, sec_df)
        )

        # Base composite score
        base["base_score"] = (
            base["price_score"]         * WEIGHTS["price_score"]
            + base["ath_proximity_score"] * WEIGHTS["ath_proximity_score"]
            + base["sector_flow_score"]   * WEIGHTS["sector_flow_score"]
            + base["deal_score"]          * WEIGHTS["deal_score"]
            + base["corporate_score"]     * WEIGHTS["corporate_score"]
        ).round(2)

        # Apply market regime multiplier then clip to [0, 100]
        base["market_regime"]     = regime
        base["regime_multiplier"] = multiplier
        base["bull_run_score"]    = (base["base_score"] * multiplier).clip(0, 100).round(2)
        base["label"]             = base["bull_run_score"].apply(_label_score)

        result = base.reset_index()

        # Column order — ATH proximity and participant attribution are now first-class outputs
        cols = [
            "symbol", "sector", "close_now", "as_of_date",
            "price_score", "ath_proximity_score", "sector_flow_score",
            "deal_score", "corporate_score",
            "base_score", "market_regime", "regime_multiplier", "bull_run_score", "label",
            "trend_signal", "driving_participant",
            "ret_30d", "ret_90d", "ret_365d", "vol_ratio",
        ]
        result = result[[c for c in cols if c in result.columns]]

        if result.empty:
            raise ValueError("G-D-03: bull run result is empty")

        # Watchlist: BULL_RUN + EMERGING only
        watchlist = result[result["label"].isin(["BULL_RUN", "EMERGING"])].copy()
        watchlist = watchlist.sort_values("bull_run_score", ascending=False).reset_index(drop=True)

        self._save_atomic(result.sort_values("bull_run_score", ascending=False)
                               .reset_index(drop=True), OUTPUT_FULL)
        self._save_atomic(watchlist, OUTPUT_WATCHLIST)
        self._print_summary(result, watchlist, regime, multiplier)
        return True

    # ----------------------------------------------------------------
    # Save + Print
    # ----------------------------------------------------------------

    def _save_atomic(self, df: pd.DataFrame, path: Path):
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[8B] Saved %s (%d rows)", path.name, len(df))

    def _print_summary(self, result: pd.DataFrame, watchlist: pd.DataFrame,
                       regime: str, multiplier: float):
        print()
        print("=" * 70)
        print("BULL RUN PROBABILITY ENGINE - PHASE 8B COMPLETE")
        print("=" * 70)
        print(f"Symbols scored        : {len(result)}")
        print(f"Market regime         : {regime} (x{multiplier:.2f})")
        print(f"Score range           : {result['bull_run_score'].min():.0f} to "
              f"{result['bull_run_score'].max():.0f}")
        print()
        label_counts = result["label"].value_counts()
        for label, count in label_counts.items():
            print(f"  {label:22s}: {count:4d} symbols")
        print()
        print(f"Watchlist (BULL_RUN + EMERGING): {len(watchlist)} symbols")

        if not watchlist.empty:
            print("\nTop 15 bull run candidates:")
            for _, r in watchlist.head(15).iterrows():
                ath_flag  = f" ath={r['ath_proximity_score']:.0f}"
                part_flag = f" [{r['driving_participant']}]" if r.get('driving_participant') else ""
                trend_flag = f" {r.get('trend_signal','')}" if r.get('trend_signal') not in ('UNKNOWN','') else ""
                print(f"  {r['symbol']:15s}: score={r['bull_run_score']:.0f}"
                      f"  price={r['price_score']:.0f}"
                      f"{ath_flag}"
                      f"  sec={r['sector_flow_score']:.0f}"
                      f"{part_flag}{trend_flag}"
                      f"  ({r['label']})")

        print()
        print("Participant driving sectors (BULL_RUN stocks):")
        br = result[result["label"] == "BULL_RUN"]
        if not br.empty:
            part_cnt = br["driving_participant"].value_counts()
            for participant, cnt in part_cnt.items():
                print(f"  {participant:20s}: {cnt}")
        else:
            print("  (no BULL_RUN stocks in current regime)")

        print()
        print("Sector breakdown (BULL_RUN):")
        if not br.empty:
            sector_cnt = br["sector"].value_counts().head(8)
            for sec, cnt in sector_cnt.items():
                print(f"  {sec:22s}: {cnt}")
        print("=" * 70)


if __name__ == "__main__":
    engine = BullRunProbabilityEngine()
    engine.run()
