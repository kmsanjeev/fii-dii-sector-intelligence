"""
Daily Intelligence Refresh -- Phase 19
Runs the full intelligence + RAG pipeline in dependency order.

Kill mechanism: create data/pipeline.stop to abort between stages.
Status:         data/pipeline_status.json  (polled by frontend every 5s)
Log:            data/intelligence/refresh_log.csv  (per-stage rows)

Run manually:   py -3.11 -m engines.orchestration.daily_refresh
"""

import json
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

STATUS_FILE = Path("data/pipeline_status.json")
STOP_FLAG   = Path("data/pipeline.stop")
REFRESH_LOG = cfg.INTELLIGENCE_DIR / "refresh_log.csv"

# ── Pipeline definition ───────────────────────────────────────────────────────
# (stage_id, module_path, label, timeout_seconds)

STAGES = [
    # ── SECTION 1: DAILY ACQUISITION ─────────────────────────────────────────
    # Download today's raw files from NSE, then build the adjusted+cached datasets
    # that all intelligence engines depend on.
    ("1A_bhavcopy_equity",  "engines.acquisition.nse_equity_acquisition_engine",              "NSE Equity Bhavcopy Download",          600),
    ("1B_bhavcopy_fno",     "engines.acquisition.nse_fno_acquisition_engine",                 "NSE F&O Bhavcopy Download",             600),
    ("1C_corp_actions",     "engines.acquisition.nse_corporate_actions_acquisition_engine",   "Corporate Actions Update",              300),
    ("1D_equity_master",    "engines.equity_master_engine",                                   "Equity Master Refresh",                 120),
    # Price Adjustment MUST run after bhavcopy download and before stock_history_builder.
    # Converts raw bhavcopy → split/bonus-adjusted OHLCV in data/NSE/adjusted_equity/
    ("1E_price_adjust",     "engines.analytics.price_adjustment_engine",                      "Price Adjustment (adjusted OHLCV)",     300),
    # Stock History Cache reads from adjusted_equity — must come after 1E
    ("1F_stock_history",    "engines.acquisition.stock_history_builder",                      "Stock History Cache (incremental)",     600),

    # ── SECTION 2: INTELLIGENCE GATHERING ────────────────────────────────────
    # Foundational reference data
    ("17_symbol_change",            "engines.foundation.symbol_change_engine",                "Symbol Change History",                 120),
    # Participant flows — critical path: all sector/intelligence engines depend on fresh 5A data
    ("5A_participant_acquisition",  "engines.participant.participant_acquisition_engine",      "Participant Acquisition (NSE API)",     600),
    ("5B_participant_flow",         "engines.participant.participant_flow_engine",             "Participant Flow Scores",               60),
    ("5C_participant_intelligence", "engines.participant.participant_intelligence_engine",     "Participant Intelligence",              60),
    # Sector flows (depend on 5A/5B)
    ("6A_sector_capital_flow",      "engines.participant.sector_capital_flow_engine",          "Sector Capital Flow",                   300),
    ("6B_sector_flow_scores",       "engines.participant.sector_flow_score_engine",            "Sector Flow Scores",                    30),
    # FPI fortnightly ownership data (NSDL/CDSL/SEBI) — depends on nothing; skips on non-fortnight days
    ("FPI_A_sector_fpi_fetch",      "engines.fpi.sector_fpi_engine",                          "FPI Sector AUC Fetch (fortnightly)",    300),
    ("FPI_B_sector_fpi_signals",    "engines.fpi.fpi_sector_signal_engine",                   "FPI Sector Signals (Z-scores)",          30),
    ("6C_sector_rotation",          "engines.participant.sector_rotation_intelligence_engine", "Sector Rotation Intelligence (3-factor)", 30),
    # Corporate data (independent of participant flow)
    ("7A_block_bulk_deals",         "engines.corporate.block_bulk_deal_engine",               "Block/Bulk Deals (NSE API)",             300),
    ("7C_corp_action_intel",        "engines.corporate.corporate_action_intelligence_engine", "Corporate Action Intelligence",         120),
    ("18A_announcements",           "engines.corporate.announcement_intelligence_engine",     "Corporate Announcements (incremental)", 600),
    # Management Intelligence (uses Anthropic API — non-critical, failures tolerated)
    ("16A_management_sentiment",    "engines.management.management_sentiment_engine",         "Management Sentiment (Claude AI)",      300),
    # Technical + F&O signals (depend on fresh stock_history_cache from 1F)
    ("A1_technical_indicators",     "engines.intelligence.technical_engine",                  "Technical Indicators",                  120),
    ("A2_fno_intelligence",         "engines.intelligence.fno_engine",                        "F&O Intelligence (PCR + OI signals)",   60),
    # Price scoring (depends on 5B sector flow + 7A deals + 7C corporate confidence)
    ("8A_price_momentum",           "engines.intelligence.price_momentum_engine",             "Price Momentum",                        60),
    ("8B_bull_run_probability",     "engines.intelligence.bull_run_probability_engine",       "Bull Run Probability",                  60),
    # ML inference (reads fresh feature matrix; no model retrain)
    ("12_ml_scorer",                "engines.ml.ml_scorer",                                  "ML Scorer (inference)",                 60),
    # Trade Conviction (depends on technical A1, F&O A2, sector rotation 6C, ML 12)
    ("C1_trade_conviction",         "engines.intelligence.trade_conviction_engine",           "Trade Conviction Scores",               60),
    # AstroFinance planetary signals (depends on sector rotation 6C; runs before RAG so signals are indexed)
    ("AF_astro_engine",             "engines.intelligence.astro_engine",                     "AstroFinance Planetary Signals",        60),
    # Vedic Kundli + Gann (natal charts for all NSE stocks; depends on equity_master + price_momentum)
    ("KU_kundli_engine",            "engines.intelligence.kundli_engine",                    "Vedic Kundli Natal Charts",            180),
    ("KU_gann_engine",              "engines.intelligence.gann_engine",                      "Gann Square of 9 Price Levels",         60),
    # RAG indexes (rebuilt from fresh intelligence CSVs above)
    ("13A_document_builder",        "engines.ai.knowledge.document_builder",                 "RAG Document Builder",                  30),
    ("13B_faiss_indexer",           "engines.ai.knowledge.faiss_indexer",                    "FAISS Indexer (embedding)",             180),
    ("13C_bm25_indexer",            "engines.ai.knowledge.bm25_indexer",                     "BM25 Indexer",                          30),
    # Portfolio overlay (fresh intelligence applied to holdings)
    ("20_portfolio",                "engines.portfolio.portfolio_engine",                    "Portfolio Intelligence Rebuild",        30),
    # Alerts — always last, fires on fully-refreshed intelligence
    ("9_alert_engine",              "alerts.alert_engine",                                   "Alert Engine (Telegram push)",          60),
]

