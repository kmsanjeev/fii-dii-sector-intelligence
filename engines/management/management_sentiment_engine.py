"""
Management Sentiment Engine -- Phase 16C
Scores management quality and sentiment from:
  - Holding trend signals (promoter stake change)
  - Announcement patterns (dividends, buybacks, AGM tone)
  - Claude API tone scoring of board meeting text (ANTHROPIC_API_KEY required)

Output: data/NSE/shareholding/management_sentiment.csv

Columns:
  symbol, holding_signal, announcement_score, ai_tone_score,
  management_score (0-100), management_label, as_of_date

Management labels:
  HIGH_CONVICTION   : score >= 75 (promoter buying + FII in + positive announcements)
  POSITIVE          : score >= 55
  NEUTRAL           : score >= 35
  WEAK              : score <  35 (promoter selling or negative signals)

Security:
  ANTHROPIC_API_KEY ALWAYS from os.getenv() -- NEVER hardcoded.
  If not set, AI tone scoring is skipped (engine still runs with rule-based score).

Guardrails:
  - G-D-02: atomic writes
  - G-D-03: no empty DataFrame writes
  - G-A-01: rate limiting for Claude API calls
"""

import os
import time
import shutil
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger(__name__)

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
HOLDING_TRENDS  = SHAREHOLDING_DIR / "holding_trends.csv"
ANNOUNCEMENTS   = SHAREHOLDING_DIR / "board_announcements.csv"
OUTPUT_PATH     = SHAREHOLDING_DIR / "management_sentiment.csv"

# Signal -> score weights for rule-based component
HOLDING_SIGNAL_SCORES = {
    "STRONG_PROMOTER_FII_BUY":   90,
    "FII_DII_ACCUMULATION":      75,
    "STRONG_PROMOTER_BUY":       70,
    "FII_ACCUMULATION":          60,
    "DII_ACCUMULATION":          55,
    "STABLE":                    50,
    "FII_DII_DIVERGENCE":        40,
    "PROMOTER_SELLING":          20,
}

ANNOUNCEMENT_SCORES = {
    "BUYBACK":     80,
    "DIVIDEND":    70,
    "BONUS":       65,
    "ACQUISITION": 60,
    "BOARD_MEETING": 50,
    "AGM_EGM":     50,
    "FUNDRAISE":   45,
    "STOCK_SPLIT": 55,
    "OTHER":       50,
}


