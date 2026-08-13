from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
BACKEND_PORT = 8012
FRONTEND_PORT = 4173
BACKEND_BASE = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_BASE = f"http://127.0.0.1:{FRONTEND_PORT}"


def _read_fixture_payload() -> dict:
    fixture_path = ROOT / "tests" / "fixtures" / "veda_p001" / "astrology_golden.json"
    with open(fixture_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["rest_human"][0]["input"]


def _wait_for_http(url: str, *, timeout_seconds: int = 60) -> requests.Response:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                return response
        except Exception as exc:  # pragma: no cover - smoke path only
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _start_backend(log_dir: Path) -> tuple[subprocess.Popen, list]:
    env = os.environ.copy()
    env["VEDA_RUNTIME_ENV"] = "local"
    env["VEDA_AUTH_ENABLED"] = "false"
    stdout = open(log_dir / "backend.stdout.log", "w", encoding="utf-8")
    stderr = open(log_dir / "backend.stderr.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=ROOT,
        env=env,
        stdout=stdout,
        stderr=stderr,
    )
    return proc, [stdout, stderr]


def _start_frontend(log_dir: Path) -> tuple[subprocess.Popen, list]:
    stdout = open(log_dir / "frontend.stdout.log", "w", encoding="utf-8")
    stderr = open(log_dir / "frontend.stderr.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(ROOT / "frontend" / "node_modules" / ".bin" / "vite.cmd"),
            "--host",
            "127.0.0.1",
            "--port",
            str(FRONTEND_PORT),
            "--strictPort",
        ],
        cwd=ROOT / "frontend",
        stdout=stdout,
        stderr=stderr,
    )
    return proc, [stdout, stderr]


def _stop_process(proc: subprocess.Popen | None, handles: list | None = None) -> None:
    if not proc:
        if handles:
            for handle in handles:
                handle.close()
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:  # pragma: no cover - smoke path only
                proc.kill()
                proc.wait(timeout=10)
    finally:
        if handles:
            for handle in handles:
                handle.close()


def run_smoke() -> dict:
    checks: list[dict] = []
    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None
    backend_handles: list | None = None
    frontend_handles: list | None = None

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        log_dir = Path(temp_dir)
        try:
            backend_proc, backend_handles = _start_backend(log_dir)
            backend_health = _wait_for_http(f"{BACKEND_BASE}/health")
            health_payload = backend_health.json()
            _assert(backend_health.status_code == 200, "/health did not return HTTP 200")
            _assert(health_payload.get("status") == "ok", "/health status was not ok")
            checks.append(
                {
                    "check": "backend_startup_and_health",
                    "status": "PASS",
                    "details": {
                        "status_code": backend_health.status_code,
                        "datasets_loaded": health_payload.get("datasets_loaded"),
                        "datasets_total": health_payload.get("datasets_total"),
                    },
                }
            )

            auth_config = requests.get(f"{BACKEND_BASE}/api/auth/config", timeout=10)
            auth_payload = auth_config.json()
            _assert(auth_config.status_code == 200, "auth config request failed")
            _assert(auth_payload.get("runtime_env") == "local", "auth runtime_env mismatch")
            _assert(auth_payload.get("enabled") is False, "auth should be disabled in local smoke mode")
            checks.append(
                {
                    "check": "authentication_configuration",
                    "status": "PASS",
                    "details": auth_payload,
                }
            )

            chat_caps = requests.get(f"{BACKEND_BASE}/api/chat/capabilities", timeout=10)
            chat_payload = chat_caps.json()
            _assert(chat_caps.status_code == 200, "chat capabilities request failed")
            _assert("research_enabled" in chat_payload, "chat capabilities missing research_enabled")
            _assert("supported_attachment_mime_prefixes" in chat_payload, "chat capabilities missing attachment prefixes")
            checks.append(
                {
                    "check": "chat_capability",
                    "status": "PASS",
                    "details": {
                        "research_enabled": chat_payload.get("research_enabled"),
                        "research_runtime_ready": chat_payload.get("research_runtime_ready"),
                        "attachments_enabled": chat_payload.get("attachments_enabled"),
                    },
                }
            )

            research = requests.get(f"{BACKEND_BASE}/api/research/universe/stats", timeout=10)
            research_payload = research.json()
            _assert(research.status_code == 200, "research universe stats request failed")
            _assert(isinstance(research_payload, dict), "research universe stats was not an object")
            checks.append(
                {
                    "check": "retrieval_capability",
                    "status": "PASS",
                    "details": {
                        "keys": sorted(research_payload.keys())[:10],
                    },
                }
            )

            kundli = requests.post(
                f"{BACKEND_BASE}/api/kundli/human",
                json=_read_fixture_payload(),
                timeout=20,
            )
            kundli_payload = kundli.json()
            _assert(kundli.status_code == 200, "human kundli request failed")
            _assert(kundli_payload.get("kundli", {}).get("lagna", {}).get("sign"), "human kundli missing lagna sign")
            _assert("planets" in kundli_payload.get("kundli", {}), "human kundli missing planets")
            checks.append(
                {
                    "check": "kundli_calculation",
                    "status": "PASS",
                    "details": {
                        "lagna_sign": kundli_payload["kundli"]["lagna"]["sign"],
                        "planet_count": len(kundli_payload["kundli"].get("planets", {})),
                    },
                }
            )

            pipeline = requests.get(f"{BACKEND_BASE}/api/pipeline/status", timeout=10)
            pipeline_payload = pipeline.json()
            _assert(pipeline.status_code == 200, "pipeline status request failed")
            _assert("state" in pipeline_payload, "pipeline status missing state")
            checks.append(
                {
                    "check": "pipeline_status",
                    "status": "PASS",
                    "details": {
                        "state": pipeline_payload.get("state"),
                        "next_run_ist": pipeline_payload.get("next_run_ist"),
                    },
                }
            )

            broker = requests.get(f"{BACKEND_BASE}/api/broker/status", timeout=10)
            broker_payload = broker.json()
            _assert(broker.status_code == 200, "broker status request failed")
            _assert("connected" in broker_payload, "broker status missing connected")
            checks.append(
                {
                    "check": "broker_status",
                    "status": "PASS",
                    "details": {
                        "connected": broker_payload.get("connected"),
                        "broker": broker_payload.get("broker"),
                    },
                }
            )

            frontend_proc, frontend_handles = _start_frontend(log_dir)
            frontend_response = _wait_for_http(FRONTEND_BASE, timeout_seconds=60)
            _assert(frontend_response.status_code == 200, "frontend root did not return HTTP 200")
            _assert("id=\"root\"" in frontend_response.text, "frontend root markup missing app mount")
            checks.append(
                {
                    "check": "frontend_startup",
                    "status": "PASS",
                    "details": {
                        "status_code": frontend_response.status_code,
                        "url": FRONTEND_BASE,
                    },
                }
            )

            return {"status": "PASS", "checks": checks}
        finally:
            _stop_process(frontend_proc, frontend_handles)
            _stop_process(backend_proc, backend_handles)


def main() -> None:
    result = run_smoke()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
