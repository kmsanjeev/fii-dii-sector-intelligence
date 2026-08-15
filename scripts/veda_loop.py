"""Bounded persistent outer loop for one-activity VEDA Codex executions."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs" / "roadmap" / "veda" / "LOOP_STATE.json"
LOG_DIR = ROOT / ".veda-loop"
LOCK_PATH = LOG_DIR / "controller.lock"
DEFAULT_TIMEOUT = 1800
DEFAULT_RETRIES = 2


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
    # Only tracked modifications are unsafe at controller start. New controller
    # files may be staged/committed by the implementation workflow itself.
    return [line[3:] for line in output.splitlines() if line.strip() and not line.startswith("??")]


def select_next_priority(state: dict) -> str:
    if state.get("verified_empirical_cases", 0) < 25 and state.get("prospective_predictions", 0) == 0:
        return "EMPIRICAL_OR_PROSPECTIVE_EVIDENCE"
    if state.get("resolved_predictions", 0) < 10:
        return "TIMING_METHOD_VALIDATION_OR_OUTCOME_RESOLUTION"
    return "SOURCE_PROVENANCE_AND_CALIBRATION"


def compose_prompt(state: dict, *, repair: bool = False) -> str:
    mode = "REPAIR_CURRENT_ACTIVITY" if repair else "NORMAL_CONTINUATION"
    priority = select_next_priority(state)
    return f"""You are executing the VEDA autonomous engineering programme.

Read repository authority first and continue from the current LOOP_STATE.
This is one bounded Codex invocation, mode={mode}. Complete exactly ONE
highest-priority meaningful activity, then stop your own work and return a
dashboard. Do not begin a second major activity.

Current priority: {priority}
Current LOOP_STATE: {json.dumps(state, ensure_ascii=False)}

Preserve source trust zones, selective Git staging, no fake empirical cases,
no fabricated prospective subjects/outcomes, no force push, no autonomous
Approved Core promotion, and all existing human-validation statuses. If the
activity completes, update LOOP_STATE with the completed activity, commit/tag,
counts, blockers and next priority. The outer controller will invoke Codex
again automatically; a dashboard is not a programme stop.
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


def run_codex(prompt: str, timeout: int, output_path: Path) -> tuple[int, str, str]:
    command = ["codex", "exec", "--json", "--ephemeral", "--dangerously-bypass-approvals-and-sandbox", "-C", str(ROOT), "-"]
    error_path = output_path.with_suffix(".stderr.log")
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        with output_path.open("w", encoding="utf-8") as stdout_handle, error_path.open("w", encoding="utf-8") as stderr_handle:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout_handle, stderr=stderr_handle, text=True, encoding="utf-8", errors="replace", creationflags=creationflags)
            try:
                process.communicate(prompt, timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
                else:
                    process.kill()
                process.wait(timeout=15)
                return 124, output_path.read_text(encoding="utf-8", errors="replace"), error_path.read_text(encoding="utf-8", errors="replace")
        return process.returncode, output_path.read_text(encoding="utf-8", errors="replace"), error_path.read_text(encoding="utf-8", errors="replace")


def run(max_loops: int, retries: int, timeout: int, sleep_seconds: float, dry_run: bool) -> int:
    acquire_lock()
    try:
        initial = status_paths()
        allowed = {str(STATE_PATH.relative_to(ROOT)).replace("\\", "/")}
        unsafe = [path for path in initial if path not in allowed]
        if unsafe:
            print(f"refusing to run with unrelated tracked changes: {unsafe}", file=sys.stderr)
            return 2
        state = load_state()
        if dry_run:
            print(json.dumps({"state": state, "next_priority": select_next_priority(state), "command": "codex exec --json --dangerously-bypass-approvals-and-sandbox -C <repo> -"}, indent=2))
            return 0
        for _ in range(max_loops):
            state = load_state()
            if not state.get("enabled", True) or state.get("stop_reason"):
                return 0
            state["active_activity"] = select_next_priority(state)
            save_state(state)
            starting_head = git("rev-parse", "HEAD")
            start = now()
            prompt = compose_prompt(state)
            exit_code = 1
            stdout = stderr = ""
            output_path = LOG_DIR / f"iteration-{state['loop_number']:04d}.jsonl"
            for attempt in range(retries + 1):
                exit_code, stdout, stderr = run_codex(prompt, timeout, output_path)
                if exit_code == 0:
                    break
                if attempt < retries:
                    time.sleep(sleep_seconds)
            ending_head = git("rev-parse", "HEAD")
            paths = status_paths()
            unexpected = [path for path in paths if path not in allowed]
            record = {"iteration": state["loop_number"], "start_time": start, "end_time": now(), "activity": state["active_activity"], "exit_code": exit_code, "starting_head": starting_head, "ending_head": ending_head, "dirty_paths": unexpected, "next_priority": select_next_priority(state), "stop_reason": None if exit_code == 0 and not unexpected else "REPAIR_CURRENT_ACTIVITY"}
            append_log(record)
            state["last_commit"] = ending_head
            state["active_activity"] = None
            state["next_priority"] = select_next_priority(state)
            state["blockers"] = (["CODEX_PROCESS_FAILURE"] if exit_code else []) + (["UNEXPECTED_TRACKED_CHANGES"] if unexpected else [])
            state["stop_reason"] = "CRITICAL_REPOSITORY_FAILURE" if unexpected else None
            state["loop_number"] += 1
            save_state(state)
            if exit_code or unexpected:
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
    parser.add_argument("--codex-timeout-seconds", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--sleep-between-loops-seconds", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run(args.max_loops, args.max_codex_retries, args.codex_timeout_seconds, args.sleep_between_loops_seconds, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