class ManagementSentimentEngine:
    """
    Combines holding trend signals + announcement patterns + optional AI tone.
    """

    def __init__(self, use_ai: bool = True):
        SHAREHOLDING_DIR.mkdir(parents=True, exist_ok=True)
        self.use_ai = use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
        if use_ai and not os.getenv("ANTHROPIC_API_KEY"):
            logger.info("[MgmtSentiment] ANTHROPIC_API_KEY not set -- skipping AI tone scoring")

    def run(self) -> bool:
        logger.info("[MgmtSentiment] Starting management sentiment scoring")

        # Load inputs
        holding_df = pd.read_csv(HOLDING_TRENDS) if HOLDING_TRENDS.exists() else pd.DataFrame()
        ann_df     = pd.read_csv(ANNOUNCEMENTS) if ANNOUNCEMENTS.exists() else pd.DataFrame()

        if holding_df.empty and ann_df.empty:
            logger.warning("[MgmtSentiment] No holding trends or announcements data available")
            return False

        symbols = self._get_symbols(holding_df, ann_df)
        rows = []
        for symbol in progress(symbols, desc="Scoring symbols"):
            row = self._score_symbol(symbol, holding_df, ann_df)
            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty:
            return False

        if self.use_ai:
            df = self._apply_ai_tone(df, ann_df)

        df = self._finalize_scores(df)
        self._save(df)
        logger.info(f"[MgmtSentiment] Complete: {len(df)} symbols")
        return True

    def _get_symbols(self, holding_df: pd.DataFrame, ann_df: pd.DataFrame) -> list[str]:
        symbols = set()
        if not holding_df.empty and "symbol" in holding_df.columns:
            symbols.update(holding_df["symbol"].unique())
        if not ann_df.empty and "symbol" in ann_df.columns:
            symbols.update(ann_df["symbol"].unique())
        return sorted(symbols)

    def _score_symbol(self, symbol: str, holding_df: pd.DataFrame, ann_df: pd.DataFrame) -> dict:
        # Holding signal score
        holding_signal = "STABLE"
        holding_score = 50.0
        if not holding_df.empty and "symbol" in holding_df.columns:
            sym_holdings = holding_df[holding_df["symbol"] == symbol]
            if not sym_holdings.empty and "conviction_signal" in sym_holdings.columns:
                latest_signal = sym_holdings.sort_values("period").iloc[-1]["conviction_signal"]
                holding_signal = str(latest_signal)
                holding_score = float(HOLDING_SIGNAL_SCORES.get(holding_signal, 50))

        # Announcement score (average of last 4 announcements)
        ann_score = 50.0
        recent_anns: list[str] = []
        if not ann_df.empty and "symbol" in ann_df.columns:
            sym_anns = ann_df[ann_df["symbol"] == symbol]
            if not sym_anns.empty and "announcement_type" in sym_anns.columns:
                recent_anns = sym_anns.sort_values("date", ascending=False).head(4)["announcement_type"].tolist()
                if recent_anns:
                    ann_score = sum(ANNOUNCEMENT_SCORES.get(a, 50) for a in recent_anns) / len(recent_anns)

        return {
            "symbol": symbol,
            "holding_signal": holding_signal,
            "holding_score": round(holding_score, 1),
            "announcement_types": "|".join(recent_anns[:4]) if recent_anns else "",
            "announcement_score": round(ann_score, 1),
            "ai_tone_score": None,  # filled in by _apply_ai_tone
        }

    def _apply_ai_tone(self, df: pd.DataFrame, ann_df: pd.DataFrame) -> pd.DataFrame:
        """
        Use Claude API to score tone of board meeting announcement text.
        Only runs when ANTHROPIC_API_KEY is set.
        Processes top 50 symbols by preliminary combined score to stay within budget.
        """
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Get text for top candidates
        if ann_df.empty or "symbol" not in ann_df.columns:
            return df

        df["_pre_score"] = 0.5 * df["holding_score"] + 0.5 * df["announcement_score"]
        top = df.nlargest(50, "_pre_score")

        ai_scores: dict[str, float] = {}
        for _, row in top.iterrows():
            symbol = row["symbol"]
            sym_anns = ann_df[ann_df["symbol"] == symbol]
            if sym_anns.empty or "text_snippet" not in sym_anns.columns:
                continue

            # Combine last 3 announcement snippets
            text = " ".join(sym_anns.sort_values("date", ascending=False)
                           .head(3)["text_snippet"].tolist())
            if not text.strip():
                continue

            try:
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",  # cheap, fast for scoring
                    max_tokens=64,
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Score management quality from 0-100 based on this announcement text. "
                            f"Respond with ONLY a number. "
                            f"100=excellent management (buybacks, dividends, acquisitions). "
                            f"50=neutral. 0=poor (selling, dilution). Text: {text[:500]}"
                        )
                    }],
                )
                score_text = resp.content[0].text.strip()
                ai_score = float(score_text.split()[0])
                ai_scores[symbol] = max(0, min(100, ai_score))
                logger.debug(f"[MgmtSentiment] AI tone {symbol}: {ai_score}")
            except Exception as e:
                logger.debug(f"[MgmtSentiment] AI scoring failed {symbol}: {e}")

            time.sleep(cfg.API_DELAY)

        df["ai_tone_score"] = df["symbol"].map(ai_scores)
        df = df.drop(columns=["_pre_score"], errors="ignore")
        return df

    def _finalize_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute final management_score from components."""
        def composite(row):
            h = float(row.get("holding_score") or 50)
            a = float(row.get("announcement_score") or 50)
            ai = row.get("ai_tone_score")

            if ai and not pd.isna(ai):
                return round(0.4 * h + 0.25 * a + 0.35 * float(ai), 1)
            return round(0.6 * h + 0.4 * a, 1)

        df["management_score"] = df.apply(composite, axis=1).clip(0, 100)
        df["management_label"] = df["management_score"].apply(_label)
        df["as_of_date"] = pd.Timestamp.now().date().isoformat()
        return df

    def _save(self, df: pd.DataFrame):
        if df.empty:
            return
        out_cols = [
            "symbol", "holding_signal", "holding_score", "announcement_score",
            "ai_tone_score", "management_score", "management_label",
            "announcement_types", "as_of_date",
        ]
        out_df = df[[c for c in out_cols if c in df.columns]]
        tmp = OUTPUT_PATH.with_suffix(".tmp.csv")
        out_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))
        logger.info(f"[MgmtSentiment] Saved {len(out_df)} symbols -> {OUTPUT_PATH}")


def _label(score: float) -> str:
    if score >= 75:
        return "HIGH_CONVICTION"
    if score >= 55:
        return "POSITIVE"
    if score >= 35:
        return "NEUTRAL"
    return "WEAK"


if __name__ == "__main__":
    engine = ManagementSentimentEngine(use_ai=True)
    engine.run()
    if OUTPUT_PATH.exists():
        df = pd.read_csv(OUTPUT_PATH)
        print(f"Management sentiment: {len(df)} symbols")
        print(df["management_label"].value_counts())
        top = df.nlargest(10, "management_score")
        print(top[["symbol", "holding_signal", "management_score", "management_label"]].to_string())
