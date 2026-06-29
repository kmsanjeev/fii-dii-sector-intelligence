"""
Alert Scheduler — Phase 9E
APScheduler: daily digest at 18:30 IST, alert checks every 30 min post-market.
No checks during market hours (09:15-15:30 IST) per G-A-04.

Usage:
    py -3.11 alerts/alert_scheduler.py
"""

import os
import sys
import time
from datetime import datetime

from engines.common.logger import get_logger

logger = get_logger(__name__)


def _check_env():
    missing = [v for v in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"] if not os.getenv(v)]
    if missing:
        logger.error(f"[AlertScheduler] Missing env vars: {', '.join(missing)}")
        sys.exit(1)


def _is_market_hours() -> bool:
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    total_minutes = hour * 60 + minute
    market_open  = 9 * 60 + 15
    market_close = 15 * 60 + 30
    return market_open <= total_minutes <= market_close


def run_alert_cycle():
    """Evaluate all alert types and send eligible alerts via Telegram."""
    if _is_market_hours():
        logger.info("[AlertScheduler] Skipping — market hours active (G-A-04)")
        return

    try:
        from alerts.alert_store import AlertStore
        from alerts.alert_engine import AlertEngine
        from alerts.telegram_bot import send_alerts

        store = AlertStore()
        previous_regime = store.get_previous_regime()

        engine = AlertEngine(previous_regime=previous_regime)
        raw_alerts = engine.run()

        eligible = store.filter_eligible(raw_alerts)

        if eligible:
            sent = send_alerts(eligible)
            for alert in eligible[:sent]:
                store.mark_sent(alert)

        # Update stored regime so P1 can detect changes next cycle
        import pandas as pd
        from engines.common import config as cfg
        PARTICIPANT_INTEL = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
        if PARTICIPANT_INTEL.exists():
            df = pd.read_csv(PARTICIPANT_INTEL, usecols=["date", "Market_Regime"])
            df = df.dropna(subset=["Market_Regime"]).sort_values("date")
            if not df.empty:
                current_regime = str(df.iloc[-1]["Market_Regime"])
                store.set_current_regime(current_regime)

        logger.info(f"[AlertScheduler] Cycle complete — {len(eligible)} sent")

    except Exception as e:
        logger.error(f"[AlertScheduler] Alert cycle failed: {e}", exc_info=True)


def run_daily_digest():
    """Build and send the 18:30 IST daily digest."""
    try:
        from alerts.daily_digest import build_digest
        from alerts.telegram_bot import send_raw
        from alerts.alert_store import AlertStore
        from alerts.alert_engine import Alert, P7_DAILY_DIGEST

        digest_alert = Alert(
            alert_type=P7_DAILY_DIGEST,
            priority=7,
            title="Daily Digest",
            body="",
        )

        store = AlertStore()
        eligible = store.filter_eligible([digest_alert])
        if not eligible:
            logger.info("[AlertScheduler] Daily digest suppressed by cooldown")
            return

        text = build_digest()
        if send_raw(text):
            store.mark_sent(digest_alert)
            logger.info("[AlertScheduler] Daily digest sent")
        else:
            logger.error("[AlertScheduler] Daily digest send failed")

    except Exception as e:
        logger.error(f"[AlertScheduler] Daily digest failed: {e}", exc_info=True)


def main():
    _check_env()

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error(
            "[AlertScheduler] APScheduler not installed. "
            "Run: py -3.11 -m pip install 'APScheduler==3.*'"
        )
        sys.exit(1)

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # Daily digest at 18:30 IST
    scheduler.add_job(
        run_daily_digest,
        trigger=CronTrigger(hour=18, minute=30, timezone="Asia/Kolkata"),
        id="daily_digest",
        name="Daily Intelligence Digest",
    )

    # Alert checks every 30 min from 16:00 to 22:00 IST on weekdays
    scheduler.add_job(
        run_alert_cycle,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour="16-22",
            minute="0,30",
            timezone="Asia/Kolkata",
        ),
        id="alert_cycle",
        name="Post-Market Alert Check",
    )

    print("[AlertScheduler] Starting scheduler")
    print("  Daily digest: 18:30 IST")
    print("  Alert checks: 16:00-22:00 IST every 30 min (weekdays)")
    print("  Press Ctrl+C to stop")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[AlertScheduler] Stopped")


if __name__ == "__main__":
    main()
