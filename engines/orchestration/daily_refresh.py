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
    # Phase 17 — Symbol Change (foundational; check daily, NSE updates infrequently)
    ("17_symbol_change",            "engines.foundation.symbol_change_engine",                 "Symbol Change History",                120),
    # Phase 5 — Participant flows (critical path: if 5A fails, nothing downstream is fresh)
    ("5A_participant_acquisition",  "engines.participant.participant_acquisition_engine",       "Participant Acquisition (NSE API)",     600),
    ("5B_participant_flow",         "engines.participant.participant_flow_engine",              "Participant Flow Scores",               60),
    ("5C_participant_intelligence", "engines.participant.participant_intelligence_engine",      "Participant Intelligence",              60),
    # Phase 6 — Sector flows
    ("6A_sector_capital_flow",      "engines.participant.sector_capital_flow_engine",           "Sector Capital Flow",                  300),
    ("6B_sector_flow_scores",       "engines.participant.sector_flow_score_engine",             "Sector Flow Scores",                   30),
    ("6C_sector_rotation",          "engines.participant.sector_rotation_intelligence_engine",  "Sector Rotation Intelligence",         30),
    # Phase 7 — Corporate data
    ("7A_block_bulk_deals",         "engines.corporate.block_bulk_deal_engine",                "Block/Bulk Deals (NSE API)",            300),
    ("7C_corp_action_intel",        "engines.corporate.corporate_action_intelligence_engine",  "Corporate Action Intelligence",        120),
    # Phase 18 — Corporate Announcements (incremental: re-fetches last 3 months + dedup)
    ("18A_announcements",           "engines.corporate.announcement_intelligence_engine",      "Corporate Announcements (incremental)", 600),
    # Phase 16 — Management Intelligence (uses Anthropic API — non-critical, failures tolerated)
    ("16A_management_sentiment",    "engines.management.management_sentiment_engine",          "Management Sentiment (Claude AI)",     300),
    # Phase 8 — Price & Bull Run (depends on fresh participant + corporate data above)
    ("8A_price_momentum",           "engines.intelligence.price_momentum_engine",              "Price Momentum",                       60),
    ("8B_bull_run_probability",     "engines.intelligence.bull_run_probability_engine",        "Bull Run Probability",                 60),
    # Phase 12 — ML inference only (no retrain; reads fresh feature matrix + pre-trained model)
    ("12_ml_scorer",                "engines.ml.ml_scorer",                                   "ML Scorer (inference)",                60),
    # Phase 13 — RAG (rebuild indexes from fresh intelligence CSVs)
    ("13A_document_builder",        "engines.ai.knowledge.document_builder",                  "RAG Document Builder",                 30),
    ("13B_faiss_indexer",           "engines.ai.knowledge.faiss_indexer",                     "FAISS Indexer (embedding)",            180),
    ("13C_bm25_indexer",            "engines.ai.knowledge.bm25_indexer",                      "BM25 Indexer",                        30),
    # Phase 9 — Alerts (always last — fires on fresh intelligence)
    ("9_alert_engine",              "alerts.alert_engine",                                    "Alert Engine (Telegram push)",         60),
]

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
