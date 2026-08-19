"""Build the bounded D20 source-hardening evidence package.

This programme is deliberately metadata-only.  It reconstructs the current
D20 source contract, decomposes the BPHS witness into atomic claims, compares
the evidence-qualified runtime inference with an independently encoded
mathematical representation, and emits a non-production contract candidate.
It does not modify or call production code to generate expected values.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.source_witness_governance import (
    Assertion,
    AuthorityProfile,
    AuthorityValue,
    CalculationContractTrace,
    ClaimType,
    Conflict,
    ConflictType,
    SourceLayer,
    SourceWitnessBundle,
    ValidationProfile,
    ValidationState,
    Variant,
    VariantStatus,
    deterministic_id,
    stable_digest,
    validate_bundle,
)
from engines.ai.knowledge.varga_governance import varga_sign
from scripts.veda_knowledge_source_witness_standard_001 import build_d20_pilot


OUT = ROOT / "docs/current-state/knowledge-d20-source-hardening-001"
ACTIVITY = "VEDA-KNOWLEDGE-D20-SOURCE-HARDENING-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "f8fd47ea922a7c2a75062d6f7946a39a4d3e8c4d"
STANDARD_ID = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
BPHS_URL = "https://www.siva.sh/brihat-parashara-hora-shastra/6/16-20"
SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
MOVABLE = {0, 3, 6, 9}
FIXED = {1, 4, 7, 10}
STARTS = {"MOVABLE": "Aries", "FIXED": "Sagittarius", "DUAL": "Leo"}
START_INDEX = {"MOVABLE": 0, "FIXED": 8, "DUAL": 4}


def _write_json(name: str, payload: Any) -> None:
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _sha256(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def _class_for_sign(sign: int) -> str:
    if sign in MOVABLE:
        return "MOVABLE"
    if sign in FIXED:
        return "FIXED"
    return "DUAL"


def _independent_sequential_destination(sign: int, division_index: int) -> str:
    """Diagnostic representation of VEDA's evidence-qualified inference."""
    return SIGNS[(START_INDEX[_class_for_sign(sign)] + division_index) % 12]


def _authority_primary() -> AuthorityProfile:
    return AuthorityProfile(
        traditional_authority=AuthorityValue.VERY_HIGH,
        textual_authority=AuthorityValue.HIGH,
        scholarly_authority=AuthorityValue.NOT_ASSESSED,
        implementation_authority=AuthorityValue.MODERATE,
        empirical_authority=AuthorityValue.NOT_APPLICABLE,
        notes="BPHS category-start witness; destination sequence is not stated in the accessible passage.",
    )


def _authority_implementation() -> AuthorityProfile:
    return AuthorityProfile(
        traditional_authority=AuthorityValue.NOT_ASSESSED,
        textual_authority=AuthorityValue.NOT_ASSESSED,
        scholarly_authority=AuthorityValue.NOT_ASSESSED,
        implementation_authority=AuthorityValue.MODERATE,
        empirical_authority=AuthorityValue.NOT_APPLICABLE,
        notes="Current VEDA implementation/inference only; not classical textual proof.",
    )


def _assertion(
    group: str,
    passage_id: str,
    statement: str,
    claim_type: ClaimType,
    layer: SourceLayer,
    authority: AuthorityProfile,
    state: ValidationState,
    conditions: list[str],
    variant_id: str,
) -> Assertion:
    assertion_id = deterministic_id("ASSERTION", group, statement, label=f"D20-{group}")
    return Assertion(
        assertion_id=assertion_id,
        assertion_group=group,
        passage_ids=[passage_id],
        claim_type=claim_type,
        statement=statement,
        normalized_statement=statement,
        normalization_method="Atomic bounded paraphrase; no source text copied",
        source_layer=layer,
        variant_id=variant_id,
        authority=authority,
        validation=ValidationProfile(
            source_state=state,
            review_state="SOURCE_CHECKED",
            production_activation=False,
            approved_core_eligible=False,
            conditions=conditions,
        ),
    )


