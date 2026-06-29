"""
Daily Digest — Phase 9D
Builds the 18:30 IST daily summary from all intelligence layers.
Outputs a single formatted Telegram message.
"""

import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Intelligence sources ──────────────────────────────────────────────────────

PARTICIPANT_INTEL   = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
BULL_RUN_WATCHLIST  = cfg.INTELLIGENCE_DIR / "bull_run_watchlist.csv"
SECTOR_ROTATION     = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
DEAL_SIGNALS        = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
FLOW_SCORES         = cfg.INTELLIGENCE_DIR / "participant_flow_scores.csv"


class DailyDigest:
    """Assembles and returns the 18:30 IST daily intelligence summary."""

    def build(self) -> str:
        today = date.today().strftime("%Y-%m-%d")
        parts = [
            f"<b>CAPITAL FLOW INTELLIGENCE</b>",
            f"<i>Daily Digest | {today}</i>",
            "",
        ]

        parts.extend(self._market_regime_section())
        parts.extend(self._participant_flow_section())
        parts.extend(self._sector_rotation_section())
        parts.extend(self._watchlist_section())
        parts.extend(self._deals_section())

        text = "\n".join(parts)
        logger.info(f"[DailyDigest] Built digest: {len(text)} chars")
        return text

    # ── Market regime ─────────────────────────────────────────────────────────

    def _market_regime_section(self) -> list:
        if not PARTICIPANT_INTEL.exists():
            return ["[Market Regime] Data not available", ""]

        df = pd.read_csv(PARTICIPANT_INTEL)
        df = df.dropna(subset=["Market_Regime"]).sort_values("date")
        if df.empty:
            return ["[Market Regime] No data", ""]

        latest = df.iloc[-1]
        regime = str(latest["Market_Regime"])
        smart_money = float(latest.get("Smart_Money_Score", 0))
        fii_conviction = float(latest.get("FII_conviction", 0))
        data_date = str(latest["date"])

        sm_dir = "+" if smart_money > 0 else ""
        return [
            f"<b>MARKET REGIME: {regime}</b>",
            f"Smart Money Score: {sm_dir}{smart_money:.1f}",
            f"FII Conviction: {fii_conviction:.0f}%",
            f"Data: {data_date}",
            "",
        ]

    # ── Participant flows ─────────────────────────────────────────────────────

    def _participant_flow_section(self) -> list:
        if not PARTICIPANT_INTEL.exists():
            return []

        df = pd.read_csv(PARTICIPANT_INTEL, usecols=[
            "date", "FII_flow_score", "DII_flow_score",
            "PRO_flow_score", "CLIENT_flow_score"
        ])
        df = df.sort_values("date")
        if df.empty:
            return []

        latest = df.iloc[-1]

        def fmt(score):
            v = float(score) if pd.notna(score) else 0.0
            prefix = "+" if v > 0 else ""
            return f"{prefix}{v:.1f}"

        return [
            "<b>PARTICIPANT FLOWS</b>",
            f"FII: {fmt(latest['FII_flow_score'])}  |  DII: {fmt(latest['DII_flow_score'])}",
            f"PRO: {fmt(latest['PRO_flow_score'])}  |  CLIENT: {fmt(latest['CLIENT_flow_score'])}",
            "",
        ]

    # ── Sector rotation ───────────────────────────────────────────────────────

    def _sector_rotation_section(self) -> list:
        if not SECTOR_ROTATION.exists():
            return []

        df = pd.read_csv(SECTOR_ROTATION, usecols=["sector", "rotation_signal", "combined_score"])

        early = df[df["rotation_signal"] == "EARLY_ROTATION"].sort_values(
            "combined_score", ascending=False
        ).head(3)
        leading = df[df["rotation_signal"] == "LEADING"].sort_values(
            "combined_score", ascending=False
        ).head(3)

        lines = ["<b>SECTOR SIGNALS</b>"]
        if not early.empty:
            sectors = ", ".join(early["sector"].tolist())
            lines.append(f"EARLY_ROTATION: {sectors}")
        if not leading.empty:
            sectors = ", ".join(leading["sector"].tolist())
            lines.append(f"LEADING: {sectors}")
        if early.empty and leading.empty:
            lines.append("No rotation signals today")
        lines.append("")
        return lines

    # ── Bull run watchlist top 5 ──────────────────────────────────────────────

    def _watchlist_section(self) -> list:
        if not BULL_RUN_WATCHLIST.exists():
            return []

        df = pd.read_csv(BULL_RUN_WATCHLIST, usecols=["symbol", "bull_run_score", "sector"])
        top = df.nlargest(5, "bull_run_score")
        if top.empty:
            return []

        lines = ["<b>TOP WATCHLIST (EMERGING)</b>"]
        for _, row in top.iterrows():
            lines.append(
                f"  {row['symbol']:12s} {row['bull_run_score']:.0f}  ({row['sector']})"
            )
        lines.append("")
        return lines

    # ── Deals ─────────────────────────────────────────────────────────────────

    def _deals_section(self) -> list:
        if not DEAL_SIGNALS.exists():
            return []

        df = pd.read_csv(DEAL_SIGNALS, usecols=["symbol", "inst_net_value_cr", "dominant_participant"])
        df = df[df["inst_net_value_cr"].fillna(0).abs() >= 25].copy()
        df = df.sort_values("inst_net_value_cr", ascending=False).head(5)

        if df.empty:
            return []

        lines = ["<b>INSTITUTIONAL DEALS (top, >= 25 Cr)</b>"]
        for _, row in df.iterrows():
            direction = "BUY" if float(row["inst_net_value_cr"]) > 0 else "SELL"
            lines.append(
                f"  {row['symbol']:12s} {direction} {abs(row['inst_net_value_cr']):.0f} Cr"
                f"  [{row.get('dominant_participant', 'INST')}]"
            )
        lines.append("")
        return lines


def build_digest() -> str:
    return DailyDigest().build()


if __name__ == "__main__":
    digest = build_digest()
    print(digest)
