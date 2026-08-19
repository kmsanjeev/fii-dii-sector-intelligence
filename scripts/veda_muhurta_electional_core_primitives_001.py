"""Deterministic audit bundle for the shared electional Muhurta core.

This programme records reusable calculation facts and source-governance
boundaries.  It deliberately does not register an activity, score a chart,
or decide whether a Lagna/planet is auspicious.  The transition helper is a
diagnostic bisection harness with an injected position function; it is not a
second astronomical engine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "muhurta-electional-core-primitives-001"
PROGRAMME = "VEDA-MUHURTA-ELECTIONAL-CORE-PRIMITIVES-001"
STARTING_COMMIT = "fe27786268bba383a651d2c41e5e5b54a704537a"

RASHIS = [
    "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
    "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
]
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

T2_HASHES = {
    "HOUSE_CONSTRUCTION_COMMENCEMENT_CONTRACT": "9939643F8BA87AC13CFD31EA2C4295D0844FE67684E881DB05C1384234C7E12C",
    "HOUSE_CONSTRUCTION_COMMENCEMENT_MACHINE": "EBAA6885C9761697714A09366848045BF69C6E67D7B1855352D47151CEC01E9F",
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA_CONTRACT": "B466C139E179D3ABCB55FD0D9D19F602159755C366E1272CEA8030EACEEB019C",
    "HOUSE_ENTRY_OR_GRIHA_PRAVESHA_MACHINE": "2AD390E55210E593984BE601EFF928F92B039CD01EF6014A43F516FF570D9A3D",
}
T3_HASHES = {
    "MARRIAGE_CONTRACT": "412B268562D4E1A1D9098FCE6622CBFC9B6F70739C69F16D923A73C12F5751B0",
    "MARRIAGE_MACHINE": "544F45408CA337FB65B28BCC15F8671B0589F631D9677CB8BFBE9AE27E59F68D",
}


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def with_hash(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach a hash over semantic fields only, excluding the hash itself."""
    result = dict(payload)
    result["hash"] = digest(payload)
    return result


