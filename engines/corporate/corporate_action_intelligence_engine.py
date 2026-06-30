"""
Corporate Action Intelligence Engine
Phase 7C — Classify corporate actions (1999-2026) and score corporate confidence

Reads the already-downloaded corporate actions data from
  data/NSE/corporate_actions/<YYYY>.csv  (1999-2026, downloaded by Phase 2)

Classifies each EQ action into:
  DIVIDEND, BONUS, SPLIT, BUYBACK, RIGHTS, MERGER, AGM_EGM, OTHER

Extracts amounts/ratios from the subject text:
  Dividend: Rs amount per share
  Bonus: ratio (e.g. 1:2 → 0.5 bonus shares per existing)
  Split: new face value

Computes per-symbol Corporate Confidence Score (rolling 12M):
  BUYBACK  : +3  (management confident, buying own stock)
  BONUS    : +2  (rewarding shareholders, confident in future)
  SPLIT    : +1  (expects retail interest, confidence signal)
  DIVIDEND : +0.5 (positive but may signal limited reinvestment)
  RIGHTS   : -0.5 (dilution — needs capital)
  MERGER   : 0   (neutral — outcome uncertain)
  AGM_EGM  : 0   (routine)

Outputs:
  data/intelligence/corporate_action_signals.csv    — classified history
  data/intelligence/corporate_confidence_scores.csv — per-symbol rolling 12M score
"""

import re
import shutil
from pathlib import Path
import sys

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("corporate_action_intelligence")

CORP_ACTIONS_DIR = cfg.DATA_DIR / "NSE" / "corporate_actions"
INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
SIGNALS_OUTPUT   = INTELLIGENCE_DIR / "corporate_action_signals.csv"
SCORES_OUTPUT    = INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
CLASSIFICATION   = cfg.DATA_DIR / "reference" / "company_classification_v4.csv"

# Confidence weights per action type
CONFIDENCE_WEIGHTS = {
    "BUYBACK":  3.0,
    "BONUS":    2.0,
    "SPLIT":    1.0,
    "DIVIDEND": 0.5,
    "RIGHTS":  -0.5,
    "MERGER":   0.0,
    "AGM_EGM":  0.0,
    "OTHER":    0.0,
}

ROLLING_MONTHS = 12


def _classify_action(subject: str) -> str:
    if not subject or pd.isna(subject):
        return "OTHER"
    s = str(subject).strip().lower()
    if any(kw in s for kw in ["buy back", "buyback"]):
        return "BUYBACK"
    if "bonus" in s:
        return "BONUS"
    if any(kw in s for kw in ["split", "sub-division", "sub division"]):
        return "SPLIT"
    if any(kw in s for kw in ["right", "rights"]):
        return "RIGHTS"
    if any(kw in s for kw in ["amalgam", "merger", "scheme of", "acquisition"]):
        return "MERGER"
    if any(kw in s for kw in ["agm", "egm", "annual general", "extra ordinary", "extraordinary"]):
        return "AGM_EGM"
    if any(kw in s for kw in ["dividend", "div ", "div-", "div."]):
        return "DIVIDEND"
    return "OTHER"


def _extract_dividend_amount(subject: str) -> float:
    """Extract dividend amount in Rs from subject string."""
    if not subject:
        return np.nan
    patterns = [
        r'rs\.?\s*([\d\.]+)\s*per\s*share',
        r're\.?\s*([\d\.]+)\s*per\s*share',
        r'rs\.?\s*([\d\.]+)',
        r'([\d\.]+)\s*%.*dividend',
    ]
    for pat in patterns:
        m = re.search(pat, str(subject).lower())
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return np.nan


def _extract_bonus_ratio(subject: str) -> float:
    """Extract bonus ratio (new shares per existing) from subject like 'Bonus 1:2'."""
    m = re.search(r'bonus\s+(\d+)\s*:\s*(\d+)', str(subject).lower())
    if m:
        try:
            numerator   = int(m.group(1))
            denominator = int(m.group(2))
            return round(numerator / denominator, 4) if denominator else np.nan
        except ValueError:
            pass
    return np.nan


