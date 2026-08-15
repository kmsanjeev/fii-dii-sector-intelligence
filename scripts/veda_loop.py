"""Bounded persistent outer loop for one-activity VEDA Codex executions."""

from __future__ import annotations

import argparse
import hashlib
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
TRACKS = ("CLASSICAL_KNOWLEDGE", "CALCULATION_VALIDATION", "TIMING", "EMPIRICAL", "PROSPECTIVE", "CALIBRATION_ML", "RAG", "MUHURTA", "PRASHNA", "GOVERNANCE", "CLASSICAL_SOURCE_EXPANSION", "TIMING_VALIDATION", "METHOD_COMPARISON", "TAJIKA_FOUNDATION", "ASHTAKAVARGA_VALIDATION", "SHADBALA_VALIDATION", "MUHURTA_SOURCE_EXPANSION", "EMPIRICAL_INPUT_PREPARATION", "PROSPECTIVE_SUBJECT_DISCOVERY")
ACTIVITIES = {
    "CLASSICAL_KNOWLEDGE": ("CLASSICAL_KNOWLEDGE_VALIDATION", "VALIDATION", "Classical knowledge source validation"),
    "CALCULATION_VALIDATION": ("CALCULATION_VALIDATION", "VALIDATION", "Calculation validation"),
    "TIMING": ("TIMING_METHOD_VALIDATION", "VALIDATION", "Timing method validation"),
    "EMPIRICAL": ("EMPIRICAL_EVIDENCE", "EVIDENCE_RECONCILIATION", "Empirical evidence reconciliation"),
    "PROSPECTIVE": ("PROSPECTIVE_SHADOW_PREDICTION", "SHADOW_PREDICTION", "Prospective shadow prediction"),
    "CALIBRATION_ML": ("SOURCE_PROVENANCE_CALIBRATION", "VALIDATION", "Source provenance and calibration"),
    "RAG": ("RAG_VALIDATION", "VALIDATION", "RAG validation"),
    "MUHURTA": ("MUHURTA_READINESS", "ROADMAP_READINESS", "Muhurta readiness"),
    "PRASHNA": ("PRASHNA_READINESS", "ROADMAP_READINESS", "Prashna readiness"),
    "GOVERNANCE": ("GOVERNANCE_RECONCILIATION", "GOVERNANCE", "Governance reconciliation"),
    "CLASSICAL_SOURCE_EXPANSION": ("CLASSICAL_SOURCE_EXPANSION", "SOURCE_RESEARCH", "Classical source expansion"),
    "TIMING_VALIDATION": ("TIMING_VALIDATION", "TIMING_RESEARCH", "Timing validation"),
    "METHOD_COMPARISON": ("METHOD_COMPARISON", "VARIANT_RESEARCH", "Method variant comparison"),
    "TAJIKA_FOUNDATION": ("TAJIKA_FOUNDATION", "CALCULATION_RESEARCH", "Tajika and annual forecasting foundation"),
    "ASHTAKAVARGA_VALIDATION": ("ASHTAKAVARGA_VALIDATION", "CALCULATION_RESEARCH", "Ashtakavarga predictive validation"),
    "SHADBALA_VALIDATION": ("SHADBALA_VALIDATION", "CALCULATION_RESEARCH", "Shadbala source validation"),
    "MUHURTA_SOURCE_EXPANSION": ("MUHURTA_SOURCE_EXPANSION", "SOURCE_RESEARCH", "Muhurta source expansion"),
    "EMPIRICAL_INPUT_PREPARATION": ("EMPIRICAL_CASE_ACQUISITION", "INPUT_GOVERNANCE", "Empirical case acquisition"),
    "PROSPECTIVE_SUBJECT_DISCOVERY": ("PROSPECTIVE_SUBJECT_DISCOVERY", "INPUT_GOVERNANCE", "Prospective subject discovery"),
}
ACTIVITY_CONTRACTS = {
    "CLASSICAL_SOURCE_EXPANSION": {"question": "Which unresolved rule family has a new source family or passage?", "expected": "new source passage or lineage conclusion", "novelty": "HIGH", "gain": "HIGH"},
    "TIMING_VALIDATION": {"question": "Which unresolved timing claim can be validated against a changed input or new source?", "expected": "new validated timing rule or explicit negative finding", "novelty": "LOW", "gain": "MEDIUM"},
    "METHOD_COMPARISON": {"question": "Which two legitimate methods produce the better-governed result for a shared comparison input?", "expected": "independent method comparison outcome", "novelty": "HIGH", "gain": "HIGH"},
    "TAJIKA_FOUNDATION": {"question": "Which Tajika foundation dependency is currently unresolved?", "expected": "new source-backed calculation or dependency finding", "novelty": "HIGH", "gain": "HIGH"},
    "ASHTAKAVARGA_VALIDATION": {"question": "Which Ashtakavarga validation claim remains unresolved?", "expected": "independent fixture or validation conclusion", "novelty": "HIGH", "gain": "HIGH"},
    "SHADBALA_VALIDATION": {"question": "Which Shadbala method or source discrepancy remains unresolved?", "expected": "method comparison or defect finding", "novelty": "HIGH", "gain": "HIGH"},
    "MUHURTA_SOURCE_EXPANSION": {"question": "Which missing Muhurta source family resolves a documented dependency?", "expected": "new source passage or dependency conclusion", "novelty": "HIGH", "gain": "MEDIUM"},
    "EMPIRICAL_INPUT_PREPARATION": {"question": "Which measurable acquisition step increases verified usable empirical cases?", "expected": "new identity, event, timezone resolution, exclusion, or eligible case", "novelty": "HIGH", "gain": "HIGH"},
    "PROSPECTIVE_SUBJECT_DISCOVERY": {"question": "What new consented subject or event avenue can close the prospective blocker?", "expected": "new admissible subject avenue", "novelty": "MEDIUM", "gain": "HIGH"},
}
for _track, (_activity_id, _activity_type, _title) in ACTIVITIES.items():
    ACTIVITY_CONTRACTS.setdefault(_track, {"question": f"What unresolved {_track.lower()} question can current inputs answer?", "expected": "new authoritative conclusion", "novelty": "MEDIUM", "gain": "MEDIUM"})