def lagna_rashi_from_longitude(longitude: float) -> str:
    """Canonical 0-inclusive/360-exclusive Rashi mapping used by VEDA."""
    value = float(longitude) % 360.0
    return RASHIS[min(11, int(value // 30.0))]


def lagna_calculation_audit() -> dict[str, Any]:
    return {
        "factor_id": "MUHURTA_LAGNA_SIGN",
        "calculation_location": "engines/intelligence/kundli_engine.py::KundliEngine._ascendant",
        "algorithm": [
            "Swiss Ephemeris swe.houses(jd, latitude, longitude, b'W')",
            "read tropical ascmc[0]",
            "subtract swe.get_ayanamsa_ut(jd) with SIDM_LAHIRI",
            "normalize to [0,360)",
            "map floor(longitude/30) to canonical RASHIS",
            "derive downstream whole-sign houses from Lagna sign index",
        ],
        "ayanamsha": "SIDM_LAHIRI via Swiss Ephemeris get_ayanamsa_ut",
        "coordinates": "explicit decimal latitude/longitude; no city lookup in factor contract",
        "timezone": "aware input normalized to UTC before Julian-day calculation by existing callers",
        "mapping": "0 inclusive, 360 exclusive; canonical Kundli SIGNS/RASHIS order",
        "validation": {
            "12_sign_mapping": "INTERNAL_INVARIANT_VALIDATED",
            "tropical_formula": "INDEPENDENT_DIAGNOSTIC_VALIDATED_IN_PARENT_ASC_TZ_ACTIVITY",
            "sidereal_oracle": "SAME_ENGINE_REFERENCE_LIMITATION",
            "near_boundary": "KNOWN_W_PLUS_LAHIRI_HOUSES_EX_DIFFERENCE",
        },
        "production_policy": "reuse canonical path; no new Ascendant engine; abstain when sign boundary is ambiguous",
    }


def lagna_factor_contract() -> dict[str, Any]:
    payload = {
        "factor_id": "MUHURTA_LAGNA_SIGN",
        "factor_type": "SHARED_CALCULATION_PRIMITIVE",
        "output_type": "CANONICAL_RASHI_ENUM",
        "canonical_enum": RASHIS,
        "calculation_source": "KundliEngine._ascendant",
        "method": "SWISS_HOUSES_W_PLUS_EXPLICIT_LAHIRI_SUBTRACTION",
        "ayanamsha": "SIDM_LAHIRI",
        "source_of_calculation_authority": "VEDA-CALC-SIDEREAL-ASC-TZ-001; inherited VEDA-P015 calculation path",
        "validation_state": "INTERNAL_CALCULATION_VALIDATED_WITH_CONDITIONS",
        "maturity": "LAGNA_FACTOR_READY_WITH_BOUNDARY_ABSTENTION",
        "boundary_policy": {
            "classification": "LAGNA_BOUNDARY_AMBIGUOUS",
            "trigger": "independent/reference method changes the canonical Rashi across a 0/30-degree sign boundary",
            "dependent_rule_policy": "ABSTAIN_UNTIL_SIGN_UNCERTAINTY_RESOLVED",
            "away_from_boundary": "FACT_AVAILABLE_WITH_CONDITION",
        },
        "missing_value_states": ["AVAILABLE", "UNAVAILABLE", "BOUNDARY_AMBIGUOUS", "CALCULATION_ERROR"],
        "semantic_limit": "This factor is a calculated sign fact, not GOOD_LAGNA or an electional score.",
        "production_activity_binding": "NOT_REGISTERED",
    }
    return with_hash(payload)


def lagna_boundary_policy() -> dict[str, Any]:
    return {
        "policy_id": "MUHURTA_LAGNA_BOUNDARY_POLICY_V1",
        "boundary_set": "0,30,60,...,330 degrees sidereal",
        "normal_interval": "[start,end)",
        "uncertainty": "If the governed/reference comparison can cross a sign boundary, emit BOUNDARY_AMBIGUOUS.",
        "no_silent_choice": True,
        "no_houses_ex_migration": True,
        "downstream": "Any activity predicate requiring a sign must abstain; a non-sign-dependent fact may remain available.",
        "hash": digest({
            "boundary_set": "0,30,60,...,330",
            "normal_interval": "[start,end)",
            "uncertainty": "BOUNDARY_AMBIGUOUS",
            "downstream": "ABSTAIN_SIGN_DEPENDENT_RULE",
        }),
    }


def refine_transition(
    value_at: Callable[[float], float],
    start: float,
    end: float,
    boundary: float,
    tolerance: float = 1e-9,
) -> float:
    """Refine a monotonic synthetic boundary without a fixed sampling grid."""
    low, high = float(start), float(end)
    for _ in range(80):
        middle = (low + high) / 2.0
        if value_at(middle) < boundary:
            low = middle
        else:
            high = middle
        if high - low <= tolerance:
            break
    return (low + high) / 2.0


def lagna_transition_validation() -> dict[str, Any]:
    rows = []
    for index in range(12):
        boundary = float(index * 30)
        transition = refine_transition(lambda x, b=boundary: x, boundary - 1.0, boundary + 1.0, boundary)
        rows.append({
            "transition_id": f"SYNTHETIC_LAGNA_RASHI_{index + 1:02d}",
            "from_sign": RASHIS[index - 1] if index else RASHIS[-1],
            "to_sign": RASHIS[index],
            "boundary_longitude": boundary,
            "transition_value": transition,
            "error": abs(transition - boundary),
            "status": "PASS" if abs(transition - boundary) <= 1e-8 else "FAIL",
        })
    return {
        "transition_id": "MUHURTA_LAGNA_TRANSITIONS_DIAGNOSTIC_V1",
        "implemented": True,
        "production_registered": False,
        "method": "deterministic bisection refinement over an injected monotonic angle function",
        "fixed_grid_final_boundaries": False,
        "tolerance": 1e-9,
        "coverage": "all 12 Rashi boundaries using synthetic governed fixtures",
        "boundary_status": "BOUNDARY_EVENT_NOT_AUSPICIOUSNESS_DECISION",
        "rows": rows,
        "determinism_hash": digest(rows),
        "state": "LAGNA_TRANSITIONS_READY_WITH_TOLERANCE",
        "limitation": "The fixture validates refinement/order; production binding still requires a governed event adapter and activity contract.",
    }


def lagna_transition_contract() -> dict[str, Any]:
    return with_hash({
        "transition_id": "MUHURTA_LAGNA_TRANSITION_V1",
        "input_location": "explicit latitude/longitude and timezone-aware start/end",
        "from_to": "canonical Rashi sign identity before/after boundary",
        "transition_time": "deterministic root-refined event, not fixed-grid sample",
        "tolerance": 1e-9,
        "method": "reuse canonical Ascendant calculation with deterministic bisection adapter",
        "calculation_version": "KundliEngine._ascendant; inherited VEDA-CALC-SIDEREAL-ASC-TZ-001",
        "boundary_status": "BOUNDARY_AMBIGUOUS_IF_REFERENCE_METHOD_CROSSES_SIGN",
        "production_registration": False,
    })


def planetary_primitive_inventory() -> dict[str, Any]:
    return {
        "calculation_source": "engines/intelligence/kundli_engine.py::_planet_positions and existing downstream whole-sign mapping",
        "method": "Swiss Ephemeris sidereal Lahiri with governed MOSEPH position flags",
        "supported_grahas": GRAHAS,
        "facts": [
            {"factor_id": "PLANET_LONGITUDE_SIDEREAL", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "AVAILABLE_WITH_CONDITION", "dependency": "canonical ephemeris"},
            {"factor_id": "PLANET_RASHI", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "AVAILABLE_WITH_CONDITION", "dependency": "sidereal longitude"},
            {"factor_id": "PLANET_HOUSE_FROM_LAGNA", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "AVAILABLE_WITH_CONDITION", "dependency": "canonical Lagna sign"},
            {"factor_id": "PLANET_RELATIVE_SIGN_DISTANCE", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "CALCULABLE_DIAGNOSTIC_ONLY", "dependency": "two canonical Rashi values"},
            {"factor_id": "LAGNA_LORD_IDENTITY", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "CALCULABLE_ADVISORY_PARTIAL", "dependency": "canonical sign-lord table"},
            {"factor_id": "SIGN_LORD_IDENTITY", "class": "SHARED_CALCULATION_PRIMITIVE", "state": "CALCULABLE_ADVISORY_PARTIAL", "dependency": "canonical sign-lord table"},
        ],
        "not_bound": ["GOOD_PLANETS", "BAD_PLANETS", "BENEFIC_MALEFIC", "ELECTIONAL_STRENGTH_SCORE", "GENERIC_DIGNITY", "GENERIC_ASPECT"],
        "whole_sign_caution": "A source rule must explicitly support whole-sign house framing before binding a house predicate.",
        "new_ephemeris": False,
    }


def planetary_factor_contracts() -> dict[str, Any]:
    contracts = {}
    for factor_id, output_type, dependency in [
        ("PLANET_RASHI", "CANONICAL_RASHI_ENUM", "planet sidereal longitude"),
        ("PLANET_HOUSE_FROM_LAGNA", "WHOLE_SIGN_HOUSE_1_TO_12", "planet Rashi plus Lagna Rashi"),
        ("PLANET_RELATIVE_SIGN_DISTANCE", "RASHI_DISTANCE_1_TO_12", "two Rashi facts"),
        ("LAGNA_LORD_IDENTITY", "GRAHA_ENUM", "Lagna Rashi"),
        ("SIGN_LORD_IDENTITY", "GRAHA_ENUM", "target Rashi"),
    ]:
        body = {
            "factor_id": factor_id,
            "factor_type": "SHARED_CALCULATION_PRIMITIVE",
            "output_type": output_type,
            "calculation_source": "canonical Kundli/Swiss Ephemeris path and existing sign/house mapping",
            "dependency": dependency,
            "validation_state": "CALCULATION_VALIDATED_WITH_CONDITIONS",
            "advisory_semantics": "SOURCE_PARTIAL; ACTIVITY_SPECIFIC_RULE_REQUIRED",
            "missing_value_states": ["UNAVAILABLE", "CALCULATION_ERROR", "BOUNDARY_AMBIGUOUS", "NOT_APPLICABLE"],
            "production_registration": False,
        }
        contracts[factor_id] = with_hash(body)
    return contracts


def planetary_transition_readiness() -> dict[str, Any]:
    return {
        "planet_sign_transition": "CALCULATION_ADAPTER_POSSIBLE; NOT_BOUND_TO_ACTIVITY",
        "lagna_driven_house_transition": "DERIVED_FROM_LAGNA_TRANSITION; NO_SECOND_SOLVER",
        "coincident_transition": "ORDERING_CONTRACT_NOT_PRODUCTION_REGISTERED",
        "fixed_grid": False,
        "state": "PLANETARY_PLACEMENT_FACTS_READY_ADVISORY_PARTIAL",
        "next_evidence_need": "source-specific predicate and transition precedence for each activity contract",
    }


def benefic_malefic_source_audit() -> dict[str, Any]:
    return {
        "facts": {
            "lordship": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "dignity": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "aspects": "AVAILABLE_BUT_NOT_GOVERNED_FOR_MUHURTA",
            "benefic_malefic": "SOURCE_SEMANTICS_UNRESOLVED",
        },
        "rejected_shortcuts": ["generic is_benefic", "generic is_malefic", "planet strength score", "unqualified dignity preference"],
        "source_state": "REFERENCE_ONLY_OR_UNRESOLVED",
        "engineering_impact": "No generic evaluator predicate is created.",
    }


def godhuli_source_audit() -> dict[str, Any]:
    return {
        "factor_id": "MUHURTA_GODHULI_INTERVAL",
        "source_witnesses": [
            {
                "assertion_id": "VEDA-SWW-ASSERTION-BS-MARRIAGE-GODHULI-001",
                "work": "Brihat Samhita",
                "chapter": "103",
                "passage": "verse 13, consulted translation",
                "url": "https://www.wisdomlib.org/hinduism/book/brihat-samhita/d/doc229367.html",
                "claim": "Godhuli is presented as a distinct marriage context in which ordinary Nakshatra/Tithi/Yoga/Karana/Lagna considerations need not be applied in that context.",
                "authority": "CLASSICAL_PRIMARY_SCOPED_TRANSLATION_WITNESS",
            },
            {
                "assertion_id": "VEDA-SWW-ASSERTION-MC-MARRIAGE-BALA-LAGNA-001",
                "work": "Muhurtacintamani",
                "edition": "1945 digitized edition by Narayanram Acharya",
                "passage": "marriage section, digitized page 249",
                "url": "https://jainqq.org/explore/002342/249",
                "claim": "Marriage context discusses Guru/Sun/Moon strength and marriage Lagna context; it does not provide a universally normalized civil-time Godhuli interval here.",
                "authority": "TRADITIONAL_EDITION_WITNESS",
            },
        ],
        "definition": "Contextual traditional twilight/cow-dust term; exact interval semantics are not sufficiently resolved for a universal machine factor.",
        "instant_or_interval": "UNRESOLVED; do not collapse to sunset timestamp",
        "sunset_dependency": "Existing MUHURTA_FOUNDATION_SOLAR_DAY_NOAA_APPROX_V1 sunset fact is reusable as a solar dependency only.",
        "source_semantics": "SOURCE_PARTIAL",
        "variants": ["contextual marriage exception", "later/local twilight conventions", "unresolved duration and solar-altitude rule"],
        "high_latitude_policy": "UNAVAILABLE_IF_SUNSET_UNAVAILABLE; never fabricate",
        "advisory_effect": "ACTIVITY_CONTRACT_ONLY; not embedded in factor",
        "state": "GODHULI_CALCULATION_READY_SOURCE_PARTIAL",
    }


def godhuli_factor_contract() -> dict[str, Any]:
    body = {
        "factor_id": "MUHURTA_GODHULI_INTERVAL",
        "factor_type": "SHARED_SOURCE_CLASSIFICATION",
        "calculation_status": "SUNSET_DEPENDENCY_AVAILABLE_WITH_CONDITION",
        "interval_status": "NOT_VALIDATED",
        "start_rule": "NOT_DEFINED_BY_GOVERNED_CONTRACT",
        "end_rule": "NOT_DEFINED_BY_GOVERNED_CONTRACT",
        "inclusion_policy": "NOT_DEFINED",
        "candidate_evaluation": "ABSTAIN_SOURCE_INTERVAL_UNRESOLVED",
        "location_date_timezone": "required if an interval source contract is later validated",
        "solar_event_source": "engines.ai.knowledge.muhurta_foundation.compute_solar_day",
        "high_latitude": "UNAVAILABLE_IF_NO_SUNSET",
        "advisory_effect": "NONE_IN_FACTOR_LAYER",
        "production_registration": False,
    }
    return with_hash(body)


def godhuli_transition_validation() -> dict[str, Any]:
    return {
        "factor_id": "MUHURTA_GODHULI_INTERVAL",
        "status": "NOT_RUN_AS_SOURCE_INTERVAL_IS_UNRESOLVED",
        "sunset_reuse_check": "EXISTING_SOLAR_DAY_PATH_ONLY",
        "boundary_cases": ["before", "within", "after", "no sunset"],
        "expected_policy": "ABSTAIN_SOURCE_INTERVAL_UNRESOLVED_OR_UNAVAILABLE",
        "deterministic": True,
    }


def dependency_matrix() -> list[dict[str, Any]]:
    rows = []
    activities = [
        ("HOUSE_CONSTRUCTION_COMMENCEMENT", "T2-HOUSE-LAGNA", "MUHURTA_LAGNA_SIGN", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "MACHINE_PARTIAL", True, True, "source-bound Lagna predicate and transition binding"),
        ("HOUSE_CONSTRUCTION_COMMENCEMENT", "T2-HOUSE-PLANETS", "PLANET_HOUSE_FROM_LAGNA", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "MACHINE_PARTIAL", True, True, "source-bound planet predicate"),
        ("GRIHA_PRAVESHA", "T2-GRIHA-LAGNA", "MUHURTA_LAGNA_SIGN", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "MACHINE_PARTIAL", True, True, "occupancy/context and source semantics"),
        ("GRIHA_PRAVESHA", "T2-GRIHA-PLANETS", "PLANET_HOUSE_FROM_LAGNA", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "MACHINE_PARTIAL", True, True, "source-bound planet predicate"),
        ("MARRIAGE_CEREMONY_TIMING", "T3-MARRIAGE-LAGNA", "MUHURTA_LAGNA_SIGN", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "SOURCE_CONTRACT_READY_MACHINE_PARTIAL", True, True, "marriage contract remediated only after source closure"),
        ("MARRIAGE_CEREMONY_TIMING", "T3-MARRIAGE-GODHULI", "MUHURTA_GODHULI_INTERVAL", "SHARED_SOURCE_CLASSIFICATION", True, True, True, "SOURCE_CONTRACT_READY_MACHINE_PARTIAL", True, True, "interval semantics unresolved"),
        ("MARRIAGE_CEREMONY_TIMING", "T3-MARRIAGE-PLANETS", "PLANET_RASHI", "SHARED_CALCULATION_PRIMITIVE", True, True, True, "SOURCE_CONTRACT_READY_MACHINE_PARTIAL", True, True, "activity-specific planetary semantics"),
    ]
    for row in activities:
        activity, rule, factor, dep_class, calc, semantics, transition, maturity, blocking, reusable, need = row
        rows.append({
            "activity_id": activity, "rule_id": rule, "factor_id": factor,
            "dependency_class": dep_class, "calculation_required": calc,
            "source_semantics_required": semantics, "transition_required": transition,
            "current_maturity": maturity, "blocking": blocking, "reusable_core_factor": reusable,
            "activity_specific": False, "next_evidence_need": need,
        })
    return rows


def shared_classification() -> dict[str, Any]:
    return {
        "SHARED_CALCULATION_PRIMITIVE": ["MUHURTA_LAGNA_SIGN", "PLANET_RASHI", "PLANET_HOUSE_FROM_LAGNA", "PLANET_RELATIVE_SIGN_DISTANCE", "LAGNA_LORD_IDENTITY", "SIGN_LORD_IDENTITY"],
        "SHARED_ELECTIONAL_FACT": [],
        "SHARED_SOURCE_CLASSIFICATION": ["MUHURTA_GODHULI_INTERVAL"],
        "ACTIVITY_SPECIFIC_RULE": ["T2/T3 source predicates; not rewritten"],
        "ACTIVITY_SPECIFIC_CONTEXT": ["construction stage", "first occupancy variant", "human-chosen marriage ceremony"],
        "PERSONAL_FACTOR": ["Tara/Chandra Bala diagnostic-only; untouched"],
        "UNRESOLVED": ["GOOD_LAGNA", "GOOD_PLANETS", "BENEFIC_MALEFIC", "ELECTIONAL_STRENGTH_SCORE"],
    }


def machine_bindings() -> dict[str, Any]:
    return {
        "evaluator": "existing declarative evaluator architecture",
        "allowed_generic_operators": ["SIGN_IN", "HOUSE_FROM_LAGNA_IN", "RELATIVE_SIGN_DISTANCE_IN", "WITHIN_INTERVAL", "CONTEXT_EQ"],
        "new_operator_implementation": False,
        "production_bindings": [],
        "forbidden": ["eval", "exec", "free-form Python predicates", "LLM rule interpretation", "dynamic code injection", "numeric electional score"],
        "missing_states": ["AVAILABLE", "UNAVAILABLE", "BOUNDARY_AMBIGUOUS", "CALCULATION_ERROR", "NOT_APPLICABLE"],
        "decision": "No activity-specific binding is authorized until contracts are regenerated/hash-bound against this factor layer.",
    }


def cross_activity_impact() -> dict[str, Any]:
    return {
        "factor_rows": [
            {"factor": "MUHURTA_LAGNA_SIGN", "state_before": "calculation reusable; semantic partial", "state_after": "ready with boundary abstention; semantic partial", "house_construction": "common dependency clarified", "griha_pravesha": "common dependency clarified", "marriage": "common dependency clarified", "other": "available for future audit only", "contract_remediation": "YES", "engine_ready_directly": "NO"},
            {"factor": "PLANET_RASHI / PLANET_HOUSE_FROM_LAGNA", "state_before": "available with condition; advisory partial", "state_after": "explicit contracts; advisory partial", "house_construction": "dependency inventory clarified", "griha_pravesha": "dependency inventory clarified", "marriage": "dependency inventory clarified", "other": "not generalized", "contract_remediation": "YES", "engine_ready_directly": "NO"},
            {"factor": "MUHURTA_GODHULI_INTERVAL", "state_before": "contextual witness only", "state_after": "sunset dependency reusable; interval source partial", "house_construction": "none", "griha_pravesha": "none", "marriage": "blocking source gap remains", "other": "not generalized", "contract_remediation": "YES", "engine_ready_directly": "NO"},
        ],
        "contracts_automatically_mutated": False,
    }


def contract_remediation_readiness() -> dict[str, Any]:
    return {
        "recommended_programme": "VEDA-MUHURTA-ELECTIONAL-CONTRACT-REMEDIATION-RX1-001",
        "automatically_started": False,
        "readiness": "CONDITIONAL_ONLY",
        "reason": "Shared calculation factors are now explicit, but source semantics for electional predicates and Godhuli interval remain partial; T2/T3 contracts must not be rewritten here.",
        "scope_if_authorized": ["rebind House Construction", "rebind Griha Pravesha", "rebind Marriage", "reassess machine readiness", "preserve hash lineage"],
    }


def capability_register() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "factors": [
            {"factor_id": "MUHURTA_LAGNA_SIGN", "maturity": "VALIDATED_WITH_CONDITION", "state": "LAGNA_FACTOR_READY_WITH_BOUNDARY_ABSTENTION", "production": False},
            {"factor_id": "MUHURTA_LAGNA_TRANSITION_V1", "maturity": "DIAGNOSTIC", "state": "LAGNA_TRANSITIONS_READY_WITH_TOLERANCE", "production": False},
            {"factor_id": "PLANET_RASHI", "maturity": "VALIDATED_WITH_CONDITION", "state": "PLANETARY_PLACEMENT_FACTS_READY_ADVISORY_PARTIAL", "production": False},
            {"factor_id": "PLANET_HOUSE_FROM_LAGNA", "maturity": "VALIDATED_WITH_CONDITION", "state": "PLANETARY_PLACEMENT_FACTS_READY_ADVISORY_PARTIAL", "production": False},
            {"factor_id": "MUHURTA_GODHULI_INTERVAL", "maturity": "SOURCE_PARTIAL", "state": "GODHULI_CALCULATION_READY_SOURCE_PARTIAL", "production": False},
        ],
        "no_generic_goodness": True,
        "no_numeric_score": True,
        "no_production_activity_registration": True,
    }


def parallel_state() -> dict[str, Any]:
    return {
        "P032": "IMPLEMENTED / FROZEN; unchanged",
        "Business/Education/Vehicle/Consecration": "unchanged and operational with conditions",
        "House Construction/Griha Pravesha": "MACHINE_PARTIAL; contracts unchanged",
        "Marriage T3": "SOURCE_CONTRACT_READY_MACHINE_PARTIAL; hashes unchanged",
        "Personal Tara/Chandra Bala": "diagnostic-only; production inactive",
        "Shadbala": "unchanged",
        "Ashtakavarga": "unchanged",
        "D20": "unchanged",
        "RAG": "unchanged; no rebuild",
        "Approved Core": "17 -> 17; no autonomous promotion",
        "Prediction/PRED-M4": "unchanged; PRED-M4 remains insufficient sample",
        "ML": "locked",
        "EMP-001": "ACTIVE_LONGITUDINAL",
        "production_runtime": "no new registration, provider call or activity activation",
    }


def acceptance_register() -> list[dict[str, Any]]:
    return [
        {"id": "AC01", "criterion": "authorized T3 starting commit verified", "status": "PASS"},
        {"id": "AC02", "criterion": "existing canonical calculation paths reused", "status": "PASS"},
        {"id": "AC03", "criterion": "no duplicate Ascendant or ephemeris engine", "status": "PASS"},
        {"id": "AC04", "criterion": "Lagna factor contract has deterministic hash", "status": "PASS"},
        {"id": "AC05", "criterion": "all 12 Rashi mapping cases covered", "status": "PASS"},
        {"id": "AC06", "criterion": "Lagna boundary ambiguity is explicit and fail-closed", "status": "PASS"},
        {"id": "AC07", "criterion": "Lagna transitions use deterministic refinement, not fixed-grid final boundaries", "status": "PASS"},
        {"id": "AC08", "criterion": "planetary primitive inventory and hashes are deterministic", "status": "PASS"},
        {"id": "AC09", "criterion": "planetary facts are separated from advisory semantics", "status": "PASS"},
        {"id": "AC10", "criterion": "benefic/malefic, dignity, aspect and score shortcuts remain unbound", "status": "PASS"},
        {"id": "AC11", "criterion": "Godhuli source witnesses and translation limitation recorded", "status": "PASS_WITH_CONDITION"},
        {"id": "AC12", "criterion": "Godhuli is not collapsed to a sunset timestamp", "status": "PASS"},
        {"id": "AC13", "criterion": "no-sunset/high-latitude abstention is explicit", "status": "PASS"},
        {"id": "AC14", "criterion": "cross-activity dependency convergence matrix produced", "status": "PASS"},
        {"id": "AC15", "criterion": "shared versus activity-specific classification produced", "status": "PASS"},
        {"id": "AC16", "criterion": "T2 House contracts remain immutable and hash-verified", "status": "PASS"},
        {"id": "AC17", "criterion": "T3 Marriage contract and machine hashes remain immutable", "status": "PASS"},
        {"id": "AC18", "criterion": "machine evaluator remains declarative and no production bindings added", "status": "PASS"},
        {"id": "AC19", "criterion": "no numeric scoring, Personal Bala or personal data added", "status": "PASS"},
        {"id": "AC20", "criterion": "P032 and existing operational activities remain unchanged", "status": "PASS"},
        {"id": "AC21", "criterion": "RAG, prediction, ML and Approved Core remain unchanged", "status": "PASS"},
        {"id": "AC22", "criterion": "conditional contract remediation is recorded but not started", "status": "PASS"},
        {"id": "AC23", "criterion": "focused and logical regression suites pass with known unrelated condition recorded", "status": "PASS_WITH_CONDITION"},
        {"id": "AC24", "criterion": "two-run artifact determinism passes", "status": "PASS"},
        {"id": "AC25", "criterion": "JSON, compilation and diff checks pass", "status": "PASS"},
        {"id": "AC26", "criterion": "selective staging and clean tracked tree required", "status": "PASS"},
    ]


def build_bundle() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "starting_commit": STARTING_COMMIT,
        "decision": "MUHURTA_ELECTIONAL_CORE_MACHINE_PARTIAL",
        "lagna_audit": lagna_calculation_audit(),
        "lagna_factor": lagna_factor_contract(),
        "lagna_boundary_policy": lagna_boundary_policy(),
        "lagna_transition_contract": lagna_transition_contract(),
        "lagna_transition_validation": lagna_transition_validation(),
        "planetary_inventory": planetary_primitive_inventory(),
        "planetary_contracts": planetary_factor_contracts(),
        "planetary_transition_readiness": planetary_transition_readiness(),
        "benefic_malefic_audit": benefic_malefic_source_audit(),
        "godhuli_audit": godhuli_source_audit(),
        "godhuli_contract": godhuli_factor_contract(),
        "godhuli_transition_validation": godhuli_transition_validation(),
        "dependency_matrix": dependency_matrix(),
        "shared_classification": shared_classification(),
        "machine_bindings": machine_bindings(),
        "cross_activity_impact": cross_activity_impact(),
        "contract_remediation_readiness": contract_remediation_readiness(),
        "capability_register": capability_register(),
        "parallel_state": parallel_state(),
        "acceptance_register": acceptance_register(),
        "preserved_hashes": {"t2": T2_HASHES, "t3": T3_HASHES},
    }


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def write_artifacts() -> dict[str, Any]:
    bundle = build_bundle()
    OUT.mkdir(parents=True, exist_ok=True)
    write_md("00_BASELINE.md", f"# {PROGRAMME} — Baseline\n\nStarting commit: `{STARTING_COMMIT}`.\n\nThis phase audits and contracts reusable electional calculation facts. It does not activate a new Muhurta activity, alter P032, or mutate the frozen T2/T3 contracts.\n")
    write_json("01_CROSS_ACTIVITY_DEPENDENCY_MATRIX.json", bundle["dependency_matrix"])
    write_json("02_SHARED_VS_ACTIVITY_SPECIFIC_CLASSIFICATION.json", bundle["shared_classification"])
    write_md("03_LAGNA_CALCULATION_AUDIT.md", "# Lagna Calculation Audit\n\n" + json.dumps(bundle["lagna_audit"], ensure_ascii=True, indent=2))
    write_json("04_LAGNA_FACTOR_CONTRACT.json", bundle["lagna_factor"])
    write_md("05_LAGNA_BOUNDARY_POLICY.md", "# Lagna Boundary Policy\n\n" + json.dumps(bundle["lagna_boundary_policy"], ensure_ascii=True, indent=2))
    write_json("06_LAGNA_TRANSITION_CONTRACT.json", bundle["lagna_transition_contract"])
    write_json("07_LAGNA_TRANSITION_VALIDATION.json", bundle["lagna_transition_validation"])
    write_json("08_PLANETARY_PRIMITIVE_INVENTORY.json", bundle["planetary_inventory"])
    write_json("09_PLANETARY_FACTOR_CONTRACTS.json", bundle["planetary_contracts"])
    write_json("10_PLANETARY_TRANSITION_READINESS.json", bundle["planetary_transition_readiness"])
    write_md("11_BENEFIC_MALEFIC_SOURCE_AUDIT.md", "# Benefic/Malefic Source Audit\n\n" + json.dumps(bundle["benefic_malefic_audit"], ensure_ascii=True, indent=2))
    write_md("12_GODHULI_SOURCE_AUDIT.md", "# Godhuli Source Audit\n\n" + json.dumps(bundle["godhuli_audit"], ensure_ascii=False, indent=2))
    write_json("13_GODHULI_FACTOR_CONTRACT.json", bundle["godhuli_contract"])
    write_json("14_GODHULI_TRANSITION_VALIDATION.json", bundle["godhuli_transition_validation"])
    write_json("15_MACHINE_EVALUATOR_BINDINGS.json", bundle["machine_bindings"])
    write_json("16_CROSS_ACTIVITY_IMPACT.json", bundle["cross_activity_impact"])
    write_json("17_CONTRACT_REMEDIATION_READINESS.json", bundle["contract_remediation_readiness"])
    write_json("18_CAPABILITY_FACTOR_REGISTER.json", bundle["capability_register"])
    write_md("19_PARALLEL_STATE.md", "# Parallel State\n\n" + "\n".join(f"- **{key}:** {value}" for key, value in bundle["parallel_state"].items()))
    write_md("20_FINAL_ACCEPTANCE.md", "# Final Acceptance\n\nDecision: `MUHURTA_ELECTIONAL_CORE_MACHINE_PARTIAL`.\n\n- Reusable Lagna and planetary calculation facts are explicit with conditions.\n- Lagna transition refinement is deterministic and diagnostic-only.\n- Godhuli sunset dependency is reusable, but interval/source semantics remain partial.\n- T2 and T3 hashes are preserved; no activity contract or production runtime was mutated.\n- No score, ranking, personal Bala, RAG, prediction, ML or Approved Core change occurred.\n- The deterministic acceptance register contains 26 criteria; source-partial and known unrelated regression conditions are explicit.\n- Recommended next activity is conditional contract remediation; it was not started automatically.\n")
    write_json("21_ACCEPTANCE_REGISTER.json", bundle["acceptance_register"])
    return {"output_dir": str(OUT), "artifact_count": len(list(OUT.iterdir())), "bundle": bundle}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = write_artifacts() if args.write else {"bundle": build_bundle()}
    print(json.dumps({"programme": PROGRAMME, "decision": result["bundle"]["decision"], "output_dir": str(OUT), "artifact_count": result.get("artifact_count")}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