# Stage-to-section mapping for UI grouping
STAGE_SECTIONS = {
    "Daily Acquisition":      ["1A_bhavcopy_equity", "1B_bhavcopy_fno", "1C_corp_actions",
                                "1D_equity_master", "1E_price_adjust", "1F_stock_history"],
    "Intelligence Gathering": ["17_symbol_change", "5A_participant_acquisition",
                                "5B_participant_flow", "5C_participant_intelligence",
                                "6A_sector_capital_flow", "6B_sector_flow_scores",
                                "FPI_A_sector_fpi_fetch", "FPI_B_sector_fpi_signals", "6C_sector_rotation",
                                "7A_block_bulk_deals", "7C_corp_action_intel", "18A_announcements",
                                "16A_management_sentiment", "A1_technical_indicators",
                                "A2_fno_intelligence", "8A_price_momentum", "8B_bull_run_probability",
                                "12_ml_scorer", "C1_trade_conviction",
                                "AF_astro_engine",
                                "KU_kundli_engine", "KU_gann_engine",
                                "13A_document_builder", "13B_faiss_indexer", "13C_bm25_indexer",
                                "20_portfolio", "9_alert_engine"],
}

# ── Shared state (guarded by _lock) ──────────────────────────────────────────

_lock        = threading.Lock()
_stop_event  = threading.Event()
_run_thread: threading.Thread | None = None


