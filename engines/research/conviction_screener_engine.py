"""
Conviction Screener Engine
Phase SA-1 D3 -- The investment screen: highest-conviction stocks ranked by
an EFFICACY-WEIGHTED composite, with hard investability gates.

What makes this different from the Phase 23 screener and the raw scores:
  1. WEIGHTS FOLLOW EVIDENCE: factor weights are derived from the measured
     Information Coefficients in signal_efficacy.csv (Phase SA-1 D1), not
     hand-picked. Factors whose measured IC is negative get floor weight;
     the platform's differentiated (not-yet-measurable) signals keep a
     capped prior weight until scores_history accumulates.
  2. INVESTABILITY GATES (hard filters, applied before any ranking):
       - liquidity: 20d average traded value >= MIN_ADV_CR
       - price     >= MIN_PRICE (penny-stock exclusion)
       - data coverage: bull-run + technical + ML scores all present
       - not MARKDOWN-labelled
  3. EVIDENCE PER PICK: every candidate lists its top supporting factors
     and its single biggest risk -- both sides, always.

Reads (read-only, G-D-01):
  data/intelligence/signal_efficacy.csv
  data/intelligence/bull_run_probability.csv
  data/intelligence/technical_indicators.csv
  data/intelligence/ml_scores_combined.csv
  data/intelligence/trade_conviction_scores.csv
  data/intelligence/participant_intelligence.csv   (regime)

Writes (atomic, G-D-02):
  data/intelligence/conviction_screener.csv

Run:  py -3.11 -m engines.research.conviction_screener_engine
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

EFFICACY_CSV   = cfg.INTELLIGENCE_DIR / "signal_efficacy.csv"
BULL_RUN_CSV   = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
TECHNICAL_CSV  = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
ML_CSV         = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"
CONVICTION_CSV = cfg.INTELLIGENCE_DIR / "trade_conviction_scores.csv"
PARTICIPANT_CSV= cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"

OUTPUT_CSV     = cfg.INTELLIGENCE_DIR / "conviction_screener.csv"

# ── Investability gates ───────────────────────────────────────────────────────
MIN_ADV_CR   = 1.0     # 20d avg traded value >= 1 crore INR/day
MIN_PRICE    = 20.0    # exclude penny stocks
MIN_UNIVERSE = 50      # abort if fewer symbols survive data-coverage checks

# Factors measured by the efficacy engine map to these live columns.
# 90d horizon is the investment horizon of this screen.
MEASURED_FACTOR_MAP = {
    "prox_52w_high": "prox_52w_high_score",
    "dma_trend":     "dma_trend_score",
    "ret_90d":       "price_score",       # platform momentum composite
    "vol_surge":     "vol_surge_score",
}
# Platform signals not yet measurable (prior weight, capped, until
# scores_history.parquet accumulates ~6 months)
PRIOR_FACTORS = {
    "ml_bull_run_score": 0.15,
    "deal_score":        0.10,
    "sector_flow_score": 0.10,
}
WEIGHT_FLOOR = 0.03   # measured factor with negative IC keeps a small floor

REGIME_MULT = {
    "STRONG_ACCUMULATION": 1.15, "ACCUMULATION": 1.08, "NEUTRAL": 1.0,
    "DISTRIBUTION": 0.90, "STRONG_DISTRIBUTION": 0.80,
}

COLS = [
    "rank", "symbol", "sector", "close", "conviction", "tier",
    "supporting_evidence", "primary_risk",
    "bull_run_score", "ml_bull_run_score", "prox_52w_high_pct",
    "trend_signal", "adv_20d_cr", "regime", "as_of_date",
]


class ConvictionScreenerEngine:
    """Efficacy-weighted, liquidity-gated investment candidate ranking."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()

    # ── Entry ─────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[ConvictionScreener] Starting")
        weights = self._efficacy_weights()
        base = self._assemble_universe()
        if base is None or len(base) < MIN_UNIVERSE:
            logger.warning("[ConvictionScreener] Aborted -- universe too small after gates")
            return False

        regime, mult = self._regime()
        scored = self._score(base, weights, mult, regime)
        self._save(scored)
        logger.info("[ConvictionScreener] Complete -- %d candidates (%d HIGH tier), regime %s",
                    len(scored), int((scored["tier"] == "HIGH").sum()), regime)
        return True

    # ── Efficacy-derived weights ──────────────────────────────────────────────

    def _efficacy_weights(self) -> dict[str, float]:
        """Weight measured factors by their 90d IC (floor for negative IC),
        keep capped priors for unmeasured platform signals, normalize to 1."""
        raw: dict[str, float] = {}
        if EFFICACY_CSV.exists():
            eff = pd.read_csv(EFFICACY_CSV)
            eff = eff[(eff["status"] == "MEASURED") & (eff["horizon_days"] == 90)]
            for factor, live_col in MEASURED_FACTOR_MAP.items():
                row = eff[eff["factor"] == factor]
                if row.empty:
                    raw[live_col] = WEIGHT_FLOOR
                    continue
                ic = float(row.iloc[0]["ic_mean"] or 0)
                spread = float(row.iloc[0]["decile_spread_pct"] or 0)
                # Blend IC and decile spread; negative evidence -> floor
                signal_strength = max(ic, 0) * 10 + max(spread, 0) / 100 * 4
                raw[live_col] = max(signal_strength, WEIGHT_FLOOR)
        else:
            logger.warning("[ConvictionScreener] No efficacy file -- equal weights for measured factors")
            for live_col in MEASURED_FACTOR_MAP.values():
                raw[live_col] = 0.10

        for col, w in PRIOR_FACTORS.items():
            raw[col] = w

        total = sum(raw.values())
        weights = {k: v / total for k, v in raw.items()}
        logger.info("[ConvictionScreener] Weights: %s",
                    {k: round(v, 3) for k, v in sorted(weights.items(), key=lambda x: -x[1])})
        return weights

    # ── Universe assembly + gates ─────────────────────────────────────────────

    def _assemble_universe(self) -> pd.DataFrame | None:
        for p in (BULL_RUN_CSV, TECHNICAL_CSV, ML_CSV):
            if not p.exists():
                logger.warning("[ConvictionScreener] Missing input %s", p.name)
                return None

        bull = pd.read_csv(BULL_RUN_CSV)
        tech = pd.read_csv(TECHNICAL_CSV)
        ml   = pd.read_csv(ML_CSV)
        for df in (bull, tech, ml):
            df["symbol"] = df["symbol"].str.strip().str.upper()
        # technical_indicators is the fresher source for these shared columns
        bull = bull.drop(columns=[c for c in ("close_now", "trend_signal") if c in bull.columns])

        base = bull.merge(
            tech[["symbol", "close_now", "prox_52w_high", "vs_dma_50", "trend_signal",
                  "vol_20d_avg", "rsi", "adx", "bb_squeeze"]],
            on="symbol", how="inner",
        ).merge(
            ml[["symbol", "ml_bull_run_score", "accumulation_score"]],
            on="symbol", how="left",
        )

        if CONVICTION_CSV.exists():
            conv = pd.read_csv(CONVICTION_CSV, usecols=["symbol", "score", "entry_low", "entry_high", "stop_loss"])
            conv["symbol"] = conv["symbol"].str.strip().str.upper()
            conv = conv.rename(columns={"score": "trade_conviction"})
            base = base.merge(conv, on="symbol", how="left")

        # numerics
        for c in ["close_now", "prox_52w_high", "vs_dma_50", "vol_20d_avg",
                  "bull_run_score", "ml_bull_run_score", "sector_flow_score",
                  "deal_score", "rsi", "adx"]:
            if c in base.columns:
                base[c] = pd.to_numeric(base[c], errors="coerce")

        # ── HARD GATES (institutional investability) ──────────────────────────
        n0 = len(base)
        base["adv_20d_cr"] = base["close_now"] * base["vol_20d_avg"] / 1e7
        base = base[base["adv_20d_cr"] >= MIN_ADV_CR]           # liquidity
        base = base[base["close_now"] >= MIN_PRICE]             # penny exclusion
        # Taxonomy fix (Phase V-DATA-2): AVOID was replaced by MARKDOWN a
        # while back -- this "red flag" exclusion has been a silent no-op
        # (bull_run_probability.csv has never had an "AVOID" value in the
        # current taxonomy), meaning MARKDOWN-labelled stocks were never
        # actually being filtered out of the conviction screener universe.
        base = base[base["label"] != "MARKDOWN"]                # platform red flag
        base = base.dropna(subset=["bull_run_score", "prox_52w_high", "vs_dma_50"])
        logger.info("[ConvictionScreener] Gates: %d -> %d symbols "
                    "(liquidity >= %.1f cr/day, price >= %.0f, coverage)",
                    n0, len(base), MIN_ADV_CR, MIN_PRICE)
        return base

    def _regime(self) -> tuple[str, float]:
        regime = "NEUTRAL"
        try:
            if PARTICIPANT_CSV.exists():
                p = pd.read_csv(PARTICIPANT_CSV)
                regime = str(p.sort_values("date").iloc[-1].get("Market_Regime", "NEUTRAL"))
        except Exception:
            pass
        return regime, REGIME_MULT.get(regime, 1.0)

    # ── Scoring ───────────────────────────────────────────────────────────────

    @staticmethod
    def _pct_rank(s: pd.Series) -> pd.Series:
        return s.rank(pct=True, na_option="keep") * 100.0

    def _score(self, base: pd.DataFrame, weights: dict, mult: float, regime: str) -> pd.DataFrame:
        d = base.copy()

        # Build the live factor columns the weights refer to (all 0-100 ranks)
        d["prox_52w_high_score"] = self._pct_rank(d["prox_52w_high"])       # nearer high = higher
        d["dma_trend_score"]     = self._pct_rank(d["vs_dma_50"])
        d["vol_surge_score"]     = self._pct_rank(d["vol_20d_avg"] / d["vol_20d_avg"].median())
        # price_score / ml_bull_run_score / deal_score / sector_flow_score already 0-100

        composite = pd.Series(0.0, index=d.index)
        for col, w in weights.items():
            vals = pd.to_numeric(d.get(col), errors="coerce")
            composite += vals.fillna(50.0) * w      # missing = neutral, never bonus
        d["conviction"] = (composite * mult).clip(0, 100).round(1)

        d["tier"] = np.select(
            [d["conviction"] >= 70, d["conviction"] >= 58],
            ["HIGH", "MEDIUM"], default="WATCH",
        )

        # Evidence + risk per row (both sides, always)
        ev, risk = [], []
        for _, r in d.iterrows():
            plus = []
            # prox_52w_high is in PERCENT (e.g. -12.5 = 12.5% below the high)
            if (r.get("prox_52w_high") if pd.notna(r.get("prox_52w_high")) else -100) > -5.0:
                plus.append("within 5% of 52w high (strongest measured factor)")
            if str(r.get("trend_signal", "")) in ("STRONG_UPTREND", "UPTREND"):
                plus.append(f"{r['trend_signal'].replace('_', ' ').lower()}")
            if (r.get("ml_bull_run_score") or 0) >= 70:
                plus.append(f"ML bull score {r['ml_bull_run_score']:.0f}")
            if (r.get("deal_score") or 50) >= 70:
                plus.append("institutional buying (deals)")
            if (r.get("sector_flow_score") or 50) >= 65:
                plus.append("sector rotating in")
            if str(r.get("bb_squeeze", "")).lower() in ("true", "1"):
                plus.append("volatility squeeze (breakout setup)")
            ev.append("; ".join(plus[:3]) if plus else "broad composite strength only")

            minus = []
            if (r.get("rsi") or 50) >= 78:
                minus.append(f"overbought (RSI {r['rsi']:.0f})")
            if (r.get("prox_52w_high") if pd.notna(r.get("prox_52w_high")) else 0) < -35.0:
                minus.append("35%+ below its 52w high -- long repair needed")
            if (r.get("adv_20d_cr") or 99) < 3:
                minus.append("thin liquidity -- use TWAP slices")
            if (r.get("ml_bull_run_score") or 50) < 40:
                minus.append("ML model disagrees")
            if regime in ("DISTRIBUTION", "STRONG_DISTRIBUTION"):
                minus.append("market regime is distribution")
            risk.append(minus[0] if minus else "none flagged -- normal market risk applies")
        d["supporting_evidence"] = ev
        d["primary_risk"] = risk
        d["regime"] = regime

        d = d.sort_values("conviction", ascending=False).reset_index(drop=True)
        d["rank"] = d.index + 1

        out = pd.DataFrame({
            "rank":                d["rank"],
            "symbol":              d["symbol"],
            "sector":              d.get("sector", ""),
            "close":               d["close_now"].round(2),
            "conviction":          d["conviction"],
            "tier":                d["tier"],
            "supporting_evidence": d["supporting_evidence"],
            "primary_risk":        d["primary_risk"],
            "bull_run_score":      d["bull_run_score"].round(1),
            "ml_bull_run_score":   d["ml_bull_run_score"].round(1),
            "prox_52w_high_pct":   d["prox_52w_high"].round(1),   # source is already percent
            "trend_signal":        d["trend_signal"],
            "adv_20d_cr":          d["adv_20d_cr"].round(2),
            "regime":              d["regime"],
            "as_of_date":          self.run_date,
        }, columns=COLS)
        return out

    def _save(self, df: pd.DataFrame) -> None:
        if df.empty:                                            # G-D-03
            raise ValueError("Refusing to write empty screener output")
        tmp = OUTPUT_CSV.with_suffix(".tmp.csv")                # G-D-02
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_CSV))


if __name__ == "__main__":
    ok = ConvictionScreenerEngine().run()
    sys.exit(0 if ok else 1)
