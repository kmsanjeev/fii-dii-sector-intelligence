"""Deterministic, provider-free validation for VEDA-EVIDENCE-ADB-ACCESS-RX-2026-001."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROGRAMME = "VEDA-EVIDENCE-ADB-ACCESS-RX-2026-001"
RETRIEVED_ON = "2026-08-19"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "evidence-adb-access-rx-2026-001"


def _sources() -> list[dict[str, Any]]:
    return [
        {
            "id": "ADB-READme-2026",
            "title": "ADB export readme",
            "url": "https://www.astro.com/adbexport/00_readme.htm",
            "retrieved_on": RETRIEVED_ON,
            "policy_date": "2026-03-30",
            "authority": "OFFICIAL_PROVIDER",
            "supports": [
                "full export halted due to overload",
                "contract and full download ZIP removed for duration of 2026",
                "C sample remains available",
                "serious research criteria",
                "no licenses for AI training",
                "research-tool and Astrodienst Plus route",
            ],
        },
        {
            "id": "ADB-INDEX-2026",
            "title": "ADB export directory",
            "url": "https://www.astro.com/adbexport/",
            "retrieved_on": RETRIEVED_ON,
            "authority": "OFFICIAL_PROVIDER",
            "supports": ["current public directory exposes readme and C sample artifacts"],
        },
        {
            "id": "ADB-RESEARCH-2026",
            "title": "Astrodatabank research tool",
            "url": "https://www.astro.com/cgi/aq.cgi/adb-search",
            "retrieved_on": RETRIEVED_ON,
            "authority": "OFFICIAL_PROVIDER",
            "supports": [
                "guest visitors cannot submit queries",
                "partial access supports up to two filter cards",
                "full access supports up to five filters",
                "full access route is subscription or qualified-researcher permission",
            ],
        },
        {
            "id": "ASTROPLUS-2026",
            "title": "Astrodienst Plus",
            "url": "https://www.astro.com/prod/pr_astroplus_e.htm",
            "retrieved_on": RETRIEVED_ON,
            "authority": "OFFICIAL_PROVIDER",
            "supports": ["subscription includes the Astrodatabank research tool"],
        },
        {
            "id": "ADB-CSAMPLE-2026",
            "title": "Current C sample artifact listing",
            "url": "https://www.astro.com/adbexport/c_sample.zip",
            "retrieved_on": RETRIEVED_ON,
            "authority": "OFFICIAL_PROVIDER",
            "supports": ["current C sample link observed; no download performed"],
        },
    ]


def build_route_matrix() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "retrieved_on": RETRIEVED_ON,
        "provider": "Astro-Databank / Astrodienst",
        "policy_status": "CURRENT_OFFICIAL_POLICY_RECONCILED",
        "routes": [
            {
                "route_id": "FULL_DATABASE_EXPORT_ACCESS",
                "status": "SUSPENDED_FOR_2026",
                "available_now": False,
                "application_status": "NO_APPLICATION_SUBMITTED",
                "export_capability": "NOT_AVAILABLE_PUBLICLY_DURING_2026_SUSPENSION",
                "programmatic_or_bulk_capability": "NOT_DOCUMENTED",
                "source_ids": ["ADB-READme-2026", "ADB-INDEX-2026"],
            },
            {
                "route_id": "ONLINE_RESEARCH_TOOL_ACCESS",
                "status": "PUBLIC_PARTIAL_AND_GUEST_ROUTES_OBSERVED",
                "available_now": True,
                "partial_access": "UP_TO_TWO_FILTER_CARDS",
                "full_access": "UP_TO_FIVE_FILTERS",
                "subscription_sufficiency_for_veda_scale": "PARTIAL_INTERACTIVE_SUFFICIENCY_ONLY_BULK_UNESTABLISHED",
                "export_capability": "NOT_ESTABLISHED",
                "programmatic_or_bulk_capability": "NOT_DOCUMENTED",
                "source_ids": ["ADB-RESEARCH-2026"],
            },
            {
                "route_id": "SPECIAL_QUALIFIED_RESEARCHER_PERMISSION",
                "status": "DOCUMENTED_ROUTE_NOT_SUBMITTED",
                "available_now": "REQUIRES_PROVIDER_DECISION",
                "export_capability": "REQUIRES_EXPLICIT_PROVIDER_TERMS",
                "programmatic_or_bulk_capability": "NOT_DOCUMENTED",
                "source_ids": ["ADB-READme-2026", "ADB-RESEARCH-2026"],
            },
            {
                "route_id": "FREE_C_SAMPLE_ACCESS",
                "status": "CURRENT_SAMPLE_REMAINS_AVAILABLE",
                "available_now": True,
                "use_in_this_activity": "NO_NEW_ACQUISITION",
                "export_capability": "SAMPLE_ARTIFACT_ONLY",
                "programmatic_or_bulk_capability": "NOT_DOCUMENTED_BEYOND_SAMPLE_ARTIFACT",
                "source_ids": ["ADB-READme-2026", "ADB-CSAMPLE-2026"],
            },
        ],
        "sources": _sources(),
        "veda_request": {
            "requested_access": "provider-directed research access or permitted research-tool route; no full export requested while suspended",
            "full_export_requested": False,
            "research_tool_or_special_permission_requested": True,
            "scraping": False,
            "redistribution": False,
            "ai_ml_training": False,
            "raw_adb_in_rag": False,
            "provider_calls_added": 0,
            "submission_sent": False,
            "purchase_or_license_accepted": False,
        },
        "governance": {
            "r2_state": "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED",
            "r2_started": False,
            "astrology": False,
            "feature_activation": False,
            "feature_values": False,
            "ml": False,
            "pred_m4": "UNCHANGED",
            "production": False,
            "rag_changed": False,
            "approved_core_changed": False,
            "raw_provider_data_committed": False,
        },
    }


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_manifest() -> dict[str, Any]:
    matrix = build_route_matrix()
    expected = [
        "00_CURRENT_ADB_POLICY.md",
        "01_ACCESS_ROUTE_MATRIX.json",
        "02_VEDA_RESEARCH_SUMMARY.md",
        "03_DATA_GOVERNANCE_STATEMENT.md",
        "04_AI_ML_NONTRAINING_STATEMENT.md",
        "05_PROVIDER_REQUEST_DRAFT.md",
        "06_FOUNDER_ADB_ACCESS_ACTION_CARD.md",
        "07_R2_DEPENDENCY.md",
        "08_FINAL_ACCEPTANCE.md",
    ]
    return {
        "programme": PROGRAMME,
        "retrieved_on": RETRIEVED_ON,
        "route_matrix_sha256": canonical_hash(matrix),
        "expected_artifacts": expected,
        "artifact_presence": {name: (OUT / name).exists() for name in expected},
        "provider_calls_added": 0,
        "raw_adb_in_scope": False,
        "deterministic": True,
    }


def validate() -> list[str]:
    errors: list[str] = []
    matrix = build_route_matrix()
    if matrix["veda_request"]["full_export_requested"]:
        errors.append("full export must not be requested during 2026 suspension")
    if matrix["veda_request"]["submission_sent"]:
        errors.append("external submission must remain false")
    if matrix["governance"]["r2_started"]:
        errors.append("POSEND R2 must remain not started")
    if matrix["governance"]["rag_changed"]:
        errors.append("RAG must remain unchanged")
    if matrix["governance"]["raw_provider_data_committed"]:
        errors.append("raw provider data must not be committed")
    for source in matrix["sources"]:
        if not source["url"].startswith("https://www.astro.com/"):
            errors.append(f"non-official policy URL: {source['url']}")
    for name, present in build_manifest()["artifact_presence"].items():
        if not present:
            errors.append(f"missing governed artifact: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    errors = validate()
    if args.write_manifest:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "09_DETERMINISTIC_BUILD.json").write_text(
            json.dumps(build_manifest(), ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(json.dumps(build_manifest(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
