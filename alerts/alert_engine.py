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
ANN_CSV              = cfg.INTELLIGENCE_DIR / "company_announcements.csv"

# ── Thresholds ────────────────────────────────────────────────────────────────

DEAL_MIN_CR           = 50.0       # net institutional value threshold (Cr)
CORP_CONF_THRESHOLD   = 2.0        # corporate confidence crossing level
DIV_THRESHOLD         = 2.0        # FII/CLIENT divergence sigma
STRONG_SCORE          = 65.0       # bull_run_score for STRONG_CANDIDATE
EMERGING_SCORE        = 45.0       # bull_run_score for EMERGING
DATA_STALENESS_DAYS   = 2          # max trading days lag before ignoring source
ANN_DISTINCT_MIN      = 3          # min distinct announcement types in 30d (confluence)
ANN_VELOCITY_MIN      = 1.5        # min 30d/60d announcement velocity ratio
ORDER_WIN_MIN_6M      = 2          # min ORDER_WIN events in 6 months
ANN_MAX_ALERTS        = 8          # cap per run to prevent flooding

# ── Alert priorities ──────────────────────────────────────────────────────────

P1_REGIME_CHANGE          = "REGIME_CHANGE"
P2_STRONG_CANDIDATE       = "STRONG_CANDIDATE"
P3_SECTOR_ROTATION        = "SECTOR_ROTATION"
P4_INSTITUTIONAL_DEAL     = "INSTITUTIONAL_DEAL"
P5_CORPORATE_CONFIDENCE   = "CORPORATE_CONFIDENCE"
P6_PARTICIPANT_DIVERGENCE = "PARTICIPANT_DIVERGENCE"
P7_DAILY_DIGEST           = "DAILY_DIGEST"
P8_ANNOUNCEMENT_MOMENTUM  = "ANNOUNCEMENT_MOMENTUM"

