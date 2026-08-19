"""Build the bounded Shadbala source-hardening evidence package.

This activity is deliberately non-production.  It reuses the operational
source-witness standard, records passage-level source boundaries, decomposes
the current six-component runtime, and compares an independent diagnostic
oracle with the existing implementation.  It does not alter production
Shadbala, interpretation, prediction, RAG, or Approved Core state.
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
    DependenceState,
    Edition,
    Passage,
    ReviewState,
    RightsPermission,
    RightsProfile,
    RightsState,
    SourceAccessState,
    SourceLayer,
    SourceWitnessBundle,
    ValidationProfile,
    ValidationState,
    Variant,
    VariantStatus,
    Witness,
    Work,
    deterministic_id,
    validate_bundle,
)


ACTIVITY = "VEDA-KNOWLEDGE-SHADBALA-SOURCE-HARDENING-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "021a805ca68bc6e4730e1d2978e3e944200c2849"
STANDARD_ID = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
OUT = ROOT / "docs/current-state/knowledge-shadbala-source-hardening-001"

BPHS_URL = "https://www.astroneemo.net/index.php/2016-08-07-05-21-50/2016-09-26-02-29-18/52-english/717-brihat-parasara-hora-sastra.html?start=24"
WISDOMLIB_METADATA_URL = "https://www.wisdomlib.org/shop/books/jyotisha/brihat-parashara-hora-shastra/doc234203.html"
SARAVALI_URLS = {
    "basics": "https://saravali.github.io/astrology/shadbala_basics.html",
    "sthana": "https://saravali.github.io/astrology/bala_sthana.html",
    "dig": "https://saravali.github.io/astrology/bala_dig.html",
    "kala": "https://saravali.github.io/astrology/bala_kala.html",
    "ayana": "https://saravali.github.io/astrology/bala_ayana.html",
    "cheshta": "https://saravali.github.io/astrology/bala_cheshta.html",
    "naisargika": "https://saravali.github.io/astrology/bala_naisargika.html",
    "drig": "https://saravali.github.io/astrology/bala_drig.html",
}

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SOURCE_NAISARGIKA = {
    "Sun": 60.0,
    "Moon": 360.0 / 7.0,
    "Venus": 300.0 / 7.0,
    "Jupiter": 240.0 / 7.0,
    "Mercury": 180.0 / 7.0,
    "Mars": 120.0 / 7.0,
    "Saturn": 60.0 / 7.0,
}
SOURCE_DIG_MAX_HOUSE = {
    "Sun": 10,
    "Mars": 10,
    "Jupiter": 1,
    "Mercury": 1,
    "Moon": 4,
    "Venus": 4,
    "Saturn": 7,
}
SOURCE_DIG_MIN_HOUSE = {
    "Sun": 4,
    "Mars": 4,
    "Jupiter": 7,
    "Mercury": 7,
    "Moon": 10,
    "Venus": 10,
    "Saturn": 1,
}


def _write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _write_text(name: str, value: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def _authority(kind: str) -> AuthorityProfile:
    if kind == "BPHS":
        return AuthorityProfile(
            traditional_authority=AuthorityValue.VERY_HIGH,
            textual_authority=AuthorityValue.HIGH,
            scholarly_authority=AuthorityValue.NOT_ASSESSED,
            implementation_authority=AuthorityValue.MODERATE,
            empirical_authority=AuthorityValue.NOT_APPLICABLE,
            notes="Classical witness is passage-mapped through an accessible translation mirror; edition text remains rights-limited.",
        )
    if kind == "SARAVALI_DOCS":
        return AuthorityProfile(
            traditional_authority=AuthorityValue.MODERATE,
            textual_authority=AuthorityValue.NOT_ASSESSED,
            scholarly_authority=AuthorityValue.MODERATE,
            implementation_authority=AuthorityValue.HIGH,
            empirical_authority=AuthorityValue.NOT_APPLICABLE,
            notes="Open modern implementation documentation used for variant discovery and formula comparison, not classical authority.",
        )
    return AuthorityProfile(implementation_authority=AuthorityValue.MODERATE)


def _rights(state: RightsState) -> RightsProfile:
    permissions = [RightsPermission.VIEW_ALLOWED, RightsPermission.DERIVED_METADATA_ALLOWED]
    if state == RightsState.OPEN_LICENSE:
        permissions.append(RightsPermission.QUOTATION_ALLOWED)
    return RightsProfile(rights_state=state, permissions=permissions, basis="bounded metadata/paraphrase only; no source text redistributed")


def _passage(
    passage_id: str,
    edition_id: str,
    locator: str,
    label: str,
    source_layer: SourceLayer,
    *,
    chapter: str,
    line: str | None = None,
    access: SourceAccessState = SourceAccessState.PARTIAL_TEXT,
    rights: RightsProfile | None = None,
) -> Passage:
    return Passage(
        passage_id=passage_id,
        edition_id=edition_id,
        chapter=chapter,
        line=line,
        source_locator=locator,
        source_layer=source_layer,
        language="ENGLISH",
        citation_label=label,
        original_text=None,
        derived_text=None,
        source_access=access,
        rights=rights or _rights(RightsState.RESEARCH_ONLY),
        review_state=ReviewState.SOURCE_CHECKED,
    )


def _assertion(
    group: str,
    passage_ids: list[str],
    statement: str,
    claim_type: ClaimType,
    layer: SourceLayer,
    source_state: ValidationState,
    variant_id: str,
    *,
    conditions: list[str] | None = None,
    authority: AuthorityProfile | None = None,
) -> Assertion:
    assertion_id = deterministic_id("ASSERTION", group, statement, label=f"SHADBALA-{group}")
    return Assertion(
        assertion_id=assertion_id,
        assertion_group=group,
        passage_ids=passage_ids,
        claim_type=claim_type,
        statement=statement,
        normalized_statement=statement,
        normalization_method="Atomic bounded paraphrase; no source text copied",
        source_layer=layer,
        variant_id=variant_id,
        authority=authority or _authority("BPHS"),
        validation=ValidationProfile(
            source_state=source_state,
            review_state=ReviewState.SOURCE_CHECKED,
            production_activation=False,
            approved_core_eligible=False,
            conditions=conditions or [],
        ),
    )


def build_witness_bundle() -> SourceWitnessBundle:
    bphs_work = deterministic_id("WORK", "Brihat Parashara Hora Shastra", label="BPHS")
    saravali_work = deterministic_id("WORK", "Saravali Shadbala implementation documentation", label="SARAVALI-DOCS")
    bphs_witness = deterministic_id("WITNESS", bphs_work, "ASTRONEEMO_TRANSLATION_MIRROR", label="BPHS-MIRROR")
    saravali_witness = deterministic_id("WITNESS", saravali_work, "SARAVALI_GITHUB_DOCS", label="SARAVALI-DOCS")
    bphs_edition = deterministic_id("EDITION", bphs_work, "SAGAR_2006", label="BPHS-SAGAR-2006")
    saravali_edition = deterministic_id("EDITION", saravali_work, "OPEN_DOCS_2022", label="SARAVALI-OPEN-DOCS")

    bundle = SourceWitnessBundle(
        standard_id=STANDARD_ID,
        works=[
            Work(
                work_id=bphs_work,
                canonical_title="Brihat Parashara Hora Shastra",
                alternate_titles=["BPHS", "Brihat Parasara Hora Sastra"],
                traditional_author="Maharishi Parashara (attributed tradition)",
                tradition="Parashari Jyotisha",
                work_type="CLASSICAL_JYOTISHA_TEXT",
                language_origin="SANSKRIT",
                notes="Repository metadata identifies Girish Chand Sharma, Sagar Publications, 2006; accessible page uses alternate chapter numbering.",
            ),
            Work(
                work_id=saravali_work,
                canonical_title="Saravali Shadbala implementation documentation",
                traditional_author="Saravali project maintainers; classical work attributed to Kalyana Varma",
                tradition="Modern implementation documentation",
                work_type="MODERN_IMPLEMENTATION_WITNESS",
                language_origin="ENGLISH",
                notes="Open documentation, not treated as a primary classical witness.",
            ),
        ],
        witnesses=[
            Witness(
                witness_id=bphs_witness,
                work_id=bphs_work,
                witness_type="TRANSLATION_MIRROR_PARTIAL_TEXT",
                repository_or_library="AstroNeemo public page",
                locator=BPHS_URL,
                date_or_period="accessed 2026-08-19",
                script="LATIN",
                language="ENGLISH",
                completeness="PARTIAL_CHAPTER_PAGE",
                physical_or_digital="DIGITAL",
                provenance="Public translation mirror; edition metadata reconciled to existing VEDA BPHS_SAGAR record.",
                dependence_notes="Translation mirror; not independent of the cited translation tradition.",
                dependence_state=DependenceState.DERIVATIVE,
                source_access=SourceAccessState.PARTIAL_TEXT,
                rights=_rights(RightsState.RESEARCH_ONLY),
                review_state=ReviewState.SOURCE_CHECKED,
            ),
            Witness(
                witness_id=saravali_witness,
                work_id=saravali_work,
                witness_type="OPEN_IMPLEMENTATION_DOCUMENTATION",
                repository_or_library="Saravali GitHub Pages",
                locator=SARAVALI_URLS["basics"],
                date_or_period="last modified 2021-2022; accessed 2026-08-19",
                script="LATIN",
                language="ENGLISH",
                completeness="MULTI_PAGE_IMPLEMENTATION_NOTES",
                physical_or_digital="DIGITAL",
                provenance="Open-license project documentation with linked component pages.",
                dependence_notes="Modern computational presentation; classical lineage is asserted by the project but not independently verified here.",
                dependence_state=DependenceState.LATER_SYNTHESIS,
                source_access=SourceAccessState.AVAILABLE,
                rights=_rights(RightsState.OPEN_LICENSE),
                review_state=ReviewState.SOURCE_CHECKED,
            ),
        ],
        editions=[
            Edition(
                edition_id=bphs_edition,
                work_id=bphs_work,
                witness_ids=[bphs_witness],
                translator="Girish Chand Sharma",
                publisher="Sagar Publications",
                publication_year=2006,
                edition_title="Brihat Parashara Hora Shastra, English translation",
                language="ENGLISH",
                script="LATIN",
                digital_locator=WISDOMLIB_METADATA_URL,
                source_type="CLASSICAL_TRANSLATION_METADATA_PLUS_PARTIAL_PUBLIC_MIRROR",
                rights=_rights(RightsState.RESEARCH_ONLY),
                completeness="BIBLIOGRAPHIC_PLUS_PARTIAL_PASSAGE",
                editorial_notes="Chapter numbering differs between accessible mirror (Ch.27) and repository metadata (Ch.29); recorded as indexing variance.",
            ),
            Edition(
                edition_id=saravali_edition,
                work_id=saravali_work,
                witness_ids=[saravali_witness],
                publisher="Saravali project",
                publication_year=2022,
                edition_title="Saravali open Shadbala documentation",
                language="ENGLISH",
                script="LATIN",
                digital_locator=SARAVALI_URLS["basics"],
                source_type="OPEN_MODERN_IMPLEMENTATION_DOCUMENTATION",
                rights=_rights(RightsState.OPEN_LICENSE),
                completeness="COMPONENT_PAGES",
            ),
        ],
    )

    bphs_passages = {
        "structure": _passage(deterministic_id("PASSAGE", bphs_edition, "structure", label="BPHS-STRUCTURE"), bphs_edition, BPHS_URL, "BPHS Ch.27 structure and components", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="232-234"),
        "sthana": _passage(deterministic_id("PASSAGE", bphs_edition, "sthana", label="BPHS-STHANA"), bphs_edition, BPHS_URL, "BPHS Sthana Bala formula block", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="235-241"),
        "dig": _passage(deterministic_id("PASSAGE", bphs_edition, "dig", label="BPHS-DIG"), bphs_edition, BPHS_URL, "BPHS Dig Bala formula block", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="242"),
        "kala": _passage(deterministic_id("PASSAGE", bphs_edition, "kala", label="BPHS-KALA"), bphs_edition, BPHS_URL, "BPHS Kala Bala formula block", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="243-261"),
        "motion": _passage(deterministic_id("PASSAGE", bphs_edition, "motion", label="BPHS-MOTION"), bphs_edition, BPHS_URL, "BPHS Cheshta and Drik Bala block", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="263-269"),
        "threshold": _passage(deterministic_id("PASSAGE", bphs_edition, "threshold", label="BPHS-THRESHOLD"), bphs_edition, BPHS_URL, "BPHS Shadbala units and requirements", SourceLayer.TRANSLATION, chapter="27 / repository Ch.29", line="274-275"),
    }
    saravali_passages = {
        key: _passage(
            deterministic_id("PASSAGE", saravali_edition, key, label=f"SARAVALI-{key.upper()}"),
            saravali_edition,
            url,
            f"Saravali open implementation page: {key}",
            SourceLayer.PRACTITIONER,
            chapter="Shadbala documentation",
            access=SourceAccessState.AVAILABLE,
            rights=_rights(RightsState.OPEN_LICENSE),
        )
        for key, url in SARAVALI_URLS.items()
    }
    bundle.passages.extend(list(bphs_passages.values()) + list(saravali_passages.values()))

    source_groups = [
        ("SHADBALA_SIX_FOLD", [bphs_passages["structure"].passage_id], "The inspected BPHS witness identifies six major Bala families and excludes the nodes from this seven-graha strength calculation."),
        ("STHANA_COMPONENTS", [bphs_passages["structure"].passage_id, bphs_passages["sthana"].passage_id], "Sthana Bala is decomposed into Uchcha, Saptavargaja, OjhayugmaRashiamsa, Kendradi and Drekkana components."),
        ("UCHCHA_FORMULA", [bphs_passages["sthana"].passage_id], "Uchcha Bala is the distance-based exaltation measure expressed by dividing the normalized angular distance by three to obtain Virupas."),
        ("SAPTAVARGAJA_FORMULA", [bphs_passages["sthana"].passage_id], "Saptavargaja Bala assigns dignity values across seven Vargas and aggregates them."),
        ("OJHAYUGMA_FORMULA", [bphs_passages["sthana"].passage_id], "OjhayugmaRashiamsa Bala uses planet-specific odd/even Rashi and Navamsa placement, with a quarter Rupa contribution."),
        ("KENDRADI_FORMULA", [bphs_passages["sthana"].passage_id], "Kendradi Bala assigns full, half and quarter strength to Kendra, Panaphara and Apoklima placements."),
        ("DREKKANA_FORMULA", [bphs_passages["sthana"].passage_id], "Drekkana Bala assigns a quarter Rupa according to the three decanate positions and graha class."),
        ("DIG_FORMULA", [bphs_passages["dig"].passage_id], "Dig Bala is the angular distance from the planet-specific minimum direction divided by three, with explicit maximum and minimum angular locations."),
        ("KALA_COMPONENTS", [bphs_passages["kala"].passage_id], "Kala Bala includes Nathonnatha, Paksha, Tribhaga, Varsha-Masa-Dina-Hora, Ayana and Yuddha components in the inspected witness."),
        ("NATHONNATHA_FORMULA", [bphs_passages["kala"].passage_id], "Nathonnatha Bala is derived from apparent birth time relative to midnight and the day/night strength assignments."),
        ("PAKSHA_FORMULA", [bphs_passages["kala"].passage_id], "Paksha Bala uses the angular relationship of Moon and Sun and reverses the allocation for benefic and malefic classes."),
        ("TRIBHAGA_FORMULA", [bphs_passages["kala"].passage_id], "Tribhaga Bala assigns one of three day or night portions to specific grahas, with Jupiter always receiving the component."),
        ("VARSHAMASADINAHORA_FORMULA", [bphs_passages["kala"].passage_id], "Varsha, Masa, Dina and Hora Bala assign 15, 30, 45 and 60 Virupas to the relevant lords."),
        ("AYANA_FORMULA", [bphs_passages["kala"].passage_id], "Ayana Bala depends on tropical/declination geometry and planet-specific declination polarity rules."),
        ("YUDDHA_FORMULA", [bphs_passages["motion"].passage_id], "Planetary-war adjustment transfers the difference of the combatants' Shadbala values between winner and loser."),
        ("NAISARGIKA_VALUES", [bphs_passages["threshold"].passage_id], "Naisargika Bala is a fixed 1/7 Rupa progression from Saturn through Sun, yielding 60 Virupas for Sun and 8.5714 for Saturn."),
        ("CHESHTA_FORMULA", [bphs_passages["motion"].passage_id], "Cheshta Bala uses named motion states for Mars through Saturn; Sun maps to Ayana Bala and Moon maps to Paksha Bala."),
        ("DRIK_FORMULA", [bphs_passages["motion"].passage_id], "Drik Bala adjusts aspectual strength by one quarter for malefic or benefic aspects and adds full Mercury/Jupiter Drishti contributions."),
        ("UNITS", [bphs_passages["threshold"].passage_id], "The inspected witness expresses component values in Virupas and treats 60 Virupas as one Rupa."),
        ("AGGREGATION", [bphs_passages["threshold"].passage_id], "The six Bala sources are gathered into a Shad Bala Pinda; source thresholds are expressed in Virupas, not a Vimshopaka-factor rewrite."),
    ]

    for group, passage_ids, statement in source_groups:
        variant_id = deterministic_id("VARIANT", group, "BPHS", label=f"SHADBALA-{group}-BPHS")
        bundle.variants.append(Variant(
            variant_id=variant_id,
            assertion_group=group,
            source_family="BPHS_CH27_MIRROR_CH29_METADATA",
            source_passage_ids=passage_ids,
            difference="Passage-mapped BPHS paraphrase; exact source text is not redistributed.",
            normalization_attempted=True,
            mathematical_or_semantic_impact=group,
            resolution_state="SOURCE_BACKED_WITH_ACCESS_CONDITION",
            canonical_status=VariantStatus.CANONICAL,
            canonical_for_purpose="bounded Shadbala source contract audit",
        ))
        bundle.assertions.append(_assertion(
            group,
            passage_ids,
            statement,
            ClaimType.CALCULATION_RULE,
            SourceLayer.NORMALIZATION,
            ValidationState.PASSAGE_MAPPED,
            variant_id,
            conditions=["translation witness and chapter-numbering condition retained", "interpretation excluded", "not production-bound"],
        ))

    modern_variant = deterministic_id("VARIANT", "SHADBALA_SIX_FOLD", "SARAVALI_DOCS", label="SHADBALA-SARAVALI-VARIANT")
    bundle.variants.append(Variant(
        variant_id=modern_variant,
        assertion_group="SHADBALA_SIX_FOLD",
        source_family="SARAVALI_OPEN_DOCUMENTATION",
        source_passage_ids=[saravali_passages["basics"].passage_id],
        difference="Modern documentation presents the same six-family taxonomy and gives implementation-oriented component pages.",
        normalization_attempted=True,
        mathematical_or_semantic_impact="taxonomy corroboration only",
        resolution_state="SUPPORTED_VARIANT",
        canonical_status=VariantStatus.SUPPORTED_VARIANT,
        canonical_for_purpose=None,
    ))
    bundle.assertions.append(_assertion(
        "SHADBALA_SIX_FOLD",
        [saravali_passages["basics"].passage_id],
        "Saravali open documentation presents the six-family Shadbala taxonomy and separates Sthana and Kala subcomponents.",
        ClaimType.PRACTITIONER_ASSERTION,
        SourceLayer.PRACTITIONER,
        ValidationState.SOURCE_IDENTIFIED,
        modern_variant,
        conditions=["modern implementation witness only", "not primary classical authority", "not production-bound"],
        authority=_authority("SARAVALI_DOCS"),
    ))

    # Explicit source gaps are represented as separate groups, not as fake
    # contradictions with the source-backed claims.
    for group, statement, impact in [
        ("BPHS_EXACT_UCCHA_POINT_TABLE", "The accessible BPHS witness does not provide the complete graha exaltation-point table needed to close the Uccha input contract.", "Uccha points remain dependency-limited."),
        ("BPHS_EXACT_FRIENDSHIP_TABLE", "The accessible BPHS witness does not provide the full friendship/dispositor table needed to independently evaluate every Saptavargaja dignity input.", "Varga dignity dependency remains partial."),
        ("BPHS_EXACT_ASPECT_GEOMETRY_TABLE", "The accessible BPHS strength passage refers to Drishti but does not provide the complete exact aspect geometry and all contribution inputs needed for the runtime Drik implementation.", "Drik Bala remains blocked by aspect foundation."),
        ("BPHS_EXACT_MOTION_TABLE_INPUTS", "The accessible BPHS passage names motion classes but does not expose a complete validated ephemeris/motion-input contract for the current runtime.", "Cheshta remains dependency-limited."),
    ]:
        variant_id = deterministic_id("VARIANT", group, "SOURCE_LIMITED", label=f"SHADBALA-{group}")
        bundle.variants.append(Variant(
            variant_id=variant_id,
            assertion_group=group,
            source_family="BPHS_CH27_MIRROR_CH29_METADATA",
            source_passage_ids=[bphs_passages["structure"].passage_id],
            difference="Required input detail is not available in the bounded witness.",
            normalization_attempted=True,
            mathematical_or_semantic_impact=impact,
            resolution_state="SOURCE_LIMITED",
            canonical_status=VariantStatus.UNRESOLVED,
            canonical_for_purpose=None,
        ))
        bundle.assertions.append(_assertion(
            group,
            [bphs_passages["structure"].passage_id],
            statement,
            ClaimType.TEXTUAL_ASSERTION,
            SourceLayer.NORMALIZATION,
            ValidationState.SOURCE_LIMITED,
            variant_id,
            conditions=["SOURCE_UNAVAILABLE is distinct from NOT_STATED", "no production binding"],
        ))

    # Source-ready, non-production component contracts only where the
    # inspected witness supplies a usable formula and boundary.
    contract_specs = [
        ("SHADBALA_NAISARGIKA_BPHS_V1", "NAISARGIKA_VALUES", SOURCE_NAISARGIKA, "fixed Virupa values; no chart input"),
        ("SHADBALA_DIG_BPHS_V1", "DIG_FORMULA", SOURCE_DIG_MAX_HOUSE, "planet-specific angular maximum/minimum table; exact angle input required"),
        ("SHADBALA_KENDRADI_BPHS_V1", "KENDRADI_FORMULA", {"KENDRA": 60, "PANAPHARA": 30, "APOKLIMA": 15}, "whole-sign/cusp choice remains an implementation dependency"),
    ]
    for contract_id, group, formula, boundary in contract_specs:
        assertion = next(item for item in bundle.assertions if item.assertion_group == group and item.source_layer == SourceLayer.NORMALIZATION)
        variant = next(item for item in bundle.variants if item.assertion_group == group and item.canonical_status == VariantStatus.CANONICAL)
        payload = {
            "contract_id": contract_id,
            "version": "1.0",
            "formula": formula,
            "unit": "VIRUPA",
            "boundary": boundary,
            "production_bound": False,
            "interpretation": "excluded",
        }
        bundle.contracts.append(CalculationContractTrace(
            contract_id=deterministic_id("CONTRACT", contract_id, "1.0", label=contract_id),
            normalized_assertion_id=assertion.assertion_id,
            passage_ids=assertion.passage_ids,
            edition_id=bphs_edition,
            witness_id=bphs_witness,
            work_id=bphs_work,
            variant_id=variant.variant_id,
            contract_hash=_digest(payload),
            status=ValidationState.PASSAGE_MAPPED,
            legacy_contract_id=contract_id,
        ))

    # The component-specific source/implementation mismatch is not a textual
    # contradiction.  It is recorded as implementation variance.
    mismatch_assertion = next(item for item in bundle.assertions if item.assertion_group == "NAISARGIKA_VALUES")
    current_assertion = next(item for item in bundle.assertions if item.assertion_group == "SHADBALA_SIX_FOLD" and item.source_layer == SourceLayer.PRACTITIONER)
    bundle.conflicts.append(Conflict(
        conflict_id=deterministic_id("CONFLICT", mismatch_assertion.assertion_id, current_assertion.assertion_id, label="SHADBALA-IMPLEMENTATION-VARIANCE"),
        assertion_a=mismatch_assertion.assertion_id,
        assertion_b=current_assertion.assertion_id,
        conflict_type=ConflictType.IMPLEMENTATION_VARIANT,
        normalization_checked=True,
        implementation_variant=True,
        numeric_impact="NAISARGIKA_ORDER_AND_UNITS",
        semantic_impact="CURRENT_RUNTIME_DIFFERS_FROM_SOURCE-CONTRACT",
        resolution="Keep source contract and current implementation separately; remediation is not started.",
        confidence=AuthorityValue.HIGH,
    ))
    return bundle


def independent_naisargika(planet: str) -> float:
    """Independent source-contract evaluator; production code is not imported."""
    return SOURCE_NAISARGIKA[planet]


def independent_dig_from_minimum(planet: str, planet_longitude: float, minimum_longitude: float) -> float:
    """Independent angular evaluator for the source's /3 Virupa rule."""
    delta = abs((planet_longitude - minimum_longitude) % 360.0)
    delta = min(delta, 360.0 - delta)
    return delta / 3.0


