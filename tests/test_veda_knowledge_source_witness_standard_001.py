"""Focused tests for the reusable source-witness governance standard."""

import hashlib

import pytest
from pydantic import ValidationError

from engines.ai.knowledge.astrology_governance import validate_registry_directory
from engines.ai.knowledge.source_witness_governance import (
    Assertion,
    AuthorityProfile,
    AuthorityValue,
    ClaimType,
    Conflict,
    ConflictType,
    Edition,
    Passage,
    RightsProfile,
    RightsState,
    SourceAccessState,
    SourceLayer,
    SourceWitnessBundle,
    ValidationProfile,
    ValidationState,
    Variant,
    VariantStatus,
    deterministic_id,
    legacy_source_mapping,
    validate_bundle,
)
from scripts.veda_knowledge_source_witness_standard_001 import OUT, build, build_ashtakavarga_pilot, build_d20_pilot, emit


def test_ids_are_deterministic_and_input_sensitive():
    first = deterministic_id("WORK", "Brihat Parashara Hora Shastra", "Parashara", label="BPHS")
    second = deterministic_id("WORK", "Brihat Parashara Hora Shastra", "Parashara", label="BPHS")
    other = deterministic_id("WORK", "Phaladeepika", "Mantreswara", label="PHALADEEPIKA")
    assert first == second
    assert first != other
    assert first.startswith("VEDA-SWW-WORK-BPHS-")
    assert legacy_source_mapping("BPHS", "Brihat Parashara Hora Shastra")["mapping_state"] == "LEGACY_COMPATIBLE"


def test_pilot_bundles_validate_and_preserve_lineage():
    asht = build_ashtakavarga_pilot()
    d20 = build_d20_pilot()
    assert validate_bundle(asht).is_valid
    assert validate_bundle(d20).is_valid
    assert len(asht.contracts) == 2
    assert any(item.canonical_status == VariantStatus.SUPERSEDED_INVALID_HYBRID for item in asht.variants)
    assert any(item.canonical_status == VariantStatus.LEGACY_VARIANT for item in d20.variants)
    assert all(contract.normalized_assertion_id for contract in asht.contracts + d20.contracts)


def test_translation_and_commentary_layers_are_guarded():
    edition_id = deterministic_id("EDITION", "work", label="TEST-EDITION")
    passage = Passage(
        passage_id=deterministic_id("PASSAGE", edition_id, "translation", label="TEST-TRANSLATION"),
        edition_id=edition_id,
        source_locator="fixture",
        source_layer=SourceLayer.TRANSLATION,
        citation_label="fixture translation",
        original_text="must not be present in translation layer",
    )
    bundle = SourceWitnessBundle(editions=[Edition(edition_id=edition_id, work_id="missing", rights=RightsProfile(rights_state=RightsState.UNKNOWN))], passages=[passage])
    report = validate_bundle(bundle)
    assert any("translation cannot impersonate original" in error for error in report.errors)

    commentary = passage.model_copy(update={"passage_id": deterministic_id("PASSAGE", edition_id, "commentary", label="TEST-COMMENTARY"), "source_layer": SourceLayer.COMMENTARY, "original_text": None})
    report = validate_bundle(SourceWitnessBundle(editions=[bundle.editions[0]], passages=[commentary]))
    assert any("commentary requires base_passage_id" in error for error in report.errors)


def test_linked_entities_require_parent_work():
    bundle = SourceWitnessBundle(
        witnesses=[
            {
                "witness_id": "VEDA-SWW-WITNESS-ORPHAN",
                "work_id": "VEDA-SWW-WORK-MISSING",
                "witness_type": "digital",
                "locator": "local://orphan",
            }
        ]
    )
    report = validate_bundle(bundle)
    assert "work required for linked source-witness entities" in report.errors


def test_not_stated_is_not_contradiction_and_unavailable_is_distinct():
    conflict = Conflict(
        conflict_id=deterministic_id("CONFLICT", "a", "b", label="TEST-CONFLICT"),
        assertion_a="a",
        assertion_b="b",
        conflict_type=ConflictType.NOT_STATED,
        resolution="No assertion was made; no contradiction inferred.",
    )
    assert conflict.conflict_type == ConflictType.NOT_STATED
    assert SourceAccessState.SOURCE_UNAVAILABLE.value != ConflictType.NOT_STATED.value


def test_authority_has_independent_dimensions_and_no_master_score():
    profile = AuthorityProfile(
        traditional_authority=AuthorityValue.HIGH,
        textual_authority=AuthorityValue.MODERATE,
        scholarly_authority=AuthorityValue.NOT_ASSESSED,
        implementation_authority=AuthorityValue.LOW,
        empirical_authority=AuthorityValue.UNKNOWN,
    )
    assert profile.traditional_authority != profile.implementation_authority
    with pytest.raises(ValidationError):
        AuthorityProfile.model_validate({"weighted_master_score": 72})


def test_legacy_registry_remains_valid_and_governance_boundaries_hold():
    report = validate_registry_directory()
    assert report.is_valid
    result = build()
    assert result["decision"] == "SOURCE_WITNESS_STANDARD_OPERATIONAL_WITH_CONDITION"
    assert result["governance"]["approved_core_before"] == 17
    assert result["governance"]["approved_core_after"] == 17
    assert result["governance"]["rag_changed"] is False
    assert result["governance"]["production_changed"] is False
    assert result["governance"]["calculation_changed"] is False
    assert result["governance"]["provider_calls"] == 0


def test_exports_are_deterministic():
    emit(build())
    names = sorted(path.name for path in OUT.iterdir() if path.is_file())
    before = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    emit(build())
    after = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    assert before == after
    assert "18_STANDARD_SCHEMA.json" in names
    assert "11_ASHTAKAVARGA_PILOT.json" in names
    assert "12_SECOND_PILOT.json" in names
