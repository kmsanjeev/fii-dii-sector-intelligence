"""
Data Operations Router — Phase 11 (GUI v2)
GET  /api/data/status          -- integrity report for all data modules
GET  /api/data/run/{engine}    -- SSE stream: spawn engine subprocess, stream output live
GET  /api/data/engines         -- list available engines + descriptions
"""

import json
import os
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Generator

_TQDM_RE = re.compile(r'^\s*\S.*:\s+\d+%\|')

import pandas as pd
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("data_ops")
router = APIRouter(prefix="/api/data", tags=["data_ops"])

# ── Process lifecycle management ──────────────────────────────────────────────
# Only one engine subprocess runs at a time.  _current_run_id is incremented on
# every kill so that orphaned SSE generators detect they are stale and exit.

_running_proc: "subprocess.Popen | None" = None
_proc_lock    = threading.Lock()
_current_run_id: int = 0


def _kill_running() -> bool:
    """Terminate the current subprocess (if any). Returns True if something was killed."""
    global _running_proc, _current_run_id
    _current_run_id += 1          # invalidates all active SSE generators
    killed = False
    with _proc_lock:
        if _running_proc is not None and _running_proc.poll() is None:
            try:
                _running_proc.kill()
                _running_proc.wait(timeout=5)
            except Exception:
                pass
            killed = True
        _running_proc = None
    return killed


def _register_proc(proc: "subprocess.Popen") -> None:
    global _running_proc
    with _proc_lock:
        _running_proc = proc


@router.post("/kill")
def kill_engine():
    """Stop any currently running engine subprocess."""
    killed = _kill_running()
    return {"status": "killed" if killed else "nothing_running"}


@router.get("/running")
def get_running_status():
    """Returns whether an engine subprocess is currently active."""
    with _proc_lock:
        active = _running_proc is not None and _running_proc.poll() is None
    return {"running": active, "run_id": _current_run_id}

# ── Engine registry ───────────────────────────────────────────────────────────

ENGINES = {
    "bhavcopy_equity": {
        "label": "Bhavcopy Equity Downloader",
        "script": "engines/acquisition/nse_equity_acquisition_engine.py",
        "phase": "1",
    },
    "bhavcopy_fno": {
        "label": "Bhavcopy F&O Downloader",
        "script": "engines/acquisition/nse_fno_acquisition_engine.py",
        "phase": "1",
    },
    "corporate_actions": {
        "label": "Corporate Actions Downloader",
        "script": "engines/acquisition/nse_corporate_actions_acquisition_engine.py",
        "phase": "2",
    },
    "equity_master": {
        "label": "Equity Master Refresher",
        "script": "engines/equity_master_engine.py",
        "phase": "1",
    },
    "stock_history_build": {
        "label": "Stock History Cache Builder (incremental)",
        "script": "engines/acquisition/stock_history_builder.py",
        "phase": "Cache",
    },
    "stock_history_full": {
        "label": "Stock History Cache Builder (full rebuild)",
        "script": "engines/acquisition/stock_history_builder.py",
        "args": ["--full"],
        "phase": "Cache",
    },
    "participant_5a": {
        "label": "Participant Acquisition (5A)",
        "script": "engines/participant/participant_acquisition_engine.py",
        "phase": "5A",
    },
    "participant_5b": {
        "label": "Participant Flow Engine (5B)",
        "script": "engines/participant/participant_flow_engine.py",
        "phase": "5B",
    },
    "participant_5c": {
        "label": "Participant Intelligence (5C)",
        "script": "engines/participant/participant_intelligence_engine.py",
        "phase": "5C",
    },
    "sector_6a": {
        "label": "Sector Capital Flow (6A)",
        "script": "engines/participant/sector_capital_flow_engine.py",
        "phase": "6A",
    },
    "sector_6b": {
        "label": "Sector Flow Scores (6B)",
        "script": "engines/participant/sector_flow_score_engine.py",
        "phase": "6B",
    },
    "sector_6c": {
        "label": "Sector Rotation Intelligence (6C)",
        "script": "engines/participant/sector_rotation_intelligence_engine.py",
        "phase": "6C",
    },
    "deals_7a": {
        "label": "Block/Bulk Deal Engine (7A)",
        "script": "engines/corporate/block_bulk_deal_engine.py",
        "phase": "7A",
    },
    "events_7b": {
        "label": "Event Calendar Engine (7B)",
        "script": "engines/corporate/corporate_event_calendar_engine.py",
        "phase": "7B",
    },
    "corp_actions_7c": {
        "label": "Corporate Action Intelligence (7C)",
        "script": "engines/corporate/corporate_action_intelligence_engine.py",
        "phase": "7C",
    },
    "momentum_8a": {
        "label": "Price Momentum Engine (8A)",
        "script": "engines/intelligence/price_momentum_engine.py",
        "phase": "8A",
    },
    "bull_run_8b": {
        "label": "Bull Run Probability Engine (8B)",
        "script": "engines/intelligence/bull_run_probability_engine.py",
        "phase": "8B",
    },
    "ml_12": {
        "label": "ML Intelligence (12)",
        "script": "engines/ml/feature_engineering.py",
        "phase": "12",
    },
    "alerts_9": {
        "label": "Alert Engine (9)",
        "script": "alerts/alert_engine.py",
        "phase": "9",
    },
}

