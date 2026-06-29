"""
Alert Engine — Phase 9A
Evaluates all intelligence CSVs and emits alert objects by priority.
Never modifies intelligence files. Read-only consumer of all outputs.
"""

import os
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Intelligence source paths ─────────────────────────────────────────────────

PARTICIPANT_INTEL     = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
BULL_RUN_PROB        = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
BULL_RUN_WATCHLIST   = cfg.INTELLIGENCE_DIR / "bull_run_watchlist.csv"
SECTOR_ROTATION      = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
DEAL_SIGNALS         = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
CORP_CONFIDENCE      = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
FLOW_SCORES          = cfg.INTELLIGENCE_DIR / "participant_flow_scores.csv"

# ── Thresholds ────────────────────────────────────────────────────────────────

DEAL_MIN_CR           = 50.0       # net institutional value threshold (Cr)
CORP_CONF_THRESHOLD   = 2.0        # corporate confidence crossing level
DIV_THRESHOLD         = 2.0        # FII/CLIENT divergence sigma
STRONG_SCORE          = 65.0       # bull_run_score for STRONG_CANDIDATE
EMERGING_SCORE        = 45.0       # bull_run_score for EMERGING
DATA_STALENESS_DAYS   = 2          # max trading days lag before ignoring source

# ── Alert priorities ──────────────────────────────────────────────────────────

P1_REGIME_CHANGE          = "REGIME_CHANGE"
P2_STRONG_CANDIDATE       = "STRONG_CANDIDATE"
P3_SECTOR_ROTATION        = "SECTOR_ROTATION"
P4_INSTITUTIONAL_DEAL     = "INSTITUTIONAL_DEAL"
P5_CORPORATE_CONFIDENCE   = "CORPORATE_CONFIDENCE"
P6_PARTICIPANT_DIVERGENCE = "PARTICIPANT_DIVERGENCE"
P7_DAILY_DIGEST           = "DAILY_DIGEST"

PRIORITY_ORDER = [
    P1_REGIME_CHANGE,
    P2_STRONG_CANDIDATE,
    P3_SECTOR_ROTATION,
    P4_INSTITUTIONAL_DEAL,
    P5_CORPORATE_CONFIDENCE,
    P6_PARTICIPANT_DIVERGENCE,
    P7_DAILY_DIGEST,
]


@dataclass
class Alert:
    alert_type: str
    priority: int                    # 1 = highest
    title: str
    body: str
    symbol: Optional[str] = None     # None for market-level alerts
    sector: Optional[str] = None
    score: Optional[float] = None
    data_date: Optional[str] = None  # date of the underlying intelligence data
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def telegram_text(self) -> str:
        lines = [
            f"[P{self.priority}] {self.title}",
            self.body,
        ]
        if self.score is not None:
            lines.append(f"Score: {self.score:.1f}")
        if self.data_date:
            lines.append(f"Data: {self.data_date}")
        lines.append(f"Generated: {self.created_at}")
        return "\n".join(lines)


