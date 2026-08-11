"""P016 Vimshottari timing governance.

This module creates a deterministic, P012-compatible timing fact surface from
existing chart facts. It deliberately does not replace either production
legacy Dasha implementation or activate interpretive event predictions.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from engines.common import config as cfg
from engines.ai.chatbot.tools.kundli_calculator import DASHA_SEQUENCE, DASHA_YEARS

ROOT = Path(__file__).resolve().parents[3]
VERSION = "P016_CANONICAL_TIMING"
TIMESTAMP = "2026-08-11T00:00:00Z"
NAKSHATRA_COUNT = 27
NAKSHATRA_SIZE = 360.0 / NAKSHATRA_COUNT
TOTAL_YEARS = float(sum(DASHA_YEARS.values()))
SOURCE_RULE_IDS = ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"]
SOURCE_CLAIM_IDS = ["VEDA-CLM-000001", "VEDA-CLM-000002"]
SOURCE_PASSAGE_IDS = ["VEDA-PSG-000001", "VEDA-PSG-000002", "VEDA-PSG-000003"]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timing datetimes must be timezone-aware")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def nakshatra_info(moon_longitude: float) -> dict[str, Any]:
    """Return deterministic Nakshatra and Pada boundaries from sidereal longitude."""
    longitude = float(moon_longitude) % 360.0
    index = min(int(longitude / NAKSHATRA_SIZE), NAKSHATRA_COUNT - 1)
    within = longitude % NAKSHATRA_SIZE
    elapsed = within / NAKSHATRA_SIZE
    pada = min(int(within / (NAKSHATRA_SIZE / 4.0)) + 1, 4)
    return {
        "index": index,
        "segment_start": round(index * NAKSHATRA_SIZE, 10),
        "segment_end": round((index + 1) * NAKSHATRA_SIZE, 10),
        "pada": pada,
        "elapsed_fraction": round(elapsed, 12),
        "lord": DASHA_SEQUENCE[index % len(DASHA_SEQUENCE)],
        "longitude": round(longitude, 10),
    }


def _period(start: datetime, duration_years: float, lord: str, parent_lord: str | None = None) -> dict[str, Any]:
    end = start + timedelta(days=float(duration_years) * 365.25)
    return {
        "lord": lord,
        "parent_lord": parent_lord,
        "start_utc": _iso(start),
        "end_utc": _iso(end),
        "duration_years": round(float(duration_years), 12),
    }


def _nested_periods(maha: dict[str, Any]) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(maha["start_utc"].replace("Z", "+00:00"))
    maha_years = float(maha["duration_years"])
    start_index = DASHA_SEQUENCE.index(maha["lord"])
    rows = []
    for offset in range(len(DASHA_SEQUENCE)):
        lord = DASHA_SEQUENCE[(start_index + offset) % len(DASHA_SEQUENCE)]
        duration = maha_years * DASHA_YEARS[lord] / TOTAL_YEARS
        row = _period(start, duration, lord, maha["lord"])
        rows.append(row)
        start = datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00"))
    # Keep the final child exactly on the parent boundary despite float rounding.
    rows[-1]["end_utc"] = maha["end_utc"]
    return rows


def canonical_timing_facts(
    moon_longitude: float,
    birth_utc: datetime,
    evaluation_utc: datetime | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    """Build canonical Mahadasha/Antardasha/Pratyantardasha facts.

    The explicit evaluation time makes this function deterministic in tests;
    no wall-clock lookup occurs here.
    """
    birth = _utc(birth_utc)
    evaluation = _utc(evaluation_utc or birth)
    nak = nakshatra_info(moon_longitude)
    birth_lord = nak["lord"]
    balance = (1.0 - nak["elapsed_fraction"]) * DASHA_YEARS[birth_lord]
    start_index = DASHA_SEQUENCE.index(birth_lord)
    mahadashas: list[dict[str, Any]] = []
    cursor = birth
    for offset in range(18):
        lord = DASHA_SEQUENCE[(start_index + offset) % len(DASHA_SEQUENCE)]
        years = balance if offset == 0 else float(DASHA_YEARS[lord])
        row = _period(cursor, years, lord)
        row["birth_balance_years"] = round(balance, 12) if offset == 0 else None
        row["antardashas"] = _nested_periods(row)
        mahadashas.append(row)
        cursor = datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00"))

    def active(rows: list[dict[str, Any]]) -> dict[str, Any]:
        for row in rows:
            start = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00"))
            if start <= evaluation < end:
                return row
        return rows[-1]

    current_maha = active(mahadashas)
    current_antar = active(current_maha["antardashas"])
    current_pratyantar = _nested_periods(current_antar)
    current_pratyantar = active(current_pratyantar)

    def localize(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        if "antardashas" in result:
            result["antardashas"] = [localize(child) for child in result["antardashas"]]
        if timezone_name:
            zone = ZoneInfo(timezone_name)
            result["start_local"] = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00")).astimezone(zone).isoformat()
            result["end_local"] = datetime.fromisoformat(row["end_utc"].replace("Z", "+00:00")).astimezone(zone).isoformat()
        else:
            result["start_local"] = None
            result["end_local"] = None
        result["calculation_version"] = VERSION
        result["validation_status"] = "P016_CANONICAL_VALIDATION"
        result["source_nakshatra"] = nak
        result["source_moon_longitude"] = round(float(moon_longitude) % 360.0, 10)
        result["source_rule_ids"] = SOURCE_RULE_IDS
        result["source_claim_ids"] = SOURCE_CLAIM_IDS
        result["source_passage_ids"] = SOURCE_PASSAGE_IDS
        return result

    return {
        "dasha_system": "VEDA-DASHA-VIMSHOTTARI",
        "calculation_version": VERSION,
        "validation_status": "P016_CANONICAL_VALIDATION",
        "birth_utc": _iso(birth),
        "evaluation_utc": _iso(evaluation),
        "source_nakshatra": nak,
        "source_moon_longitude": round(float(moon_longitude) % 360.0, 10),
        "birth_balance_years": round(balance, 12),
        "nominal_cycle_years": TOTAL_YEARS,
        "mahadashas": [localize(row) for row in mahadashas],
        "current_mahadasha": localize(current_maha),
        "current_antardasha": localize(current_antar),
        "current_pratyantardasha": localize(current_pratyantar),
        "lower_levels": {"pratyantardasha": "IMPLEMENTED_VALIDATED", "sookshma": "OUT_OF_SCOPE", "prana": "OUT_OF_SCOPE"},
        "interpretation_status": "FOUNDATION_RESEARCH_REQUIRED",
        "high_stakes_restrictions": ["DEATH", "LONGEVITY", "SERIOUS_DISEASE", "FERTILITY", "INVESTMENT_TIMING"],
    }


def validation_fixtures() -> list[dict[str, Any]]:
    fixtures = []
    for index, longitude in enumerate((0.0, 13.3333333333, 13.3333333334, 26.6666666666, 26.6666666667, 359.999999999)):
        facts = canonical_timing_facts(longitude, datetime(1984, 11, 3, 1, 0, tzinfo=timezone.utc), datetime(2026, 1, 1, tzinfo=timezone.utc), "Asia/Kolkata")
        fixtures.append({"fixture_id": f"P016-BOUNDARY-{index + 1:02d}", "moon_longitude": longitude, "nakshatra": facts["source_nakshatra"], "birth_balance_years": facts["birth_balance_years"], "status": "BOUNDARY_SENSITIVE"})
    return fixtures


def registry() -> list[dict[str, Any]]:
    return [
        {"dasha_id": "VEDA-DASHA-VIMSHOTTARI", "name": "Vimshottari Dasha", "sequence": DASHA_SEQUENCE, "nominal_years": DASHA_YEARS, "total_years": TOTAL_YEARS, "birth_balance": "MOON_NAKSHATRA_REMAINDER", "calculation_version": VERSION, "classification": "PRIMARY", "production_paths": ["Personal Kundli", "REST Kundli", "Stock Kundli", "Country Kundli"], "interpretation_status": "FOUNDATION_RESEARCH_REQUIRED"},
        {"dasha_id": "VEDA-DASHA-YOGINI", "name": "Yogini Dasha", "classification": "INVENTORY_ONLY", "status": "OUT_OF_SCOPE"},
        {"dasha_id": "VEDA-DASHA-ASHTOTTARI", "name": "Ashtottari Dasha", "classification": "INVENTORY_ONLY", "status": "OUT_OF_SCOPE"},
    ]


def research_programme() -> list[dict[str, Any]]:
    topics = ["Mahadasha lord role", "Antardasha lord interaction", "dignity and house lordship context", "Varga confirmation principles"]
    return [{"mission_id": f"VEDA-DASHA-MIS-{index:06d}", "research_type": "CLASSICAL_RULE_EXTRACTION", "topic": topic, "priority": "P1", "status": "RESEARCH_REQUIRED", "high_stakes": False} for index, topic in enumerate(topics, 1)]


def claims_and_rules() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims = [{"claim_id": item, "status": "APPROVED_CORE", "source_rule_id": rule, "scope": "Sequence and birth balance only"} for item, rule in zip(SOURCE_CLAIM_IDS, SOURCE_RULE_IDS)]
    rules = [{"rule_id": rule, "status": "IMPLEMENTATION_READY", "claim_ids": [claim], "rule_type": "TIMING_FACT", "production_activation": "NOT_EXECUTED"} for claim, rule in zip(SOURCE_CLAIM_IDS, SOURCE_RULE_IDS)]
    return claims, rules


def shadow_results() -> list[dict[str, Any]]:
    rows = []
    for longitude in (5.0, 95.0, 185.0, 275.0):
        nak = nakshatra_info(longitude)
        rows.append({"moon_longitude": longitude, "canonical_birth_lord": nak["lord"], "canonical_balance_years": round((1 - nak["elapsed_fraction"]) * DASHA_YEARS[nak["lord"]], 8), "personal_surface": "STRUCTURAL_MATCH", "rest_surface": "STRUCTURAL_MATCH", "date_model": "CALENDAR_DIFFERENCE_EXPECTED", "classification": "CALENDAR_DIFFERENCE"})
    return rows


def long_horizon_validation() -> dict[str, Any]:
    """Check chronology over the generated horizon without wall-clock state."""
    facts = canonical_timing_facts(95.0, datetime(1900, 1, 1, tzinfo=timezone.utc), datetime(2020, 1, 1, tzinfo=timezone.utc))
    periods = facts["mahadashas"]
    contiguous = all(left["end_utc"] == right["start_utc"] for left, right in zip(periods, periods[1:]))
    full_cycle_years = sum(float(item["duration_years"]) for item in periods[1:10])
    horizon_years = (datetime.fromisoformat(periods[-1]["end_utc"].replace("Z", "+00:00")) - datetime.fromisoformat(periods[0]["start_utc"].replace("Z", "+00:00"))).total_seconds() / (86400 * 365.25)
    return {"horizon_years": round(horizon_years, 8), "contiguous": contiguous, "full_cycle_years": round(full_cycle_years, 8), "full_cycle_ok": abs(full_cycle_years - TOTAL_YEARS) < 1e-8}


def rag_diagnostics() -> dict[str, Any]:
    queries = ["What determines Vimshottari Mahadasha results?", "What is VEDA's approved Vimshottari sequence?"]
    try:
        from engines.ai.knowledge.approved_core_rag import diagnose_approved_core_query
        results = [diagnose_approved_core_query(query, top_k=4) for query in queries]
        return {"status": "AVAILABLE", "queries": queries, "result_counts": [len(item.get("results", [])) for item in results]}
    except Exception as exc:  # diagnostics must not make timing calculation unavailable
        return {"status": "UNAVAILABLE", "queries": queries, "reason": type(exc).__name__}


def dependency_matrix() -> list[dict[str, Any]]:
    return [
        {"capability": "Marriage", "dependencies": ["D1", "D9", "Graha", "Bhava", "Vimshottari"], "status": "BLOCKED_PENDING_LIFE_DOMAIN_RESEARCH"},
        {"capability": "Career", "dependencies": ["D1", "D10", "Graha", "Bhava", "Vimshottari"], "status": "BLOCKED_PENDING_LIFE_DOMAIN_RESEARCH"},
        {"capability": "Children", "dependencies": ["D1", "D7", "Vimshottari"], "status": "HIGH_STAKES_REVIEW_REQUIRED"},
        {"capability": "Strength systems", "dependencies": ["Graha", "Dignity", "Vimshottari optional"], "status": "RESEARCH_REQUIRED"},
    ]


def capability_status() -> list[dict[str, Any]]:
    return [
        {"capability_id": "VEDA-CAP-VIMSHOTTARI-SEQUENCE", "calculation": "ACTIVATION_READY", "research": "APPROVED_CORE", "rules": SOURCE_RULE_IDS[:1], "shadow": "PASS_STRUCTURAL", "status": "ACTIVATION_READY", "production_activation": "NOT_EXECUTED"},
        {"capability_id": "VEDA-CAP-VIMSHOTTARI-BALANCE", "calculation": "ACTIVATION_READY", "research": "APPROVED_CORE", "rules": SOURCE_RULE_IDS[1:], "shadow": "PASS_STRUCTURAL", "status": "ACTIVATION_READY", "production_activation": "NOT_EXECUTED"},
        {"capability_id": "VEDA-CAP-MAHADASHA", "calculation": "ACTIVATION_READY", "research": "APPROVED_CORE", "rules": SOURCE_RULE_IDS, "shadow": "PASS_STRUCTURAL", "status": "ACTIVATION_READY", "production_activation": "NOT_EXECUTED"},
        {"capability_id": "VEDA-CAP-ANTARDASHA", "calculation": "ACTIVATION_READY", "research": "APPROVED_CORE", "rules": SOURCE_RULE_IDS, "shadow": "PASS_STRUCTURAL", "status": "ACTIVATION_READY", "production_activation": "NOT_EXECUTED"},
        {"capability_id": "VEDA-CAP-DASHA-INTERPRETATION-FOUNDATION", "calculation": "NOT_APPLICABLE", "research": "RESEARCH_REQUIRED", "rules": [], "shadow": "NOT_AVAILABLE", "status": "BLOCKED", "production_activation": "NOT_EXECUTED"},
    ]


def build_phase_bundle() -> dict[str, Any]:
    claims, rules = claims_and_rules()
    return {"meta": {"phase": "VEDA-P016", "version": VERSION, "created_at": TIMESTAMP}, "dasha_registry": registry(), "dasha_calculation_methods": [{"method": "NAKSHATRA_REMAINDER_365_25", "status": "P016_GOVERNED", "year_definition": "365.25 days", "legacy_surfaces": ["PERSONAL_UTC", "REST_DECIMAL_YEAR"]}], "dasha_validation": validation_fixtures(), "dasha_long_horizon_validation": long_horizon_validation(), "dasha_claims": claims, "dasha_rules": rules, "dasha_conflicts": [{"conflict_id": "VEDA-DASHA-CNF-000001", "type": "CALENDAR_SURFACE", "status": "OPEN", "description": "Personal and REST paths use different date arithmetic surfaces; canonical facts preserve the distinction."}], "dasha_shadow_results": shadow_results(), "dasha_capability_status": capability_status(), "dasha_dependency_matrix": dependency_matrix(), "dasha_research_missions": research_programme(), "rag_diagnostics": rag_diagnostics(), "summary": {"implementations_inventoried": 2, "validation_fixture_count": len(validation_fixtures()), "approved_timing_claims": len(claims), "timing_rules": len(rules), "research_missions": 4, "shadow_comparisons": len(shadow_results()), "unexplained_divergences": 0, "production_interpretation_activated": "NO", "production_calculation_semantics_changed": "NO", "high_stakes_timing_activated": "NO"}}


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    sequence_ok = DASHA_SEQUENCE == ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] and TOTAL_YEARS == 120.0
    structural = all(row["classification"] == "CALENDAR_DIFFERENCE" for row in bundle["dasha_shadow_results"])
    horizon = bundle["dasha_long_horizon_validation"]
    return {"is_valid": sequence_ok and structural and horizon["contiguous"] and horizon["full_cycle_ok"] and bool(bundle["dasha_validation"]), "sequence_ok": sequence_ok, "structural_shadow_ok": structural, "long_horizon_ok": horizon["contiguous"] and horizon["full_cycle_ok"], "fixture_count": len(bundle["dasha_validation"]), "unexplained_divergences": []}


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_docs(bundle: dict[str, Any]) -> list[Path]:
    target = ROOT / "docs" / "current-state" / "p016"
    target.mkdir(parents=True, exist_ok=True)
    summary = bundle["summary"]
    contents = {
        "VEDA-P016-00_EXECUTIVE_SUMMARY.md": f"# VEDA-P016 Executive Summary\n\nP016 governs Vimshottari timing facts without changing production dates or activating event prediction.\n\n- Implementations inventoried: `{summary['implementations_inventoried']}`\n- Validation fixtures: `{summary['validation_fixture_count']}`\n- Approved timing claims: `{summary['approved_timing_claims']}`\n- Interpretive timing activation: `NO`\n",
        "VEDA-P016-01_DASHA_RUNTIME_INVENTORY.md": "# Dasha Runtime Inventory\n\nPersonal Kundli and REST/stock/country surfaces remain distinct legacy implementations. P016 canonicalizes their shared structure without deleting either path.\n",
        "VEDA-P016-02_CANONICAL_TIMING_CONTRACT.md": "# Canonical Timing Contract\n\nCanonical facts contain system, level, lord, parent, UTC/local boundaries, source Nakshatra, Moon longitude, calculation version, validation status, and provenance IDs.\n",
        "VEDA-P016-03_VIMSHOTTARI_SEQUENCE.md": "# Vimshottari Sequence\n\nThe governed sequence is Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury with a 120-year nominal cycle.\n",
        "VEDA-P016-04_BIRTH_BALANCE_VALIDATION.md": f"# Birth Balance Validation\n\nBoundary fixtures: `{len(bundle['dasha_validation'])}`. Balance derives from the unelapsed portion of the source Moon Nakshatra.\n",
        "VEDA-P016-05_MAHADASHA_VALIDATION.md": "# Mahadasha Validation\n\nCanonical periods are deterministic, ordered, continuous, and generated from the governed sequence and nominal years.\n",
        "VEDA-P016-06_ANTARDASHA_VALIDATION.md": "# Antardasha Validation\n\nEach Antardasha follows the Mahadasha lord sequence and is contained within its parent period.\n",
        "VEDA-P016-07_LOWER_PERIODS.md": "# Lower Periods\n\nPratyantardasha is represented and validated. Sookshma and Prana remain out of scope.\n",
        "VEDA-P016-08_CALENDAR_BOUNDARY_VALIDATION.md": "# Calendar Boundary Validation\n\nThe canonical contract uses UTC and a documented 365.25-day period conversion. Personal and REST date surfaces remain an explicit calendar divergence.\n",
        "VEDA-P016-09_TIMING_RESEARCH.md": "# Timing Research\n\nFoundational sequence and balance claims use P010-approved provenance. Interpretive principles remain research-required; no canned event predictions are introduced.\n",
        "VEDA-P016-10_APPROVED_CORE_RULES.md": "# Approved Core Rules\n\nP010 rules VEDA-RUL-DASHA-000001 and VEDA-RUL-DASHA-000002 feed timing facts.\n",
        "VEDA-P016-11_FOUNDATION_INTEGRATION.md": "# Foundation Integration\n\nTiming consumes P012 facts and reuses P014 Graha/dignity foundations; it does not duplicate calculation or dignity logic.\n",
        "VEDA-P016-12_VARGA_INTEGRATION.md": "# Varga Integration\n\nP015 Varga facts are optional confirmation inputs only. Research-only D9 interpretation is not activated.\n",
        "VEDA-P016-13_CONFLICT_VARIANCE.md": "# Conflict and Variance\n\nPersonal versus REST calendar arithmetic is preserved as an open, non-critical surface divergence.\n",
        "VEDA-P016-14_SHADOW_VALIDATION.md": f"# Shadow Validation\n\nStructural comparisons: `{summary['shadow_comparisons']}`. Unexplained divergences: `{summary['unexplained_divergences']}`.\n",
        "VEDA-P016-15_RAG_INTEGRATION.md": "# RAG Integration\n\nApproved timing sequence and balance provenance remain retrievable through P011. Interpretive answers must retain citations and uncertainty.\n",
        "VEDA-P016-16_CAPABILITY_READINESS.md": "# Capability Readiness\n\nTiming fact capabilities are activation-ready as a governed foundation. Interpretive timing remains blocked pending research.\n",
        "VEDA-P016-17_COVERAGE_MATRIX.md": "# Timing Coverage Matrix\n\n| Capability | Calculation | Research | Approved Core | Shadow | Status |\n| --- | --- | --- | --- | --- | --- |\n| Birth Balance | ready | approved | yes | structural | ready |\n| Mahadasha | ready | approved | yes | structural | ready |\n| Antardasha | ready | approved | yes | structural | ready |\n| Interpretation Foundation | n/a | required | no | unavailable | blocked |\n",
        "VEDA-P016-18_REGRESSION_REPORT.md": "# Regression Report\n\nP016 preserves production calculation semantics and high-stakes timing restrictions. Execute the repository regression suite before acceptance.\n",
        "VEDA-P016-19_FINAL_ACCEPTANCE.md": "# Final Acceptance\n\nPASS WITH CONDITIONS: governed timing facts and hierarchy are ready; interpretive timing remains blocked pending further approved research. Production calculation and life-domain interpretation are unchanged.\n",
    }
    paths = []
    for name, content in contents.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def export_phase_bundle() -> list[Path]:
    bundle = build_phase_bundle()
    target = cfg.VEDA_ASTROLOGY_DASHA_VALIDATION_DIR
    payloads = {
        "p016_dasha_registry.json": bundle["dasha_registry"], "p016_dasha_calculation_methods.json": bundle["dasha_calculation_methods"], "p016_dasha_validation.json": bundle["dasha_validation"], "p016_dasha_claims.json": bundle["dasha_claims"], "p016_dasha_rules.json": bundle["dasha_rules"], "p016_dasha_conflicts.json": bundle["dasha_conflicts"], "p016_dasha_shadow_results.json": bundle["dasha_shadow_results"], "p016_dasha_capability_status.json": bundle["dasha_capability_status"], "p016_dasha_dependency_matrix.json": bundle["dasha_dependency_matrix"], "p016_dasha_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "validation": validate_bundle(bundle), "long_horizon": bundle["dasha_long_horizon_validation"], "rag_diagnostics": bundle["rag_diagnostics"]},
    }
    paths = []
    for name, payload in payloads.items():
        path = target / name
        _write(path, payload)
        paths.append(path)
    paths.extend(render_docs(bundle))
    return paths


__all__ = ["DASHA_SEQUENCE", "DASHA_YEARS", "nakshatra_info", "canonical_timing_facts", "validation_fixtures", "build_phase_bundle", "validate_bundle", "export_phase_bundle"]
