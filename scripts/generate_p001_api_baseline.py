from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.auth.middleware import _PUBLIC
from backend.main import app


FIXTURE_DIR = ROOT / "tests" / "fixtures" / "veda_p001"
OUTPUT_PATH = FIXTURE_DIR / "api_contract_baseline.json"

CRITICAL_ENDPOINTS = [
    ("GET", "/health"),
    ("POST", "/api/auth/login"),
    ("GET", "/api/auth/config"),
    ("GET", "/api/chat/capabilities"),
    ("POST", "/api/chat"),
    ("GET", "/api/stocks/{symbol}/kundli"),
    ("POST", "/api/kundli/human"),
    ("GET", "/api/research/universe/stats"),
    ("GET", "/api/broker/status"),
    ("GET", "/api/pipeline/status"),
]


def _classify_auth_requirement(path: str) -> str:
    if path == "/api/auth/setup":
        return "LOOPBACK_SETUP"
    if path in _PUBLIC or path.startswith("/ws/"):
        return "PUBLIC"
    if path.startswith("/api"):
        return "AUTH_MIDDLEWARE"
    return "PUBLIC"


def _response_content_types(responses: dict) -> list[str]:
    content_types: set[str] = set()
    for response in responses.values():
        content_types.update((response.get("content") or {}).keys())
    return sorted(content_types)


def build_api_contract_payload() -> dict:
    spec = app.openapi()
    endpoints = []

    for path, methods in sorted(spec.get("paths", {}).items()):
        for method, details in sorted(methods.items()):
            parameters = details.get("parameters", [])
            request_body = details.get("requestBody") or {}
            endpoints.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "owner": (details.get("tags") or [path.strip("/").split("/", 1)[0] or "root"])[0],
                    "operation_id": details.get("operationId"),
                    "tags": details.get("tags", []),
                    "auth_requirement": _classify_auth_requirement(path),
                    "request_body_required": bool(request_body.get("required", False)),
                    "request_body_content_types": sorted((request_body.get("content") or {}).keys()),
                    "path_params": sorted(param["name"] for param in parameters if param.get("in") == "path"),
                    "query_params": sorted(param["name"] for param in parameters if param.get("in") == "query"),
                    "response_codes": sorted(details.get("responses", {}).keys()),
                    "response_content_types": _response_content_types(details.get("responses", {})),
                }
            )

    endpoint_lookup = {(item["method"], item["path"]): item for item in endpoints}

    return {
        "meta": {
            "baseline_id": "VEDA-P001-M003",
            "generated_on": "2026-08-10",
            "openapi_path_count": len(spec.get("paths", {})),
            "operation_count": len(endpoints),
        },
        "critical_endpoints": [
            endpoint_lookup[endpoint]
            for endpoint in CRITICAL_ENDPOINTS
            if endpoint in endpoint_lookup
        ],
        "endpoints": endpoints,
    }


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(build_api_contract_payload(), indent=2), encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
