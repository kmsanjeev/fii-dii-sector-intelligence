"""
Refresh Scheduler -- Phase 19
APScheduler trigger: runs daily_refresh at 18:00 IST on market weekdays.

This module is imported by backend/main.py on startup.
The scheduler runs in a background thread alongside the FastAPI server.

Manual trigger: py -3.11 -m engines.orchestration.refresh_scheduler
"""

import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from engines.orchestration.daily_refresh import start_pipeline, read_status
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Scheduler singleton ───────────────────────────────────────────────────────

_scheduler: BackgroundScheduler | None = None

# 18:00 IST = 12:30 UTC (IST is UTC+5:30)
_IST_HOUR_UTC   = 12
_IST_MINUTE_UTC = 30


def _scheduled_run() -> None:
    """Called by APScheduler at 18:00 IST weekdays."""
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    logger.info("[Scheduler] Triggered at %s IST", ist_now.strftime("%Y-%m-%d %H:%M"))

    # Guard: skip if already running
    status = read_status()
    if status.get("state") == "RUNNING":
        logger.info("[Scheduler] Pipeline already running — skipping scheduled trigger")
        return

    ok, msg = start_pipeline()
    logger.info("[Scheduler] %s", msg)


def start_scheduler() -> None:
    """Start the APScheduler background scheduler. Call once on app startup."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.info("[Scheduler] Already running")
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _scheduled_run,
        trigger=CronTrigger(
            day_of_week="mon-fri",    # weekdays only
            hour=_IST_HOUR_UTC,
            minute=_IST_MINUTE_UTC,
            timezone="UTC",
        ),
        id="daily_refresh",
        name="Daily Intelligence Refresh (18:00 IST)",
        replace_existing=True,
        misfire_grace_time=3600,       # run up to 1h late if server was down
    )
    _scheduler.start()
    logger.info(
        "[Scheduler] Started — daily refresh scheduled at %02d:%02d UTC (18:00 IST) Mon-Fri",
        _IST_HOUR_UTC, _IST_MINUTE_UTC,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")
    _scheduler = None


def next_run_ist() -> str | None:
    """Return next scheduled run time as IST string, or None."""
    if _scheduler is None or not _scheduler.running:
        return None
    job = _scheduler.get_job("daily_refresh")
    if job and job.next_run_time:
        ist = job.next_run_time.astimezone(timezone.utc) + timedelta(hours=5, minutes=30)
        return ist.strftime("%Y-%m-%d %H:%M IST")
    return None


# ── CLI entry point (test / standalone) ──────────────────────────────────────

if __name__ == "__main__":
    import time
    print("Starting scheduler in foreground (Ctrl-C to stop)...")
    start_scheduler()
    print(f"Next run: {next_run_ist()}")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
        print("Scheduler stopped.")