AUTHORITATIVE_ACTIVITY_OUTPUTS = {
    "docs/current-state/pred-004/06_SOURCE_PROVENANCE_AND_CALIBRATION.md",
    "docs/PROJECT_MASTER_STATE.md",
    "docs/governance/CHANGELOG.md",
}
TRANSIENT_RUN_STOPS = {"LOW_VALUE_REPETITION", "MAX_LOOPS_REACHED", "COOLDOWN_EXHAUSTED_FOR_CURRENT_RUN"}
HUMAN_BLOCK_STOPS = {"FOUNDER_APPROVAL_REQUIRED", "DESTRUCTIVE_MIGRATION_APPROVAL_REQUIRED", "CREDENTIAL_REQUIRED"}
PROGRAMME_STOPS = {"NO_MEANINGFUL_NEXT_ACTIVITY", "LONGITUDINAL_ONLY_REMAINS", "CRITICAL_REPOSITORY_FAILURE", "USER_REQUESTED_STOP"}


class NoAvailableTrackError(RuntimeError):
    """Raised when every configured track is explicitly blocked."""


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


def status_entries() -> list[dict[str, str]]:
    output = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True, encoding="utf-8", errors="replace")
    entries = []
    for line in output.splitlines():
        if line.strip():
            entries.append({"code": line[:2], "path": line[3:]})
    return entries


def _stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def activity_contract(track: str) -> dict:
    return dict(ACTIVITY_CONTRACTS[track])


def stop_reason_code(stop_reason: str | None) -> str | None:
    if not stop_reason:
        return None
    return stop_reason.split(":", 1)[0].strip()