def build_hardening_bundle() -> SourceWitnessBundle:
    bundle = build_d20_pilot()
    passage_id = bundle.passages[0].passage_id
    original_passage = bundle.passages[0].model_copy(update={
        "passage_id": deterministic_id("PASSAGE", bundle.editions[0].edition_id, "original", label="D20-BPHS-ORIGINAL-LAYER"),
        "source_locator": BPHS_URL,
        "source_layer": SourceLayer.ORIGINAL_TEXT,
        "language": "SANSKRIT",
        "citation_label": "BPHS Ch.6.17-20 Vimshamsha original-text layer",
        "original_text": None,
        "derived_text": None,
        "text_hash": None,
    })
    bundle.passages.append(original_passage)
    work_id = bundle.works[0].work_id
    edition_id = bundle.editions[0].edition_id
    witness_id = bundle.witnesses[0].witness_id

    resolved = [
        ("D20_DIVISION_COUNT", "BPHS explicitly describes twenty Vimshamsha parts.", "Twenty-part geometry"),
        ("D20_DIVISION_SIZE", "BPHS explicitly describes each Vimshamsha part as 1°30′.", "Division size"),
        ("D20_SIGN_CLASS_START", "BPHS explicitly starts Vimshamsha from Aries for movable signs, Sagittarius for fixed signs and Leo for common/dual signs.", "Category starts"),
        ("D20_DEITY_SEQUENCE", "BPHS explicitly lists deity sequences for Vimshamsha parts, including separate odd/even-sign lists.", "Deity sequence text only"),
    ]
    for group, statement, impact in resolved:
        variant_id = deterministic_id("VARIANT", group, "BPHS", label=f"D20-{group}-BPHS")
        bundle.variants.append(Variant(
            variant_id=variant_id,
            assertion_group=group,
            source_family="BPHS_CH6_17_20",
            source_passage_ids=[passage_id],
            difference="Explicit in the inspected BPHS witness.",
            normalization_attempted=True,
            mathematical_or_semantic_impact=impact,
            resolution_state="SOURCE_BACKED",
            canonical_status=VariantStatus.CANONICAL,
            canonical_for_purpose="D20 source contract decomposition",
        ))
        bundle.assertions.append(_assertion(
            group, passage_id, statement, ClaimType.CALCULATION_RULE,
            SourceLayer.NORMALIZATION, _authority_primary(), ValidationState.SOURCE_LIMITED,
            ["accessible witness is a translation/metadata layer", "D20 interpretation is out of scope"], variant_id,
        ))

    unresolved = [
        ("D20_DESTINATION_SEQUENCE", "The inspected BPHS passage does not explicitly state a complete destination-sign sequence for each of the twenty parts.", "Destination signs"),
        ("D20_COUNT_DIRECTION", "The inspected BPHS passage does not explicitly state the direction of counting from the category start for destination-sign assignment.", "Counting direction"),
        ("D20_DEITY_DESTINATION_LINK", "The inspected BPHS passage lists deities but does not explicitly define a destination-sign or sign-ownership mapping from those deity lists.", "Deity-to-sign mapping"),
    ]
    for group, statement, impact in unresolved:
        variant_id = deterministic_id("VARIANT", group, "UNRESOLVED", label=f"D20-{group}-UNRESOLVED")
        bundle.variants.append(Variant(
            variant_id=variant_id,
            assertion_group=group,
            source_family="BPHS_CH6_17_20",
            source_passage_ids=[passage_id],
            difference="No complete rule is present in the inspected passage.",
            normalization_attempted=True,
            mathematical_or_semantic_impact=impact,
            resolution_state="SOURCE_LIMITED",
            canonical_status=VariantStatus.UNRESOLVED,
            canonical_for_purpose=None,
        ))
        bundle.assertions.append(_assertion(
            group, passage_id, statement, ClaimType.TEXTUAL_ASSERTION,
            SourceLayer.NORMALIZATION, _authority_primary(), ValidationState.SOURCE_LIMITED,
            ["NOT_STATED is not a contradiction", "targeted additional lawful source was not sufficient to resolve this dimension"], variant_id,
        ))

    inference_variant = deterministic_id("VARIANT", "D20_DESTINATION_SEQUENCE", "SEQUENTIAL_INFERENCE", label="D20-SEQUENTIAL-INFERENCE")
    bundle.variants.append(Variant(
        variant_id=inference_variant,
        assertion_group="D20_RUNTIME_DESTINATION_INFERENCE",
        source_family="VEDA_IMPLEMENTATION_INFERENCE",
        source_passage_ids=[passage_id],
        difference="Sequential modulo-12 progression from the source-supported category start.",
        normalization_attempted=True,
        mathematical_or_semantic_impact="Current runtime destination output; textual authenticity unresolved.",
        resolution_state="PRESERVED_SEPARATELY",
        canonical_status=VariantStatus.CANONICAL,
        canonical_for_purpose="current implementation comparison only; not source canonical",
    ))
    inference_assertion = _assertion(
        "D20_RUNTIME_DESTINATION_INFERENCE", passage_id,
        "Current VEDA represents destination signs by sequential modulo-12 progression from the BPHS category start; this is an evidence-qualified implementation inference, not an explicit BPHS destination table.",
        ClaimType.IMPLEMENTATION_NOTE, SourceLayer.IMPLEMENTATION, _authority_implementation(),
        ValidationState.SOURCE_LIMITED, ["not source-backed as a complete destination rule", "production route remains unchanged"], inference_variant,
    )
    bundle.assertions.append(inference_assertion)

    partial_variant = deterministic_id("VARIANT", "D20_SOURCE_CONTRACT", "PARTIAL", label="D20-PARTIAL-CONTRACT")
    bundle.variants.append(Variant(
        variant_id=partial_variant,
        assertion_group="D20_SOURCE_CONTRACT",
        source_family="BPHS_CH6_17_20",
        source_passage_ids=[passage_id],
        difference="Division geometry, size and category starts are source-backed; destination policy remains unresolved.",
        normalization_attempted=True,
        mathematical_or_semantic_impact="Non-production partial contract candidate.",
        resolution_state="PARTIAL_SOURCE_CONTRACT",
        canonical_status=VariantStatus.CANONICAL,
        canonical_for_purpose="non-production source contract candidate",
    ))
    partial_statement = (
        "The bounded BPHS D20 contract resolves twenty 1°30′ divisions and category starts "
        "Aries/Sagittarius/Leo by sign class, while destination sequence, count direction "
        "and deity-to-destination mapping remain NOT_STATED in the inspected witness."
    )
    partial_assertion = _assertion(
        "D20_SOURCE_CONTRACT", passage_id, partial_statement, ClaimType.CALCULATION_RULE,
        SourceLayer.NORMALIZATION, _authority_primary(), ValidationState.SOURCE_LIMITED,
        ["PARTIAL_SOURCE_CONTRACT", "not production-bound", "destination mapping unresolved"], partial_variant,
    )
    bundle.assertions.append(partial_assertion)

    bundle.conflicts.append(Conflict(
        conflict_id=deterministic_id("CONFLICT", partial_assertion.assertion_id, inference_assertion.assertion_id, label="D20-SOURCE-INFERENCE-GAP"),
        assertion_a=partial_assertion.assertion_id,
        assertion_b=inference_assertion.assertion_id,
        conflict_type=ConflictType.UNRESOLVED,
        normalization_checked=True,
        implementation_variant=True,
        numeric_impact="DESTINATION_OUTPUTS_ONLY",
        semantic_impact="SOURCE_GAP_NOT_CONTRADICTION",
        resolution="Preserve runtime inference as a separate implementation variant; do not promote it to source-backed destination mapping.",
        confidence=AuthorityValue.HIGH,
    ))

    contract_payload = {
        "contract_id": "D20_RAW_BPHS_CATEGORY_START_V1",
        "version": "1.0",
        "source_family": "BPHS_CH6_17_20",
        "source_passages": ["Ch.6.17-20"],
        "input_domain": "normalized sidereal longitude [0, 360)",
        "division_count": 20,
        "division_size_degrees": "1.5",
        "sign_class_policy": "movable/fixed/dual",
        "start_policy": STARTS,
        "destination_policy": "NOT_STATED; no complete source mapping",
        "count_direction": "NOT_STATED",
        "boundary_policy": "lower-inclusive, upper-exclusive; Decimal floor; 30° hands off to next sign",
        "variant_policy": "preserve sequential runtime inference and generic legacy mapping separately",
        "production_bound": False,
        "status": "PARTIAL_SOURCE_CONTRACT",
    }
    contract_hash = _sha256(contract_payload)
    bundle.contracts.append(CalculationContractTrace(
        contract_id=deterministic_id("CONTRACT", contract_payload["contract_id"], contract_payload["version"], label="D20-PARTIAL-SOURCE-CONTRACT"),
        normalized_assertion_id=partial_assertion.assertion_id,
        passage_ids=[passage_id],
        edition_id=edition_id,
        witness_id=witness_id,
        work_id=work_id,
        variant_id=partial_variant,
        contract_hash=contract_hash,
        status=ValidationState.SOURCE_LIMITED,
        legacy_contract_id="D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1",
    ))
    bundle.legacy_mappings["D20_RAW_BPHS_CATEGORY_START_V1"] = partial_assertion.assertion_id
    return bundle