PRIORITY_ORDER = [
    P1_REGIME_CHANGE,
    P2_STRONG_CANDIDATE,
    P3_SECTOR_ROTATION,
    P4_INSTITUTIONAL_DEAL,
    P5_CORPORATE_CONFIDENCE,
    P6_PARTICIPANT_DIVERGENCE,
    P7_DAILY_DIGEST,
    P8_ANNOUNCEMENT_MOMENTUM,
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
        alerts.extend(self._check_announcement_momentum())

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


    # ── P8: Announcement Momentum ─────────────────────────────────────────────
    # Two sub-signals:
    #   CONFLUENCE  -- distinct_types_30d >= 3 AND velocity >= 1.5 (pre-discovery pattern)
    #   ORDER_WIN   -- 2+ contract wins in 6M with recent activity (revenue pipeline)
    # Only fires on WATCHLIST/NEUTRAL (pre-EMERGING stocks not yet in the watchlist).

    def _check_announcement_momentum(self) -> list[Alert]:
        if not ANN_CSV.exists() or not BULL_RUN_PROB.exists():
            return []

        # Load 180d of announcements (keeps memory footprint small)
        ann = pd.read_csv(
            ANN_CSV,
            usecols=["symbol", "date", "announcement_type", "signal_score"],
            dtype=str,
        )
        ann["date"]         = pd.to_datetime(ann["date"], errors="coerce")
        ann["signal_score"] = pd.to_numeric(ann["signal_score"], errors="coerce").fillna(0).astype(int)
        ann["symbol"]       = ann["symbol"].str.strip().str.upper()
        ann = ann.dropna(subset=["date"])

        today  = pd.Timestamp.now().normalize()
        cut30  = today - pd.Timedelta(days=30)
        cut60  = today - pd.Timedelta(days=60)
        cut180 = today - pd.Timedelta(days=180)

        w30  = ann[ann["date"] >= cut30]
        w60  = ann[ann["date"] >= cut60]
        w180 = ann[ann["date"] >= cut180]

        # Per-symbol metrics
        distinct_30d = w30.groupby("symbol")["announcement_type"].nunique()
        cnt_30d      = w30.groupby("symbol").size()
        cnt_60d      = w60.groupby("symbol").size().clip(lower=1)
        velocity     = (cnt_30d / cnt_60d).round(2)
        high_30d     = (w30[w30["signal_score"] >= 70]
                        .groupby("symbol").size())
        order_wins   = (w180[w180["announcement_type"] == "ORDER_WIN"]
                        .groupby("symbol").size())
        latest_order = (w180[w180["announcement_type"] == "ORDER_WIN"]
                        .groupby("symbol")["date"].max()
                        .dt.strftime("%Y-%m-%d"))
        dominant_30d = (w30.groupby("symbol")["announcement_type"]
                        .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "OTHER"))

        metrics = pd.DataFrame({
            "distinct_types_30d": distinct_30d,
            "ann_velocity_30d":   velocity,
            "high_signal_30d":    high_30d,
            "order_wins_6m":      order_wins,
            "latest_order_date":  latest_order,
            "dominant_type":      dominant_30d,
        }).fillna({"distinct_types_30d": 0, "ann_velocity_30d": 0,
                   "high_signal_30d": 0, "order_wins_6m": 0})
        metrics = metrics.reset_index().rename(columns={"index": "symbol"})

        # Bull run labels
        bull = pd.read_csv(
            BULL_RUN_PROB,
            usecols=["symbol", "sector", "label", "bull_run_score", "as_of_date"],
        )
        bull["symbol"] = bull["symbol"].str.strip().str.upper()

        combined = metrics.merge(bull, on="symbol", how="inner")
        PRE_DISCOVERY = {"NEUTRAL", "WATCHLIST"}

        alerts: list[Alert] = []

        # --- Sub-signal 1: Momentum Confluence ---
        confluence = combined[
            (combined["distinct_types_30d"] >= ANN_DISTINCT_MIN) &
            (combined["ann_velocity_30d"]   >= ANN_VELOCITY_MIN) &
            (combined["label"].isin(PRE_DISCOVERY))
        ].copy()
        confluence["_rank"] = (
            confluence["distinct_types_30d"] * confluence["ann_velocity_30d"]
        )
        confluence = confluence.sort_values("_rank", ascending=False).head(ANN_MAX_ALERTS // 2)

        for _, row in confluence.iterrows():
            types_n  = int(row["distinct_types_30d"])
            velocity = float(row["ann_velocity_30d"])
            high_n   = int(row.get("high_signal_30d", 0))
            dom_type = str(row.get("dominant_type", ""))
            alerts.append(Alert(
                alert_type=P8_ANNOUNCEMENT_MOMENTUM,
                priority=8,
                title=f"ANNOUNCEMENT MOMENTUM: {row['symbol']}",
                body=(
                    f"{row['symbol']} ({row['sector']}) - Pre-discovery momentum building.\n"
                    f"Label: {row['label']} | Bull Run Score: {row['bull_run_score']:.1f}\n"
                    f"Signal types (30d): {types_n} distinct | Velocity: {velocity:.1f}x\n"
                    f"High-signal events: {high_n} | Dominant: {dom_type}"
                ),
                symbol=str(row["symbol"]),
                sector=str(row["sector"]),
                score=float(row["bull_run_score"]),
                data_date=str(row.get("as_of_date", self.today)),
            ))

        # --- Sub-signal 2: Order Win Cluster ---
        order_cluster = combined[
            (combined["order_wins_6m"] >= ORDER_WIN_MIN_6M) &
            (combined["label"].isin(PRE_DISCOVERY | {"EMERGING"}))
        ].copy()
        # Only alert if a win happened in the last 30d
        order_cluster = order_cluster[
            order_cluster["latest_order_date"].notna() &
            (order_cluster["latest_order_date"] >= cut30.strftime("%Y-%m-%d"))
        ]
        order_cluster = order_cluster.sort_values("order_wins_6m", ascending=False).head(ANN_MAX_ALERTS // 2)

        for _, row in order_cluster.iterrows():
            # Skip if already emitted via confluence
            if any(a.symbol == str(row["symbol"]) for a in alerts):
                continue
            wins_n     = int(row["order_wins_6m"])
            latest_dt  = str(row.get("latest_order_date", ""))
            alerts.append(Alert(
                alert_type=P8_ANNOUNCEMENT_MOMENTUM,
                priority=8,
                title=f"ORDER WIN CLUSTER: {row['symbol']}",
                body=(
                    f"{row['symbol']} ({row['sector']}) - Order/contract wins accelerating.\n"
                    f"Label: {row['label']} | Bull Run Score: {row['bull_run_score']:.1f}\n"
                    f"Order wins (6M): {wins_n} | Latest: {latest_dt}"
                ),
                symbol=str(row["symbol"]),
                sector=str(row["sector"]),
                score=float(row["bull_run_score"]),
                data_date=str(row.get("as_of_date", self.today)),
            ))

        logger.info(f"[AlertEngine] P8 announcement momentum alerts: {len(alerts)}")
        return alerts


if __name__ == "__main__":
    engine = AlertEngine(previous_regime="DISTRIBUTION")
    alerts = engine.run()
    for a in alerts:
        print(f"[P{a.priority}] {a.alert_type}: {a.title}")