def classify_stop_reason(stop_reason: str | None) -> str:
    code = stop_reason_code(stop_reason)
    if code in TRANSIENT_RUN_STOPS:
        return "TRANSIENT_RUN_STOP"
    if code in HUMAN_BLOCK_STOPS:
        return "HUMAN_BLOCK"
    if code == "ROADMAP_REBASELINE_REQUIRED":
        return "RECOVERABLE_FAILURE"
    if code in PROGRAMME_STOPS:
        return "PROGRAMME_STOP"
    if code in {"LEGITIMATE_INPUT_REQUIRED", "ALL_TRACKS_BLOCKED"}:
        return "TRACK_BLOCKER"
    return "PROGRAMME_STOP" if code else "NONE"


def _stored_priority_decision(state: dict) -> dict | None:
    priority = state.get("next_priority")
    if not priority:
        return None
    return next((item for item in candidate_decisions(state) if item["track"] == priority or item["activity_id"] == priority), None)


def resume_from_transient_stop(state: dict, *, dry_run: bool = False) -> dict:
    classification = classify_stop_reason(state.get("stop_reason"))
    result = {"classification": classification, "resumed": False, "selected": None, "reason": state.get("stop_reason")}
    if classification != "TRANSIENT_RUN_STOP":
        return result
    decision = _stored_priority_decision(state)
    if not decision or not decision["selected"]:
        candidates = [item for item in candidate_decisions(state) if item["selected"]]
        decision = max(candidates, key=lambda item: (item["score"], -TRACKS.index(item["track"]))) if candidates else None
    if not decision:
        result["reason"] = "NO_ELIGIBLE_RESUME_PRIORITY"
        return result
    result["resumed"] = True
    result["selected"] = decision["track"]
    result["reason"] = None
    if not dry_run:
        state.setdefault("stop_history", []).append({"reason": state.get("stop_reason"), "classification": classification, "recorded_at": now(), "resumed_as": decision["track"]})
        state["stop_history"] = state["stop_history"][-25:]
        state["stop_reason"] = None
        state["controller_state"] = "READY"
        state["activity_status"] = "READY"
        state["next_priority"] = decision["track"]
        state["programme_status"] = state.get("programme_status", "ACTIVE") or "ACTIVE"
        state["resume_event"] = {"from": classification, "selected": decision["track"], "recorded_at": now()}
        save_state(state)
    return result


def relevant_input_fingerprint(state: dict, track: str) -> str:
    payload = {
        "head": state.get("input_revision") or state.get("last_commit") or "",
        "knowledge_counts": state.get("knowledge_counts", {}),
        "empirical_cases": state.get("verified_empirical_cases", 0),
        "prospective_predictions": state.get("prospective_predictions", 0),
        "resolved_predictions": state.get("resolved_predictions", 0),
        "blockers": sorted(state.get("blockers", [])),
        "blocked_tracks": sorted(state.get("blocked_tracks", [])),
        "dependency_state": state.get("dependency_state", {}),
        "method_versions": state.get("method_versions", {}),
        "roadmap_state": state.get("roadmap_state", {}),
        "track": track,
        "question": activity_contract(track)["question"],
    }
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]


def output_fingerprint(*, starting_head: str, ending_head: str, paths: list[str] | None = None, deltas: dict | None = None) -> str:
    payload = {"starting_head": starting_head, "ending_head": ending_head, "paths": sorted(paths or []), "deltas": deltas or {}}
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]


def _history_for(state: dict, track: str) -> list[dict]:
    activity_id = ACTIVITIES[track][0]
    return [item for item in state.get("activity_history", []) if item.get("activity_id") == activity_id or item.get("track") == track]


def _same_input_no_progress(state: dict, track: str) -> bool:
    fingerprint = relevant_input_fingerprint(state, track)
    return any(item.get("input_fingerprint") == fingerprint and item.get("material_progress") in {"NO_NEW_INFORMATION", "LOW_INFORMATION_GAIN", "DOCUMENTATION_ONLY"} for item in _history_for(state, track))


