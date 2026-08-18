import json
from pathlib import Path

from scripts.veda_evidence_adb_access_rx_2026_001 import (
    OUT,
    build_route_matrix,
    canonical_hash,
    validate,
)


def test_policy_routes_are_distinct_and_currently_bounded():
    routes = {row["route_id"]: row for row in build_route_matrix()["routes"]}
    assert routes["FULL_DATABASE_EXPORT_ACCESS"]["status"] == "SUSPENDED_FOR_2026"
    assert routes["ONLINE_RESEARCH_TOOL_ACCESS"]["full_access"] == "UP_TO_FIVE_FILTERS"
    assert routes["SPECIAL_QUALIFIED_RESEARCHER_PERMISSION"]["status"] == "DOCUMENTED_ROUTE_NOT_SUBMITTED"
    assert routes["FREE_C_SAMPLE_ACCESS"]["use_in_this_activity"] == "NO_NEW_ACQUISITION"


def test_governance_blocks_external_and_ai_actions():
    matrix = build_route_matrix()
    request = matrix["veda_request"]
    governance = matrix["governance"]
    assert request["full_export_requested"] is False
    assert request["submission_sent"] is False
    assert request["purchase_or_license_accepted"] is False
    assert request["ai_ml_training"] is False
    assert request["raw_adb_in_rag"] is False
    assert request["provider_calls_added"] == 0
    assert governance["r2_state"] == "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED"
    assert governance["r2_started"] is False


def test_all_policy_sources_are_official_astrodienst_urls():
    assert all(source["url"].startswith("https://www.astro.com/") for source in build_route_matrix()["sources"])


def test_artifacts_have_no_fabricated_founder_claims():
    draft = (OUT / "05_PROVIDER_REQUEST_DRAFT.md").read_text(encoding="utf-8")
    card = (OUT / "06_FOUNDER_ADB_ACCESS_ACTION_CARD.md").read_text(encoding="utf-8")
    assert "[FOUNDER NAME]" in draft
    assert "[CONTACT EMAIL]" in draft
    assert "Do not invent credentials" in card
    assert "no claim that VEDA has provider approval" in card


def test_safety_boundary_text_is_present():
    text = "\n".join(path.read_text(encoding="utf-8") for path in OUT.glob("*.md"))
    assert "no positive signal" in text
    assert "PRED-M4" in text
    assert "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED" in text
    assert "No ADB data is ingested into the VEDA RAG corpus" in text
    assert "No provider login" in text


def test_route_matrix_artifact_is_json_and_deterministic():
    artifact = json.loads((OUT / "01_ACCESS_ROUTE_MATRIX.json").read_text(encoding="utf-8"))
    assert artifact["programme"] == "VEDA-EVIDENCE-ADB-ACCESS-RX-2026-001"
    assert canonical_hash(build_route_matrix())
    assert artifact["veda_request"]["provider_calls_added"] == 0


def test_generator_validation_is_clean():
    assert validate() == []
