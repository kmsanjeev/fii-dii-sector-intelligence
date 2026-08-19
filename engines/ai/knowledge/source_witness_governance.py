"""Reusable source -> witness -> passage -> assertion governance.

This module extends the existing P002 astrology registry without replacing it.
It is intentionally metadata-only: it does not ingest books, perform source
research, alter calculation contracts, or promote knowledge.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


ID_RE = re.compile(r"^VEDA-SWW-(WORK|WITNESS|EDITION|PASSAGE|ASSERTION|VARIANT|CONFLICT|CONTRACT)-[A-Z0-9-]+$")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any, length: int = 12) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest().upper()[:length]


def _slug(value: str, limit: int = 34) -> str:
    text = re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")
    return (text or "UNSPECIFIED")[:limit].strip("-")


def deterministic_id(kind: str, *parts: Any, label: str | None = None) -> str:
    kind = kind.upper()
    if kind not in {"WORK", "WITNESS", "EDITION", "PASSAGE", "ASSERTION", "VARIANT", "CONFLICT", "CONTRACT"}:
        raise ValueError(f"unsupported source-witness entity kind: {kind}")
    payload = {"kind": kind, "parts": parts}
    prefix = _slug(label or str(parts[0] if parts else "UNSPECIFIED"))
    return f"VEDA-SWW-{kind}-{prefix}-{stable_digest(payload)}"


class SourceLayer(str, Enum):
    ORIGINAL_TEXT = "ORIGINAL_TEXT"
    DIPLOMATIC_TRANSCRIPTION = "DIPLOMATIC_TRANSCRIPTION"
    NORMALIZED_TEXT = "NORMALIZED_TEXT"
    TRANSLITERATION = "TRANSLITERATION"
    TRANSLATION = "TRANSLATION"
    COMMENTARY = "COMMENTARY"
    NORMALIZATION = "NORMALIZATION"
    PRACTITIONER = "PRACTITIONER"
    SCHOLARLY = "SCHOLARLY"
    IMPLEMENTATION = "IMPLEMENTATION"
    EMPIRICAL = "EMPIRICAL"


class ClaimType(str, Enum):
    TEXTUAL_ASSERTION = "TEXTUAL_ASSERTION"
    COMMENTARY_ASSERTION = "COMMENTARY_ASSERTION"
    PRACTITIONER_ASSERTION = "PRACTITIONER_ASSERTION"
    SCHOLARLY_ASSERTION = "SCHOLARLY_ASSERTION"
    CALCULATION_RULE = "CALCULATION_RULE"
    IMPLEMENTATION_NOTE = "IMPLEMENTATION_NOTE"
    EMPIRICAL_FINDING = "EMPIRICAL_FINDING"
    SYSTEM_INFERENCE = "SYSTEM_INFERENCE"


class SourceAccessState(str, Enum):
    AVAILABLE = "AVAILABLE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    FULL_TEXT_UNAVAILABLE = "FULL_TEXT_UNAVAILABLE"
    BIBLIOGRAPHIC_ONLY = "BIBLIOGRAPHIC_ONLY"
    PARTIAL_TEXT = "PARTIAL_TEXT"
    RIGHTS_RESTRICTED = "RIGHTS_RESTRICTED"


class RightsState(str, Enum):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    OPEN_LICENSE = "OPEN_LICENSE"
    LICENSED = "LICENSED"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"
    EXCLUDED = "EXCLUDED"


class RightsPermission(str, Enum):
    VIEW_ALLOWED = "VIEW_ALLOWED"
    LOCAL_RESEARCH_ALLOWED = "LOCAL_RESEARCH_ALLOWED"
    QUOTATION_ALLOWED = "QUOTATION_ALLOWED"
    DERIVED_METADATA_ALLOWED = "DERIVED_METADATA_ALLOWED"
    REDISTRIBUTION_ALLOWED = "REDISTRIBUTION_ALLOWED"


class AuthorityValue(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ValidationState(str, Enum):
    SOURCE_LOCATED = "SOURCE_LOCATED"
    SOURCE_IDENTIFIED = "SOURCE_IDENTIFIED"
    WITNESS_IDENTIFIED = "WITNESS_IDENTIFIED"
    PASSAGE_MAPPED = "PASSAGE_MAPPED"
    NORMALIZED = "NORMALIZED"
    VARIANTS_RECONCILED = "VARIANTS_RECONCILED"
    CONTRACT_FROZEN = "CONTRACT_FROZEN"
    IMPLEMENTED = "IMPLEMENTED"
    INTERNALLY_VALIDATED = "INTERNALLY_VALIDATED"
    EXTERNALLY_NUMERICALLY_VALIDATED = "EXTERNALLY_NUMERICALLY_VALIDATED"
    SOURCE_LIMITED = "SOURCE_LIMITED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SUPERSEDED = "SUPERSEDED"


class ReviewState(str, Enum):
    AUTOMATED_EXTRACTED = "AUTOMATED_EXTRACTED"
    SOURCE_CHECKED = "SOURCE_CHECKED"
    EXPERT_REVIEWED = "EXPERT_REVIEWED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    NOT_REVIEWED = "NOT_REVIEWED"


class DependenceState(str, Enum):
    POTENTIALLY_INDEPENDENT = "POTENTIALLY_INDEPENDENT"
    PARTIALLY_DEPENDENT = "PARTIALLY_DEPENDENT"
    LATER_SYNTHESIS = "LATER_SYNTHESIS"
    DERIVATIVE = "DERIVATIVE"
    UNKNOWN = "UNKNOWN"


class VariantStatus(str, Enum):
    CANONICAL = "CANONICAL"
    SUPPORTED_VARIANT = "SUPPORTED_VARIANT"
    RESEARCH_VARIANT = "RESEARCH_VARIANT"
    LEGACY_VARIANT = "LEGACY_VARIANT"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED_INVALID_HYBRID = "SUPERSEDED_INVALID_HYBRID"


class ConflictType(str, Enum):
    NOT_STATED = "NOT_STATED"
    CONTRADICTION = "CONTRADICTION"
    TRANSLATION_VARIANCE = "TRANSLATION_VARIANCE"
    TEXTUAL_VARIANT = "TEXTUAL_VARIANT"
    IMPLEMENTATION_VARIANT = "IMPLEMENTATION_VARIANT"
    DIFFERENT_SCOPE = "DIFFERENT_SCOPE"
    UNRESOLVED = "UNRESOLVED"


class SupersessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class WitnessBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RightsProfile(WitnessBase):
    rights_state: RightsState = RightsState.UNKNOWN
    permissions: list[RightsPermission] = Field(default_factory=list)
    basis: str | None = None


class AuthorityProfile(WitnessBase):
    traditional_authority: AuthorityValue = AuthorityValue.NOT_ASSESSED
    textual_authority: AuthorityValue = AuthorityValue.NOT_ASSESSED
    scholarly_authority: AuthorityValue = AuthorityValue.NOT_ASSESSED
    implementation_authority: AuthorityValue = AuthorityValue.NOT_ASSESSED
    empirical_authority: AuthorityValue = AuthorityValue.NOT_ASSESSED
    notes: str | None = None


class Work(WitnessBase):
    work_id: str
    canonical_title: str
    alternate_titles: list[str] = Field(default_factory=list)
    traditional_author: str | None = None
    tradition: str | None = None
    approximate_period: str | None = None
    period_confidence: str | None = None
    work_type: str
    language_origin: str | None = None
    notes: str | None = None
    legacy_source_ids: list[str] = Field(default_factory=list)


class Witness(WitnessBase):
    witness_id: str
    work_id: str
    witness_type: str
    repository_or_library: str | None = None
    locator: str | None = None
    date_or_period: str | None = None
    script: str | None = None
    language: str | None = None
    completeness: str | None = None
    physical_or_digital: str | None = None
    provenance: str | None = None
    dependence_notes: str | None = None
    dependence_state: DependenceState = DependenceState.UNKNOWN
    witness_hash: str | None = None
    source_access: SourceAccessState = SourceAccessState.AVAILABLE
    rights: RightsProfile = Field(default_factory=RightsProfile)
    review_state: ReviewState = ReviewState.NOT_REVIEWED
    legacy_source_id: str | None = None


class Edition(WitnessBase):
    edition_id: str
    work_id: str
    witness_ids: list[str] = Field(default_factory=list)
    editor: str | None = None
    translator: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    edition_title: str | None = None
    language: str | None = None
    script: str | None = None
    bibliographic_identifier: str | None = None
    digital_locator: str | None = None
    source_type: str | None = None
    rights: RightsProfile = Field(default_factory=RightsProfile)
    completeness: str | None = None
    editorial_notes: str | None = None
    edition_hash: str | None = None


class Passage(WitnessBase):
    passage_id: str
    edition_id: str
    chapter: str | None = None
    section: str | None = None
    verse: str | None = None
    page: str | None = None
    line: str | None = None
    table: str | None = None
    source_locator: str
    source_layer: SourceLayer
    language: str | None = None
    text_hash: str | None = None
    citation_label: str
    original_text: str | None = None
    derived_text: str | None = None
    base_passage_id: str | None = None
    source_access: SourceAccessState = SourceAccessState.AVAILABLE
    rights: RightsProfile = Field(default_factory=RightsProfile)
    review_state: ReviewState = ReviewState.NOT_REVIEWED


class ValidationProfile(WitnessBase):
    source_state: ValidationState
    review_state: ReviewState = ReviewState.NOT_REVIEWED
    empirical_state: str = "UNTESTED"
    production_activation: bool = False
    approved_core_eligible: bool = False
    conditions: list[str] = Field(default_factory=list)


class Assertion(WitnessBase):
    assertion_id: str
    assertion_group: str
    passage_ids: list[str] = Field(default_factory=list)
    claim_type: ClaimType
    statement: str
    normalized_statement: str
    normalization_method: str | None = None
    source_layer: SourceLayer
    variant_id: str | None = None
    authority: AuthorityProfile
    validation: ValidationProfile
    parent_assertion_ids: list[str] = Field(default_factory=list)
    assertion_hash: str | None = None


class Variant(WitnessBase):
    variant_id: str
    assertion_group: str
    source_family: str
    source_passage_ids: list[str] = Field(default_factory=list)
    difference: str
    normalization_attempted: bool = False
    mathematical_or_semantic_impact: str
    resolution_state: str
    canonical_status: VariantStatus
    canonical_for_purpose: str | None = None
    supersedes_variant_id: str | None = None


class Conflict(WitnessBase):
    conflict_id: str
    assertion_a: str
    assertion_b: str
    conflict_type: ConflictType
    normalization_checked: bool = False
    translation_issue: bool = False
    indexing_issue: bool = False
    textual_variant: bool = False
    implementation_variant: bool = False
    numeric_impact: str = "NOT_STATED"
    semantic_impact: str = "NOT_STATED"
    resolution: str
    confidence: AuthorityValue = AuthorityValue.NOT_ASSESSED


class CalculationContractTrace(WitnessBase):
    contract_id: str
    normalized_assertion_id: str
    passage_ids: list[str] = Field(default_factory=list)
    edition_id: str
    witness_id: str
    work_id: str
    variant_id: str | None = None
    contract_hash: str | None = None
    status: ValidationState
    supersession_status: SupersessionStatus = SupersessionStatus.ACTIVE
    legacy_contract_id: str | None = None


class Supersession(WitnessBase):
    superseded_id: str
    superseding_id: str
    reason: str
    date: str
    programme: str


class SourceWitnessBundle(WitnessBase):
    standard_id: str = "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
    standard_version: str = "1.0.0"
    works: list[Work] = Field(default_factory=list)
    witnesses: list[Witness] = Field(default_factory=list)
    editions: list[Edition] = Field(default_factory=list)
    passages: list[Passage] = Field(default_factory=list)
    assertions: list[Assertion] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    contracts: list[CalculationContractTrace] = Field(default_factory=list)
    supersessions: list[Supersession] = Field(default_factory=list)
    legacy_mappings: dict[str, str] = Field(default_factory=dict)


@dataclass(slots=True)
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {"errors": self.errors, "warnings": self.warnings, "is_valid": self.is_valid}

    def assert_valid(self) -> None:
        if self.errors:
            raise ValueError("Source-witness validation failed: " + "; ".join(self.errors))


def _index(items: Iterable[WitnessBase], field_name: str) -> tuple[dict[str, WitnessBase], list[str]]:
    result: dict[str, WitnessBase] = {}
    errors: list[str] = []
    for item in items:
        identifier = getattr(item, field_name)
        if identifier in result:
            errors.append(f"duplicate {field_name}: {identifier}")
        result[identifier] = item
    return result, errors


def validate_bundle(bundle: SourceWitnessBundle) -> ValidationReport:
    report = ValidationReport()
    if not bundle.works and any(
        (
            bundle.witnesses,
            bundle.editions,
            bundle.passages,
            bundle.assertions,
            bundle.variants,
            bundle.conflicts,
            bundle.contracts,
            bundle.supersessions,
        )
    ):
        report.errors.append("work required for linked source-witness entities")
    works, errors = _index(bundle.works, "work_id")
    report.errors.extend(errors)
    witnesses, errors = _index(bundle.witnesses, "witness_id")
    report.errors.extend(errors)
    editions, errors = _index(bundle.editions, "edition_id")
    report.errors.extend(errors)
    passages, errors = _index(bundle.passages, "passage_id")
    report.errors.extend(errors)
    assertions, errors = _index(bundle.assertions, "assertion_id")
    report.errors.extend(errors)
    variants, errors = _index(bundle.variants, "variant_id")
    report.errors.extend(errors)
    conflicts, errors = _index(bundle.conflicts, "conflict_id")
    report.errors.extend(errors)
    contracts, errors = _index(bundle.contracts, "contract_id")
    report.errors.extend(errors)

    for work in works.values():
        if not work.canonical_title.strip():
            report.errors.append(f"{work.work_id}: canonical title is required")
    for witness in witnesses.values():
        if witness.work_id not in works:
            report.errors.append(f"{witness.witness_id}: unknown work {witness.work_id}")
    for edition in editions.values():
        if edition.work_id not in works:
            report.errors.append(f"{edition.edition_id}: unknown work {edition.work_id}")
        for witness_id in edition.witness_ids:
            if witness_id not in witnesses:
                report.errors.append(f"{edition.edition_id}: unknown witness {witness_id}")
    for passage in passages.values():
        if passage.edition_id not in editions:
            report.errors.append(f"{passage.passage_id}: unknown edition {passage.edition_id}")
        if passage.source_layer == SourceLayer.TRANSLATION and passage.original_text:
            report.errors.append(f"{passage.passage_id}: translation cannot impersonate original text")
        if passage.source_layer == SourceLayer.COMMENTARY and not passage.base_passage_id:
            report.errors.append(f"{passage.passage_id}: commentary requires base_passage_id")
        if passage.base_passage_id and passage.base_passage_id not in passages:
            report.errors.append(f"{passage.passage_id}: unknown base passage {passage.base_passage_id}")
        if passage.source_access != SourceAccessState.AVAILABLE and passage.rights.rights_state == RightsState.UNKNOWN:
            report.warnings.append(f"{passage.passage_id}: source access is limited and rights remain UNKNOWN")
    for assertion in assertions.values():
        for passage_id in assertion.passage_ids:
            if passage_id not in passages:
                report.errors.append(f"{assertion.assertion_id}: unknown passage {passage_id}")
        for parent_id in assertion.parent_assertion_ids:
            if parent_id not in assertions:
                report.errors.append(f"{assertion.assertion_id}: unknown parent assertion {parent_id}")
        if assertion.variant_id:
            if assertion.variant_id not in variants:
                report.errors.append(f"{assertion.assertion_id}: unknown variant {assertion.variant_id}")
            elif variants[assertion.variant_id].assertion_group != assertion.assertion_group:
                report.errors.append(f"{assertion.assertion_id}: variant belongs to another assertion group")
    groups: dict[str, list[Variant]] = {}
    for variant in variants.values():
        groups.setdefault(variant.assertion_group, []).append(variant)
        for passage_id in variant.source_passage_ids:
            if passage_id not in passages:
                report.errors.append(f"{variant.variant_id}: unknown source passage {passage_id}")
    for group, group_variants in groups.items():
        active = [item for item in group_variants if item.canonical_status != VariantStatus.UNRESOLVED]
        canonical = [item for item in group_variants if item.canonical_status == VariantStatus.CANONICAL]
        if active and len(canonical) != 1:
            report.errors.append(f"{group}: canonical variant selection must be explicit and unique")
    for conflict in bundle.conflicts:
        if conflict.assertion_a not in assertions:
            report.errors.append(f"{conflict.conflict_id}: unknown assertion_a {conflict.assertion_a}")
        if conflict.assertion_b not in assertions:
            report.errors.append(f"{conflict.conflict_id}: unknown assertion_b {conflict.assertion_b}")
        if conflict.conflict_type == ConflictType.NOT_STATED and conflict.resolution.upper() == "CONTRADICTION":
            report.errors.append(f"{conflict.conflict_id}: NOT_STATED cannot be labelled CONTRADICTION")
    valid_ids = set(works) | set(witnesses) | set(editions) | set(passages) | set(assertions) | set(variants) | set(conflicts) | set(contracts)
    for contract in contracts.values():
        if contract.normalized_assertion_id not in assertions:
            report.errors.append(f"{contract.contract_id}: unknown assertion {contract.normalized_assertion_id}")
        if contract.edition_id not in editions or contract.witness_id not in witnesses or contract.work_id not in works:
            report.errors.append(f"{contract.contract_id}: incomplete contract lineage")
        for passage_id in contract.passage_ids:
            if passage_id not in passages:
                report.errors.append(f"{contract.contract_id}: unknown passage {passage_id}")
        if contract.variant_id and contract.variant_id not in variants:
            report.errors.append(f"{contract.contract_id}: unknown variant {contract.variant_id}")
        elif contract.variant_id and assertions.get(contract.normalized_assertion_id) and variants[contract.variant_id].assertion_group != assertions[contract.normalized_assertion_id].assertion_group:
            report.errors.append(f"{contract.contract_id}: variant does not belong to contract assertion group")
    for link in bundle.supersessions:
        if link.superseded_id not in valid_ids or link.superseding_id not in valid_ids:
            report.errors.append(f"supersession: unknown artifact {link.superseded_id} or {link.superseding_id}")
        if link.superseded_id == link.superseding_id:
            report.errors.append(f"supersession: self-supersession is invalid for {link.superseded_id}")
        if not link.reason.strip() or not link.programme.strip():
            report.errors.append("supersession: reason and programme are required")
    return report


def legacy_source_mapping(source_id: str, title: str) -> dict[str, str]:
    """Return a non-mutating mapping for a P002 source record."""
    work_id = deterministic_id("WORK", title, label=title)
    return {"legacy_source_id": source_id, "work_id": work_id, "mapping_state": "LEGACY_COMPATIBLE"}


def schema() -> dict[str, Any]:
    """Return the machine-readable Pydantic schema for the reusable bundle."""
    return SourceWitnessBundle.model_json_schema()


__all__ = [
    "Assertion", "AuthorityProfile", "AuthorityValue", "CalculationContractTrace", "ClaimType", "Conflict",
    "ConflictType", "DependenceState", "Edition", "Passage", "RightsPermission", "RightsProfile", "RightsState",
    "ReviewState", "SourceAccessState", "SourceLayer", "SourceWitnessBundle", "Supersession", "SupersessionStatus",
    "ValidationProfile", "ValidationReport", "ValidationState", "Variant", "VariantStatus", "Witness", "Work",
    "deterministic_id", "legacy_source_mapping", "schema", "stable_digest", "validate_bundle",
]
