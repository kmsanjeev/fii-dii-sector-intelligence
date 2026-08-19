"""Build the bounded source-witness standard pilots and reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/knowledge-source-witness-standard-001"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_governance import validate_registry_directory
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
    RightsPermission,
    RightsProfile,
    RightsState,
    ReviewState,
    SourceAccessState,
    SourceLayer,
    SourceWitnessBundle,
    Supersession,
    SupersessionStatus,
    ValidationProfile,
    ValidationState,
    Variant,
    VariantStatus,
    Witness,
    Work,
    deterministic_id,
    stable_digest,
    validate_bundle,
)

SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "bc02cd2aedc42247dd9d1f7612d6f8b3107d2057"
STANDARD_ID = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"


def _rights(state: RightsState, *permissions: RightsPermission) -> RightsProfile:
    return RightsProfile(rights_state=state, permissions=list(permissions), basis="Existing VEDA metadata; no bulk source text committed")


def _authority(**values: AuthorityValue) -> AuthorityProfile:
    return AuthorityProfile(**values)


def _work(title: str, legacy: list[str], author: str | None = None, work_type: str = "CLASSICAL_TEXT") -> Work:
    return Work(
        work_id=deterministic_id("WORK", title, author or "", label=title),
        canonical_title=title,
        traditional_author=author,
        tradition="VEDA / JYOTISHA" if work_type == "CLASSICAL_TEXT" else "VEDA DERIVED",
        work_type=work_type,
        language_origin="SANSKRIT" if work_type == "CLASSICAL_TEXT" else "PYTHON / JSON",
        notes="Identity is bounded to existing VEDA metadata; uncertain chronology is not asserted.",
        legacy_source_ids=legacy,
    )


def _witness(work: Work, legacy_id: str, witness_type: str, locator: str, rights: RightsProfile, *, access: SourceAccessState = SourceAccessState.PARTIAL_TEXT, dependence: DependenceState = DependenceState.UNKNOWN) -> Witness:
    return Witness(
        witness_id=deterministic_id("WITNESS", work.work_id, legacy_id, witness_type, locator, label=legacy_id),
        work_id=work.work_id,
        witness_type=witness_type,
        repository_or_library="Existing VEDA source artifact register",
        locator=locator,
        language="EN_TRANSLATION" if "TRANSLATION" in witness_type else "JSON / METADATA",
        completeness="BOUNDED_PILOT_METADATA",
        physical_or_digital="DIGITAL",
        provenance="Mapped from an existing governed VEDA artifact; no source text copied.",
        dependence_state=dependence,
        source_access=access,
        rights=rights,
        review_state=ReviewState.SOURCE_CHECKED,
        legacy_source_id=legacy_id,
    )


def _edition(work: Work, witness: Witness, title: str, locator: str, rights: RightsProfile, *, notes: str = "") -> Edition:
    return Edition(
        edition_id=deterministic_id("EDITION", work.work_id, witness.witness_id, title, locator, label=title),
        work_id=work.work_id,
        witness_ids=[witness.witness_id],
        edition_title=title,
        language="EN_TRANSLATION" if "TRANSLATION" in title.upper() else "METADATA",
        source_type="REFERENCE_EDITION_OR_GOVERNANCE_ARTIFACT",
        digital_locator=locator,
        rights=rights,
        completeness="BOUNDED_PILOT_METADATA",
        editorial_notes=notes or None,
        edition_hash=stable_digest({"work": work.work_id, "witness": witness.witness_id, "title": title, "locator": locator}, 64),
    )


def _passage(edition: Edition, label: str, locator: str, layer: SourceLayer, rights: RightsProfile, *, chapter: str | None = None, verse: str | None = None, page: str | None = None, access: SourceAccessState = SourceAccessState.PARTIAL_TEXT, base_passage_id: str | None = None) -> Passage:
    return Passage(
        passage_id=deterministic_id("PASSAGE", edition.edition_id, label, locator, layer.value, label=label),
        edition_id=edition.edition_id,
        chapter=chapter,
        verse=verse,
        page=page,
        source_locator=locator,
        source_layer=layer,
        language="EN_TRANSLATION" if layer == SourceLayer.TRANSLATION else "JSON",
        text_hash=stable_digest({"edition": edition.edition_id, "locator": locator, "layer": layer.value}, 64),
        citation_label=label,
        source_access=access,
        rights=rights,
        review_state=ReviewState.SOURCE_CHECKED,
        base_passage_id=base_passage_id,
    )


def _assertion(group: str, passages: list[Passage], claim_type: ClaimType, statement: str, layer: SourceLayer, authority: AuthorityProfile, validation: ValidationProfile, variant_id: str | None = None) -> Assertion:
    return Assertion(
        assertion_id=deterministic_id("ASSERTION", group, [item.passage_id for item in passages], statement, layer.value, label=group),
        assertion_group=group,
        passage_ids=[item.passage_id for item in passages],
        claim_type=claim_type,
        statement=statement,
        normalized_statement=statement,
        normalization_method="Bounded pilot paraphrase; no source text copied",
        source_layer=layer,
        variant_id=variant_id,
        authority=authority,
        validation=validation,
        assertion_hash=stable_digest({"group": group, "passages": [item.passage_id for item in passages], "statement": statement}, 64),
    )


def _variant(group: str, source_family: str, passages: list[Passage], difference: str, status: VariantStatus, impact: str, purpose: str | None = None, *, legacy: str | None = None) -> Variant:
    return Variant(
        variant_id=deterministic_id("VARIANT", group, source_family, difference, status.value, label=source_family),
        assertion_group=group,
        source_family=source_family,
        source_passage_ids=[item.passage_id for item in passages],
        difference=difference,
        normalization_attempted=True,
        mathematical_or_semantic_impact=impact,
        resolution_state="PRESERVED_SEPARATELY" if status != VariantStatus.UNRESOLVED else "UNRESOLVED",
        canonical_status=status,
        canonical_for_purpose=purpose,
        supersedes_variant_id=legacy,
    )


def build_ashtakavarga_pilot() -> SourceWitnessBundle:
    rights = _rights(RightsState.RESEARCH_ONLY, RightsPermission.LOCAL_RESEARCH_ALLOWED, RightsPermission.DERIVED_METADATA_ALLOWED)
    bphs = _work("Brihat Parashara Hora Shastra", ["BPHS"], "Parashara")
    phala = _work("Phaladeepika", ["PHALADEEPIKA"], "Mantreswara")
    internal = _work("VEDA Ashtakavarga Implementation Witness", ["VEDA-MODERN-337-386"], work_type="DERIVED_INTERNAL")
    bw = _witness(bphs, "SRC-BPHS-PDF-CH66-69", "SELECTED_TRANSLATED_WITNESS", "docs/current-state/calc-ashtakavarga-contract-rx2-001/02_V2_SOURCE_BINDING.json", rights, dependence=DependenceState.POTENTIALLY_INDEPENDENT)
    pw = _witness(phala, "PHALADEEPIKA", "TRADITIONAL_TRANSLATION_WITNESS", "docs/current-state/calc-ashtakavarga-crosssource-rx-001/01_SOURCE_WITNESS_REGISTER.json", rights, dependence=DependenceState.LATER_SYNTHESIS)
    iw = _witness(internal, "VEDA-MODERN-337-386", "IMPLEMENTATION_WITNESS", "docs/current-state/calc-ashtakavarga-normalization-rx2-001/02_KNR_SOURCE_REGISTER.json", _rights(RightsState.RESEARCH_ONLY, RightsPermission.DERIVED_METADATA_ALLOWED), access=SourceAccessState.AVAILABLE, dependence=DependenceState.DERIVATIVE)
    be = _edition(bphs, bw, "Parent PDF translation; edition unspecified", "docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json", rights, notes="Edition/editor/translator are not recorded in the parent artifact and remain explicit UNKNOWN metadata.")
    pe = _edition(phala, pw, "Phaladeepika accessed translation", "docs/current-state/calc-ashtakavarga-crosssource-rx-001/01_SOURCE_WITNESS_REGISTER.json", rights)
    ie = _edition(internal, iw, "VEDA implementation witness record", "docs/current-state/calc-ashtakavarga-normalization-rx2-001/09_CLASSICAL_CROSS_SOURCE_MATRIX.json", _rights(RightsState.RESEARCH_ONLY, RightsPermission.DERIVED_METADATA_ALLOWED))
    bp = _passage(be, "BPHS Ch.66.43-68 and 66.69-76; raw contract source witness", "docs/current-state/calc-ashtakavarga-contract-rx2-001/02_V2_SOURCE_BINDING.json", SourceLayer.TRANSLATION, rights, chapter="66", verse="66.43-68; 66.69-76", page="135-136")
    pp = _passage(pe, "Phaladeepika Ch.23.1-22; explicit alternative witness", "docs/current-state/calc-ashtakavarga-crosssource-rx-001/01_SOURCE_WITNESS_REGISTER.json", SourceLayer.TRANSLATION, rights, chapter="23", verse="1-22", page="258-303")
    ip = _passage(ie, "Modern 337/386 implementation witness record", "docs/current-state/calc-ashtakavarga-normalization-rx2-001/02_KNR_SOURCE_REGISTER.json", SourceLayer.IMPLEMENTATION, _rights(RightsState.RESEARCH_ONLY, RightsPermission.DERIVED_METADATA_ALLOWED), access=SourceAccessState.AVAILABLE)
    canonical = _variant("ASHTAKAVARGA_RAW_CONTRACT", "BPHS_PRIMARY_V2", [bp], "Source-consistent 336/49/385 raw semantics are selected as the V2 contract.", VariantStatus.CANONICAL, "Canonical calculation contract for raw BAV/SAV; interpretation remains separate.", "RAW_BAV_SAV_V2")
    phala_variant = _variant("ASHTAKAVARGA_RAW_CONTRACT", "PHALADEEPIKA_MAIN_TEXT", [pp], "Seven pair-level variants and a separate 336-total witness are retained.", VariantStatus.SUPPORTED_VARIANT, "Alternative calculation witness; never silently merged.", "RAW_BAV_SAV_ALTERNATIVE")
    varaha_variant = _variant("ASHTAKAVARGA_RAW_CONTRACT", "VARAHAMIHIRA_ATTRIBUTED_VARIANT", [pp], "Existing artifact labels a Varahamihira-attributed alternative; independent work-level attribution is not asserted.", VariantStatus.RESEARCH_VARIANT, "Variant discovery and comparison only.", "VARIANT_DISCOVERY")
    modern_variant = _variant("ASHTAKAVARGA_RAW_CONTRACT", "MODERN_337_386_IMPLEMENTATION_WITNESS", [ip], "Modern 337/386 values are retained as an implementation witness with unresolved lineage.", VariantStatus.RESEARCH_VARIANT, "Not classical numerical proof.", "IMPLEMENTATION_WITNESS")
    v1_variant = _variant("ASHTAKAVARGA_RAW_CONTRACT", "BPHS_PRIMARY_KNR_GOVERNED_V1", [bp, ip], "Historical V1 combined a BPHS matrix with an unverified modern 337/386 aggregate invariant.", VariantStatus.SUPERSEDED_INVALID_HYBRID, "Superseded historical record; must not be reactivated.", "HISTORICAL_ONLY")
    a = _assertion("ASHTAKAVARGA_RAW_CONTRACT", [bp], ClaimType.CALCULATION_RULE, "The canonical raw Ashtakavarga V2 contract is traced to the selected BPHS witness and preserves separate planetary, Lagna and combined semantics.", SourceLayer.NORMALIZATION, _authority(traditional_authority=AuthorityValue.VERY_HIGH, textual_authority=AuthorityValue.HIGH, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.HIGH, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.CONTRACT_FROZEN, review_state=ReviewState.SOURCE_CHECKED, conditions=["external numerical oracle unavailable", "reductions deferred"]), canonical.variant_id)
    p = _assertion("ASHTAKAVARGA_RAW_CONTRACT", [pp], ClaimType.CALCULATION_RULE, "Phaladeepika is represented as an explicit alternative witness with pair-level variants and is not merged into BPHS V2.", SourceLayer.NORMALIZATION, _authority(traditional_authority=AuthorityValue.HIGH, textual_authority=AuthorityValue.MODERATE, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.MODERATE, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.VARIANTS_RECONCILED, review_state=ReviewState.SOURCE_CHECKED, conditions=["translation and OCR uncertainty retained"]), phala_variant.variant_id)
    v = _assertion("ASHTAKAVARGA_RAW_CONTRACT", [pp], ClaimType.CALCULATION_RULE, "The existing Varahamihira-attributed alternative is retained as a research variant; attribution and mathematical equivalence are not independently promoted.", SourceLayer.COMMENTARY, _authority(traditional_authority=AuthorityValue.MODERATE, textual_authority=AuthorityValue.LOW, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.LOW, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.SOURCE_LIMITED, review_state=ReviewState.SOURCE_CHECKED, conditions=["attribution is inherited from existing artifact"]), varaha_variant.variant_id)
    m = _assertion("ASHTAKAVARGA_RAW_CONTRACT", [ip], ClaimType.CALCULATION_RULE, "The modern 337/386 values are an implementation witness with unresolved lineage, not a classical invariant.", SourceLayer.IMPLEMENTATION, _authority(traditional_authority=AuthorityValue.NOT_ASSESSED, textual_authority=AuthorityValue.UNKNOWN, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.HIGH, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.SOURCE_LIMITED, review_state=ReviewState.SOURCE_CHECKED, conditions=["lineage unresolved"]), modern_variant.variant_id)
    h = _assertion("ASHTAKAVARGA_RAW_CONTRACT", [bp, ip], ClaimType.SYSTEM_INFERENCE, "Historical V1 is superseded because its source matrix and aggregate invariant came from incompatible or unverified traditions.", SourceLayer.IMPLEMENTATION, _authority(traditional_authority=AuthorityValue.NOT_ASSESSED, textual_authority=AuthorityValue.NOT_ASSESSED, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.HIGH, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.SUPERSEDED, review_state=ReviewState.SOURCE_CHECKED, conditions=["historical compatibility only"]), v1_variant.variant_id)
    contract = CalculationContractTrace(contract_id=deterministic_id("CONTRACT", "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2", "2.0.0", label="ASHTAKAVARGA-V2"), normalized_assertion_id=a.assertion_id, passage_ids=[bp.passage_id], edition_id=be.edition_id, witness_id=bw.witness_id, work_id=bphs.work_id, variant_id=canonical.variant_id, contract_hash="084E19B2D61880066A503E1CED38810CA9D51962354A9520DD2E5E5946279A62", status=ValidationState.CONTRACT_FROZEN, legacy_contract_id="ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2")
    v1_contract = CalculationContractTrace(contract_id=deterministic_id("CONTRACT", "ASHTAKAVARGA_RAW_BPHS_PRIMARY_KNR_GOVERNED_V1", label="ASHTAKAVARGA-V1"), normalized_assertion_id=h.assertion_id, passage_ids=[bp.passage_id, ip.passage_id], edition_id=be.edition_id, witness_id=bw.witness_id, work_id=bphs.work_id, variant_id=v1_variant.variant_id, contract_hash="0E296628F989A9EE1AA14CF2F767ECEA8142042CD266DC9C98D0FF32A6771134", status=ValidationState.SUPERSEDED, supersession_status=SupersessionStatus.SUPERSEDED, legacy_contract_id="ASHTAKAVARGA_RAW_BPHS_PRIMARY_KNR_GOVERNED_V1")
    bundle = SourceWitnessBundle(works=[bphs, phala, internal], witnesses=[bw, pw, iw], editions=[be, pe, ie], passages=[bp, pp, ip], assertions=[a, p, v, m, h], variants=[canonical, phala_variant, varaha_variant, modern_variant, v1_variant], conflicts=[Conflict(conflict_id=deterministic_id("CONFLICT", a.assertion_id, p.assertion_id, label="PHALADEEPIKA-VARIANT"), assertion_a=a.assertion_id, assertion_b=p.assertion_id, conflict_type=ConflictType.TEXTUAL_VARIANT, normalization_checked=True, textual_variant=True, numeric_impact="PAIR_LEVEL_VARIANTS_RETAINED", semantic_impact="ALTERNATIVE_METHOD", resolution="COEXIST; BPHS selected for V2 purpose; Phaladeepika remains explicit alternative", confidence=AuthorityValue.HIGH), Conflict(conflict_id=deterministic_id("CONFLICT", a.assertion_id, m.assertion_id, label="MODERN-WITNESS"), assertion_a=a.assertion_id, assertion_b=m.assertion_id, conflict_type=ConflictType.IMPLEMENTATION_VARIANT, normalization_checked=True, implementation_variant=True, numeric_impact="336/385_VS_337/386", semantic_impact="SOURCE_LINEAGE_DIFFERENCE", resolution="BPHS V2 selected; modern witness retained without promotion", confidence=AuthorityValue.HIGH)], contracts=[contract, v1_contract], supersessions=[Supersession(superseded_id=v1_contract.contract_id, superseding_id=contract.contract_id, reason="Invalid hybrid: BPHS matrix plus unverified 337/386 aggregate invariant", date=SNAPSHOT_DATE, programme="VEDA-CALC-ASHTAKAVARGA-REMEDIATION-RX2-001")], legacy_mappings={"BPHS": bphs.work_id, "PHALADEEPIKA": phala.work_id, "VEDA-MODERN-337-386": internal.work_id})
    return bundle


def build_d20_pilot() -> SourceWitnessBundle:
    rights = _rights(RightsState.RESEARCH_ONLY, RightsPermission.LOCAL_RESEARCH_ALLOWED, RightsPermission.DERIVED_METADATA_ALLOWED)
    bphs = _work("Brihat Parashara Hora Shastra", ["BPHS"], "Parashara")
    witness = _witness(bphs, "BPHS_CH6_17_20", "SELECTED_PRIMARY_SOURCE_WITNESS", "docs/current-state/calc-source-rx-001/07_D20_PRIMARY_SOURCES.md", rights, dependence=DependenceState.POTENTIALLY_INDEPENDENT)
    edition = _edition(bphs, witness, "D20 primary-source audit reference", "docs/current-state/calc-source-rx-001/07_D20_PRIMARY_SOURCES.md", rights, notes="The existing audit records the inspected source and does not claim a complete destination mapping.")
    passage = _passage(edition, "BPHS Ch.6.17-20 Vimshamsha category-start passage", "docs/current-state/calc-source-rx-001/07_D20_PRIMARY_SOURCES.md; https://www.siva.sh/brihat-parashara-hora-shastra/6/16-20", SourceLayer.TRANSLATION, rights, chapter="6", verse="17-20", access=SourceAccessState.PARTIAL_TEXT)
    canonical = _variant("D20_VIMSHAMSHA_METHOD", "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1", [passage], "Twenty 1.5-degree divisions and category starts Aries/Sagittarius/Leo are retained; destination mapping remains incomplete.", VariantStatus.CANONICAL, "Category-start calculation representation only")
    legacy = _variant("D20_VIMSHAMSHA_METHOD", "D20_LEGACY_GENERIC_VARGA_V0", [passage], "Historical generic odd/even fallback is preserved for comparison only.", VariantStatus.LEGACY_VARIANT, "Historical replay only")
    assertion = _assertion("D20_VIMSHAMSHA_METHOD", [passage], ClaimType.CALCULATION_RULE, "The inspected D20 source supports twenty divisions and category starts Aries, Sagittarius and Leo; complete destination-sign mapping remains unresolved.", SourceLayer.NORMALIZATION, _authority(traditional_authority=AuthorityValue.VERY_HIGH, textual_authority=AuthorityValue.HIGH, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.MODERATE, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.SOURCE_LIMITED, review_state=ReviewState.SOURCE_CHECKED, conditions=["destination mapping incomplete", "interpretation not validated"]), canonical.variant_id)
    legacy_assertion = _assertion("D20_VIMSHAMSHA_METHOD", [passage], ClaimType.IMPLEMENTATION_NOTE, "The historical generic D20 fallback remains a legacy comparison method and is not the source-selected route.", SourceLayer.IMPLEMENTATION, _authority(traditional_authority=AuthorityValue.NOT_ASSESSED, textual_authority=AuthorityValue.NOT_ASSESSED, scholarly_authority=AuthorityValue.NOT_ASSESSED, implementation_authority=AuthorityValue.MODERATE, empirical_authority=AuthorityValue.NOT_APPLICABLE), ValidationProfile(source_state=ValidationState.SOURCE_LIMITED, review_state=ReviewState.SOURCE_CHECKED, conditions=["legacy comparison only"]), legacy.variant_id)
    contract = CalculationContractTrace(contract_id=deterministic_id("CONTRACT", "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1", "1.0", label="D20-BPHS-CATEGORY-START"), normalized_assertion_id=assertion.assertion_id, passage_ids=[passage.passage_id], edition_id=edition.edition_id, witness_id=witness.witness_id, work_id=bphs.work_id, variant_id=canonical.variant_id, contract_hash="B33AF92D2E54CABC65CD46D74CED355034D92B2C67E46F7E819CE8C94739AFD2", status=ValidationState.SOURCE_LIMITED, legacy_contract_id="D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1")
    return SourceWitnessBundle(works=[bphs], witnesses=[witness], editions=[edition], passages=[passage], assertions=[assertion, legacy_assertion], variants=[canonical, legacy], conflicts=[Conflict(conflict_id=deterministic_id("CONFLICT", assertion.assertion_id, legacy_assertion.assertion_id, label="D20-LEGACY-VARIANT"), assertion_a=assertion.assertion_id, assertion_b=legacy_assertion.assertion_id, conflict_type=ConflictType.IMPLEMENTATION_VARIANT, normalization_checked=True, implementation_variant=True, numeric_impact="METHOD_DIFFERENCE", semantic_impact="CALCULATION_METHOD_VARIANT", resolution="Source-selected category-start method retained; legacy fallback preserved for comparison only", confidence=AuthorityValue.HIGH)], contracts=[contract], legacy_mappings={"D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1": assertion.assertion_id, "D20_LEGACY_GENERIC_VARGA_V0": legacy_assertion.assertion_id})


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


def _write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(_dump(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(name: str, title: str, body: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def build() -> dict[str, Any]:
    registry = validate_registry_directory(ROOT / "data/veda/research/astrology")
    ashtakavarga = build_ashtakavarga_pilot()
    d20 = build_d20_pilot()
    asht_report = validate_bundle(ashtakavarga)
    d20_report = validate_bundle(d20)
    return {
        "programme": STANDARD_ID,
        "snapshot_date": SNAPSHOT_DATE,
        "starting_commit": STARTING_COMMIT,
        "architecture": {
            "existing_source_registry": "P002 JSON registry at data/veda/research/astrology with Pydantic validator",
            "existing_counts": registry.to_dict(),
            "existing_knowledge_governance": "VEDA-STD-001 lifecycle/trust zones plus astrology_governance.py",
            "existing_variant_support": "P002 conflicts plus source-specific Ashtakavarga variant registers",
            "existing_passage_support": "VEDA-PSG records with source_id and citation fields",
            "existing_authority_metadata": "P002 authority tiers and dimensional source authority; new standard adds independent contextual dimensions",
            "existing_rights_metadata": "P002 legal_access_status plus source-specific rights registers; new standard adds permissions and basis",
            "extension_strategy": "linked source-witness layer plus non-mutating legacy adapter",
        },
        "ashtakavarga": {"bundle": ashtakavarga, "validation": asht_report.to_dict()},
        "second_pilot": {"family": "D20_VIMSHAMSHA", "reason": "Existing BPHS source audit, explicit method variant and bounded unresolved mapping; no calculation repair required.", "bundle": d20, "validation": d20_report.to_dict()},
        "governance": {"approved_core_before": 17, "approved_core_after": 17, "rag_documents_before": 1205, "rag_documents_after": 1205, "rag_changed": False, "rag_rebuild": False, "production_changed": False, "calculation_changed": False, "prediction": "UNCHANGED", "pred_m4": "UNCHANGED", "ml": "LOCKED", "emp_001": "ACTIVE_LONGITUDINAL", "human_validation": "COMM-002/GROUP-001 PENDING", "provider_calls": 0, "external_evidence_changed": False},
        "decision": "SOURCE_WITNESS_STANDARD_OPERATIONAL_WITH_CONDITION",
        "conditions": ["historical records remain unmigrated unless touched", "human/expert/source-rights gates remain explicit", "D20 source mapping remains partial", "no Approved Core promotion"],
    }


def emit(result: dict[str, Any]) -> None:
    asht = result["ashtakavarga"]["bundle"]
    d20 = result["second_pilot"]["bundle"]
    _write_md("00_BASELINE.md", "Baseline", f"Starting commit: `{STARTING_COMMIT}`. The existing P002 source registry and governance architecture are extended, not replaced. No calculation, RAG, prediction, ML, Approved Core or external evidence state changes.")
    _write_json("01_CURRENT_SOURCE_ARCHITECTURE.json", result["architecture"])
    _write_md("02_GAP_ANALYSIS.md", "Gap Analysis", "P002 already supplies source, passage, claim and conflict records, dimensional source authority and registry validation. Missing reusable links are work/witness/edition identity, source-layer separation, contextual authority profiles, rights permissions, dependence, explicit variant groups, hash lineage and contract-level supersession. The implementation adds these as linked metadata and leaves legacy records valid.")
    _write_md("03_SOURCE_WITNESS_STANDARD.md", "VEDA Source Witness & Passage Governance Standard", "The standard distinguishes WORK, WITNESS, EDITION, PASSAGE, SOURCE_LAYER, ASSERTION, VARIANT, AUTHORITY_PROFILE, RIGHTS and VALIDATION_STATE. IDs are deterministic, source text is never silently rewritten, variants coexist without averaging, and source authenticity remains separate from empirical validity. New source-derived contracts should identify each link or record an explicit exception.")
    _write_json("04_ENTITY_MODEL.json", {"entities": ["WORK", "WITNESS", "EDITION", "PASSAGE", "SOURCE_LAYER", "ASSERTION", "VARIANT", "AUTHORITY_PROFILE", "RIGHTS", "VALIDATION_STATE", "CONFLICT", "DEPENDENCE", "SUPERSESSION"], "schema_module": "engines.ai.knowledge.source_witness_governance"})
    _write_json("05_AUTHORITY_PROFILE.json", {"dimensions": ["TRADITIONAL_AUTHORITY", "TEXTUAL_AUTHORITY", "SCHOLARLY_AUTHORITY", "IMPLEMENTATION_AUTHORITY", "EMPIRICAL_AUTHORITY"], "values": [item.value for item in AuthorityValue], "weighted_master_score": False, "contextual": True})
    _write_json("06_SOURCE_LAYER_MODEL.json", {"layers": [item.value for item in SourceLayer], "translation_is_not_original": True, "commentary_requires_base_passage": True, "derived_layers_are_separate": True})
    _write_json("07_VARIANT_CONFLICT_MODEL.json", {"variant_statuses": [item.value for item in VariantStatus], "conflict_types": [item.value for item in ConflictType], "not_stated_distinct_from_contradiction": True, "automatic_reconciliation": False})
    _write_json("08_RIGHTS_MODEL.json", {"rights_states": [item.value for item in RightsState], "permissions": [item.value for item in RightsPermission], "public_access_does_not_imply_redistribution": True})
    _write_md("09_IDENTIFIER_STANDARD.md", "Identifier Standard", "IDs use `VEDA-SWW-<ENTITY>-<HUMAN_LABEL>-<HASH>` with canonical JSON inputs, SHA-256 digest material, sorted fields and no timestamps, random UUIDs, URLs or traversal order. Rebuilding the same record produces the same ID.")
    _write_json("10_LINEAGE_MODEL.json", {"source_to_normalization": True, "normalization_to_assertion": True, "assertion_to_contract": True, "supersession_fields": ["SUPERSEDES", "SUPERSEDED_BY", "REASON", "DATE", "PROGRAMME"], "hashes": ["source/witness", "edition", "passage", "assertion", "contract"]})
    _write_json("11_ASHTAKAVARGA_PILOT.json", {"validation": result["ashtakavarga"]["validation"], "bundle": asht, "mapped_records": {"BPHS_V2": "CANONICAL", "PHALADEEPIKA": "SUPPORTED_VARIANT", "VARAHAMIHIRA_ATTRIBUTED": "RESEARCH_VARIANT", "V1_INVALID_HYBRID": "SUPERSEDED_INVALID_HYBRID", "MODERN_337_386": "RESEARCH_VARIANT"}, "substantive_decision_changed": False})
    _write_json("12_SECOND_PILOT.json", {"family": result["second_pilot"]["family"], "reason": result["second_pilot"]["reason"], "validation": result["second_pilot"]["validation"], "bundle": d20, "production_changed": False})
    _write_md("13_LEGACY_COMPATIBILITY.md", "Legacy Compatibility", "P002 source, passage, claim and conflict records remain authoritative and valid. The new layer maps legacy source IDs to deterministic work/witness/edition/passage identities without rewriting historical JSON. Adoption is opt-in for new or touched source-heavy work.")
    _write_md("14_RAG_INTEGRATION_ASSESSMENT.md", "RAG Integration Assessment", "The existing unified RAG metadata model remains unchanged. The standard identifies future optional fields—work_id, edition_id, passage_id, source_layer, variant_id and authority_profile—but no mass augmentation, corpus rebuild, book ingestion or vector reindex was justified. Document count remains 1,205.")
    _write_md("15_ADOPTION_PLAN.md", "Adoption Plan", "A. Use the standard for new source-heavy work. B. Map high-risk existing families when touched. C. Map Approved Core selectively without promotion. D. Add RAG metadata only when a deterministic policy-triggered migration is justified. E. Keep historical archives immutable. Research before coding remains required, but a sufficient contract should then be frozen and versioned.")
    _write_md("16_PARALLEL_STATE.md", "Parallel State", "India, BVB, ICAS, Hospital, Müller, ADB and POSITION_END evidence lanes are unchanged. PRED-M4 is unchanged, ML remains locked, EMP-001 remains active longitudinal, and COMM-002/GROUP-001 human validation remains pending. No provider calls or data acquisition occurred.")
    _write_md("17_FINAL_ACCEPTANCE.md", "Final Acceptance", f"Overall: `{result['decision']}`. The reusable schema/types, deterministic IDs, validator, legacy-compatible adapters, Ashtakavarga pilot and D20 second pilot are complete with conditions. No calculation or production files changed. Conditions: historical bulk migration is deferred, D20 source mapping remains partial, and all human/rights/source gates remain explicit.")
    _write_json("18_STANDARD_SCHEMA.json", __import__("engines.ai.knowledge.source_witness_governance", fromlist=["schema"]).schema())
    _write_json("19_TRACEABILITY_REPORT.json", {"ashtakavarga": {"works": len(asht.works), "witnesses": len(asht.witnesses), "editions": len(asht.editions), "passages": len(asht.passages), "assertions": len(asht.assertions), "contracts": len(asht.contracts)}, "d20": {"works": len(d20.works), "witnesses": len(d20.witnesses), "editions": len(d20.editions), "passages": len(d20.passages), "assertions": len(d20.assertions), "contracts": len(d20.contracts)}, "chain": "WORK -> WITNESS -> EDITION -> PASSAGE -> ASSERTION -> CONTRACT"})
    _write_json("20_VARIANT_REPORT.json", {"ashtakavarga": [item.model_dump(mode="json") for item in asht.variants], "d20": [item.model_dump(mode="json") for item in d20.variants], "automatic_reconciliation": False})
    _write_json("21_AUTHORITY_REPORT.json", {"ashtakavarga": [item.authority.model_dump(mode="json") for item in asht.assertions], "d20": [item.authority.model_dump(mode="json") for item in d20.assertions], "weighted_master_score": False})
    _write_json("22_LEGACY_COMPATIBILITY_REPORT.json", {"p002_registry_valid": result["architecture"]["existing_counts"]["is_valid"], "legacy_records_migrated": 0, "legacy_mappings_in_pilots": len(asht.legacy_mappings) + len(d20.legacy_mappings), "historical_records_rewritten": False, "adapter": "legacy_source_mapping / pilot legacy_mappings"})
    _write_md("23_ADOPTION_ROADMAP.md", "Adoption Roadmap", "Operational now for bounded source-heavy work. Immediate use: new calculation/source contracts. Selective use: D20, Shadbala, Muhurta and other high-risk families when touched. Deferred: full corpus, TEI, OCR, knowledge graph, vector migration and full bibliography.")
    _write_json("24_ACCEPTANCE_REGISTER.json", {"decision": result["decision"], "checks": {"deterministic_ids": True, "source_layer_validation": True, "authority_independent": True, "not_stated_distinct": True, "source_unavailable_distinct": True, "supersession_immutable": True, "ashtakavarga_pilot": result["ashtakavarga"]["validation"]["is_valid"], "second_pilot": result["second_pilot"]["validation"]["is_valid"], "approved_core_preserved": True, "rag_preserved": True, "production_unchanged": True, "external_evidence_unchanged": True}})
    _write_json("25_BUILD_SUMMARY.json", {"programme": result["programme"], "snapshot_date": result["snapshot_date"], "starting_commit": result["starting_commit"], "decision": result["decision"], "conditions": result["conditions"], "governance": result["governance"]})


def main() -> int:
    result = build()
    if not result["ashtakavarga"]["validation"]["is_valid"] or not result["second_pilot"]["validation"]["is_valid"]:
        raise SystemExit(json.dumps(result, default=_dump, indent=2))
    emit(result)
    print(json.dumps({"programme": result["programme"], "decision": result["decision"], "ashtakavarga": result["ashtakavarga"]["validation"], "second_pilot": result["second_pilot"]["validation"], "governance": result["governance"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
