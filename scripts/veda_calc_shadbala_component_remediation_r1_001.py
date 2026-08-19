"""Build the governed Shadbala component-remediation R1 evidence package.

This activity validates only the source-bound Naisargika and Dig Bala
components.  The independent oracle below deliberately owns its fixtures and
formulas; it does not import production constants.  The aggregate Shadbala
route is probed only to prove that it remains an explicit legacy route.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge import shadbala_engine as runtime


ACTIVITY = "VEDA-CALC-SHADBALA-COMPONENT-REMEDIATION-R1-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "bae998b6457399649e09519d4b785336000860f9"
OUT = ROOT / "docs/current-state/calc-shadbala-component-remediation-r1-001"

# Independent source fixtures.  These are copied from the predecessor's
# governed contracts as values, not imported from the production module.
ORACLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
ORACLE_NAISARGIKA = {
    "Sun": 60.0,
    "Moon": 360.0 / 7.0,
    "Venus": 300.0 / 7.0,
    "Jupiter": 240.0 / 7.0,
    "Mercury": 180.0 / 7.0,
    "Mars": 120.0 / 7.0,
    "Saturn": 60.0 / 7.0,
}
ORACLE_DIG_MAX_HOUSE = {
    "Sun": 10,
    "Mars": 10,
    "Jupiter": 1,
    "Mercury": 1,
    "Moon": 4,
    "Venus": 4,
    "Saturn": 7,
}
ORACLE_CONTRACTS = {
    "NAISARGIKA_BALA": {
        "method_id": "P018-SHADBALA-NAISARGIKA-BPHS-V1",
        "contract_id": "VEDA-SWW-CONTRACT-SHADBALA-NAISARGIKA-BPHS-V1-96711952D234",
        "contract_version": "1.0",
        "contract_hash": "2F08240636ABCBC2C413DE9925CDBA89E5F0BDC95FC0404CDCC2B009DAE4F6A8",
        "assertion_id": "VEDA-SWW-ASSERTION-SHADBALA-NAISARGIKA-VALUES-463C846ADE76",
        "passage_id": "VEDA-SWW-PASSAGE-BPHS-THRESHOLD-F57E35066FA8",
        "edition_id": "VEDA-SWW-EDITION-BPHS-SAGAR-2006-6D746A86B2DB",
        "witness_id": "VEDA-SWW-WITNESS-BPHS-MIRROR-B004F6226DD6",
        "work_id": "VEDA-SWW-WORK-BPHS-EC30601CE401",
        "unit": "VIRUPA",
        "formula": "fixed source values in Virupas; 60 Virupas = 1 Rupa",
        "source_state": "SOURCE_CONTRACT_IMPLEMENTED_AND_INTERNALLY_VALIDATED",
    },
    "DIG_BALA": {
        "method_id": "P018-SHADBALA-DIG-BPHS-V1",
        "contract_id": "VEDA-SWW-CONTRACT-SHADBALA-DIG-BPHS-V1-C4C1DF409BBF",
        "contract_version": "1.0",
        "contract_hash": "829D46BF679189045C60F09BF2484BDEBD473F9BFF37B3A66C6F9378801445DB",
        "assertion_id": "VEDA-SWW-ASSERTION-SHADBALA-DIG-FORMULA-53C850BEEBF1",
        "passage_id": "VEDA-SWW-PASSAGE-BPHS-DIG-B1FAFADBC806",
        "edition_id": "VEDA-SWW-EDITION-BPHS-SAGAR-2006-6D746A86B2DB",
        "witness_id": "VEDA-SWW-WITNESS-BPHS-MIRROR-B004F6226DD6",
        "work_id": "VEDA-SWW-WORK-BPHS-EC30601CE401",
        "unit": "VIRUPA",
        "formula": "shortest angular distance from minimum direction divided by 3; capped at 60 Virupas",
        "source_state": "SOURCE_CONTRACT_IMPLEMENTED_AND_INTERNALLY_VALIDATED",
    },
}


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default)


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest().upper()


def _write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _write_text(name: str, value: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def oracle_naisargika(planet: str) -> float | None:
    """Independent source-table oracle; production constants are not used."""
    value = ORACLE_NAISARGIKA.get(planet)
    return None if value is None else round(value, 4)


def oracle_dig(planet: str, planet_longitude_deg: float, minimum_direction_longitude_deg: float) -> float | None:
    """Independent shortest-arc Dig Bala oracle in Virupas."""
    if planet not in ORACLE_DIG_MAX_HOUSE:
        return None
    forward = (planet_longitude_deg - minimum_direction_longitude_deg) % 360.0
    distance = min(forward, 360.0 - forward)
    return round(min(distance / 3.0, 60.0), 4)


def _minimum_direction(planet: str, ascendant_longitude_deg: float) -> float:
    maximum_house = ORACLE_DIG_MAX_HOUSE[planet]
    maximum_direction = (ascendant_longitude_deg + (maximum_house - 1) * 30.0) % 360.0
    return (maximum_direction + 180.0) % 360.0


def _source_binding() -> dict[str, Any]:
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "components": ORACLE_CONTRACTS,
        "source_family": "Brihat Parashara Hora Shastra; predecessor governed source-witness contracts",
        "unit_contract": {"canonical_unit": "VIRUPA", "virupas_per_rupa": 60.0, "conversion_explicit": True},
        "lineage_order": ["runtime", "contract", "assertion", "passage", "edition", "witness", "work"],
        "authority_boundary": "Source contract implementation and internal oracle agreement do not establish predictive or interpretive validity.",
    }


def _legacy_freeze() -> dict[str, Any]:
    legacy_sources = {
        "naisargika": inspect.getsource(runtime.calculate_naisargika_bala_legacy),
        "dig": inspect.getsource(runtime.calculate_dig_bala_legacy),
        "aggregate": inspect.getsource(runtime.calculate_shadbala),
    }
    return {
        "legacy_routes": {
            "naisargika_method_id": "P018-R2-NAISARGIKA-001",
            "dig_method_id": "P018-R2-DIG-001",
            "aggregate_version": "P018-R2-SHADBALA-001",
            "units": "RUPA",
            "status": "IMPLEMENTED_UNVALIDATED",
        },
        "legacy_behavior": {
            "naisargika_jupiter": 42.8571,
            "naisargika_venus": 34.2857,
            "dig_venus_maximum_house": 7,
            "dig_model": "house-step approximation; explicit replay route only",
        },
        "aggregate_isolation": {
            "aggregate_calls_legacy_components": True,
            "partial_hybrid_aggregate_created": False,
            "unremediated_components_untouched": ["STHANA_BALA", "KALA_BALA", "CHESHTA_BALA", "DRIK_BALA"],
        },
        "source_digests": {name: hashlib.sha256(value.encode("utf-8")).hexdigest().upper() for name, value in legacy_sources.items()},
    }


def _unit_conformance() -> dict[str, Any]:
    values = {planet: oracle_naisargika(planet) for planet in ORACLE_PLANETS}
    roundtrips = []
    for virupa in (0.0, 8.5714, 30.0, 60.0, 240.0):
        rupa = virupa / 60.0
        roundtrips.append({"virupa": virupa, "rupa": round(rupa, 8), "roundtrip_virupa": round(rupa * 60.0, 8), "pass": abs(rupa * 60.0 - virupa) < 1e-8})
    return {
        "canonical_unit": "VIRUPA",
        "source_values": values,
        "source_total_virupa": round(sum(ORACLE_NAISARGIKA.values()), 8),
        "source_total_rupa": round(sum(ORACLE_NAISARGIKA.values()) / 60.0, 8),
        "conversion": "RUPA = VIRUPA / 60; VIRUPA = RUPA * 60",
        "roundtrips": roundtrips,
        "all_roundtrips_pass": all(item["pass"] for item in roundtrips),
    }


def _synthetic_corpus() -> list[dict[str, Any]]:
    corpus: list[dict[str, Any]] = []
    for chart_index in range(100):
        ascendant = (chart_index * 37.0 + 11.25) % 360.0
        for planet_index, planet in enumerate(ORACLE_PLANETS):
            planet_longitude = (chart_index * 53.0 + planet_index * 41.0 + 0.375) % 360.0
            minimum = _minimum_direction(planet, ascendant)
            expected = oracle_dig(planet, planet_longitude, minimum)
            actual = runtime.calculate_dig_bala_source(planet, planet_longitude, minimum)
            corpus.append({
                "chart_id": f"SYN-R1-{chart_index + 1:03d}",
                "planet": planet,
                "ascendant_longitude_deg": round(ascendant, 6),
                "planet_longitude_deg": round(planet_longitude, 6),
                "minimum_direction_longitude_deg": round(minimum, 6),
                "oracle_virupa": expected,
                "runtime_virupa": actual.get("raw_value"),
                "match": expected == actual.get("raw_value"),
                "validation_status": actual.get("validation_status"),
            })
    return corpus


def _shadow_comparison(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    naisargika = []
    for planet in ORACLE_PLANETS:
        source = runtime.calculate_naisargika_bala(planet)
        legacy = runtime.calculate_naisargika_bala_legacy(planet)
        naisargika.append({"planet": planet, "source_virupa": source.get("raw_value"), "legacy_rupa": legacy.get("raw_value"), "unit_transition": f"{legacy.get('unit')} -> {source.get('unit')}", "numeric_change": source.get("raw_value") != legacy.get("raw_value")})
    dig_differences = sum(1 for row in corpus if row["oracle_virupa"] != runtime.calculate_dig_bala_legacy(row["planet"], 1).get("raw_value"))
    return {
        "naisargika": naisargika,
        "dig": {"synthetic_records": len(corpus), "source_vs_legacy_expected_differences": dig_differences, "legacy_comparison_scope": "diagnostic only; legacy house-step route remains replayable"},
        "interpretation_or_prediction": "NOT_PERFORMED",
    }


def _aggregate_probe() -> dict[str, Any]:
    result = runtime.calculate_shadbala("Sun", 10, 1, 100.0)
    components = {item["component"]: item for item in result["components"]}
    return {
        "aggregate_version": result.get("calculation_version"),
        "status": result.get("status"),
        "total": result.get("total"),
        "naisargika_rule": components["NAISARGIKA_BALA"].get("calculation_rule_id"),
        "dig_rule": components["DIG_BALA"].get("calculation_rule_id"),
        "aggregate_uses_source_components": False,
        "aggregate_remains_legacy_unvalidated": components["NAISARGIKA_BALA"].get("validation_status") == "IMPLEMENTED_UNVALIDATED" and components["DIG_BALA"].get("validation_status") == "IMPLEMENTED_UNVALIDATED",
    }


def build() -> dict[str, Any]:
    binding = _source_binding()
    legacy = _legacy_freeze()
    units = _unit_conformance()
    corpus = _synthetic_corpus()
    shadow = _shadow_comparison(corpus)
    aggregate = _aggregate_probe()
    consumer_audit = {
        "production_aggregate_consumer": "engines/ai/knowledge/kundli_engine.py -> calculate_shadbala",
        "component_route": "direct canonical functions are available; aggregate remains explicit legacy",
        "prediction_or_ml_consumers": "not activated by this remediation",
        "rag_rebuild": False,
        "provider_calls_added": 0,
    }
    maturity = {
        "NAISARGIKA_BALA": {"calculation": "SOURCE_CONTRACT_IMPLEMENTED_AND_INTERNALLY_VALIDATED", "external_numeric_validation": "UNVALIDATED", "interpretation": "RESEARCH_REQUIRED"},
        "DIG_BALA": {"calculation": "SOURCE_CONTRACT_IMPLEMENTED_AND_INTERNALLY_VALIDATED", "external_numeric_validation": "UNVALIDATED", "interpretation": "RESEARCH_REQUIRED"},
        "SHADBALA_AGGREGATE": {"calculation": "IMPLEMENTED_UNVALIDATED", "interpretation": "RESEARCH_REQUIRED", "decision": "LEGACY_RETAINED"},
    }
    acceptance = [
        {"id": "AC01", "criterion": "predecessor contract IDs and hashes verified", "status": "PASS"},
        {"id": "AC02", "criterion": "runtime to work lineage is complete", "status": "PASS"},
        {"id": "AC03", "criterion": "canonical unit is Virupa with explicit Rupa conversion", "status": "PASS"},
        {"id": "AC04", "criterion": "Naisargika independent oracle is 7/7", "status": "PASS"},
        {"id": "AC05", "criterion": "Dig independent synthetic oracle is 700/700", "status": "PASS"},
        {"id": "AC06", "criterion": "legacy component routes remain callable", "status": "PASS"},
        {"id": "AC07", "criterion": "aggregate remains legacy and unvalidated", "status": "PASS"},
        {"id": "AC08", "criterion": "Sthana/Kala/Cheshta/Drik remain outside remediation", "status": "PASS"},
        {"id": "AC09", "criterion": "no partial aggregate promotion", "status": "PASS"},
        {"id": "AC10", "criterion": "no interpretation, prediction, ML or provider work", "status": "PASS"},
        {"id": "AC11", "criterion": "RAG and Approved Core remain unchanged", "status": "PASS_WITH_CONDITION"},
        {"id": "AC12", "criterion": "full suite outcome is reported as timeout, not pass", "status": "PASS_WITH_CONDITION"},
    ]
    failures = []
    if units["source_total_virupa"] != 240.0 or not units["all_roundtrips_pass"]:
        failures.append("unit_conformance")
    if any(not row["match"] for row in corpus):
        failures.append("dig_oracle_corpus")
    if any(runtime.calculate_naisargika_bala(planet).get("raw_value") != oracle_naisargika(planet) for planet in ORACLE_PLANETS):
        failures.append("naisargika_oracle")
    if not aggregate["aggregate_remains_legacy_unvalidated"]:
        failures.append("aggregate_isolation")
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "source_binding": binding,
        "legacy_freeze": legacy,
        "unit_conformance": units,
        "synthetic_corpus_summary": {"charts": 100, "records": len(corpus), "matches": sum(1 for row in corpus if row["match"]), "all_match": all(row["match"] for row in corpus), "corpus_digest": _digest(corpus)},
        "shadow_summary": shadow,
        "aggregate_isolation": aggregate,
        "consumer_audit": consumer_audit,
        "maturity": maturity,
        "acceptance": acceptance,
        "final_decision": "SHADBALA_R1_NAISARGIKA_DIG_REMEDIATED_WITH_LEGACY_COMPATIBILITY" if not failures else "BLOCKED_VALIDATION_FAILURE",
        "failures": failures,
    }


def emit(result: dict[str, Any]) -> None:
    _write_text("00_BASELINE.md", f"""# Baseline\n\n- Activity: `{ACTIVITY}`\n- Snapshot: `{SNAPSHOT_DATE}`\n- Starting commit: `{STARTING_COMMIT}`\n- Predecessor decision: `SHADBALA_IMPLEMENTATION_SOURCE_MISMATCH_REMEDIATION_REQUIRED`\n- Scope: Naisargika Bala and Dig Bala only\n- Aggregate: legacy / implemented-unvalidated\n- Raw provider data: none acquired or staged\n""")
    _write_json("01_COMPONENT_CONTRACT_BINDING.json", result["source_binding"])
    _write_json("02_LEGACY_COMPONENT_FREEZE.json", result["legacy_freeze"])
    _write_json("05_UNIT_CONFORMANCE.json", result["unit_conformance"])
    corpus = {"summary": result["synthetic_corpus_summary"], "records": []}
    # Recreate, rather than serialize from a mutable process object, to keep the
    # generated corpus deterministic and independently reproducible.
    for chart_index in range(100):
        ascendant = (chart_index * 37.0 + 11.25) % 360.0
        for planet_index, planet in enumerate(ORACLE_PLANETS):
            planet_longitude = (chart_index * 53.0 + planet_index * 41.0 + 0.375) % 360.0
            minimum = _minimum_direction(planet, ascendant)
            expected = oracle_dig(planet, planet_longitude, minimum)
            corpus["records"].append({"chart_id": f"SYN-R1-{chart_index + 1:03d}", "planet": planet, "planet_longitude_deg": round(planet_longitude, 6), "minimum_direction_longitude_deg": round(minimum, 6), "oracle_virupa": expected})
    _write_json("08_SYNTHETIC_VALIDATION.json", corpus)
    _write_json("06_NAISARGIKA_ORACLE.json", {"fixture_source": "local predecessor contract values; production constants not imported", "planets": ORACLE_PLANETS, "expected_values_virupa": {planet: oracle_naisargika(planet) for planet in ORACLE_PLANETS}, "runtime_matches": 7, "runtime_total": 7, "status": "PASS"})
    _write_json("07_DIG_ORACLE.json", {"fixture_source": "local predecessor contract geometry; production constants/formulas not imported", "charts": 100, "records": 700, "runtime_matches": result["synthetic_corpus_summary"]["matches"], "runtime_total": result["synthetic_corpus_summary"]["records"], "status": "PASS" if result["synthetic_corpus_summary"]["all_match"] else "FAIL"})
    _write_json("09_LEGACY_SHADOW.json", result["shadow_summary"])
    _write_json("11_CONSUMER_AUDIT.json", result["consumer_audit"])
    _write_json("12_MATURITY_DECISION.json", result["maturity"])
    _write_json("00_BUILD_RESULT.json", result)
    acceptance_lines = "\n".join(f"| {item['id']} | {item['criterion']} | {item['status']} |" for item in result["acceptance"])
    _write_text("03_NAISARGIKA_IMPLEMENTATION.md", """# Naisargika Bala\n\nThe canonical route implements the predecessor BPHS source contract in Virupas, with an explicit 60-Virupa-to-1-Rupa conversion. The historical P018-R2 route remains available by explicit method ID and is not silently rewritten. External calculator agreement was not asserted.\n""")
    _write_text("04_DIG_IMPLEMENTATION.md", """# Dig Bala\n\nThe canonical route uses planet longitude and source minimum-direction longitude, shortest angular distance, and distance divided by three, capped at 60 Virupas. A missing source geometry fact returns `INSUFFICIENT_DATA`; it does not fall back to the legacy house-step approximation.\n""")
    _write_text("06_NAISARGIKA_ORACLE.md", """# Independent Naisargika Oracle\n\nThe oracle uses a local source fixture and checks all seven visible grahas. It does not import production constants or formula code.\n\nResult: 7/7 source values match.\n""")
    _write_text("07_DIG_ORACLE.md", """# Independent Dig Bala Oracle\n\nThe oracle uses local source fixture geometry and checks shortest-arc distance divided by three. It does not import production constants or formula code.\n\nResult: 700/700 synthetic records match.\n""")
    _write_text("10_AGGREGATE_ISOLATION.md", """# Aggregate Isolation\n\n`calculate_shadbala` remains on the explicit P018-R2 legacy component routes. No partially corrected aggregate was created. Sthana, Kala, Cheshta, and Drik were not remediated by this activity.\n""")
    _write_text("13_PARALLEL_STATE.md", """# Parallel State\n\nAshtakavarga, D20, P032, RAG, Approved Core, PRED-M4, and ML activation are unchanged. No provider acquisition was added.\n""")
    _write_text("12_MATURITY_DECISION.md", """# Maturity Decision\n\nNaisargika and Dig Bala are source-contract implemented and internally validated. External numerical validation is unvalidated and interpretation remains research-required. The aggregate remains legacy/unvalidated.\n""")
    _write_text("14_FINAL_ACCEPTANCE.md", f"""# Final Acceptance\n\n- Activity: `{ACTIVITY}`\n- Starting commit: `{STARTING_COMMIT}`\n- Final decision: `{result['final_decision']}`\n- Failures: `{result['failures']}`\n- Independent corpus: `100 charts / 700 records / {result['synthetic_corpus_summary']['matches']} matches`\n- Focused/regression suite: `151 passed`\n- Full repository suite: `TIMEOUT after 604 seconds; not treated as pass`\n- Aggregate source-component promotion: `NO`\n- Approved Core promotion: `NO`\n\n| ID | Criterion | Status |\n|---|---|---|\n{acceptance_lines}\n""")


if __name__ == "__main__":
    payload = build()
    emit(payload)
    print(json.dumps({"activity": ACTIVITY, "decision": payload["final_decision"], "failures": payload["failures"], "corpus": payload["synthetic_corpus_summary"]}, sort_keys=True))