ACQUISITION_PIPELINE = [
    "bhavcopy_equity", "bhavcopy_fno", "corporate_actions",
    "equity_master", "stock_history_build",
]
INTELLIGENCE_PIPELINE = [
    "participant_5a", "participant_5b", "participant_5c",
    "sector_6a", "sector_6b", "sector_6c",
    "deals_7a", "events_7b", "corp_actions_7c",
    "momentum_8a", "bull_run_8b", "ml_12",
]
PIPELINE_SEQUENCE = ACQUISITION_PIPELINE + INTELLIGENCE_PIPELINE


# ── Status scan ───────────────────────────────────────────────────────────────

def _count_files(path: Path, pattern: str = "*.csv") -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob(pattern))


def _file_info(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "rows": 0, "last_modified": None, "as_of_date": None}
    try:
        df = pd.read_csv(path, low_memory=False)
        rows = len(df)
        mtime = pd.Timestamp(path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
        # Try common date columns
        as_of = None
        for col in ["as_of_date", "date", "last_date", "ex_date", "event_date"]:
            if col in df.columns:
                val = df[col].dropna()
                if not val.empty:
                    as_of = str(val.max())[:10]
                    break
        return {"exists": True, "rows": rows, "last_modified": mtime, "as_of_date": as_of}
    except Exception:
        return {"exists": True, "rows": 0, "last_modified": None, "as_of_date": None}


@router.get("/status")
def get_data_status():
    status = {}

    # ── Bhavcopy equity (canonical NSE path) ─────────────────────────────────
    eq_files = sorted(
        list(cfg.NSE_EQUITY_BHAVCOPY_DIR.rglob("*.csv")) +
        list(cfg.NSE_EQUITY_BHAVCOPY_DIR.rglob("*.gz"))
    )
    status["bhavcopy_equity"] = {
        "label": "Bhavcopy Equity",
        "status": "OK" if eq_files else "EMPTY",
        "records": f"{len(eq_files)} files",
        "coverage": f"{eq_files[0].parent.name if eq_files else '-'} → {eq_files[-1].parent.name if eq_files else '-'}",
        "last_modified": (
            pd.Timestamp(max(eq_files, key=lambda f: f.stat().st_mtime).stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
            if eq_files else None
        ),
    }

    # ── Bhavcopy F&O ─────────────────────────────────────────────────────────
    # Count only actual bhavcopy files (fo_YYYYMMDD.csv), not registry/coverage CSVs
    fno_files = sorted(cfg.NSE_FNO_BHAVCOPY_DIR.rglob("fo_*.csv"))
    fno_years = sorted({f.parent.name for f in fno_files if f.parent.name.isdigit()})
    fno_coverage = f"{fno_years[0]} - {fno_years[-1]}" if fno_years else "-"
    status["bhavcopy_fno"] = {
        "label": "Bhavcopy F&O",
        "status": "OK" if fno_files else "EMPTY",
        "records": f"{len(fno_files):,} files",
        "coverage": fno_coverage,
        "last_modified": (
            pd.Timestamp(max(fno_files, key=lambda f: f.stat().st_mtime).stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
            if fno_files else None
        ),
    }

    # ── Corporate actions ─────────────────────────────────────────────────────
    ca_files = sorted(cfg.CORPORATE_ACTIONS_DIR.glob("*.csv"))
    ca_rows = 0
    for f in ca_files:
        try:
            ca_rows += len(pd.read_csv(f, usecols=[0]))
        except Exception:
            pass
    status["corporate_actions"] = {
        "label": "Corporate Actions",
        "status": "OK" if ca_files else "EMPTY",
        "records": f"{ca_rows:,} rows / {len(ca_files)} year files",
        "coverage": f"{ca_files[0].stem if ca_files else '-'} → {ca_files[-1].stem if ca_files else '-'}",
        "last_modified": (
            pd.Timestamp(max(ca_files, key=lambda f: f.stat().st_mtime).stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
            if ca_files else None
        ),
    }

    # ── Equity master ─────────────────────────────────────────────────────────
    em_path = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
    em = _file_info(em_path)
    eq_count_master = 0
    if em["exists"]:
        try:
            df = pd.read_csv(em_path, usecols=["series"])
            eq_count_master = len(df[df["series"] == "EQ"])
        except Exception:
            pass
    status["equity_master"] = {
        "label": "Equity Master",
        "status": "OK" if em["exists"] else "EMPTY",
        "records": f"{em['rows']:,} symbols ({eq_count_master} EQ)",
        "coverage": "-",
        "last_modified": em["last_modified"],
    }

    # ── Index constituents ────────────────────────────────────────────────────
    idx_path = cfg.INDICES_DIR / "index_membership.csv"
    idx = _file_info(idx_path)
    status["index_constituents"] = {
        "label": "Index Constituents",
        "status": "OK" if idx["exists"] else "EMPTY",
        "records": f"{idx['rows']:,} memberships",
        "coverage": "-",
        "last_modified": idx["last_modified"],
    }

    # ── Holidays ──────────────────────────────────────────────────────────────
    hol = _file_info(cfg.NSE_HOLIDAY_FILE)
    status["holidays"] = {
        "label": "NSE Holidays",
        "status": "OK" if hol["exists"] else "EMPTY",
        "records": f"{hol['rows']} entries",
        "coverage": "-",
        "last_modified": hol["last_modified"],
    }

    # ── Participant flows ─────────────────────────────────────────────────────
    hist_dir = cfg.DATA_DIR / "historical" / "institutional"
    fno_hist = _file_info(hist_dir / "institutional_positioning_history.csv")
    cash_hist = _file_info(hist_dir / "cash_market_flows_history.csv")
    status["participant_flows"] = {
        "label": "Participant Flows (Raw)",
        "status": "OK" if fno_hist["exists"] else "EMPTY",
        "records": f"F&O {fno_hist['rows']:,} rows | Cash {cash_hist['rows']:,} rows",
        "coverage": f"up to {fno_hist['as_of_date'] or '-'}",
        "last_modified": fno_hist["last_modified"],
    }

    # ── Stock history cache ────────────────────────────────────────────────────
    cache_files = list(cfg.STOCK_HISTORY_CACHE.glob("*.parquet"))
    manifest_path = cfg.STOCK_HISTORY_CACHE / "manifest.json"
    manifest_data = {}
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text())
        except Exception:
            pass
    cache_last_date = manifest_data.get("last_processed_date")   # data date
    cache_mtime     = (
        pd.Timestamp(manifest_path.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")
        if manifest_path.exists() else None
    )
    # PARTIAL if data date is more than 30 days behind today
    import datetime as _dt
    cache_status = "EMPTY"
    if cache_files:
        if cache_last_date:
            days_behind = (_dt.date.today() - _dt.date.fromisoformat(cache_last_date)).days
            cache_status = "OK" if days_behind <= 30 else "PARTIAL"
        else:
            cache_status = "OK"
    status["stock_history_cache"] = {
        "label": "Stock History Cache",
        "status": cache_status,
        "records": (
            f"{len(cache_files):,} symbols | data to {cache_last_date}"
            if cache_last_date else f"{len(cache_files):,} symbol files"
        ),
        "coverage": f"up to {cache_last_date or '-'}",
        "last_modified": cache_mtime,   # file system time, not data date
    }

    # ── Intelligence outputs ──────────────────────────────────────────────────
    intel_files = {
        "participant_intelligence":       "participant_intelligence.csv",
        "participant_flow_scores":        "participant_flow_scores.csv",
        "sector_rotation_intelligence":   "sector_rotation_intelligence.csv",
        "sector_flow_scores":             "sector_flow_scores.csv",
        "bull_run_probability":           "bull_run_probability.csv",
        "bull_run_watchlist":             "bull_run_watchlist.csv",
        "deal_signals":                   "institutional_deal_signals.csv",
        "block_bulk_deals":               "block_bulk_deals.csv",
        "event_calendar":                 "event_calendar.csv",
        "upcoming_catalysts":             "upcoming_catalysts.csv",
        "corporate_confidence":           "corporate_confidence_scores.csv",
        "corporate_action_signals":       "corporate_action_signals.csv",
        "price_momentum":                 "price_momentum.csv",
        "ml_scores_combined":             "ml_scores_combined.csv",
    }
    intelligence = {}
    for key, fname in intel_files.items():
        info = _file_info(cfg.INTELLIGENCE_DIR / fname)
        intelligence[key] = {
            "label": fname.replace(".csv", "").replace("_", " ").title(),
            "status": "OK" if info["exists"] and info["rows"] > 0 else "EMPTY",
            "records": f"{info['rows']:,} rows" if info["exists"] else "0 rows",
            "as_of_date": info["as_of_date"],
            "last_modified": info["last_modified"],
        }

    return {
        "acquisition": status,
        "intelligence": intelligence,
        "engines": list(ENGINES.keys()),
    }


@router.get("/engines")
def list_engines():
    return {k: {"label": v["label"], "phase": v["phase"]} for k, v in ENGINES.items()}


# ── SSE engine runner ─────────────────────────────────────────────────────────

def _run_engine_sse(engine_name: str) -> Generator[str, None, None]:
    """Spawn engine subprocess and yield SSE lines from its stdout/stderr.

    Calls _kill_running() first so any stale subprocess is terminated before
    the new one starts.  Each generator captures its run_id at creation time
    and exits immediately if _current_run_id advances (i.e. a newer run or a
    manual kill arrived while this generator was mid-stream).
    """
    # Kill any stale process and capture our run-slot id
    _kill_running()
    my_run_id = _current_run_id

    if engine_name == "pipeline_all":
        engines_to_run = PIPELINE_SEQUENCE
    elif engine_name == "pipeline_acquisition":
        engines_to_run = ACQUISITION_PIPELINE
    elif engine_name == "pipeline_intelligence":
        engines_to_run = INTELLIGENCE_PIPELINE
    else:
        engines_to_run = [engine_name]

    for eng in engines_to_run:
        # Bail out if a newer run or kill arrived
        if _current_run_id != my_run_id:
            yield f"data: {json.dumps({'line': 'Stopped.', 'all_done': True})}\n\n"
            return

        if eng not in ENGINES:
            yield f"data: {json.dumps({'line': f'ERROR: Unknown engine {eng}'})}\n\n"
            continue

        cfg_eng = ENGINES[eng]
        script_path = ROOT / cfg_eng["script"]
        extra_args = cfg_eng.get("args", [])

        if not script_path.exists():
            msg = f"ERROR: Script not found: {cfg_eng['script']}"
            yield f"data: {json.dumps({'line': msg})}\n\n"
            continue

        cmd = [sys.executable, str(script_path)] + extra_args

        start_msg = f"--- Starting {cfg_eng['label']} ---"
        yield f"data: {json.dumps({'line': start_msg, 'engine': eng})}\n\n"

        q: queue.Queue = queue.Queue()

        def _reader(proc, q=q):
            try:
                for line in proc.stdout:
                    stripped = line.rstrip()
                    if _TQDM_RE.match(stripped):
                        item: dict = {"line": stripped, "type": "progress"}
                        m_pct = re.search(r'(\d+)%\|', stripped)
                        if m_pct:
                            item["pct"] = int(m_pct.group(1))
                        m_nd = re.search(r'\|\s*(\d+)/(\d+)\s*\[', stripped)
                        if m_nd:
                            item["n"] = int(m_nd.group(1))
                            item["total"] = int(m_nd.group(2))
                        m_time = re.search(r'\[(\d+:\d+)<(\d+:\d+)', stripped)
                        if m_time:
                            item["elapsed"] = m_time.group(1)
                            item["eta"] = m_time.group(2)
                        q.put(item)
                    elif stripped:
                        q.put({"line": stripped})
            finally:
                proc.wait()
                q.put({"_done": True, "exit_code": proc.returncode})

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(ROOT),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                bufsize=1,
            )
            _register_proc(proc)
            t = threading.Thread(target=_reader, args=(proc,), daemon=True)
            t.start()

            while True:
                # Check for external kill / newer run before blocking
                if _current_run_id != my_run_id:
                    yield f"data: {json.dumps({'line': 'Stopped by user.', 'all_done': True})}\n\n"
                    return
                try:
                    item = q.get(timeout=2)
                    if item.get("_done"):
                        break          # internal sentinel — do not forward to client
                    yield f"data: {json.dumps(item)}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'ping': True})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'line': f'ERROR launching process: {exc}', 'all_done': True, 'exit_code': -1})}\n\n"

    yield f"data: {json.dumps({'all_done': True})}\n\n"


@router.get("/run/{engine_name}")
def run_engine(engine_name: str):
    """SSE endpoint — stream live output from an engine subprocess."""
    valid = list(ENGINES.keys()) + ["pipeline_all", "pipeline_acquisition", "pipeline_intelligence"]
    if engine_name not in valid:
        return {"error": f"Unknown engine '{engine_name}'. Valid: {valid}"}

    return StreamingResponse(
        _run_engine_sse(engine_name),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
