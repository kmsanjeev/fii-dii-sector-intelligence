from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_p001_api_baseline import build_api_contract_payload

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "veda_p001" / "api_contract_baseline.json"


def _load_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def test_api_contract_baseline_snapshot():
    assert build_api_contract_payload() == _load_fixture()


def test_api_contract_baseline_matches_current_canonical_endpoint_count():
    payload = _load_fixture()
    assert payload["meta"]["openapi_path_count"] == 153
    assert payload["meta"]["operation_count"] == 166


def test_api_contract_critical_endpoints_are_present():
    payload = _load_fixture()
    critical = {(item["method"], item["path"]): item for item in payload["critical_endpoints"]}

    assert ("GET", "/health") in critical
    assert critical[("GET", "/health")]["auth_requirement"] == "PUBLIC"

    assert ("POST", "/api/auth/login") in critical
    assert critical[("POST", "/api/auth/login")]["request_body_required"] is True

    assert ("GET", "/api/chat/capabilities") in critical
    assert ("POST", "/api/chat") in critical
    assert ("GET", "/api/stocks/{symbol}/kundli") in critical
    assert ("POST", "/api/kundli/human") in critical
    assert ("GET", "/api/gochar/stock/{symbol}") in critical
    assert ("POST", "/api/gochar/human") in critical
    assert ("GET", "/api/gochar/country/{name}") in critical
    assert ("GET", "/api/research/universe/stats") in critical
    assert ("GET", "/api/broker/status") in critical
    assert ("GET", "/api/pipeline/status") in critical