def _same_input_repeat(state: dict, track: str) -> bool:
    fingerprint = relevant_input_fingerprint(state, track)
    return any(item.get("input_fingerprint") == fingerprint for item in _history_for(state, track))


def candidate_decisions(state: dict) -> list[dict]:
    blocked = set(state.get("blocked_tracks", []))
    previous = state.get("last_completed_activity") or (state.get("activity_identity") or {}).get("activity_id")
    decisions = []
    for track in TRACKS:
        contract = activity_contract(track)
        fingerprint = relevant_input_fingerprint(state, track)
        history = _history_for(state, track)
        same_input = _same_input_no_progress(state, track)
        same_input_repeat = _same_input_repeat(state, track)
        cooldowns = state.get("cooldowns", {})
        cooldown = cooldowns.get(ACTIVITIES[track][0])
        reasons = []
        if state.get("available_tracks") and track not in state["available_tracks"]:
            reasons.append("NOT_AVAILABLE")
        if track in blocked:
            reasons.append("BLOCKED")
        if cooldown and cooldown.get("input_fingerprint") == fingerprint and not state.get("manual_override"):
            reasons.append("COOLDOWN")
        if same_input:
            reasons.append("SAME_INPUT_NO_PROGRESS")
        if same_input_repeat and "SAME_INPUT_NO_PROGRESS" not in reasons:
            reasons.append("SAME_INPUT_REPEAT")
        if previous == ACTIVITIES[track][0] and same_input_repeat:
            reasons.append("CONSECUTIVE_REPEAT")
        selected = not reasons
        score = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}[contract["gain"]]
        if previous == ACTIVITIES[track][0]:
            score -= 1
        if history and not same_input:
            score += 1
        decisions.append({"track": track, "activity_id": ACTIVITIES[track][0], "question": contract["question"], "expected_information_gain": contract["gain"], "novelty": contract["novelty"], "input_fingerprint": fingerprint, "relevant_input_changed": bool(history and not same_input), "selected": selected, "rejected": reasons, "score": score})
    return decisions


def select_track(state: dict) -> str:
    blocked = set(state.get("blocked_tracks", []))
    # Preserve the compact pre-R3 helper contract for callers that provide only
    # the legacy counters. Persisted controller state always carries the R3
    # scheduler fields and uses candidate_decisions below.
    if not any(key in state for key in ("activity_history", "cooldowns", "selection_trace", "available_tracks")):
        if state.get("verified_empirical_cases", 0) < 25 and state.get("prospective_predictions", 0) == 0:
            if "EMPIRICAL" not in blocked:
                return "EMPIRICAL"
            if "PROSPECTIVE" not in blocked:
                return "PROSPECTIVE"
        if state.get("resolved_predictions", 0) < 10 and "TIMING" not in blocked:
            return "TIMING"
        for track in TRACKS:
            if track not in blocked:
                return track
        raise NoAvailableTrackError("ALL_TRACKS_BLOCKED")
    candidates = [item for item in candidate_decisions(state) if item["selected"]]
    if candidates:
        # Keep roadmap urgency, then information gain, then track diversity, then stable order.
        if state.get("resolved_predictions", 0) < 10 and "TIMING" not in blocked:
            timing = next((item for item in candidates if item["track"] == "TIMING"), None)
            if timing:
                return "TIMING"
        return max(candidates, key=lambda item: (item["score"], -TRACKS.index(item["track"])))["track"]
    raise NoAvailableTrackError("ALL_TRACKS_BLOCKED")


def select_next_priority(state: dict) -> str:
    track = select_track(state)
    return {"EMPIRICAL": "EMPIRICAL_EVIDENCE", "PROSPECTIVE": "PROSPECTIVE_SHADOW_PREDICTION", "TIMING": "TIMING_METHOD_VALIDATION", "CALIBRATION_ML": "SOURCE_PROVENANCE_CALIBRATION"}.get(track, ACTIVITIES[track][0])