class AlertEngine:
    """
    Evaluates all intelligence CSVs and returns a list of Alert objects.
    Caller (alert_store) decides which ones to suppress based on cooldown.
    """

    def __init__(self, previous_regime: Optional[str] = None):
        self.previous_regime = previous_regime
        self.today = date.today().isoformat()

    def run(self) -> list[Alert]:
        alerts: list[Alert] = []

        alerts.extend(self._check_regime_change())
        alerts.extend(self._check_strong_candidates())
        alerts.extend(self._check_sector_rotation())
        alerts.extend(self._check_institutional_deals())
        alerts.extend(self._check_corporate_confidence())
        alerts.extend(self._check_participant_divergence())

        logger.info(f"[AlertEngine] Generated {len(alerts)} raw alerts")
        return alerts

    # ── P1: Regime Change ─────────────────────────────────────────────────────

    def _check_regime_change(self) -> list[Alert]:
        if not PARTICIPANT_INTEL.exists():
            logger.warning("[AlertEngine] participant_intelligence.csv not found")
            return []

        df = pd.read_csv(PARTICIPANT_INTEL, usecols=["date", "Market_Regime"])
        df = df.dropna(subset=["Market_Regime"]).sort_values("date")
        if df.empty:
            return []

        latest = df.iloc[-1]
        current_regime = str(latest["Market_Regime"])
        data_date = str(latest["date"])

        if self.previous_regime is None or current_regime == self.previous_regime:
            return []

        alert = Alert(
            alert_type=P1_REGIME_CHANGE,
            priority=1,
            title="MARKET REGIME CHANGE",
            body=(
                f"Regime changed from {self.previous_regime} to {current_regime}.\n"
                f"Review sector rotation and bull run watchlist immediately."
            ),
            data_date=data_date,
        )
        logger.info(f"[AlertEngine] P1 regime change: {self.previous_regime} -> {current_regime}")
        return [alert]

    # ── P2: Strong Candidates ─────────────────────────────────────────────────

    def _check_strong_candidates(self) -> list[Alert]:
        if not BULL_RUN_PROB.exists():
            return []

        df = pd.read_csv(BULL_RUN_PROB, usecols=["symbol", "sector", "bull_run_score", "label", "as_of_date"])
        strong = df[df["bull_run_score"] >= STRONG_SCORE].copy()
        if strong.empty:
            return []

        alerts = []
        for _, row in strong.iterrows():
            alerts.append(Alert(
                alert_type=P2_STRONG_CANDIDATE,
                priority=2,
                title="STRONG CANDIDATE",
                body=(
                    f"{row['symbol']} ({row['sector']}) has entered STRONG_CANDIDATE territory."
                ),
                symbol=str(row["symbol"]),
                sector=str(row["sector"]),
                score=float(row["bull_run_score"]),
                data_date=str(row["as_of_date"]),
            ))
        logger.info(f"[AlertEngine] P2 strong candidates: {len(alerts)}")
        return alerts

    # ── P3: Sector Rotation ───────────────────────────────────────────────────

    def _check_sector_rotation(self) -> list[Alert]:
        if not SECTOR_ROTATION.exists():
            return []

        df = pd.read_csv(SECTOR_ROTATION, usecols=["sector", "rotation_signal", "combined_score", "last_date"])
        early = df[df["rotation_signal"] == "EARLY_ROTATION"].copy()
        if early.empty:
            return []

        alerts = []
        for _, row in early.iterrows():
            alerts.append(Alert(
                alert_type=P3_SECTOR_ROTATION,
                priority=3,
                title="SECTOR ROTATION SIGNAL",
                body=(
                    f"{row['sector']} has entered EARLY_ROTATION.\n"
                    f"Combined score: {row['combined_score']:.1f}"
                ),
                sector=str(row["sector"]),
                score=float(row["combined_score"]),
                data_date=str(row.get("last_date", "")),
            ))
        logger.info(f"[AlertEngine] P3 sector rotation alerts: {len(alerts)}")
        return alerts

    # ── P4: Institutional Deals ───────────────────────────────────────────────

    def _check_institutional_deals(self) -> list[Alert]:
        if not DEAL_SIGNALS.exists():
            return []

        df = pd.read_csv(DEAL_SIGNALS, usecols=[
            "symbol", "inst_net_value_cr", "deal_signal", "dominant_participant",
            "fii_net_value_cr", "as_of_date"
        ])
        significant = df[df["inst_net_value_cr"].fillna(0) >= DEAL_MIN_CR].copy()
        if significant.empty:
            return []

        alerts = []
        for _, row in significant.iterrows():
            direction = "BUYING" if float(row["inst_net_value_cr"]) > 0 else "SELLING"
            alerts.append(Alert(
                alert_type=P4_INSTITUTIONAL_DEAL,
                priority=4,
                title="INSTITUTIONAL DEAL",
                body=(
                    f"Institutions {direction} {row['symbol']}.\n"
                    f"Net value: {row['inst_net_value_cr']:.1f} Cr | "
                    f"Lead: {row.get('dominant_participant', 'N/A')}"
                ),
                symbol=str(row["symbol"]),
                score=float(row["inst_net_value_cr"]),
                data_date=str(row.get("as_of_date", "")),
            ))
        logger.info(f"[AlertEngine] P4 deal alerts: {len(alerts)}")
        return alerts

    # ── P5: Corporate Confidence ──────────────────────────────────────────────

    def _check_corporate_confidence(self) -> list[Alert]:
        if not CORP_CONFIDENCE.exists():
            return []

        df = pd.read_csv(CORP_CONFIDENCE, usecols=[
            "symbol", "confidence_score_12m", "confidence_label",
            "last_action_type", "as_of_date"
        ])
        high_conf = df[df["confidence_score_12m"].fillna(0) >= CORP_CONF_THRESHOLD].copy()
        if high_conf.empty:
            return []

        alerts = []
        for _, row in high_conf.iterrows():
            alerts.append(Alert(
                alert_type=P5_CORPORATE_CONFIDENCE,
                priority=5,
                title="CORPORATE CONFIDENCE",
                body=(
                    f"{row['symbol']} corporate confidence at {row['confidence_score_12m']:.2f} "
                    f"({row.get('confidence_label', '')}).\n"
                    f"Last action: {row.get('last_action_type', 'N/A')}"
                ),
                symbol=str(row["symbol"]),
                score=float(row["confidence_score_12m"]),
                data_date=str(row.get("as_of_date", "")),
            ))
        logger.info(f"[AlertEngine] P5 corporate confidence alerts: {len(alerts)}")
        return alerts

    # ── P6: Participant Divergence ────────────────────────────────────────────

    def _check_participant_divergence(self) -> list[Alert]:
        if not PARTICIPANT_INTEL.exists():
            return []

        df = pd.read_csv(PARTICIPANT_INTEL, usecols=[
            "date", "FII_DII_Divergence", "Smart_Retail_Divergence", "Market_Regime"
        ])
        df = df.dropna(subset=["FII_DII_Divergence"]).sort_values("date")
        if df.empty:
            return []

        latest = df.iloc[-1]
        fii_dii_div = float(latest.get("FII_DII_Divergence", 0))
        smart_retail_div = float(latest.get("Smart_Retail_Divergence", 0))
        data_date = str(latest["date"])

        alerts = []
        if abs(fii_dii_div) >= DIV_THRESHOLD:
            direction = "FII OUTPACING DII" if fii_dii_div > 0 else "DII OUTPACING FII"
            alerts.append(Alert(
                alert_type=P6_PARTICIPANT_DIVERGENCE,
                priority=6,
                title="PARTICIPANT DIVERGENCE",
                body=(
                    f"FII/DII divergence at {fii_dii_div:.2f} sigma — {direction}.\n"
                    f"Smart/Retail divergence: {smart_retail_div:.2f}"
                ),
                score=fii_dii_div,
                data_date=data_date,
            ))
        logger.info(f"[AlertEngine] P6 divergence alerts: {len(alerts)}")
        return alerts


if __name__ == "__main__":
    engine = AlertEngine(previous_regime="DISTRIBUTION")
    alerts = engine.run()
    for a in alerts:
        print(f"[P{a.priority}] {a.alert_type}: {a.title}")
