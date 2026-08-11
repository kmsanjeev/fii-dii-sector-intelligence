import json
from pathlib import Path

import jsonschema

from engines.ai.knowledge.strength_governance import (
    build_phase_bundle,
    canonical_strength_fact,
    validate_bundle,
)


def test_p018_inventory_explicitly_records_absent_implementations():
    bundle = build_phase_bundle()
    assert bundle["summary"]["existing_shadbala"] is False
    assert bundle["summary"]["existing_ashtakavarga"] is False
    assert {row["system_id"] for row in bundle["strength_registry"]} == {"DIGNITY", "SHADBALA", "ASHTAKAVARGA"}


def test_p018_dignity_is_not_collapsed_into_strength():
    bundle = build_phase_bundle()
    dignity = next(row for row in bundle["strength_registry"] if row["system_id"] == "DIGNITY")
    shadbala = next(row for row in bundle["strength_registry"] if row["system_id"] == "SHADBALA")
    assert dignity["kind"] != shadbala["kind"]
    assert dignity["status"] == "GOVERNED_SEPARATE_SYSTEM"


def test_p018_unsupported_components_are_explicitly_blocked():
    bundle = build_phase_bundle()
    assert next(row for row in bundle["capability_status"] if row["component"] == "DRIK_BALA")["status"] == "BLOCKED_BY_ASPECT_FOUNDATION"
    assert next(row for row in bundle["capability_status"] if row["component"] == "SAV")["status"] == "BLOCKED_BY_BAV"
    assert validate_bundle(bundle)["is_valid"] is True


def test_p018_strength_fact_schema_preserves_missing_values_as_null():
    fact = canonical_strength_fact(strength_system="SHADBALA", subject_entity="VEDA-GRAHA-JUPITER", component="STHANA_BALA")
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "astrology" / "strength_fact.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(fact, schema)
    assert fact["raw_value"] is None
    assert fact["validation_status"] == "RESEARCH_REQUIRED"


def test_p018_production_and_interpretation_are_inactive():
    bundle = build_phase_bundle()
    assert all(row["production_activation"] == "NOT_EXECUTED" for row in bundle["capability_status"])
    assert all(row["interpretation"] == "RESEARCH_REQUIRED" for row in bundle["capability_status"])
    assert bundle["summary"]["production_strength_interpretation_activated"] == "NO"


def test_p018_governed_artifacts_include_claims_conflicts_and_dependencies():
    bundle = build_phase_bundle()
    assert bundle["strength_claims"]
    assert bundle["strength_conflicts"]
    assert any(row["status"] == "AVAILABLE_SEPARATE_CONCEPT" for row in bundle["dependency_updates"])