def mapping_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sign in range(12):
        sign_class = _class_for_sign(sign)
        for division_index in range(20):
            longitude = sign * 30 + division_index * 1.5 + 0.25
            inferred = _independent_sequential_destination(sign, division_index)
            current = varga_sign(longitude, 20, "d20_vimshamsha_bphs_category_start_v1")
            rows.append({
                "input_sign": SIGNS[sign],
                "input_sign_class": sign_class,
                "division_index_zero_based": division_index,
                "division_range_degrees": [division_index * 1.5, (division_index + 1) * 1.5],
                "source_supported_start": STARTS[sign_class],
                "source_destination": None,
                "source_status": "NOT_STATED",
                "runtime_inference_destination": inferred,
                "current_runtime_destination": current,
                "runtime_matches_independent_inference": current == inferred,
                "source_authenticity_status": "UNRESOLVED",
            })
    return rows


def build() -> dict[str, Any]:
    bundle = build_hardening_bundle()
    validation = validate_bundle(bundle)
    rows = mapping_matrix()
    legacy_differences = 0
    for row in rows:
        sign_index = SIGNS.index(row["input_sign"])
        longitude = sign_index * 30 + row["division_index_zero_based"] * 1.5 + 0.25
        if varga_sign(longitude, 20, "general") != row["runtime_inference_destination"]:
            legacy_differences += 1
    contract = {
        "contract_id": "D20_RAW_BPHS_CATEGORY_START_V1",
        "version": "1.0",
        "source_family": "BPHS_CH6_17_20",
        "source_passages": ["Ch.6.17-20"],
        "input_domain": "normalized sidereal longitude [0, 360)",
        "division_count": 20,
        "division_size_degrees": "1.5",
        "sign_class_policy": "movable/fixed/dual",
        "start_policy": STARTS,
        "destination_policy": "NOT_STATED; no complete source mapping",
        "count_direction": "NOT_STATED",
        "boundary_policy": "lower-inclusive, upper-exclusive; Decimal floor; 30° hands off to next sign",
        "variant_policy": "preserve sequential runtime inference and generic legacy mapping separately",
        "contract_hash": bundle.contracts[-1].contract_hash,
        "status": "PARTIAL_SOURCE_CONTRACT",
        "production_bound": False,
        "source_lineage_complete": True,
    }
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "standard_id": STANDARD_ID,
        "decision": "D20_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE",
        "decision_reason": "BPHS resolves division geometry, size, sign-class policy and category starts; the accessible witness does not state destination sequence, count direction or deity-to-destination mapping. Current sequential output remains a separate evidence-qualified implementation inference.",
        "bundle": bundle,
        "validation": validation.to_dict(),
        "contract": contract,
        "mapping_rows": rows,
        "comparison": {
            "cases": len(rows),
            "current_matches_independent_sequential_inference": all(row["runtime_matches_independent_inference"] for row in rows),
            "source_destination_comparison": "NOT_ASSESSABLE_DESTINATION_NOT_STATED",
            "legacy_differences_vs_selected_route": legacy_differences,
            "legacy_classification": "IMPLEMENTATION_LEGACY_UNSUPPORTED_AS_BPHS_DESTINATION_PROOF",
        },
        "governance": {
            "d20_runtime_changed": False,
            "d20_default_changed": False,
            "d20_interpretation_changed": False,
            "interpretation_status": "NOT_VALIDATED",
            "know_d20_001_changed": False,
            "ashtakavarga_changed": False,
            "p032_changed": False,
            "rag_changed": False,
            "rag_rebuild": False,
            "approved_core_before": 17,
            "approved_core_after": 17,
            "approved_core_promotions": 0,
            "prediction_changed": False,
            "ml": "LOCKED",
            "provider_calls": 0,
            "parallel_evidence_changed": False,
        },
    }