def activity_identity(state: dict) -> dict[str, str]:
    track = select_track(state)
    activity_id, activity_type, title = ACTIVITIES[track]
    return {"activity_id": activity_id, "track": track, "activity_type": activity_type, "title": title}


def classify_material_progress(*, activity: dict, starting_head: str, ending_head: str, validation_gain: bool = False, defect_closed: bool = False, evidence_gain: bool = False, blocker_refined: bool = False) -> str:
    if starting_head != ending_head:
        return "REPOSITORY_CHANGE"
    if defect_closed:
        return "DEFECT_CLOSED"
    if evidence_gain:
        return "EVIDENCE_GAIN"
    if blocker_refined:
        return "BLOCKER_REFINED"
    if validation_gain:
        return "VALIDATION_GAIN"
    return "NO_MATERIAL_PROGRESS"


def classify_activity_result(*, starting_head: str, ending_head: str, output: str, activity_outputs: list[str], exit_code: int) -> str:
    if ending_head != starting_head:
        return "HIGH_INFORMATION_GAIN"
    if exit_code != 0:
        return "NO_NEW_INFORMATION"
    lowered = output.lower()
    evidence_markers = ("new source passage", "new verified claim", "new validated", "new defect", "defect closed", "comparison outcome", "new independent fixture", "blocker closed", "blocker refined", "material contradiction")
    if any(marker in lowered for marker in evidence_markers):
        return "MEDIUM_INFORMATION_GAIN"
    if any(marker in lowered for marker in ("validated_no_change", "no new information", "no material progress", "unchanged inputs")):
        return "NO_NEW_INFORMATION"
    if activity_outputs:
        return "DOCUMENTATION_ONLY"
    return "NO_NEW_INFORMATION"