# ── Status helpers ────────────────────────────────────────────────────────────

def _now_ist() -> str:
    """Return current time as IST string (UTC+5:30)."""
    from datetime import timedelta
    utc = datetime.now(timezone.utc)
    ist = utc + timedelta(hours=5, minutes=30)
    return ist.strftime("%Y-%m-%d %H:%M:%S IST")


def _write_status(state: dict) -> None:
    tmp = STATUS_FILE.with_suffix(".tmp.json")
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    shutil.move(str(tmp), str(STATUS_FILE))


def read_status() -> dict:
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"state": "IDLE", "last_run_at": None, "current_stage": None, "stages": {}}


def is_running() -> bool:
    with _lock:
        return _run_thread is not None and _run_thread.is_alive()


# ── Log helpers ───────────────────────────────────────────────────────────────

def _append_log(run_id: str, stage_id: str, label: str, status: str,
                started_at: str, finished_at: str, duration_s: float,
                error: str = "") -> None:
    REFRESH_LOG.parent.mkdir(parents=True, exist_ok=True)
    header = not REFRESH_LOG.exists()
    with open(REFRESH_LOG, "a", encoding="utf-8") as f:
        if header:
            f.write("run_id,stage_id,label,status,started_at,finished_at,duration_s,error\n")
        err = error.replace('"', "'").replace("\n", " ")
        f.write(f'"{run_id}","{stage_id}","{label}","{status}",'
                f'"{started_at}","{finished_at}",{duration_s:.1f},"{err}"\n')