def _extract_split_ratio(subject: str) -> str:
    """Extract new face value from split subject like 'Split from Rs 10 to Rs 2'."""
    m = re.search(r'to\s+r[se]\.?\s*([\d\.]+)', str(subject).lower())
    if m:
        return m.group(1)
    return ""


class CorporateActionIntelligenceEngine:
    """
    Phase 7C — processes all NSE corporate actions data, classifies and scores.
    Full rebuild on each run (fast — pure CSV processing, no API calls).
    """

    def __init__(self):
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.sector_map: dict[str, str] = {}

    def run(self) -> bool:
        logger.info("[CorporateActionIntelligence] Starting Phase 7C")
        self._load_sector_map()

        raw = self._load_all_actions()
        if raw.empty:
            logger.error("[7C] No corporate actions data found in %s", CORP_ACTIONS_DIR)
            return False

        signals = self._classify_and_enrich(raw)
        scores  = self._compute_confidence_scores(signals)

        self._save_atomic(signals, SIGNALS_OUTPUT)
        self._save_atomic(scores,  SCORES_OUTPUT)
        self._print_summary(signals, scores)
        return True

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_sector_map(self):
        if not CLASSIFICATION.exists():
            return
        df = pd.read_csv(CLASSIFICATION, usecols=["SYMBOL", "SECTOR"])
        df["SYMBOL"] = df["SYMBOL"].str.strip().str.upper()
        self.sector_map = dict(zip(df["SYMBOL"], df["SECTOR"]))

    def _load_all_actions(self) -> pd.DataFrame:
        if not CORP_ACTIONS_DIR.exists():
            return pd.DataFrame()
        all_dfs = []
        files = sorted(CORP_ACTIONS_DIR.glob("*.csv"))
        for f in progress(files, desc="Loading action files"):
            if not f.stem.isdigit():
                continue
            try:
                df = pd.read_csv(f)
                all_dfs.append(df)
            except Exception as exc:
                logger.warning("[7C] Cannot read %s: %s", f.name, exc)

        if not all_dfs:
            return pd.DataFrame()
        combined = pd.concat(all_dfs, ignore_index=True)
        logger.info("[7C] Loaded %d corporate action rows from %d files",
                    len(combined), len(all_dfs))
        return combined

    # ------------------------------------------------------------------
    # Classify
    # ------------------------------------------------------------------
    def _classify_and_enrich(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = raw.copy()
        df.columns = df.columns.str.strip()

        # G-S-01: EQ series only
        if "series" in df.columns:
            df = df[df["series"].str.strip().str.upper() == "EQ"].copy()

        # Normalise key fields
        df["symbol"]  = df.get("symbol", "").astype(str).str.strip().str.upper()
        df["company"] = df.get("comp", "").astype(str).str.strip()
        df["subject"] = df.get("subject", "").astype(str).str.strip()

        # Parse ex_date
        def _parse_date(val):
            try:
                return pd.to_datetime(str(val), dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                return ""

        df["ex_date"] = df.get("exDate", "").apply(_parse_date)
        df["rec_date"] = df.get("recDate", "").apply(_parse_date)

        # Classify
        df["action_type"]    = df["subject"].apply(_classify_action)
        df["dividend_rs"]    = df.apply(
            lambda r: _extract_dividend_amount(r["subject"]) if r["action_type"] == "DIVIDEND" else np.nan, axis=1
        )
        df["bonus_ratio"]    = df.apply(
            lambda r: _extract_bonus_ratio(r["subject"]) if r["action_type"] == "BONUS" else np.nan, axis=1
        )
        df["split_new_fv"]   = df.apply(
            lambda r: _extract_split_ratio(r["subject"]) if r["action_type"] == "SPLIT" else "", axis=1
        )
        df["confidence_pts"] = df["action_type"].map(CONFIDENCE_WEIGHTS).fillna(0.0)
        df["sector"]         = df["symbol"].map(self.sector_map).fillna("OTHER")

        keep = ["ex_date", "rec_date", "symbol", "company", "sector", "subject",
                "action_type", "dividend_rs", "bonus_ratio", "split_new_fv", "confidence_pts"]
        df = df[[c for c in keep if c in df.columns]]
        df = df[df["ex_date"] != ""].sort_values("ex_date").reset_index(drop=True)
        logger.info("[7C] Classified %d EQ actions", len(df))
        return df

    # ------------------------------------------------------------------
    # Confidence scores
    # ------------------------------------------------------------------
    def _compute_confidence_scores(self, signals: pd.DataFrame) -> pd.DataFrame:
        if signals.empty:
            return pd.DataFrame()

        signals["ex_date_dt"] = pd.to_datetime(signals["ex_date"], errors="coerce")
        cutoff = signals["ex_date_dt"].max() - pd.DateOffset(months=ROLLING_MONTHS)
        recent = signals[signals["ex_date_dt"] >= cutoff].copy()

        def agg_symbol(grp):
            return pd.Series({
                "confidence_score_12m": grp["confidence_pts"].sum(),
                "action_count_12m":     len(grp),
                "buyback_count":        (grp["action_type"] == "BUYBACK").sum(),
                "bonus_count":          (grp["action_type"] == "BONUS").sum(),
                "dividend_count":       (grp["action_type"] == "DIVIDEND").sum(),
                "split_count":          (grp["action_type"] == "SPLIT").sum(),
                "rights_count":         (grp["action_type"] == "RIGHTS").sum(),
                "sector":               grp["sector"].iloc[0],
                "last_action_date":     grp["ex_date"].max(),
                "last_action_type":     grp.loc[grp["ex_date"].idxmax(), "action_type"],
            })

        if recent.empty:
            return pd.DataFrame()

        scores = recent.groupby("symbol").apply(agg_symbol).reset_index()

        def _label(score: float) -> str:
            if score >= 6:
                return "VERY_HIGH"
            if score >= 3:
                return "HIGH"
            if score >= 1:
                return "MODERATE"
            if score >= 0:
                return "NEUTRAL"
            return "CONCERN"

        scores["confidence_label"] = scores["confidence_score_12m"].apply(_label)
        scores["as_of_date"]       = signals["ex_date"].max()
        scores = scores.sort_values("confidence_score_12m", ascending=False).reset_index(drop=True)
        return scores

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[7C] Saved %s (%d rows)", path.name, len(df))

    def _print_summary(self, signals: pd.DataFrame, scores: pd.DataFrame):
        print()
        print("=" * 65)
        print("CORPORATE ACTION INTELLIGENCE ENGINE - PHASE 7C COMPLETE")
        print("=" * 65)
        if not signals.empty:
            print(f"Total EQ actions (all years) : {len(signals)}")
            print(f"Date range : {signals['ex_date'].min()} to {signals['ex_date'].max()}")
            print("Action type breakdown:")
            for atype, cnt in signals["action_type"].value_counts().items():
                w = CONFIDENCE_WEIGHTS.get(atype, 0)
                print(f"  {atype:12s}: {cnt:6d}  (confidence weight {w:+.1f})")
        if not scores.empty:
            print()
            print(f"Symbol confidence scores (12M rolling): {len(scores)}")
            print("Top 8 by corporate confidence:")
            for _, r in scores.head(8).iterrows():
                print(f"  {r['symbol']:15s}: score={r['confidence_score_12m']:+.1f}  "
                      f"label={r['confidence_label']:12s}  "
                      f"buyback={int(r['buyback_count'])}  bonus={int(r['bonus_count'])}")
        print("=" * 65)


if __name__ == "__main__":
    engine = CorporateActionIntelligenceEngine()
    engine.run()