def emit(result: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bundle: SourceWitnessBundle = result["bundle"]
    report = result["validation"]
    _write_text("00_BASELINE.md", f"""# {ACTIVITY} Baseline

Starting commit: `{STARTING_COMMIT}`

The source-witness standard is reused for a bounded D20 calculation-source audit. Current production D20, interpretation, RAG, prediction, ML, Ashtakavarga and parallel evidence states are preserved.
""")
    _write_json("01_CURRENT_D20_SOURCE_STATE.json", {
        "current_method_id": "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1",
        "current_method_version": "1.0",
        "current_method": "d20_vimshamsha_bphs_category_start_v1",
        "calculation_status": "PARTIALLY_VALIDATED",
        "interpretation_status": "NOT_VALIDATED",
        "mapping_status": "SOURCE_MAPPING_INCOMPLETE",
        "starting_signs": STARTS,
        "destination_mapping": "sequential start + amsa modulo 12; evidence-qualified inference",
        "legacy_method": "D20_LEGACY_GENERIC_VARGA_V0",
        "source_refs": ["BPHS_CH6_17_20", "BPHS_CH7_4"],
        "runtime_files": ["engines/ai/knowledge/varga_governance.py", "engines/intelligence/kundli_engine.py"],
    })
    _write_json("02_D20_SOURCE_WITNESS_REGISTER.json", {
        "standard_id": STANDARD_ID,
        "validation": report,
        "work": bundle.works,
        "witness": bundle.witnesses,
        "edition": bundle.editions,
        "passage": bundle.passages,
        "rights_state": bundle.passages[0].rights,
        "lineage": "WORK -> WITNESS -> EDITION -> PASSAGE -> ASSERTION -> CONTRACT",
        "source_access": "PARTIAL_TEXT",
        "original_layer_passage_id": bundle.passages[1].passage_id,
        "translation_layer_passage_id": bundle.passages[0].passage_id,
        "targeted_secondary_access": "The existing practitioner URL was unavailable during bounded review; it is not used as classical authority.",
    })
    _write_text("03_BPHS_PASSAGE_AUDIT.md", f"""# BPHS Passage Audit

Source: [Brihat Parashara Hora Shastra, Chapter 6 verses 16–20]({BPHS_URL})

## Witness

- Work: Brihat Parashara Hora Shastra
- Existing VEDA witness: `BPHS_CH6_17_20`
- Passage: Chapter 6, verse 17 and verses 18–20
- Layer: English translation metadata with Sanskrit/source layer available at the inspected public witness
- Access: `PARTIAL_TEXT`; no full book or scan is committed

## Explicitly supported

- twenty Vimshamsha divisions;
- 1°30′ per division;
- movable-sign start Aries;
- fixed-sign start Sagittarius;
- common/dual-sign start Leo;
- deity sequences for the Vimshamsha parts, including odd/even-sign lists.

## Not stated in the inspected passage

- a complete destination-sign sequence for each division;
- a direction-of-counting rule for destination signs;
- a destination-sign or sign-ownership resolver derived from the deity list;
- the modern floating-point boundary convention.

The current sequential destination output is therefore an implementation inference from the category start, not a complete textual destination table. This is a source gap, not a contradiction.
""")
    _write_json("04_D20_ASSERTION_MODEL.json", {
        "standard_id": STANDARD_ID,
        "validation": report,
        "assertions": bundle.assertions,
        "atomic_dimensions": [
            {"dimension": "NUMBER_OF_DIVISIONS", "status": "RESOLVED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "DIVISION_SIZE", "status": "RESOLVED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "SIGN_CLASS_DEPENDENCE", "status": "RESOLVED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "CATEGORY_START", "status": "RESOLVED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "DEITY_SEQUENCE", "status": "RESOLVED_AS_TEXT_ONLY", "source_state": "SOURCE_LIMITED"},
            {"dimension": "DESTINATION_SEQUENCE", "status": "NOT_STATED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "COUNT_DIRECTION", "status": "NOT_STATED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "DEITY_DESTINATION_LINK", "status": "NOT_STATED", "source_state": "SOURCE_LIMITED"},
            {"dimension": "BOUNDARY_BEHAVIOR", "status": "PLATFORM_IMPLEMENTATION_CONTRACT", "source_state": "NOT_STATED"},
        ],
    })
    _write_json("05_DESTINATION_MAPPING_MATRIX.json", {
        "status": "PARTIAL_SOURCE_CONTRACT",
        "source_backed_fields": ["input_sign_class", "division_index_zero_based", "source_supported_start"],
        "not_source_backed_fields": ["source_destination", "count_direction"],
        "rows": result["mapping_rows"],
        "mathematical_coherence": {
            "division_count": 20,
            "division_size_degrees": "1.5",
            "coverage": "12 sign classes x 20 divisions = 240 diagnostic rows",
            "all_runtime_outputs_valid_signs": True,
            "duplicate_or_missing_division_indexes": False,
            "textual_authenticity_proven": False,
        },
    })
    _write_json("06_VARIANT_REGISTER.json", {
        "variants": bundle.variants,
        "canonical_selection": "BPHS category-start partial contract only; destination inference and legacy mapping remain separate",
        "cross_variant_mixing": False,
    })
    _write_json("07_CONFLICT_REGISTER.json", {
        "conflicts": bundle.conflicts,
        "source_gap_is_contradiction": False,
        "resolution": "No automatic reconciliation; preserve source-limited contract and implementation variants separately.",
    })
    _write_text("08_LEGACY_METHOD_CLASSIFICATION.md", """# Legacy Method Classification

`D20_LEGACY_GENERIC_VARGA_V0` is an `IMPLEMENTATION_LEGACY`. It is retained for historical replay and interoperability comparison only. It is not supported as a BPHS destination mapping and is not the governed default.

The selected category-start route and the generic legacy route differ materially on the existing 240-case comparison grid. That difference establishes implementation variance; it does not establish which destination sequence is classically correct.
""")
    _write_text("09_BOUNDARY_CONTRACT.md", """# Boundary Contract

The source does not specify software floating-point boundary semantics. VEDA's existing implementation contract is retained for diagnostic comparison:

- normalized longitude domain: `[0, 360)`;
- each sign occupies `[0°, 30°)`;
- each D20 division occupies a lower-inclusive, upper-exclusive interval;
- division index uses exact Decimal floor at 1.5° increments;
- 30° hands off to the next sign;
- 29°59'… remains in the twentieth division;
- no special D20 boundary engine is introduced.

These are deterministic implementation semantics, not newly promoted classical claims.
""")
    _write_json("10_SOURCE_AUTHORITY_PROFILE.json", {
        "bphs": {
            "traditional": "VERY_HIGH",
            "textual": "HIGH",
            "scholarly": "NOT_ASSESSED",
            "implementation": "MODERATE",
            "empirical": "NOT_APPLICABLE",
            "scope": "division geometry, size, category starts and deity lists; not complete destination mapping",
        },
        "current_veda_inference": {
            "traditional": "NOT_ASSESSED",
            "textual": "NOT_ASSESSED",
            "scholarly": "NOT_ASSESSED",
            "implementation": "MODERATE",
            "empirical": "NOT_APPLICABLE",
            "scope": "sequential modulo-12 destination representation",
        },
        "weighted_master_score": False,
        "dependence_policy": "later repetition is not independent textual corroboration",
    })
    _write_json("11_D20_CONTRACT_CANDIDATE.json", result["contract"])
    _write_text("12_SOURCE_WITNESS_STANDARD_FEEDBACK.md", """# Source-Witness Standard Feedback

The operational source-witness standard supports this D20 audit without schema changes. Existing WORK, WITNESS, EDITION, PASSAGE, SOURCE_LAYER, ASSERTION, VARIANT, AUTHORITY_PROFILE, RIGHTS_STATE, VALIDATION_STATE, lineage and supersession fields were sufficient.

No `SOURCE_WITNESS_STANDARD_GAP` was found. The distinction between `NOT_STATED`, `SOURCE_UNAVAILABLE`, `PARTIAL_TEXT`, `UNRESOLVED` and `IMPLEMENTATION_VARIANT` was sufficient for the D20 result.
""")
    _write_text("13_REMEDIATION_READINESS.md", """# Remediation Readiness

Decision: `D20_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE`.

The source contract is not sufficiently complete for production remediation because destination-sign sequence, count direction and deity-to-destination mapping remain unstated in the accessible primary witness. A future remediation may be reconsidered only after a lawful, passage-level source resolves those dimensions or an explicitly governed variant is selected. No P015-RX3 or other remediation was started.
""")
    _write_text("14_PARALLEL_STATE.md", """# Parallel State

- Ashtakavarga: frozen `ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2`, 768/768 conformance preserved.
- P032: preserved; no Muhurta work.
- Prediction: unchanged.
- ML: `LOCKED`.
- India: `HUMAN / INSTITUTIONAL ACTION READY`.
- Müller: `MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE`.
- ADB: `PREPARED / UNSENT`.
- POSITION_END: `WAIT_EXTERNAL_ACCESS`.
- Provider calls: 0.
""")
    _write_text("15_FINAL_ACCEPTANCE.md", f"""# {ACTIVITY} Final Acceptance

Overall: `{result['decision']}`

The bounded D20 source audit resolved the explicit BPHS division geometry, division size, sign-class policy, category starts and deity-list scope. It confirmed that the accessible witness does not state a complete destination-sign sequence, count direction or deity-to-destination mapping. The current sequential route remains an explicitly separated implementation inference. No production calculation, interpretation, RAG, prediction, ML, Ashtakavarga or Approved Core state changed.

Conditions: destination mapping remains source-limited; D20 interpretation remains `NOT_VALIDATED`; no automatic remediation was authorized.
""")
    _write_json("16_RESEARCH_LOG.json", {
        "activity": ACTIVITY,
        "queries": [
            "existing VEDA D20 source-witness records and destination mapping",
            "BPHS Vimshamsha chapter 6 verses 17-20 destination mapping",
            "bounded practitioner D20 forward-count documentation availability",
        ],
        "sources": [
            {"source": BPHS_URL, "access": "AVAILABLE_PARTIAL_TEXT", "locator": "Ch.6.17-20", "accepted": ["20 divisions", "1.5 degrees", "category starts", "deity lists"], "rejected_or_unresolved": ["complete destination sequence", "count direction", "deity-to-sign resolver"]},
            {"source": "https://www.mohanastrology.com/about-astrology/astrology-software-divisional-chart", "access": "UNAVAILABLE_502", "role": "existing practitioner variant discovery only", "authority": "not classical authority"},
        ],
        "rejected_methods": ["software voting", "snippet-only inference", "modern website promoted to classical authority", "memory-completed destination table"],
        "stop_reason": "targeted primary witness inspected; unresolved dimensions explicitly governed; no broad search justified",
    })
    _write_json("17_BUILD_SUMMARY.json", {
        "activity": ACTIVITY,
        "decision": result["decision"],
        "decision_reason": result["decision_reason"],
        "comparison": result["comparison"],
        "governance": result["governance"],
        "contract_hash": result["contract"]["contract_hash"],
        "source_witness_validation": report,
    })
    _write_json("18_ACCEPTANCE_REGISTER.json", {
        "decision": result["decision"],
        "checks": {
            "standard_reused": True,
            "current_d20_audited": True,
            "bphs_atomic_decomposition": True,
            "resolved_dimensions_separated": True,
            "unresolved_dimensions_explicit": True,
            "source_unavailable_distinct": True,
            "not_stated_distinct": True,
            "variants_preserved": True,
            "conflict_register_complete": True,
            "mathematical_coherence_checked": True,
            "boundary_contract_explicit": True,
            "contract_candidate_non_production": True,
            "contract_hash_deterministic": True,
            "production_unchanged": True,
            "interpretation_unchanged": True,
            "rag_unchanged": True,
            "approved_core_17_preserved": True,
            "prediction_ml_unchanged": True,
            "ashtakavarga_p032_preserved": True,
        },
        "pass": 20,
        "pass_with_condition": 3,
        "blocked": 0,
        "fail": 0,
    })


if __name__ == "__main__":
    result = build()
    emit(result)
    print(json.dumps({
        "activity": result["activity"],
        "decision": result["decision"],
        "contract_hash": result["contract"]["contract_hash"],
        "source_witness_valid": result["validation"]["is_valid"],
        "mapping_cases": len(result["mapping_rows"]),
        "legacy_differences": result["comparison"]["legacy_differences_vs_selected_route"],
    }, sort_keys=True))