def read_log(n: int = 100) -> list[dict]:
    if not REFRESH_LOG.exists():
        return []
    import csv
    rows = []
    with open(REFRESH_LOG, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows[-n:]


# ── Stage runner ──────────────────────────────────────────────────────────────

def _run_stage(run_id: str, stage_id: str, module: str, label: str, timeout: int) -> tuple[str, str]:
    """
    Run one stage as a subprocess.
    Returns (status, error_msg): status is DONE | FAILED | TIMEOUT | STOPPED.
    Subprocess is killed if stop_event is set mid-run.
    """
    started_at = _now_ist()
    t0 = time.monotonic()

    proc = subprocess.Popen(
        [sys.executable, "-m", module],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output_lines: list[str] = []

    while True:
        try:
            line = proc.stdout.readline()  # type: ignore[union-attr]
        except Exception:
            break
        if line:
            output_lines.append(line.rstrip())
            logger.debug("[Pipeline][%s] %s", stage_id, line.rstrip())
        elif proc.poll() is not None:
            break

        if _stop_event.is_set():
            proc.kill()
            elapsed = time.monotonic() - t0
            finished_at = _now_ist()
            _append_log(run_id, stage_id, label, "STOPPED", started_at, finished_at, elapsed)
            return "STOPPED", "Stop flag set by user"

        elapsed = time.monotonic() - t0
        if elapsed > timeout:
            proc.kill()
            finished_at = _now_ist()
            _append_log(run_id, stage_id, label, "TIMEOUT", started_at, finished_at, elapsed,
                        f"Exceeded {timeout}s timeout")
            return "TIMEOUT", f"Exceeded {timeout}s timeout"

    rc = proc.wait()
    elapsed = time.monotonic() - t0
    finished_at = _now_ist()
    status = "DONE" if rc == 0 else "FAILED"
    error  = "" if rc == 0 else f"exit code {rc}. Last output: {output_lines[-3:] if output_lines else ''}"
    _append_log(run_id, stage_id, label, status, started_at, finished_at, elapsed, error)
    return status, error


# ── Pipeline runner ───────────────────────────────────────────────────────────

def _pipeline_body() -> None:
    """Runs in a background thread. Writes status JSON throughout."""
    global _run_thread

    # Clear any leftover stop flag from a previous kill
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
    _stop_event.clear()

    run_id  = datetime.now().strftime("%Y%m%d_%H%M%S")
    started = _now_ist()
    stage_statuses: dict[str, dict] = {}

    _write_status({
        "state":        "RUNNING",
        "run_id":       run_id,
        "started_at":   started,
        "last_run_at":  None,
        "current_stage": None,
        "stages":       stage_statuses,
    })

    logger.info("[Pipeline] Run %s started at %s", run_id, started)
    final_state = "DONE"

    for stage_id, module, label, timeout in STAGES:
        # Check stop before each stage
        if _stop_event.is_set() or STOP_FLAG.exists():
            _stop_event.set()
            logger.info("[Pipeline] Stopped before stage %s", stage_id)
            final_state = "STOPPED"
            break

        stage_statuses[stage_id] = {"label": label, "status": "RUNNING", "started_at": _now_ist()}
        _write_status({
            "state":         "RUNNING",
            "run_id":        run_id,
            "started_at":    started,
            "last_run_at":   None,
            "current_stage": stage_id,
            "current_label": label,
            "stages":        stage_statuses,
        })

        logger.info("[Pipeline] Starting stage: %s (%s)", stage_id, label)
        t0 = time.monotonic()
        status, error = _run_stage(run_id, stage_id, module, label, timeout)
        elapsed = time.monotonic() - t0

        stage_statuses[stage_id].update({
            "status":      status,
            "finished_at": _now_ist(),
            "duration_s":  round(elapsed, 1),
            "error":       error,
        })

        if status in ("FAILED", "TIMEOUT"):
            logger.error("[Pipeline] Stage %s %s: %s", stage_id, status, error)
            # Critical gates: abort the entire run if these fail.
            # 5A: participant data is the spine — everything downstream is stale without it.
            # All others are non-critical: log and continue.
            if stage_id == "5A_participant_acquisition":
                final_state = "FAILED"
                break
        elif status == "STOPPED":
            final_state = "STOPPED"
            break
        else:
            logger.info("[Pipeline] Stage %s done in %.1fs", stage_id, elapsed)

    finished = _now_ist()
    _write_status({
        "state":         final_state,
        "run_id":        run_id,
        "started_at":    started,
        "last_run_at":   finished,
        "current_stage": None,
        "stages":        stage_statuses,
    })
    logger.info("[Pipeline] Run %s finished: %s at %s", run_id, final_state, finished)

    with _lock:
        _run_thread = None


# ── Public API ────────────────────────────────────────────────────────────────

def start_pipeline() -> tuple[bool, str]:
    """
    Start the pipeline in a background thread.
    Returns (started: bool, message: str).
    """
    global _run_thread
    with _lock:
        if _run_thread is not None and _run_thread.is_alive():
            return False, "Pipeline already running"
        t = threading.Thread(target=_pipeline_body, daemon=True, name="daily-refresh")
        _run_thread = t
        t.start()
    return True, "Pipeline started"


def stop_pipeline() -> tuple[bool, str]:
    """
    Signal the pipeline to stop after the current stage finishes.
    Also writes the stop sentinel file so any hung subprocess can be killed.
    """
    _stop_event.set()
    STOP_FLAG.touch()
    if is_running():
        return True, "Stop signal sent - pipeline will abort after current stage"
    return True, "Stop flag set (pipeline was not running)"


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok, msg = start_pipeline()
    print(msg)
    # Block until done
    with _lock:
        t = _run_thread
    if t:
        t.join()
    status = read_status()
    print(f"Final state: {status['state']}")
    if status.get("stages"):
        for sid, s in status["stages"].items():
            dur = s.get("duration_s", "?")
            print(f"  {sid:40s}  {s['status']:8s}  {dur}s")
