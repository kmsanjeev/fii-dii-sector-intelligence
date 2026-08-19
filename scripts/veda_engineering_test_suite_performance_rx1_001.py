"""Profile and run the governed VEDA test-suite gates.

This utility is intentionally a runner and profiler, not a second test
framework.  It keeps the authoritative full suite intact while providing
explicit logical partitions for fast feedback and for external/integration
diagnostics.  Test membership is path-based and deterministic so adding a
test cannot silently move it into multiple gates.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "tests"
DEFAULT_TIMEOUT_SECONDS = 900

GROUP_ORDER = (
    "MUHURTA",
    "CALCULATION",
    "ACQUISITION_EVIDENCE",
    "RAG_KNOWLEDGE",
    "EMPIRICAL_PREDICTION",
    "LANGUAGE_CONVERSATION",
    "API_BACKEND",
    "FOUNDATION_OTHER",
)


def _test_files() -> list[Path]:
    return sorted(TEST_ROOT.rglob("test_*.py"), key=lambda path: path.relative_to(ROOT).as_posix())


def _name(path: Path) -> str:
    return path.relative_to(TEST_ROOT).as_posix().lower()


def _group_for(path: Path) -> str:
    name = _name(path)
    if "muhurta" in name or name.endswith("test_veda_p032_muhurta_foundation_001.py") or "muh_" in name:
        return "MUHURTA"
    if any(token in name for token in ("calc", "p015", "p016", "p017", "p018", "p019", "p020", "p021", "p022", "p023", "p027", "p028", "p029", "p030", "p031", "varga", "shadbala", "ashtakavarga", "dasha", "transit", "yoga_dosha")):
        return "CALCULATION"
    if any(token in name for token in ("evidence", "adb", "ogdb", "india_access", "corpus", "consent", "external_readiness")):
        return "ACQUISITION_EVIDENCE"
    if any(token in name for token in ("unified", "retrieval", "knowledge", "research", "wikidata")):
        return "RAG_KNOWLEDGE"
    if any(token in name for token in ("emp_", "signal", "pop_", "pred_", "prim_")):
        return "EMPIRICAL_PREDICTION"
    if any(token in name for token in ("lang", "comm", "group", "emo", "std003")):
        return "LANGUAGE_CONVERSATION"
    if any(token in name for token in ("api", "router", "chat", "mcp", "voice", "main")):
        return "API_BACKEND"
    return "FOUNDATION_OTHER"


def inventory() -> dict[str, Any]:
    files = _test_files()
    groups: dict[str, list[str]] = {group: [] for group in GROUP_ORDER}
    for path in files:
        groups[_group_for(path)].append(path.relative_to(ROOT).as_posix())
    return {
        "test_files": len(files),
        "group_order": list(GROUP_ORDER),
        "groups": {group: {"file_count": len(paths), "files": paths} for group, paths in groups.items()},
        "classification": "PATH_BASED_DISJOINT_PROFILE_ONLY",
    }


def _pytest_args(paths: list[str], *, durations: bool = False) -> list[str]:
    args = [sys.executable, "-m", "pytest", "-q"]
    if durations:
        args.extend(["--durations=25", "--durations-min=0.1"])
    args.extend(paths)
    return args


def run_pytest(paths: list[str], *, timeout_seconds: int, durations: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    command = _pytest_args(paths, durations=durations)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        output = f"{completed.stdout}\n{completed.stderr}".strip()
        status = "PASS" if completed.returncode == 0 else "FAIL"
        return {
            "command": " ".join(command),
            "status": status,
            "exit_code": completed.returncode,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "summary": _summary(output),
            "output_tail": output[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(str(part) for part in (exc.stdout, exc.stderr) if part)
        return {
            "command": " ".join(command),
            "status": "TIMEOUT",
            "exit_code": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "summary": _summary(output),
            "output_tail": output[-4000:],
        }


def _summary(output: str) -> dict[str, Any]:
    match = re.search(r"(?P<passed>\d+) passed(?:, (?P<failed>\d+) failed)?(?:, (?P<skipped>\d+) skipped)?(?:, (?P<warnings>\d+) warning)?", output)
    if not match:
        return {}
    return {key: int(value) for key, value in match.groupdict().items() if value is not None}


def collect(timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        output = f"{completed.stdout}\n{completed.stderr}".strip()
        match = re.search(r"(?P<count>\d+) tests collected", output)
        return {
            "command": " ".join(command),
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "exit_code": completed.returncode,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "collected": int(match.group("count")) if match else None,
            "output_tail": output[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "command": " ".join(command),
            "status": "TIMEOUT",
            "exit_code": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "collected": None,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("inventory", "gate", "profile"), default="inventory")
    parser.add_argument("--group", choices=GROUP_ORDER)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--durations", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload: dict[str, Any] = {"programme": "VEDA-ENGINEERING-TEST-SUITE-PERFORMANCE-RX1-001"}
    catalog = inventory()
    payload["inventory"] = catalog
    if args.mode in {"gate", "profile"}:
        payload["collection"] = collect(args.timeout_seconds)
        if args.group:
            paths = catalog["groups"][args.group]["files"]
            payload["runs"] = {args.group: run_pytest(paths, timeout_seconds=args.timeout_seconds, durations=args.durations)}
        elif args.mode == "profile":
            payload["runs"] = {
                group: run_pytest(details["files"], timeout_seconds=args.timeout_seconds, durations=args.durations)
                for group, details in catalog["groups"].items()
            }
        else:
            payload["runs"] = {"FULL_DETERMINISTIC": run_pytest(["tests"], timeout_seconds=args.timeout_seconds, durations=args.durations)}

    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