def classify_output(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized in AUTHORITATIVE_ACTIVITY_OUTPUTS:
        return "AUTHORITATIVE_ACTIVITY_OUTPUT"
    if normalized.startswith("docs/current-state/rm-002/") and normalized.endswith(".md"):
        return "AUTHORITATIVE_ACTIVITY_OUTPUT"
    if normalized.startswith("data/veda/research/astrology/sources/") and normalized.endswith(".json"):
        return "AUTHORITATIVE_ACTIVITY_OUTPUT"
    if normalized.startswith("data/veda/validation/foundation/p018_strength/") and normalized.endswith(".json"):
        return "AUTHORITATIVE_ACTIVITY_OUTPUT"
    if normalized in {"docs/PROJECT_MASTER_STATE.md", "docs/governance/CHANGELOG.md"}:
        return "AUTHORITATIVE_ACTIVITY_OUTPUT"
    if normalized.startswith(".veda-loop/"):
        return "RUNTIME"
    if normalized.startswith("docs/roadmap/veda/LOOP_STATE.json"):
        return "GENERATED_AUTHORITY"
    return "UNRELATED"


def validate_authoritative_output(path: str) -> bool:
    candidate = ROOT / path
    if not candidate.is_file():
        return False
    if path.replace("\\", "/").startswith("data/veda/research/astrology/sources/"):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return isinstance(payload, dict) and payload.get("source_id", "").startswith("VEDA-SRC-") and bool(payload.get("title_normalized"))
    if path.replace("\\", "/").startswith("data/veda/validation/foundation/p018_strength/"):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return isinstance(payload, dict) and bool(payload.get("fixture_id")) and payload.get("approved_core") is False
    text = candidate.read_text(encoding="utf-8", errors="replace")
    if path.replace("\\", "/") == "docs/current-state/pred-004/06_SOURCE_PROVENANCE_AND_CALIBRATION.md":
        return all(item.lower() in text.lower() for item in ("PRED-004", "Source Provenance", "No consented"))
    return text.lstrip().startswith("#") and len(text.strip()) >= 120


def reconcile_outputs() -> dict:
    entries = status_entries()
    classified = [{"path": entry["path"], "classification": classify_output(entry["path"]), "code": entry["code"]} for entry in entries]
    authoritative = [item["path"] for item in classified if item["classification"] == "AUTHORITATIVE_ACTIVITY_OUTPUT"]
    return {
        "entries": classified,
        "authoritative_uncommitted": authoritative,
        "invalid_authoritative": [path for path in authoritative if not validate_authoritative_output(path)],
        "temporary_remaining": [item["path"] for item in classified if item["classification"] == "RUNTIME"],
        "unexpected": [item["path"] for item in classified if item["classification"] == "UNRELATED"],
    }


def commit_authoritative_outputs(paths: list[str]) -> dict:
    if not paths:
        return {"committed": [], "error": None}
    if any(not validate_authoritative_output(path) for path in paths):
        return {"committed": [], "error": "INVALID_AUTHORITATIVE_OUTPUT"}
    subprocess.check_call(["git", "add", "--", *paths], cwd=ROOT)
    staged_paths = set(git("diff", "--cached", "--name-only").splitlines())
    if any(path in staged_paths for path in paths):
        return {"committed": [], "error": None}
    subprocess.check_call(["git", "commit", "-m", "docs(veda): reconcile autonomous activity output"], cwd=ROOT)
    subprocess.check_call(["git", "push", "origin", "main"], cwd=ROOT)
    return {"committed": paths, "error": None}


def completion_state(*, exit_code: int, reconciliation: dict, stop_reason: str | None = None) -> str:
    if stop_reason:
        return "STOPPED"
    if reconciliation["invalid_authoritative"] or reconciliation["unexpected"]:
        return "REPAIR_REQUIRED"
    return "ACTIVITY_COMPLETED_NO_REPO_CHANGE" if exit_code == 0 and not reconciliation["authoritative_uncommitted"] else "ACTIVITY_COMPLETED"


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
        resume_preview = resume_from_transient_stop(state, dry_run=dry_run)
        if dry_run:
            try:
                selected_track = select_track(state)
                selected_priority = select_next_priority(state)
                decisions = candidate_decisions(state)
                selected = next(item for item in decisions if item["track"] == selected_track)
            except NoAvailableTrackError:
                selected_track = None
                selected_priority = None
                decisions = candidate_decisions(state)
                selected = None
            print(json.dumps({"resume_classification": resume_preview["classification"], "would_resume": resume_preview["resumed"], "resume_selected": resume_preview["selected"], "selected_track": selected_track, "selected_priority": selected_priority, "question_to_resolve": selected["question"] if selected else None, "expected_information_gain": selected["expected_information_gain"] if selected else None, "novelty": selected["novelty"] if selected else None, "relevant_input_changed": selected["relevant_input_changed"] if selected else None, "suppressed": [{"track": item["track"], "reason": item["rejected"]} for item in decisions if not item["selected"]], "cooldowns": state.get("cooldowns", {}), "next_alternative": next((item["track"] for item in decisions if item["selected"] and item["track"] != selected_track), None), "blocked_tracks": state.get("blocked_tracks", []), "safe_execution": not unsafe, "unsafe_opt_in": unsafe, "hard_timeout_seconds": hard_timeout, "idle_timeout_seconds": idle_timeout, "retry_limit": retries, "max_loops": max_loops}, indent=2))
            return 0
        for _ in range(max_loops):
            state = load_state()
            if not state.get("enabled", True):
                return 0
            if state.get("stop_reason"):
                resume_from_transient_stop(state)
                state = load_state()
                if state.get("stop_reason"):
                    return 0
            try:
                identity = activity_identity(state)
            except NoAvailableTrackError:
                state["active_activity"] = None
                state["active_track"] = None
                state["controller_state"] = "STOPPED"
                state["activity_status"] = "BLOCKED"
                state["stop_reason"] = "ALL_TRACKS_BLOCKED"
                state["next_priority"] = None
                state["run_summary"] = {"loops_requested": max_loops, "loops_completed": 0, "activities_completed": 0, "repository_changes": False, "commits_created": 0, "authoritative_uncommitted_files": 0, "temporary_files_remaining": 0, "unexpected_files": 0, "material_progress": "NO_MATERIAL_PROGRESS", "validation_only_progress": False, "stop_reason": "ALL_TRACKS_BLOCKED", "next_priority": None}
                save_state(state)
                return 0
            state["active_activity"] = identity["activity_id"]
            state["active_track"] = identity["track"]
            state["activity_identity"] = identity
            contract = activity_contract(identity["track"])
            state["selected_decision"] = {"question": contract["question"], "expected_information_gain": contract["gain"], "novelty": contract["novelty"], "input_fingerprint": relevant_input_fingerprint(state, identity["track"]), "candidates": candidate_decisions(state)}
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
            reconciliation_entries = status_entries()
            activity_outputs = [entry["path"] for entry in reconciliation_entries if classify_output(entry["path"]) == "AUTHORITATIVE_ACTIVITY_OUTPUT"]
            unexpected = [entry["path"] for entry in reconciliation_entries if entry["path"] not in allowed and classify_output(entry["path"]) not in {"AUTHORITATIVE_ACTIVITY_OUTPUT", "GENERATED_AUTHORITY", "RUNTIME"}]
            material_progress = classify_activity_result(starting_head=starting_head, ending_head=ending_head, output=result["stdout"], activity_outputs=activity_outputs, exit_code=result["exit_code"])
            progress = material_progress not in {"NO_NEW_INFORMATION", "DOCUMENTATION_ONLY"} or result["completed_despite_timeout"]
            completed_track = state.get("active_track")
            state["last_completed_activity"] = identity["activity_id"] if result["exit_code"] == 0 or result["completed_despite_timeout"] else state.get("last_completed_activity")
            state["controller_state"] = "VERIFYING"
            state["last_commit"] = ending_head
            state["active_activity"] = None
            state["active_track"] = None
            state["activity_status"] = "COMPLETED" if result["exit_code"] == 0 or result["completed_despite_timeout"] else "FAILED"
            state["next_priority"] = select_next_priority(state)
            state["completion_state"] = "ACTIVITY_COMPLETED_NO_REPO_CHANGE" if result["exit_code"] == 0 and ending_head == starting_head else ("REPOSITORY_CHANGE" if ending_head != starting_head else "ACTIVITY_INCOMPLETE")
            metrics = state.setdefault("metrics", {})
            metrics["loops_completed"] = metrics.get("loops_completed", 0) + (1 if result["exit_code"] == 0 else 0)
            metrics["loops_failed"] = metrics.get("loops_failed", 0) + (1 if result["exit_code"] else 0)
            metrics["timeouts"] = metrics.get("timeouts", 0) + (1 if result["failure"] in {"CODEX_HARD_TIMEOUT", "CODEX_IDLE_TIMEOUT"} else 0)
            metrics["consecutive_zero_progress"] = 0 if progress else metrics.get("consecutive_zero_progress", 0) + 1
            if not progress:
                state.setdefault("cooldowns", {})[identity["activity_id"]] = {"input_fingerprint": relevant_input_fingerprint(state, completed_track), "reason": material_progress, "release_conditions": ["relevant inputs changed", "new source arrived", "dependency changed", "method changed", "manual override", "justified cooldown expiry"], "set_at": now()}
                metrics["track_switches"] = metrics.get("track_switches", 0) + 1
            if result["failure"]:
                state["blockers"] = [result["failure"]]
                state["controller_state"] = "REPAIR_REQUIRED"
            if unexpected:
                state["blockers"] = ["UNEXPECTED_TRACKED_CHANGES"]
                state["stop_reason"] = "CRITICAL_REPOSITORY_FAILURE"
            elif not result["failure"]:
                state["stop_reason"] = None
            state["material_progress"] = material_progress
            history_record = {"activity_id": identity["activity_id"], "activity_type": identity["activity_type"], "track": identity["track"], "started_at": state.get("iteration_started_at"), "completed_at": now(), "starting_head": starting_head, "ending_head": ending_head, "repository_delta": ending_head != starting_head, "knowledge_delta": {}, "evidence_delta": {}, "blocker_delta": {}, "validation_delta": {}, "material_progress": material_progress, "input_fingerprint": relevant_input_fingerprint(state, completed_track), "output_fingerprint": output_fingerprint(starting_head=starting_head, ending_head=ending_head, paths=activity_outputs), "result": result["completion"], "stop_reason": result["failure"], "question_to_resolve": contract["question"], "expected_information_gain": contract["gain"], "novelty": contract["novelty"]}
            state.setdefault("activity_history", []).append(history_record)
            state["activity_history"] = state["activity_history"][-50:]
            state["selection_trace"] = {"candidates_considered": [item["track"] for item in state.get("selected_decision", {}).get("candidates", [])], "selected": identity["activity_id"], "rejected": {item["track"]: item["rejected"] for item in state.get("selected_decision", {}).get("candidates", []) if item["rejected"]}, "cooldown": state.get("cooldowns", {}), "novelty": contract["novelty"], "expected_information_gain": contract["gain"], "why_selected": contract["question"]}
            append_log({"iteration": state["loop_number"], "start_time": state.get("iteration_started_at"), "end_time": now(), "activity": identity["activity_id"], "track": identity["track"], "activity_type": identity["activity_type"], "title": identity["title"], "exit_code": result["exit_code"], "failure": result["failure"], "event_count": result["event_count"], "last_event_type": result["last_event_type"], "elapsed_seconds": result["elapsed_seconds"], "starting_head": starting_head, "ending_head": ending_head, "dirty_paths": unexpected, "completed_despite_timeout": result["completed_despite_timeout"], "material_progress": material_progress, "completion_state": state["completion_state"], "next_priority": state["next_priority"], "input_fingerprint": history_record["input_fingerprint"], "output_fingerprint": history_record["output_fingerprint"]})
            state["loop_number"] += 1
            save_state(state)
            if unexpected:
                return 1
            if sleep_seconds:
                time.sleep(sleep_seconds)
        reconciliation = reconcile_outputs()
        state = load_state()
        commit_result = {"committed": [], "error": None}
        if not reconciliation["invalid_authoritative"] and not reconciliation["unexpected"]:
            try:
                commit_result = commit_authoritative_outputs(reconciliation["authoritative_uncommitted"])
            except (OSError, subprocess.CalledProcessError) as exc:
                commit_result = {"committed": [], "error": f"RECONCILIATION_COMMIT_FAILED: {exc}"}
        state["controller_state"] = "REPAIR_REQUIRED" if reconciliation["invalid_authoritative"] or reconciliation["unexpected"] or commit_result["error"] else "READY"
        state["reconciliation"] = {"authoritative_uncommitted": reconciliation["authoritative_uncommitted"], "temporary_remaining": reconciliation["temporary_remaining"], "unexpected": reconciliation["unexpected"], "committed": commit_result["committed"], "error": commit_result["error"]}
        state["run_summary"] = {"loops_requested": max_loops, "loops_completed": state.get("metrics", {}).get("loops_completed", 0), "activities_completed": max_loops, "repository_changes": bool(commit_result["committed"]), "commits_created": len(commit_result["committed"]), "authoritative_uncommitted_files": len(reconciliation["authoritative_uncommitted"]) - len(commit_result["committed"]), "temporary_files_remaining": len(reconciliation["temporary_remaining"]), "unexpected_files": len(reconciliation["unexpected"]), "material_progress": state.get("material_progress"), "validation_only_progress": state.get("material_progress") == "VALIDATION_GAIN", "stop_reason": state.get("stop_reason"), "next_priority": state.get("next_priority")}
        save_state(state)
        return 1 if reconciliation["invalid_authoritative"] or reconciliation["unexpected"] or commit_result["error"] else 0
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
