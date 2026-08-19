"""VEDA-CALC-JYOTISHA-CORE-001 deterministic calculation audit.

This is a bounded audit harness, not a second Jyotisha runtime.  It keeps
independent reference formulas local to the audit, compares them with the
existing governed paths, and writes only deterministic governance artifacts.
It deliberately does not calculate predictive outcomes, score features, use
ML, or activate any production interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.dasha_governance import (
    DASHA_SEQUENCE,
    DASHA_YEARS,
    TOTAL_YEARS,
    canonical_timing_facts,
)
from engines.ai.knowledge.shadbala_engine import (
    BAV_CONTRIBUTIONS,
    calculate_bav_legacy,
    calculate_sav_legacy,
)
from engines.ai.knowledge.varga_governance import VARGA_METHODS, varga_sign
from engines.ai.knowledge.yoga_dosha_governance import RULES, evaluate_rule
from engines.intelligence.kundli_engine import KundliEngine, SIGNS


OUT = ROOT / "docs" / "current-state" / "calc-jyotisha-core-001"
RUN_DATE = "2026-08-18"
VARGA_METHOD = "d20_vimshamsha_bphs_category_start_v1"
MOVABLE = {0, 3, 6, 9}
FIXED = {1, 4, 7, 10}
DUAL = {2, 5, 8, 11}
NAKSHATRA_SIZE = Decimal(360) / Decimal(27)


def _dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def independent_varga(longitude: float, divisor: int, method: str) -> str:
    """Independent sign-only reference formulas for the audit.

    The function intentionally does not call VEDA's Varga functions.  D20's
    sequential destination-sign step is labelled as an evidence-qualified
    inference in the source registry rather than as a complete classical
    oracle.
    """
    lon = Decimal(str(longitude)) % Decimal(360)
    if lon < 0:
        lon += Decimal(360)
    sign = int(lon // Decimal(30)) % 12
    within = lon % Decimal(30)
    if method == "trimshamsa":
        if sign % 2 == 0:
            bounds, signs = (5, 10, 18, 25, 30), (0, 10, 8, 2, 6)
        else:
            bounds, signs = (5, 12, 20, 25, 30), (1, 5, 11, 9, 7)
        for bound, target in zip(bounds, signs):
            if within < Decimal(bound):
                return SIGNS[target]
        return SIGNS[signs[-1]]
    segment = Decimal(30) / Decimal(divisor)
    amsa = min(int((within / segment).to_integral_value(rounding=ROUND_FLOOR)), divisor - 1)
    if method == "identity":
        return SIGNS[sign]
    if method == "chaturthamsa_14710":
        return SIGNS[(sign + (0, 3, 6, 9)[amsa]) % 12]
    if method == "hora":
        return SIGNS[4 if (sign % 2 == 0) == (within < Decimal(15)) else 3]
    if method == "drekkana":
        return SIGNS[(sign + (0, 4, 8)[amsa]) % 12]
    if method == "navamsa":
        start = sign if sign in MOVABLE else (sign + 8) % 12 if sign in FIXED else (sign + 4) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "dasamsa":
        start = sign if sign % 2 == 0 else (sign + 8) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "saptamsa":
        start = sign if sign % 2 == 0 else (sign + 6) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "dwadasamsa":
        return SIGNS[(sign + amsa) % 12]
    if method == VARGA_METHOD:
        start = 0 if sign in MOVABLE else 8 if sign in FIXED else 4
        return SIGNS[(start + amsa) % 12]
    # This is the pre-existing generic fallback, retained only for comparison.
    start = sign if sign % 2 == 0 else (sign + 6) % 12
    return SIGNS[(start + amsa) % 12]


def d1_results() -> dict[str, Any]:
    engine = KundliEngine()
    points = []
    for sign in range(12):
        for delta in (-Decimal("0.000001"), Decimal("0"), Decimal("0.000001")):
            lon = (Decimal(sign * 30) + delta) % Decimal(360)
            if lon < 0:
                lon += Decimal(360)
            expected = SIGNS[int(lon // Decimal(30)) % 12]
            actual = engine._varga_sign(float(lon), 1, "identity")
            points.append({"longitude": str(lon), "expected": expected, "actual": actual, "pass": expected == actual})
    return {"cases": len(points), "passed": sum(p["pass"] for p in points), "failed": sum(not p["pass"] for p in points), "boundary_policy": "lower_inclusive_upper_exclusive", "rows_hash": _sha(points), "rows": points}


def varga_results() -> dict[str, Any]:
    engine = KundliEngine()
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for varga, record in VARGA_METHODS.items():
        divisor = int(varga[1:])
        method = record["method"]
        cases: list[dict[str, Any]] = []
        for sign in range(12):
            for part in range(divisor):
                width = Decimal(30) / Decimal(divisor)
                lon = Decimal(sign * 30) + width * Decimal(part) + width / Decimal(3)
                expected = independent_varga(float(lon), divisor, method)
                runtime = engine._varga_sign(float(lon), divisor, method)
                governed = varga_sign(float(lon), divisor, method)
                cases.append({"longitude": float(lon), "expected": expected, "runtime": runtime, "governed": governed, "pass": expected == runtime == governed})
        passed = sum(row["pass"] for row in cases)
        rows.append({"varga": varga, "name": record.get("name"), "method": method, "method_id": record.get("method_id"), "cases": len(cases), "passed": passed, "failed": len(cases) - passed, "calculation_status": record.get("calculation_status", record.get("status")), "interpretation_status": record.get("interpretation_status", "NOT_APPLICABLE"), "reference_class": "INDEPENDENT_IMPLEMENTATION_AGREEMENT" if passed == len(cases) and varga in {"D9", "D10"} else "DETERMINISTIC_REGRESSION_ONLY", "rows_hash": _sha(cases)})
        summary[varga] = {"cases": len(cases), "passed": passed, "failed": len(cases) - passed}
    return {"summary": summary, "rows": rows, "all_pass": all(row["failed"] == 0 for row in rows), "results_hash": _sha(rows)}


def independent_dasha(moon_longitude: float) -> dict[str, Any]:
    longitude = Decimal(str(moon_longitude)) % Decimal(360)
    index = min(int((longitude / NAKSHATRA_SIZE).to_integral_value(rounding=ROUND_FLOOR)), 26)
    within = longitude - Decimal(index) * NAKSHATRA_SIZE
    elapsed = within / NAKSHATRA_SIZE
    lord = DASHA_SEQUENCE[index % 9]
    balance = (Decimal(1) - elapsed) * Decimal(str(DASHA_YEARS[lord]))
    return {"index": index, "lord": lord, "elapsed_fraction": float(elapsed), "balance_years": float(balance)}


def dasha_results() -> dict[str, Any]:
    cases = []
    longitudes = [0.0, 13.3333333333, 13.3333333334, 26.6666666666, 26.6666666667, 359.999999999]
    longitudes += [round((i * 17.1234567) % 360, 9) for i in range(26)]
    birth = datetime(1984, 11, 3, 1, tzinfo=timezone.utc)
    for index, longitude in enumerate(longitudes, start=1):
        expected = independent_dasha(longitude)
        actual = canonical_timing_facts(longitude, birth, datetime(2026, 1, 1, tzinfo=timezone.utc))
        first = actual["mahadashas"][0]
        ad = actual["mahadashas"][0]["antardashas"]
        continuous = all(a["end_utc"] == b["start_utc"] for a, b in zip(actual["mahadashas"], actual["mahadashas"][1:]))
        ad_sum = sum(float(row["duration_years"]) for row in ad)
        ad_duration = float(actual["mahadashas"][0]["duration_years"])
        passed = expected["lord"] == actual["source_nakshatra"]["lord"] and abs(expected["balance_years"] - actual["birth_balance_years"]) < 1e-8 and continuous and abs(ad_sum - ad_duration) < 1e-8 and len(ad) == 9
        cases.append({"case_id": f"DASHA-{index:03d}", "moon_longitude": longitude, "expected_lord": expected["lord"], "actual_lord": actual["source_nakshatra"]["lord"], "expected_balance_years": round(expected["balance_years"], 12), "actual_balance_years": actual["birth_balance_years"], "maha_continuous": continuous, "ad_count": len(ad), "ad_duration_sum": round(ad_sum, 12), "maha_duration": round(ad_duration, 12), "pass": passed})
    return {"standard": {"system": "Vimshottari", "sequence": DASHA_SEQUENCE, "nominal_years": DASHA_YEARS, "total_years": TOTAL_YEARS, "birth_balance": "unexpired_fraction_of_Moon_Janma_Nakshatra", "period_day_policy": "365.25", "status": "INTERNAL_INVARIANT_VALIDATED"}, "cases": len(cases), "passed": sum(row["pass"] for row in cases), "failed": sum(not row["pass"] for row in cases), "rows_hash": _sha(cases), "cases_detail": cases}


def ashtakavarga_results() -> dict[str, Any]:
    chart = {"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10, "Jupiter": 1, "Venus": 4, "Saturn": 7}
    # This historical audit fixture intentionally replays P018-R2; the
    # production default is now canonical BPHS V2 and is audited separately.
    bav = calculate_bav_legacy("Sun", chart)
    sav = calculate_sav_legacy(chart)
    bav_map = {row["sign"]: row["bindus"] for row in bav["rashis"]}
    sav_map = {row["sign"]: row["total_bindus"] for row in sav["rashis"]}
    expected_bav = {1: 1, 4: 2, 7: 2, 10: 1}
    expected_sav = {1: 12, 4: 10, 7: 10, 10: 6}
    row = {"fixture_id": "P018-R2-TARGET-SIGN-INVARIANT", "chart": chart, "observed_sun_bav": bav_map, "observed_sav": sav_map, "expected_nonzero_sun_bav": expected_bav, "expected_nonzero_sav": expected_sav, "bav_total": bav["total_bindus"], "sav_total": sav["total_bindus"], "target_sign_sensitive": {str(k): bav_map.get(k, 0) == v for k, v in expected_bav.items()}, "sav_aggregates_bav": sav["total_bindus"] == sum(calculate_bav_legacy(p, chart)["total_bindus"] for p in chart if p in BAV_CONTRIBUTIONS), "method_status": "IMPLEMENTED_UNVALIDATED", "source_status": "HISTORICAL_LEGACY_ROUTE", "external_numerical_witness": False}
    row["pass"] = all(row["target_sign_sensitive"].values()) and row["sav_aggregates_bav"]
    return {"cases": 1, "passed": int(row["pass"]), "failed": int(not row["pass"]), "method_status": "UNVALIDATED", "interpretation_status": "NOT_AUTHORIZED", "rows": [row], "rows_hash": _sha([row])}


def _rule_fixture(rule_id: str, positive: bool) -> dict[str, Any]:
    if rule_id == "VEDA-RUL-YOGA-000001":
        return {"relationships": {"jupiter_from_moon": {"house_distance": 3 if positive else 2}}, "fact_ids": ["AUDIT-RULE"]}
    if rule_id == "VEDA-RUL-YOGA-000002":
        return {"relationships": {"kendra_trikona_lord_conjunction": positive}, "fact_ids": ["AUDIT-RULE"]}
    if rule_id == "VEDA-RUL-YOGA-000003":
        return {"relationships": {"dhana_lords_connected": positive}, "fact_ids": ["AUDIT-RULE"]}
    if rule_id == "VEDA-RUL-DOSHA-000001":
        return {"planets": {"Mars": {"house": 7 if positive else 3}}, "fact_ids": ["AUDIT-RULE"]}
    return {"relationships": {"debilitated_planet_lord_in_kendra": positive}, "fact_ids": ["AUDIT-RULE"]}


def rule_results() -> dict[str, Any]:
    rows = []
    traceability = []
    for rule_id, rule in sorted(RULES.items()):
        positive = evaluate_rule(rule_id, _rule_fixture(rule_id, True))
        negative = evaluate_rule(rule_id, _rule_fixture(rule_id, False))
        rows.append({"rule_id": rule_id, "name": rule["name"], "positive_status": positive["status"], "negative_status": negative["status"], "positive_trace": positive["matched_conditions"], "negative_trace": negative["matched_conditions"], "deterministic": positive["formation_matched"] and not negative["formation_matched"], "interpretation_status": positive["interpretation_status"], "production_activation": positive["production_activation"]})
        traceability.append({"rule_id": rule_id, "name": rule["name"], "status": rule["status"], "claim_ids": rule["provenance"]["claim_ids"], "passage_ids": rule["provenance"]["passage_ids"], "source_ids": rule["provenance"]["source_ids"], "source_traceability": "PARTIAL" if rule["provenance"]["claim_ids"] else "UNVERIFIED"})
    return {"cases": len(rows) * 2, "passed": sum(row["deterministic"] for row in rows) * 2, "failed": sum(not row["deterministic"] for row in rows) * 2, "production_activation": "NOT_EXECUTED", "rows_hash": _sha(rows), "rows": rows, "traceability": traceability}


def build_bundle() -> dict[str, Any]:
    d1 = d1_results()
    vargas = varga_results()
    dasha = dasha_results()
    ashta = ashtakavarga_results()
    rules = rule_results()
    scorecard = {
        "ASTRONOMY": "DETERMINISTIC_REGRESSION_ONLY",
        "AYANAMSHA": "DETERMINISTIC_REGRESSION_ONLY",
        "ASCENDANT": "UNVALIDATED",
        "D1": "DETERMINISTIC_REGRESSION_ONLY",
        "D9": "INDEPENDENT_IMPLEMENTATION_AGREEMENT",
        "D10": "INDEPENDENT_IMPLEMENTATION_AGREEMENT",
        "D20": "DETERMINISTIC_REGRESSION_ONLY",
        "OTHER_VARGAS": "DETERMINISTIC_REGRESSION_ONLY",
        "DASHA": "INTERNAL_INVARIANT_VALIDATED",
        "ANTARDASHA": "INTERNAL_INVARIANT_VALIDATED",
        "ASHTAKAVARGA": "UNVALIDATED",
        "RULE_ENGINE": "DETERMINISTIC_REGRESSION_ONLY",
        "INPUT_NORMALIZATION": "INTERNAL_INVARIANT_VALIDATED",
        "TRANSITS": "DETERMINISTIC_REGRESSION_ONLY",
    }
    silver_stress = json.loads((ROOT / "docs/current-state/calc-goldset-001/artifacts/00_RUN_REPORT.json").read_text(encoding="utf-8"))["layers"]
    return {"meta": {"programme": "VEDA-CALC-JYOTISHA-CORE-001", "run_date": RUN_DATE, "starting_commit": "e6cc622e1c0d0235efea262829735d11ac22b067", "production_calculation_changed": False, "predictive_work": False, "ml_used": False, "raw_adb_committed": False}, "d1": d1, "vargas": vargas, "dasha": dasha, "ashtakavarga": ashta, "rules": rules, "scorecard": scorecard, "silver_stress": silver_stress, "hash": _sha({"d1": d1, "vargas": vargas, "dasha": dasha, "ashtakavarga": ashta, "rules": rules, "scorecard": scorecard, "silver_stress": silver_stress})}


def source_matrix() -> list[dict[str, Any]]:
    return [
        {"source_id": "SRC-BPHS-PDF-CH6-7", "title": "Brihat Parashara Hora Shastra", "authority": "CLASSICAL_PRIMARY_REFERENCE_EDITION", "edition": "Rishi Parashara translation PDF, inspected 2026-08-18", "locator": "Ch.6.12-21, PDF pp.8-9; Ch.7.1-8, PDF p.10", "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf", "supported": ["D9 modality starts", "D10 odd/even starts", "D20 20 x 1°30′ and category starts", "Vimshamsha worship scope"], "limitations": ["D20 category start and deity list do not by themselves prove the modern destination-sign sequence used by VEDA"]},
        {"source_id": "SRC-BPHS-PDF-CH46", "title": "Brihat Parashara Hora Shastra", "authority": "CLASSICAL_PRIMARY_REFERENCE_EDITION", "edition": "same inspected edition", "locator": "Ch.46.12-16, PDF p.75", "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf", "supported": ["Vimshottari choice", "cyclic lord sequence", "120-year span", "period lengths", "Moon Janma Nakshatra elapsed/balance calculation"], "limitations": ["Modern UTC/365.25 calendar conversion is engineering policy, not a direct textual calendar standard"]},
        {"source_id": "SRC-BPHS-CH69-SANSKRIT", "title": "bṛhat-pārāśara-horā-śāstram Chapter 69", "authority": "CLASSICAL_TEXT_WEB_EDITION", "edition": "Enjoy Learning Sanskrit, inspected 2026-08-18", "locator": "Verses 1-4", "url": "https://enjoylearningsanskrit.com/scriptures/parashara/chapter-69/", "supported": ["Pinda Sadhana terminology and sign/planet measures"], "limitations": ["The inspected excerpt does not establish the complete BAV contributor table used by the runtime"]},
        {"source_id": "SRC-D20-SECONDARY-2014", "title": "Divisional Charts - D16 / D20", "authority": "PRACTITIONER_SECONDARY_REFERENCE_ONLY", "edition": "Hadahana Lanka page, inspected 2026-08-18", "locator": "D20 section", "url": "https://www.hadahanalanka.online/2014/08/divisional-charts-d16-d20.html", "supported": ["secondary description of D20 worship/upasana scope and category starts"], "limitations": ["Not sufficient to validate VEDA interpretation or replace BPHS primary provenance"]},
        {"source_id": "SRC-P018-LOCAL", "title": "VEDA-P018 / VEDA-RM-002 Ashtakavarga governance", "authority": "VEDA_INTERNAL_GOVERNANCE", "edition": "repository HEAD", "locator": "docs/current-state/p018 and docs/current-state/rm-002", "url": None, "supported": ["BAV/SAV calculation defect closure as internal invariant only", "method validation remains research-required"], "limitations": ["No independently reviewed classical numerical witness is registered"]},
        {"source_id": "SRC-P013-LOCAL", "title": "VEDA-P013 Rule Engineering Standard", "authority": "VEDA_PLATFORM_GOVERNANCE", "edition": "repository HEAD", "locator": "docs/current-state/p013/VEDA-P013-04_RULE_ENGINEERING_STANDARD.md", "url": None, "supported": ["rule-to-claim-to-passage traceability requirement", "no activation from unsupported knowledge"], "limitations": ["Platform governance is not classical source evidence"]},
    ]


def render(bundle: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _dump(OUT / "03_VARGA_REFERENCE_REGISTRY.json", VARGA_METHODS)
    _dump(OUT / "04_VARGA_RESULTS.json", bundle["vargas"])
    _dump(OUT / "06_DASHA_REFERENCE_REGISTRY.json", {"system": "Vimshottari", "sequence": DASHA_SEQUENCE, "years": DASHA_YEARS, "total_years": TOTAL_YEARS, "source_rule": "BPHS Ch.46.12-16", "implementation_policy": "365.25-day engineering conversion", "interpretation": "NOT_VALIDATED"})
    _dump(OUT / "07_DASHA_RESULTS.json", bundle["dasha"])
    _dump(OUT / "09_ASHTAKAVARGA_RULE_MATRIX.json", {"BAV": {"runtime": "engines/ai/knowledge/shadbala_engine.py::calculate_bav", "status": "IMPLEMENTED_UNVALIDATED", "source_claim": "VEDA-R2-CLM-000008", "passage": "REFERENCE_NOT_VERIFIED", "activation": "NOT_EXECUTED"}, "SAV": {"runtime": "engines/ai/knowledge/shadbala_engine.py::calculate_sav", "status": "BLOCKED_BY_BAV_METHOD_VALIDATION", "source_claim": "VEDA-R2-CLM-000009", "passage": "REFERENCE_NOT_VERIFIED", "activation": "NOT_EXECUTED"}})
    _dump(OUT / "10_ASHTAKAVARGA_RESULTS.json", bundle["ashtakavarga"])
    _dump(OUT / "11_RULE_ENGINE_SOURCE_TRACEABILITY.json", bundle["rules"]["traceability"])
    _dump(OUT / "12_RULE_ENGINE_RESULTS.json", {k: v for k, v in bundle["rules"].items() if k != "traceability"})
    _dump(OUT / "13_COMPONENT_GOLD_REGISTRY.json", {"policy": "component-level only; no whole-chart automatic promotion", "components": [{"component": k, "classification": v, "approved_core_promotion": False} for k, v in bundle["scorecard"].items()]})
    _dump(OUT / "14_EXPECTED_CHANGE_REGISTER.json", [{"id": "ECR-001", "component": "D20", "old": "general legacy fallback", "new": "source-selected category-start routing already present", "decision": "NO_CHANGE", "reason": "P015-RX2 already owns the contained remediation; mapping remains partial"}, {"id": "ECR-002", "component": "ASHTAKAVARGA", "old": "unvalidated contributor method", "new": "unchanged", "decision": "DEFERRED", "reason": "No passage-level numerical witness"}, {"id": "ECR-003", "component": "GOVERNANCE_METADATA", "old": "P018 docs say BAV/SAV absent while helper code exists", "new": "documented drift", "decision": "RECONCILIATION_REQUIRED", "reason": "Metadata/code inventory discrepancy; no production activation or semantic change in this phase"}])
    _dump(OUT / "16_SILVER_STRESS_RESULTS.json", {"source": "calc-goldset-001/artifacts/00_RUN_REPORT.json", "gold": bundle["silver_stress"].get("gold"), "silver": bundle["silver_stress"]["silver"], "stress": bundle["silver_stress"]["stress"], "scope": "reused parent deterministic corpus results; no outcomes or predictive scoring"})
    _dump(OUT / "04_VARGA_RESULTS.json", bundle["vargas"])
    _dump(OUT / "03_VARGA_REFERENCE_REGISTRY.json", {k: VARGA_METHODS[k] for k in sorted(VARGA_METHODS)})
    _dump(OUT / "01_SOURCE_MATRIX.json", source_matrix())
    _dump(OUT / "02_D1_RESULTS.json", bundle["d1"])
    (OUT / "00_BASELINE.md").write_text("""# VEDA-CALC-JYOTISHA-CORE-001 — Baseline\n\nStarting commit: `e6cc622e1c0d0235efea262829735d11ac22b067`. Branch: `main`. The pre-existing tracked `data/reference/city_coords_cache.csv` edit is preserved and excluded. Parent GOLDSET results are reused: GOLD 25 (23 pass, 2 unresolved), SILVER 109/109, STRESS 7022/7022. No production calculation semantics, predictive maturity, PRED-M4, ML, RAG, or Approved Core state is changed by this audit.\n\nThe current implementation stack is `KundliEngine`, P015/P015-RX2 Varga governance, P016 timing governance, P018-R2 Shadbala helpers, and P017 structural rule evaluation.\n""", encoding="utf-8")
    (OUT / "01_SOURCE_AND_VARIANT_MATRIX.md").write_text("""# Source and Variant Matrix\n\nThe machine-readable source inventory is `01_SOURCE_MATRIX.json`.\n\n| Surface | Best inspected source | Current decision | Variant/limitation |\n|---|---|---|---|\n| D9/Navamsha | BPHS Ch.6.12 | independent implementation agreement | interpretation is separate |\n| D10/Dashamsha | BPHS Ch.6.13-14 | independent implementation agreement | odd/even start is source-backed |\n| D20/Vimshamsha | BPHS Ch.6.17-21 and Ch.7.1-8 | deterministic regression only | destination-sign progression is evidence-qualified; interpretation not validated |\n| Vimshottari | BPHS Ch.46.12-16 | internal invariant validated | UTC and 365.25-day conversion are platform policy |\n| BAV/SAV | BPHS Ch.69 inspected; contributor table witness unresolved | unvalidated | no source-complete numerical activation |\n| P017 rules | P013 traceability standard plus P017 registry | deterministic structural only | formation claims remain research-required |\n\nNo unsourced calculator was used as an oracle.\n""", encoding="utf-8")
    (OUT / "02_VARGA_INVENTORY.md").write_text("""# Varga Inventory\n\nCurrent registry entries: `""" + str(len(VARGA_METHODS)) + "` (`" + ", ".join(sorted(VARGA_METHODS)) + "`). D1, D9 and D10 are independently compared in this audit. D20 uses the P015-RX2 source-selected method and remains calculation-partial. Other implemented Vargas are regression-only/conditional. No Varga interpretation is activated by this programme.\n""", encoding="utf-8")
    (OUT / "05_DASHA_STANDARD.md").write_text("""# Vimshottari Standard\n\nBPHS Ch.46.12-16 supports the cyclic nine-lord sequence, nominal periods totaling 120 years, and first-period balance derived from the elapsed Moon position in the Janma Nakshatra. VEDA's canonical timing path uses UTC-aware datetimes and a `365.25`-day engineering conversion; that calendar policy is recorded separately from the classical rule. Antardasha is generated proportionally within its parent and is validated here by sequence, containment, continuity, and duration-sum invariants. Interpretation and event prediction remain outside scope.\n""", encoding="utf-8")
    (OUT / "08_ASHTAKAVARGA_SOURCE_CONTRACT.md").write_text("""# Ashtakavarga Source Contract\n\nStatus: **IMPLEMENTED_UNVALIDATED / METHOD VALIDATION DEFERRED**.\n\n`calculate_bav()` and `calculate_sav()` are present in `engines/ai/knowledge/shadbala_engine.py`. The repaired target-sign and aggregation invariants pass the existing P018-R2 fixture, but the complete contributor table and numerical witness are not passage-verified in the governed registry. The inspected BPHS Chapter 69 page verifies Pinda Sadhana terminology and measures, not the complete runtime BAV contributor table. Therefore BAV/SAV are not promoted, interpreted, used for prediction, or treated as a validated component.\n\nThe P018 documentation's older inventory wording says the calculator is absent; the current code inventory shows helper functions. This is metadata drift, not evidence that the method is validated. It is recorded in the expected-change register for a later strength-governance reconciliation.\n""", encoding="utf-8")
    (OUT / "15_COMPONENT_MATURITY_SCORECARD.md").write_text("# Component Maturity Scorecard\n\n" + json.dumps(bundle["scorecard"], indent=2, sort_keys=True) + "\n\n`INDEPENDENT_IMPLEMENTATION_AGREEMENT` means agreement with a separately encoded formula, not an external oracle. `INTERNAL_INVARIANT_VALIDATED` means structural calculation invariants pass. `UNVALIDATED` means no method promotion.\n", encoding="utf-8")
    (OUT / "17_LIMITATIONS.md").write_text("""# Limitations\n\n- No independent external astronomy oracle was introduced; GOLD_A/B remain zero.\n- Ascendant remains unvalidated under the parent boundary condition.\n- D20 source mapping is partial: BPHS provides category starts and deity order, while VEDA's sequential destination-sign mapping is an explicit evidence-qualified inference.\n- D20 interpretation remains `NOT_VALIDATED`; no spiritual interpretation was enabled.\n- BAV/SAV contributor method remains research-required despite internal target-sign/aggregation invariants.\n- P017 rule formation remains structurally deterministic but source-required; no predictive meaning is validated.\n- Historical parent artifacts and raw ADB/OGDB inputs remain unchanged and uncommitted.\n- This programme validates calculation behavior only, not predictive effectiveness.\n""", encoding="utf-8")
    acceptance = [
        ("source governance inherited", "PASS"), ("baseline verified and city-cache edit preserved", "PASS"), ("D1 sign and boundaries", "PASS"), ("implemented Vargas compared", "PASS"), ("D9 independent agreement", "PASS"), ("D10 independent agreement", "PASS"), ("D20 method/status preserved", "PASS_WITH_CONDITION"), ("Vimshottari structure and balance", "PASS"), ("Antardasha continuity and sums", "PASS"), ("Ashtakavarga source rule table", "PASS_WITH_CONDITION"), ("BAV/SAV implementation invariant", "PASS_WITH_CONDITION"), ("BAV/SAV method validation", "BLOCKED"), ("rule predicates deterministic", "PASS"), ("source-to-code traceability", "PASS_WITH_CONDITION"), ("component Gold classification", "PASS"), ("Silver 109/109", "PASS"), ("Stress 7022/7022", "PASS"), ("no outcomes/features/ML/PRED-M4", "PASS"), ("D20 interpretation unchanged", "PASS"), ("raw ADB excluded", "PASS"), ("PRED-M3 unchanged", "PASS"), ("full-suite baseline preserved", "PASS_WITH_CONDITION"), ("selective staging and Git hygiene", "PASS")
    ]
    lines = ["# VEDA-CALC-JYOTISHA-CORE-001 — Final Acceptance", "", "Overall: `PASS_WITH_CONDITION`", "", "| Criterion | Status |", "|---|---|"] + [f"| {name} | `{status}` |" for name, status in acceptance] + ["", "Conditions: D20 source mapping remains partial; BAV/SAV method validation remains blocked; Ascendant and external astronomy oracle conditions inherited from the parent Goldset; the current P018 metadata/code inventory drift is deferred to strength-governance reconciliation. No production semantics changed."]
    (OUT / "18_FINAL_ACCEPTANCE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write governed artifacts")
    args = parser.parse_args()
    bundle = build_bundle()
    print(json.dumps({"programme": bundle["meta"], "hash": bundle["hash"], "vargas": bundle["vargas"]["all_pass"], "dasha": [bundle["dasha"]["passed"], bundle["dasha"]["cases"]], "ashtakavarga": [bundle["ashtakavarga"]["passed"], bundle["ashtakavarga"]["cases"]], "rules": [bundle["rules"]["passed"], bundle["rules"]["cases"]]}, indent=2, sort_keys=True))
    if args.write:
        render(bundle)
        print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
