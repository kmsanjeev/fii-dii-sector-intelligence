"""Bounded persistent outer loop for one-activity VEDA Codex executions."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs" / "roadmap" / "veda" / "LOOP_STATE.json"
LOG_DIR = ROOT / ".veda-loop"
LOCK_PATH = LOG_DIR / "controller.lock"
DEFAULT_HARD_TIMEOUT = 1800
DEFAULT_IDLE_TIMEOUT = 300
DEFAULT_RETRIES = 2
TRACKS = ("CLASSICAL_KNOWLEDGE", "CALCULATION_VALIDATION", "TIMING", "EMPIRICAL", "PROSPECTIVE", "CALIBRATION_ML", "RAG", "MUHURTA", "PRASHNA", "GOVERNANCE")


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    state["updated_at"] = now()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()


def status_paths() -> list[str]:
    output = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True, encoding="utf-8", errors="replace")
    return [line[3:] for line in output.splitlines() if line.strip() and not line.startswith("??")]


def select_track(state: dict) -> str:
    blocked = set(state.get("blocked_tracks", []))
    if state.get("verified_empirical_cases", 0) < 25 and state.get("prospective_predictions", 0) == 0:
        if "EMPIRICAL" not in blocked:
            return "EMPIRICAL"
        if "PROSPECTIVE" not in blocked:
            return "PROSPECTIVE"
    if state.get("resolved_predictions", 0) < 10 and "TIMING" not in blocked:
        return "TIMING"
    return next(track for track in TRACKS if track not in blocked)


def select_next_priority(state: dict) -> str:
    track = select_track(state)
    return {"EMPIRICAL": "EMPIRICAL_OR_PROSPECTIVE_EVIDENCE", "PROSPECTIVE": "PROSPECTIVE_SHADOW_PREDICTIONS", "TIMING": "TIMING_METHOD_VALIDATION_OR_OUTCOME_RESOLUTION", "CALIBRATION_ML": "SOURCE_PROVENANCE_AND_CALIBRATION"}.get(track, f"{track}_VALIDATION")


def classify_failure(*, exit_code: int, hard_timeout: bool = False, idle_timeout: bool = False, interrupted: bool = False, protocol_error: bool = False) -> str | None:
    if hard_timeout:
        return "CODEX_HARD_TIMEOUT"
    if idle_timeout:
        return "CODEX_IDLE_TIMEOUT"
    if interrupted:
        return "CODEX_INTERRUPTED"
    if protocol_error:
        return "CODEX_PROTOCOL_ERROR"
    return "CODEX_EXIT_FAILURE" if exit_code else None


def partial_completion(*, starting_head: str, ending_head: str, output: str, timed_out: bool) -> str:
    if timed_out and (starting_head != ending_head or "dashboard" in output.lower()):
        return "ACTIVITY_COMPLETED_DESPITE_PROCESS_TIMEOUT"
    return "ACTIVITY_INCOMPLETE" if timed_out else "ACTIVITY_COMPLETED"


def compose_prompt(state: dict, *, repair: bool = False, budget_seconds: int = DEFAULT_HARD_TIMEOUT) -> str:
    mode = "REPAIR_CURRENT_ACTIVITY" if repair else "NORMAL_CONTINUATION"
    return f"""You are executing the VEDA autonomous engineering programme.

Read repository authority first and continue from LOOP_STATE. This is one
bounded Codex invocation, mode={mode}, track={select_track(state)},
priority={select_next_priority(state)}, execution budget={budget_seconds}
seconds. Complete exactly ONE coherent activity; if it cannot safely finish,
leave explicit resumable state rather than restarting or fabricating progress.

Current LOOP_STATE: {json.dumps(state, ensure_ascii=False)}