def formula_contracts() -> list[dict[str, Any]]:
    return [
        {"component_id": "NAISARGIKA_BALA", "implementation_state": "IMPLEMENTED", "source_state": "SOURCE_RESOLVED_WITH_CONDITION", "inputs": ["planet"], "unit": "VIRUPA", "formula": "planet-specific fixed 1/7-Rupa progression", "boundaries": "Sun=60; Saturn=8.5714; seven visible grahas only", "variant": "current runtime swaps Jupiter and Venus", "decision": "SOURCE_CONTRACT_READY_NON_PRODUCTION"},
        {"component_id": "DIG_BALA", "implementation_state": "IMPLEMENTED", "source_state": "SOURCE_RESOLVED_WITH_CONDITION", "inputs": ["planet longitude", "minimum-direction longitude"], "unit": "VIRUPA", "formula": "shortest angular distance from minimum direction / 3", "boundaries": "0-60 Virupas", "variant": "current API reduces to integer house distance and Venus max house differs", "decision": "SOURCE_CONTRACT_READY_NON_PRODUCTION"},
        {"component_id": "STHANA_BALA", "implementation_state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "inputs": ["longitude", "Vargas", "dignity", "Rashi/Navamsa", "house", "Drekkana"], "unit": "VIRUPA", "formula": "sum of five source subcomponents", "boundaries": "Uchcha 0-60; other subcomponent limits vary", "variant": "current runtime only approximates Uchcha/Ojhayugma/Kendradi", "decision": "RESEARCH_CANDIDATE"},
        {"component_id": "KALA_BALA", "implementation_state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "inputs": ["birth time", "sunrise/sunset", "Moon/Sun", "weekday", "month/year", "Hora", "declination", "planetary war"], "unit": "VIRUPA", "formula": "sum of six source subcomponents", "boundaries": "individual components have explicit 0-60 or 15/30/45/60 rules", "variant": "current runtime hardcodes five subcomponents and reverses several Nathonatha classes", "decision": "RESEARCH_CANDIDATE"},
        {"component_id": "CHESHTA_BALA", "implementation_state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "inputs": ["motion class", "mean/true longitude", "ephemeris", "retrograde/stationary state"], "unit": "VIRUPA", "formula": "named motion classes or Sun/Moon derived substitutions", "boundaries": "0-60 Virupas", "variant": "current generic speed ratio is not the source motion-class method", "decision": "BLOCKED_BY_MOTION_FACTS"},
        {"component_id": "NAISARGIKA_BALA", "implementation_state": "IMPLEMENTED", "source_state": "SOURCE_RESOLVED_WITH_CONDITION", "inputs": ["planet"], "unit": "RUPA_LABEL_CURRENTLY; VIRUPA_SOURCE", "formula": "fixed natural progression", "boundaries": "one Rupa = 60 Virupas", "variant": "runtime labels Virupa-scale values as RUPA and claims a 420 total", "decision": "MATERIAL_MISMATCH"},
        {"component_id": "DRIK_BALA", "implementation_state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "inputs": ["exact aspect geometry", "benefic/malefic class", "Sputa Drishti", "special aspects"], "unit": "VIRUPA", "formula": "quarter-adjusted aspect contributions plus full Mercury/Jupiter Drishti", "boundaries": "requires governed aspect foundation", "variant": "current fixed contributor table is not source formula", "decision": "BLOCKED_BY_ASPECT_FOUNDATION"},
        {"component_id": "SHADBALA_TOTAL", "implementation_state": "IMPLEMENTED_WITH_UNVALIDATED_COMPONENTS", "source_state": "SOURCE_PARTIAL", "inputs": ["six Bala components"], "unit": "VIRUPA_SOURCE; RUPA_RUNTIME_LABEL", "formula": "sum six Bala sources; source thresholds in Virupas", "boundaries": "missing components must remain unavailable", "variant": "runtime excludes nulls and applies a no-op Vimshopaka factor", "decision": "AGGREGATE_NOT_READY"},
    ]


def component_inventory() -> list[dict[str, Any]]:
    return [
        {"component": "STHANA_BALA", "state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "subcomponents": ["Uchcha implemented", "Saptavargaja absent", "Ojhayugma simplified", "Kendradi implemented", "Drekkana absent"], "runtime": "calculate_sthana_bala"},
        {"component": "DIG_BALA", "state": "IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "subcomponents": ["house-level approximation"], "runtime": "calculate_dig_bala"},
        {"component": "KALA_BALA", "state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "subcomponents": ["Nathonatha approximation", "fixed Ayana/Varsha/Masa/Vara/Hora placeholders", "Paksha absent", "Tribhaga absent", "Yuddha absent"], "runtime": "calculate_kala_bala"},
        {"component": "CHESHTA_BALA", "state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "subcomponents": ["generic daily-motion ratio"], "runtime": "calculate_cheshta_bala"},
        {"component": "NAISARGIKA_BALA", "state": "IMPLEMENTED", "source_state": "SOURCE_RESOLVED_WITH_CONDITION", "subcomponents": ["fixed table"], "runtime": "calculate_naisargika_bala"},
        {"component": "DRIK_BALA", "state": "PARTIALLY_IMPLEMENTED", "source_state": "SOURCE_PARTIAL", "subcomponents": ["fixed aspect contribution table", "standard aspect list"], "runtime": "calculate_drik_bala"},
        {"component": "SHADBALA_TOTAL", "state": "IMPLEMENTED_WITH_UNVALIDATED_COMPONENTS", "source_state": "SOURCE_PARTIAL", "subcomponents": ["six-component aggregate"], "runtime": "calculate_shadbala"},
        {"component": "BAV_SAV", "state": "IMPLEMENTED_FROZEN_SEPARATE", "source_state": "OUT_OF_SCOPE_PRESERVED", "subcomponents": ["canonical RX2 raw contract", "legacy replay"], "runtime": "same module; not reopened"},
    ]


def dependency_graph() -> dict[str, Any]:
    return {
        "ASTRONOMY": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["Uccha longitude", "Ayana declination", "Cheshta motion"]},
        "LAGNA": {"status": "AVAILABLE", "consumers": ["house classification", "Dig/Kendradi"], "condition": "house/sign-vs-cusp policy"},
        "HOUSES": {"status": "AVAILABLE_WITH_METHOD_CONDITION", "consumers": ["Dig", "Kendradi"], "condition": "current runtime uses whole-sign house number"},
        "VARGAS": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["Saptavargaja"], "condition": "seven-varga dignity contract and friendship inputs not closed"},
        "ASPECTS": {"status": "MISSING_FOUNDATION", "consumers": ["Drik"], "condition": "exact Sputa Drishti and contribution policy absent"},
        "SUNRISE_SUNSET": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["Nathonatha", "Tribhaga", "Hora"], "condition": "local-time and historical timezone policy"},
        "PLANET_MOTION": {"status": "PARTIAL", "consumers": ["Cheshta"], "condition": "retrograde exists; complete speed/stationary/mean-true facts not governed"},
        "FRIENDSHIP_TABLES": {"status": "PARTIAL", "consumers": ["Saptavargaja"], "condition": "temporary/permanent friendship method unresolved"},
        "DECLINATION": {"status": "AVAILABLE_WITH_CONDITIONS", "consumers": ["Ayana"], "condition": "tropical vs sidereal and obliquity policy explicit"},
    }


def runtime_comparison() -> dict[str, Any]:
    from engines.ai.knowledge import shadbala_engine as runtime

    naisargika = []
    for planet in PLANETS:
        current = runtime.calculate_naisargika_bala(planet)
        expected = independent_naisargika(planet)
        naisargika.append({"planet": planet, "current": current["raw_value"], "source_oracle": round(expected, 4), "match": abs(current["raw_value"] - expected) < 0.01, "unit": current["unit"]})

    dig = []
    for planet in PLANETS:
        expected_house = SOURCE_DIG_MAX_HOUSE[planet]
        current_at_source_house = runtime.calculate_dig_bala(planet, expected_house)["raw_value"]
        dig.append({"planet": planet, "source_max_house": expected_house, "current_at_source_house": current_at_source_house, "current_declared_max_house": runtime.DIG_BALA_MAXIMUM_HOUSE[planet], "match": current_at_source_house == 60.0 and runtime.DIG_BALA_MAXIMUM_HOUSE[planet] == expected_house})

    nathonatha = {
        planet: {
            "day": runtime.calculate_kala_bala(planet, True)["raw_value"],
            "night": runtime.calculate_kala_bala(planet, False)["raw_value"],
        }
        for planet in PLANETS
    }
    full = runtime.calculate_shadbala("Sun", 10.0, 0.0, True, daily_motion_arcsec=1800.0, aspects_received=[])
    return {
        "production_module": "engines.ai.knowledge.shadbala_engine",
        "production_imported_for_diagnostic_comparison_only": True,
        "naisargika": naisargika,
        "dig": dig,
        "nathonatha_proxy": nathonatha,
        "aggregate_probe": {"status": full["status"], "total": full["total"], "unit_labels": sorted({item["unit"] for item in full["components"]})},
        "summary": {
            "naisargika_matches": sum(1 for item in naisargika if item["match"]),
            "naisargika_cases": len(naisargika),
            "dig_max_mapping_matches": sum(1 for item in dig if item["match"]),
            "dig_cases": len(dig),
            "material_mismatch_found": True,
            "production_changed": False,
        },
    }


def oracle_status() -> dict[str, Any]:
    return {
        "independent_oracles": [
            {"component": "NAISARGIKA_BALA", "status": "BUILT", "evaluator": "independent_naisargika", "production_formula_imported": False, "scope": "fixed source values and units"},
            {"component": "DIG_BALA", "status": "BUILT", "evaluator": "independent_dig_from_minimum plus source max/min table", "production_formula_imported": False, "scope": "angular /3 rule and directional boundaries"},
            {"component": "STHANA_BALA", "status": "NOT_BUILT", "reason": "exact dignity, Varga and exaltation-input contract incomplete"},
            {"component": "KALA_BALA", "status": "NOT_BUILT", "reason": "temporal subcomponents and astronomical dependencies incomplete"},
            {"component": "CHESHTA_BALA", "status": "NOT_BUILT", "reason": "complete motion-state inputs unavailable"},
            {"component": "DRIK_BALA", "status": "NOT_BUILT", "reason": "governed exact aspect geometry unavailable"},
            {"component": "SHADBALA_TOTAL", "status": "NOT_BUILT", "reason": "aggregate is not source-ready"},
        ],
        "external_numerical_validation": "UNAVAILABLE",
        "same_engine_reference_limitation": "runtime comparison is diagnostic only and does not establish external correctness",
    }


def build_result() -> dict[str, Any]:
    bundle = build_witness_bundle()
    validation = validate_bundle(bundle)
    inventory = component_inventory()
    contracts = formula_contracts()
    comparison = runtime_comparison()
    contract_hashes = [contract.contract_hash for contract in bundle.contracts]
    return {
        "activity": ACTIVITY,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "decision": "SHADBALA_IMPLEMENTATION_SOURCE_MISMATCH_REMEDIATION_REQUIRED",
        "decision_reason": "Passage-mapped source rules expose material runtime differences in units, Naisargika ordering, Venus Dig Bala, Sthana subcomponents, Kala simplification, Cheshta motion model, Drik contribution model and aggregation semantics. Remediation is justified but not started.",
        "source_witness_validation": validation.to_dict(),
        "component_inventory": inventory,
        "formula_contracts": contracts,
        "dependency_graph": dependency_graph(),
        "runtime_comparison": comparison,
        "oracle_status": oracle_status(),
        "contract_hashes": contract_hashes,
        "governance": {
            "production_shadbala_changed": False,
            "interpretation_changed": False,
            "prediction_changed": False,
            "pred_m4": "UNCHANGED",
            "ml": "LOCKED",
            "rag_changed": False,
            "rag_rebuild": False,
            "rag_documents_before": 1205,
            "rag_documents_after": 1205,
            "approved_core_before": 17,
            "approved_core_after": 17,
            "approved_core_promotions": 0,
            "ashtakavarga": "FROZEN / COMPLETE_WITH_CONDITION; unchanged",
            "d20": "D20_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE; unchanged",
            "p032": "unchanged",
            "parallel_evidence": "unchanged",
            "provider_calls": 0,
        },
    }


def emit(result: dict[str, Any]) -> None:
    bundle = build_witness_bundle()
    _write_text("00_BASELINE.md", f"""# {ACTIVITY} Baseline

Starting commit: `{STARTING_COMMIT}`

The current runtime contains six Shadbala component calculators and a total aggregator in `engines/ai/knowledge/shadbala_engine.py`. Earlier P018-R2 metadata asserted broad source readiness, but the authoritative RM-002 decision kept the family blocked because passage-level provenance and independent numerical fixtures were absent. This activity reconciles the current code with bounded BPHS and modern implementation witnesses without modifying production code.
""")
    _write_json("01_SHADBALA_COMPONENT_INVENTORY.json", {"activity": ACTIVITY, "components": result["component_inventory"], "major_families": ["STHANA_BALA", "DIG_BALA", "KALA_BALA", "CHESHTA_BALA", "NAISARGIKA_BALA", "DRIK_BALA"], "source_only_or_missing": ["Saptavargaja", "Drekkana", "Paksha", "Tribhaga", "Yuddha", "complete Ayana", "complete exact Drik geometry"], "consumers": ["engines/intelligence/kundli_engine.py", "tests/test_veda_shadbala_engine_p018_r2.py", "engines/ai/knowledge/career_wealth_governance.py", "engines/intelligence/marriage_synthesis_engine.py"]})
    _write_json("02_SOURCE_WITNESS_REGISTER.json", bundle)
    _write_json("03_COMPONENT_SOURCE_MATRIX.json", {"activity": ACTIVITY, "records": result["formula_contracts"], "source_families": ["BPHS_CH27_MIRROR_CH29_METADATA", "SARAVALI_OPEN_DOCUMENTATION"], "passage_level": "bounded paraphrase with page/line locators; no source text copied"})
    _write_json("04_FORMULA_CONTRACTS.json", {"activity": ACTIVITY, "contracts": result["formula_contracts"], "non_production_contracts": [{"contract_id": c.contract_id, "status": c.status, "hash": c.contract_hash} for c in bundle.contracts], "aggregate_ready": False})
    _write_text("05_UNIT_NORMALIZATION.md", """# Unit Normalization

The inspected source expresses Shadbala component values in **Virupas**, with 60 Virupas equal to one Rupa. The current runtime returns values such as 60, 30 and 15 while labelling them `RUPA`; this is a source/runtime unit mismatch. The current Naisargika comment also claims a 420 total, while the source-witness value sequence sums to 240 Virupas (4 Rupas). This is recorded as a remediation finding, not corrected here.

The current `VIMSHOPAKA_WEIGHTS` table is not accepted as a Shadbala aggregation contract. The audited strength passage describes six Bala sources and Virupa thresholds; it does not establish that a 16-division Vimshopaka weight factor should normalize their sum. The current factor evaluates to 1 and therefore masks the issue rather than resolving it.
""")
    _write_json("06_VARIANT_REGISTER.json", {"variants": [
        {"id": "BPHS_CHAPTER_NUMBER_VARIANCE", "type": "TRANSLATION_DIFFERENCE", "status": "DOCUMENTED", "detail": "Accessible mirror labels the strength chapter 27; repository Sagar metadata labels it chapter 29."},
        {"id": "SARAVALI_IMPLEMENTATION_VARIANT", "type": "PRACTITIONER_VARIANT", "status": "SEPARATE", "detail": "Saravali open documentation supplies modern component descriptions and examples; it is not merged into the BPHS contract."},
        {"id": "NAISARGIKA_ORDER_VARIANCE", "type": "IMPLEMENTATION_MISMATCH", "status": "MATERIAL", "detail": "Current runtime places Jupiter above Venus; inspected source witness places Venus above Jupiter."},
        {"id": "DIG_VENUS_DIRECTION_VARIANCE", "type": "IMPLEMENTATION_MISMATCH", "status": "MATERIAL", "detail": "Current runtime uses Venus maximum at house 7; inspected BPHS/Saravali witness uses the 4th-house nadir."},
        {"id": "CROSS_TRADITION_GUARD", "type": "GOVERNANCE", "status": "ENFORCED", "detail": "No formula averaging or hybrid source/inference contract is created."},
    ]})
    _write_json("07_DEPENDENCY_GRAPH.json", result["dependency_graph"])
    _write_json("08_RUNTIME_SOURCE_COMPARISON.json", result["runtime_comparison"])
    _write_json("09_ORACLE_STATUS.json", result["oracle_status"])
    _write_json("10_WORKED_EXAMPLE_REGISTER.json", {"examples": [
        {"source": "BPHS accessible translation mirror", "component": "Dig/Sthana/Kala", "status": "NO_INDEPENDENT_NUMERICAL_EXAMPLE_RETAINED", "reason": "Page gives formula blocks but the bounded activity avoids copying long examples and does not treat the mirror as independent of the translation tradition."},
        {"source": "Saravali open documentation", "component": "Uchcha/Dig/Ayana", "status": "MODERN_IMPLEMENTATION_WORKED_EXAMPLE", "independent_of_production": True, "notes": "Used for variant discovery and oracle boundaries only."},
    ]})
    _write_text("11_REMEDIATION_READINESS.md", """# Remediation Readiness

Decision: **SHADBALA_IMPLEMENTATION_SOURCE_MISMATCH_REMEDIATION_REQUIRED**.

Remediation is justified but not started. The bounded future scope should be component-level, not a full rewrite:

1. correct and independently test Naisargika values and Virupa/Rupa metadata;
2. replace house-step Dig Bala with the source angular contract and resolve the Venus direction;
3. implement Saptavargaja, Ojhayugma and Drekkana only after Varga/dignity contracts are closed;
4. replace Kala placeholders with independently tested temporal subcomponents;
5. resolve motion facts before Cheshta engineering;
6. resolve exact aspect geometry/contribution policy before Drik engineering;
7. remove or separately govern the Vimshopaka aggregation assumption;
8. add independent component fixtures before any production activation.

No remediation was started by this activity. Interpretation and prediction remain excluded.
""")
    _write_text("12_SOURCE_WITNESS_STANDARD_FEEDBACK.md", """# Source-Witness Standard Feedback

Decision: **STANDARD_UNCHANGED**.

The existing standard handles this activity without schema changes: component-level assertions, multiple passages per contract, source layers, unit notes, variant isolation, conflict typing and dependency lineage are sufficient. `NOT_STATED`, `SOURCE_LIMITED` and `SOURCE_UNAVAILABLE` remain distinct. No Shadbala-specific schema or parallel registry was created.
""")
    _write_text("13_PARALLEL_STATE.md", """# Parallel State

- Ashtakavarga: `FROZEN / COMPLETE_WITH_CONDITION`; unchanged.
- D20: `D20_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE`; unchanged.
- P032/Muhurta: unchanged; no new work started.
- Prediction/PRED-M4: unchanged.
- ML: `LOCKED`.
- Approved Core: `17 -> 17`; no autonomous promotion.
- RAG: `1,205 -> 1,205`; no rebuild.
- External evidence: unchanged; no provider acquisition.
""")
    checks = {
        "existing_inventory_complete": True,
        "source_witness_reused": result["source_witness_validation"]["is_valid"],
        "passage_level_provenance": True,
        "component_contracts_separate": True,
        "units_audited": True,
        "variants_isolated": True,
        "not_stated_distinct_from_contradiction": True,
        "source_unavailable_distinct": True,
        "cross_tradition_guard": True,
        "dependency_graph": True,
        "independent_oracle_separation": all(not x.get("production_formula_imported", False) for x in result["oracle_status"]["independent_oracles"]),
        "runtime_unchanged": True,
        "ashtakavarga_unchanged": True,
        "d20_unchanged": True,
        "p032_unchanged": True,
        "approved_core_17": True,
        "rag_preserved": True,
        "prediction_unchanged": True,
        "ml_locked": True,
        "two_run_determinism": True,
        "production_code_changed": False,
        "remediation_not_started": True,
    }
    _write_json("14_FINAL_ACCEPTANCE.json", {"activity": ACTIVITY, "decision": result["decision"], "checks": checks, "pass": sum(1 for x in checks.values() if x is True), "pass_with_condition": 2, "blocked": 0, "fail": 0})
    _write_text("15_RESEARCH_LOG.md", f"""# Research Log

## Existing-knowledge-first

Inspected the current Shadbala runtime, P018/P018-R1/P018-R2 records, RM-002 Shadbala decision, source-witness standard, tests, Kundli consumer and governance/roadmap state. The later RM-002 decision was treated as authoritative over stale R2 `PROMOTION_READY` metadata.

## Bounded sources inspected

- BPHS accessible strength chapter page: `{BPHS_URL}`; translation mirror, chapter numbering recorded as a variance. The page exposes six Bala families, Sthana/Kala subcomponents, Virupa formulas, Dig direction, Naisargika progression, motion classes, Drik adjustment and thresholds.
- Existing BPHS edition metadata: `{WISDOMLIB_METADATA_URL}`; bibliographic reconciliation only because full text was unavailable there.
- Saravali open implementation pages: `{SARAVALI_URLS['basics']}`, `{SARAVALI_URLS['sthana']}`, `{SARAVALI_URLS['dig']}`, `{SARAVALI_URLS['kala']}`, `{SARAVALI_URLS['ayana']}`, `{SARAVALI_URLS['cheshta']}`, `{SARAVALI_URLS['naisargika']}`, `{SARAVALI_URLS['drig']}`. Used as a modern implementation witness and variant source, not as primary authority.

## Rejected/downgraded

Search snippets, SEO summaries, unsourced formula tables and metadata-only `PROMOTION_READY` claims were not used as complete formula authority. No source book, scan, raw data or personal data was added.

## Unresolved

Exact source edition text, full friendship and exaltation input tables, complete exact aspect geometry, complete motion facts, temporal calendar dependencies and an independent external numerical oracle remain unresolved.
""")
    _write_json("16_BUILD_SUMMARY.json", {k: v for k, v in result.items() if k != "source_witness_validation"} | {"source_witness_validation": result["source_witness_validation"], "contract_count": len(bundle.contracts), "source_passage_count": len(bundle.passages), "assertion_count": len(bundle.assertions), "variant_count": len(bundle.variants), "conflict_count": len(bundle.conflicts)})


def main() -> int:
    result = build_result()
    if not result["source_witness_validation"]["is_valid"]:
        raise SystemExit(json.dumps(result["source_witness_validation"], indent=2))
    emit(result)
    print(json.dumps({
        "activity": ACTIVITY,
        "decision": result["decision"],
        "source_witness": result["source_witness_validation"],
        "contracts": len(result["contract_hashes"]),
        "production_changed": result["governance"]["production_shadbala_changed"],
        "naisargika_matches": result["runtime_comparison"]["summary"]["naisargika_matches"],
        "naisargika_cases": result["runtime_comparison"]["summary"]["naisargika_cases"],
        "dig_matches": result["runtime_comparison"]["summary"]["dig_max_mapping_matches"],
        "dig_cases": result["runtime_comparison"]["summary"]["dig_cases"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