Preserve trust zones, selective Git staging, no fake empirical cases, no fake
prospective subjects/outcomes, no force push, no autonomous Approved Core
promotion, and all human-validation statuses. Update LOOP_STATE and return a
dashboard. The outer controller will invoke Codex again when allowed; a
dashboard is not a programme stop.
"""


def acquire_lock() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"another VEDA loop is active: {LOCK_PATH}") from exc
    os.close(fd)


def release_lock() -> None:
    LOCK_PATH.unlink(missing_ok=True)


def append_log(record: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    with (LOG_DIR / "iterations.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _reader(stream, events: queue.Queue, label: str) -> None:
    for line in iter(stream.readline, ""):
        events.put((label, line))
    stream.close()


def run_codex(prompt: str, hard_timeout: int, idle_timeout: int, output_path: Path, unsafe: bool, state: dict) -> dict:
    command = ["codex", "exec", "--json", "--ephemeral", "-C", str(ROOT)]
    command.append("--dangerously-bypass-approvals-and-sandbox" if unsafe else "--sandbox")
    if not unsafe:
        command.append("workspace-write")
    command.append("-")
    error_path = output_path.with_suffix(".stderr.log")
    events: queue.Queue = queue.Queue()
    start = time.monotonic()
    last_event = start
    event_count = 0
    last_type = None
    lines: list[str] = []
    errors: list[str] = []
    with output_path.open("w", encoding="utf-8") as stdout_handle, error_path.open("w", encoding="utf-8") as stderr_handle:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        process.stdin.write(prompt)
        process.stdin.close()
        threading.Thread(target=_reader, args=(process.stdout, events, "stdout"), daemon=True).start()
        threading.Thread(target=_reader, args=(process.stderr, events, "stderr"), daemon=True).start()
        failure = None
        while process.poll() is None or not events.empty():
            try:
                label, line = events.get(timeout=0.25)
            except queue.Empty:
                if process.poll() is not None:
                    continue
                elapsed = time.monotonic() - start
                if elapsed >= hard_timeout:
                    failure = "CODEX_HARD_TIMEOUT"
                    break
                if time.monotonic() - last_event >= idle_timeout:
                    failure = "CODEX_IDLE_TIMEOUT"
                    break
                continue
            last_event = time.monotonic()
            event_count += 1
            (lines if label == "stdout" else errors).append(line)
            if label == "stdout":
                stdout_handle.write(line)
                stdout_handle.flush()
                try:
                    last_type = json.loads(line).get("type")
                except json.JSONDecodeError:
                    last_type = "NON_JSON_OUTPUT"
            else:
                stderr_handle.write(line)
                stderr_handle.flush()
            state["last_codex_event_at"] = now()
            state["last_event_type"] = last_type
            state["event_count"] = event_count
            state["elapsed_seconds"] = round(time.monotonic() - start, 1)
            state["activity_status"] = "RUNNING"
            save_state(state)
        if failure:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
            else:
                process.kill()
            process.wait(timeout=15)
        elif process.poll() is None:
            process.wait(timeout=15)
        code = process.returncode if failure is None else 124
    stdout = "".join(lines)
    stderr = "".join(errors)
    output_path.write_text(stdout, encoding="utf-8")
    error_path.write_text(stderr, encoding="utf-8")
    ending_head = git("rev-parse", "HEAD")
    completion = partial_completion(starting_head=state.get("last_commit", ending_head), ending_head=ending_head, output=stdout, timed_out=failure is not None)
    return {"exit_code": code, "stdout": stdout, "stderr": stderr, "failure": failure or classify_failure(exit_code=code), "event_count": event_count, "last_event_type": last_type, "elapsed_seconds": round(time.monotonic() - start, 1), "completion": completion, "completed_despite_timeout": completion == "ACTIVITY_COMPLETED_DESPITE_PROCESS_TIMEOUT"}


def run(max_loops: int, retries: int, hard_timeout: int, idle_timeout: int, sleep_seconds: float, dry_run: bool, unsafe: bool) -> int:
    acquire_lock()
    try:
        state = load_state()
        allowed = {str(STATE_PATH.relative_to(ROOT)).replace("\\", "/")}
        unsafe_changes = [path for path in status_paths() if path not in allowed]
        if unsafe_changes:
            print(f"refusing to run with unrelated tracked changes: {unsafe_changes}", file=sys.stderr)
            return 2
        if dry_run:
            print(json.dumps({"selected_track": select_track(state), "selected_priority": select_next_priority(state), "blocked_tracks": state.get("blocked_tracks", []), "safe_execution": not unsafe, "unsafe_opt_in": unsafe, "hard_timeout_seconds": hard_timeout, "idle_timeout_seconds": idle_timeout, "retry_limit": retries, "max_loops": max_loops}, indent=2))
            return 0
        for _ in range(max_loops):
            state = load_state()
            if not state.get("enabled", True) or state.get("stop_reason"):
                return 0
            state["active_activity"] = select_next_priority(state)
            state["active_track"] = select_track(state)
            state["controller_state"] = "RUNNING"
            state["iteration_started_at"] = now()
            save_state(state)
            starting_head = git("rev-parse", "HEAD")
            result = None
            output_path = LOG_DIR / f"iteration-{state['loop_number']:04d}.jsonl"
            for attempt in range(retries + 1):
                result = run_codex(compose_prompt(state, repair=attempt > 0, budget_seconds=hard_timeout), hard_timeout, idle_timeout, output_path, unsafe, state)
                if result["exit_code"] == 0:
                    break
                if attempt < retries:
                    state["controller_state"] = "REPAIR_REQUIRED"
                    save_state(state)
                    time.sleep(sleep_seconds)
            ending_head = git("rev-parse", "HEAD")
            unexpected = [path for path in status_paths() if path not in allowed]
            progress = ending_head != starting_head or result["completed_despite_timeout"]
            completed_track = state.get("active_track")
            state["controller_state"] = "VERIFYING"
            state["last_commit"] = ending_head
            state["active_activity"] = None
            state["active_track"] = None
            state["activity_status"] = "COMPLETED" if result["exit_code"] == 0 or result["completed_despite_timeout"] else "FAILED"
            state["next_priority"] = select_next_priority(state)
            metrics = state.setdefault("metrics", {})
            metrics["loops_completed"] = metrics.get("loops_completed", 0) + (1 if result["exit_code"] == 0 else 0)
            metrics["loops_failed"] = metrics.get("loops_failed", 0) + (1 if result["exit_code"] else 0)
            metrics["timeouts"] = metrics.get("timeouts", 0) + (1 if result["failure"] in {"CODEX_HARD_TIMEOUT", "CODEX_IDLE_TIMEOUT"} else 0)
            metrics["consecutive_zero_progress"] = 0 if progress else metrics.get("consecutive_zero_progress", 0) + 1
            if metrics["consecutive_zero_progress"] >= 2:
                state.setdefault("blocked_tracks", [])
                if completed_track not in state["blocked_tracks"]:
                    state["blocked_tracks"].append(completed_track or "EMPIRICAL")
                metrics["track_switches"] = metrics.get("track_switches", 0) + 1
            if result["failure"]:
                state["blockers"] = [result["failure"]]
                state["controller_state"] = "REPAIR_REQUIRED"
            if unexpected:
                state["blockers"] = ["UNEXPECTED_TRACKED_CHANGES"]
                state["stop_reason"] = "CRITICAL_REPOSITORY_FAILURE"
            append_log({"iteration": state["loop_number"], "start_time": state.get("iteration_started_at"), "end_time": now(), "activity": state.get("next_priority"), "exit_code": result["exit_code"], "failure": result["failure"], "event_count": result["event_count"], "last_event_type": result["last_event_type"], "elapsed_seconds": result["elapsed_seconds"], "starting_head": starting_head, "ending_head": ending_head, "dirty_paths": unexpected, "completed_despite_timeout": result["completed_despite_timeout"], "next_priority": state["next_priority"]})
            state["loop_number"] += 1
            save_state(state)
            if unexpected:
                return 1
            if sleep_seconds:
                time.sleep(sleep_seconds)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        release_lock()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-loops", type=int, default=10)
    parser.add_argument("--max-codex-retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--hard-timeout-seconds", type=int, default=DEFAULT_HARD_TIMEOUT)
    parser.add_argument("--idle-timeout-seconds", type=int, default=DEFAULT_IDLE_TIMEOUT)
    parser.add_argument("--codex-timeout-seconds", type=int)
    parser.add_argument("--sleep-between-loops-seconds", type=float, default=1.0)
    parser.add_argument("--unsafe-codex", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    hard_timeout = args.codex_timeout_seconds or args.hard_timeout_seconds
    return run(args.max_loops, args.max_codex_retries, hard_timeout, args.idle_timeout_seconds, args.sleep_between_loops_seconds, args.dry_run, args.unsafe_codex)


if __name__ == "__main__":
    raise SystemExit(main())
