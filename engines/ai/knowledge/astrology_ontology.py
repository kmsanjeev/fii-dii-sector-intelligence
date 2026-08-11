from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engines.ai.knowledge.astrology_governance import (
    AllowedOutputMode,
    ApprovalStatus,
    EvidenceType,
    SourceClass,
    load_registry as load_governance_registry,
)
from engines.common import config as cfg

CONTRACT_VERSION = getattr(cfg, "VEDA_ASTROLOGY_ONTOLOGY_VERSION", "2026-08-10")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
_ENTITY_ID_RE = re.compile(r"^VEDA-[A-Z]+-[A-Z0-9_]+(?:-[A-Z0-9_]+)*$")
_RELATION_ID_RE = re.compile(r"^VEDA-REL-\d{6}$")
_RULE_ID_RE = re.compile(r"^VEDA-RUL-[A-Z0-9_]+-\d{6}$")
_LEGACY_MAPPING_ID_RE = re.compile(r"^VEDA-LMP-\d{6}$")
_EVALUATION_ID_RE = re.compile(r"^VEDA-EVL-\d{6}$")

_DEFAULT_TS = "2026-08-10T00:00:00Z"
_DEFAULT_ACTOR = "codex"


def _is_iso_datetime(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if not _ISO_TS_RE.match(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class EntityType(str, Enum):
    GRAHA = "GRAHA"
    RASHI = "RASHI"
    BHAVA = "BHAVA"
    NAKSHATRA = "NAKSHATRA"
    VARGA = "VARGA"
    DASHA = "DASHA"
    RELATIONSHIP = "RELATIONSHIP"
    DIGNITY = "DIGNITY"
    DOMAIN = "DOMAIN"
    HOUSE_CLASSIFICATION = "HOUSE_CLASSIFICATION"
    YOGA = "YOGA"
    DOSHA = "DOSHA"
    KARAKA = "KARAKA"
    AYANAMSHA = "AYANAMSHA"
    LAGNA = "LAGNA"
    TIMING = "TIMING"


class OntologyRecordStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PILOT = "PILOT"
    DEPRECATED = "DEPRECATED"


class EntitySourceStatus(str, Enum):
    CURATED_CANONICAL = "CURATED_CANONICAL"
    SOURCE_VALIDATED = "SOURCE_VALIDATED"
    LEGACY_UNGOVERNED = "LEGACY_UNGOVERNED"
    UNKNOWN = "UNKNOWN"


class RelationType(str, Enum):
    OCCUPIES = "OCCUPIES"
    RULES = "RULES"
    ASPECTS = "ASPECTS"
    RECEIVES_ASPECT = "RECEIVES_ASPECT"
    BELONGS_TO_DOMAIN = "BELONGS_TO_DOMAIN"
    SPECIALIZES = "SPECIALIZES"
    PART_OF = "PART_OF"
    NEXT_IN_SEQUENCE = "NEXT_IN_SEQUENCE"
    CLASSIFIES = "CLASSIFIES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"


class OperandKind(str, Enum):
    ENTITY = "ENTITY"
    FACT_PATH = "FACT_PATH"
    RULE = "RULE"
    CLAIM = "CLAIM"
    PASSAGE = "PASSAGE"
    SOURCE = "SOURCE"
    CONFLICT = "CONFLICT"
    LITERAL = "LITERAL"


class ConditionOperator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    BETWEEN = "BETWEEN"
    OCCUPIES = "OCCUPIES"
    RULES = "RULES"
    ASPECTS = "ASPECTS"
    CONJUNCT = "CONJUNCT"
    EXCHANGES = "EXCHANGES"
    RECEIVES_ASPECT = "RECEIVES_ASPECT"
    EXALTED = "EXALTED"
    DEBILITATED = "DEBILITATED"
    OWN_SIGN = "OWN_SIGN"
    MOOLATRIKONA = "MOOLATRIKONA"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"


class RuleType(str, Enum):
    FOUNDATIONAL_ALGORITHM = "FOUNDATIONAL_ALGORITHM"
    DASHA = "DASHA"
    DIGNITY = "DIGNITY"
    YOGA = "YOGA"
    DOSHA = "DOSHA"
    INTERPRETATION = "INTERPRETATION"
    ASTROFINANCE_HYPOTHESIS = "ASTROFINANCE_HYPOTHESIS"


class RuleLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    RESEARCHING = "RESEARCHING"
    SOURCE_VALIDATED = "SOURCE_VALIDATED"
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"
    IMPLEMENTED = "IMPLEMENTED"
    VALIDATED = "VALIDATED"
    DEPRECATED = "DEPRECATED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class ModifierType(str, Enum):
    AMPLIFY = "AMPLIFY"
    REDUCE = "REDUCE"
    SUPPRESS = "SUPPRESS"
    CANCEL = "CANCEL"
    ACTIVATE = "ACTIVATE"
    CONFIRM = "CONFIRM"
    ANNOTATE = "ANNOTATE"


class ConfirmationSource(str, Enum):
    D1 = "D1"
    VARGA = "VARGA"
    DASHA = "DASHA"
    TRANSIT = "TRANSIT"
    KARAKA = "KARAKA"
    HOUSE_LORD = "HOUSE_LORD"
    YOGA = "YOGA"


class OutcomeType(str, Enum):
    CLASSIFICATION = "CLASSIFICATION"
    DETECTION = "DETECTION"
    TIMING = "TIMING"
    SIGNAL = "SIGNAL"
    EXPLANATION = "EXPLANATION"
    CONTRACT_METADATA = "CONTRACT_METADATA"


class LegacyMappingStatus(str, Enum):
    LEGACY_UNSOURCED = "LEGACY_UNSOURCED"
    LEGACY_PARTIALLY_SOURCED = "LEGACY_PARTIALLY_SOURCED"
    SOURCE_VALIDATED = "SOURCE_VALIDATED"
    MAPPED_TO_SCHEMA = "MAPPED_TO_SCHEMA"
    MIGRATED = "MIGRATED"
    SUPERSEDED = "SUPERSEDED"


class SemanticMatch(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    APPROXIMATE = "APPROXIMATE"
    DIVERGENT = "DIVERGENT"


class ContractChartType(str, Enum):
    PERSONAL_KUNDLI = "PERSONAL_KUNDLI"
    STOCK_KUNDLI = "STOCK_KUNDLI"
    COUNTRY_KUNDLI = "COUNTRY_KUNDLI"
    GENERIC = "GENERIC"


class VersionedAstrologyArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "1.0.0"
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str
    change_reason: str
    supersedes: str | None = None
    superseded_by: str | None = None
    notes: str | None = None
    contract_version: str = CONTRACT_VERSION

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not _SEMVER_RE.fullmatch(value):
            raise ValueError("version must use semantic version format such as 1.0.0")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_datetime(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value

    @field_validator("created_by", "updated_by", "change_reason")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("field must be a non-empty string")
        return value.strip()


class EntityRecord(VersionedAstrologyArtifact):
    entity_id: str
    canonical_name: str
    entity_type: EntityType
    sanskrit_name: str | None = None
    transliteration: str | None = None
    aliases: list[str] = Field(default_factory=list)
    description: str
    source_status: EntitySourceStatus = EntitySourceStatus.CURATED_CANONICAL
    deprecated_aliases: list[str] = Field(default_factory=list)
    status: OntologyRecordStatus = OntologyRecordStatus.ACTIVE

    @field_validator("entity_id")
    @classmethod
    def _validate_entity_id(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("entity_id must use a stable VEDA identifier")
        return value

    @field_validator("canonical_name", "description")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("field is required")
        return value.strip()

    @field_validator("aliases", "deprecated_aliases")
    @classmethod
    def _normalize_aliases(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
        return normalized


class RelationRecord(VersionedAstrologyArtifact):
    relation_id: str
    subject_entity_id: str
    relation_type: RelationType
    object_entity_id: str
    description: str
    source_status: EntitySourceStatus = EntitySourceStatus.CURATED_CANONICAL
    status: OntologyRecordStatus = OntologyRecordStatus.ACTIVE

    @field_validator("relation_id")
    @classmethod
    def _validate_relation_id(cls, value: str) -> str:
        if not _RELATION_ID_RE.fullmatch(value):
            raise ValueError("relation_id must match VEDA-REL-000001")
        return value

    @field_validator("subject_entity_id", "object_entity_id")
    @classmethod
    def _validate_entity_ref(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("entity references must use stable VEDA identifiers")
        return value

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description is required")
        return value.strip()


class OperandReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    ref_type: OperandKind
    property_name: str | None = None

    @field_validator("ref")
    @classmethod
    def _validate_ref(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("operand reference is required")
        return value.strip()

    @field_validator("property_name")
    @classmethod
    def _validate_property_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _validate_fact_path_shape(self) -> "OperandReference":
        if self.ref_type == OperandKind.FACT_PATH and not self.ref.startswith("chart."):
            raise ValueError("FACT_PATH operands must begin with chart.")
        return self


class ConditionNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_id: str | None = None
    subject: OperandReference | None = None
    operator: ConditionOperator | None = None
    object: OperandReference | None = None
    value: Any | None = None
    value_entity_id: str | None = None
    value_entity_ids: list[str] = Field(default_factory=list)
    all: list["ConditionNode"] = Field(default_factory=list)
    any: list["ConditionNode"] = Field(default_factory=list)
    none: list["ConditionNode"] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("condition_id")
    @classmethod
    def _validate_condition_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("condition_id cannot be blank")
        return cleaned

    @field_validator("value_entity_id")
    @classmethod
    def _validate_value_entity_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("value_entity_id must use a stable VEDA identifier")
        return value

    @field_validator("value_entity_ids")
    @classmethod
    def _validate_value_entity_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _ENTITY_ID_RE.fullmatch(item):
                raise ValueError("value_entity_ids must use stable VEDA identifiers")
        return value

    @model_validator(mode="after")
    def _validate_condition_shape(self) -> "ConditionNode":
        has_nested = bool(self.all or self.any or self.none)
        has_atomic = any(
            item is not None and item != []
            for item in (self.subject, self.operator, self.object, self.value, self.value_entity_id, self.value_entity_ids)
        )

        if has_nested and has_atomic:
            raise ValueError("conditions may be either atomic or nested groups, not both at once")
        if not has_nested and not has_atomic:
            raise ValueError("condition must define either nested groups or an atomic condition")
        if has_nested:
            return self
        if self.subject is None or self.operator is None:
            raise ValueError("atomic conditions require subject and operator")
        if self.object is None and self.value is None and self.value_entity_id is None and not self.value_entity_ids:
            raise ValueError("atomic conditions require object, value, value_entity_id, or value_entity_ids")
        return self


class RuleConditionSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    all: list[ConditionNode] = Field(default_factory=list)
    any: list[ConditionNode] = Field(default_factory=list)
    none: list[ConditionNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_condition_set(self) -> "RuleConditionSet":
        if not (self.all or self.any or self.none):
            raise ValueError("conditions must include at least one all, any, or none entry")
        return self


class ModifierEffect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ModifierType
    weight: float | None = None
    value: Any | None = None
    note: str | None = None


class RuleModifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modifier_id: str
    condition: ConditionNode
    effect: ModifierEffect

    @field_validator("modifier_id")
    @classmethod
    def _validate_modifier_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("modifier_id is required")
        return value.strip()


class ExceptionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suppress_rule: bool = False
    override_value: Any | None = None
    note: str | None = None


class RuleException(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exception_id: str
    conditions: ConditionNode
    result: ExceptionResult

    @field_validator("exception_id")
    @classmethod
    def _validate_exception_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("exception_id is required")
        return value.strip()


class RuleConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_id: str
    source: ConfirmationSource
    description: str
    condition: ConditionNode

    @field_validator("confirmation_id", "description")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()


class RuleActivation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activation_id: str
    activation_type: str
    description: str
    condition: ConditionNode

    @field_validator("activation_id", "activation_type", "description")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()


class RuleAuthorityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    textual: int = Field(ge=0, le=5)
    traditional: int = Field(ge=0, le=5)
    cross_source: int = Field(ge=0, le=5)
    empirical: int = Field(ge=0, le=5)
    implementation: int = Field(ge=0, le=5)
    notes: str | None = None


class RuleProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_ids: list[str] = Field(default_factory=list)
    passage_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    legacy_provenance_status: LegacyMappingStatus | None = None

    @field_validator("source_ids")
    @classmethod
    def _validate_source_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-SRC-\d{6}", item):
                raise ValueError("source_ids must match VEDA-SRC-000001")
        return value

    @field_validator("passage_ids")
    @classmethod
    def _validate_passage_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-PSG-\d{6}", item):
                raise ValueError("passage_ids must match VEDA-PSG-000001")
        return value

    @field_validator("claim_ids")
    @classmethod
    def _validate_claim_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CLM-\d{6}", item):
                raise ValueError("claim_ids must match VEDA-CLM-000001")
        return value

    @field_validator("conflict_ids")
    @classmethod
    def _validate_conflict_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CNF-\d{6}", item):
                raise ValueError("conflict_ids must match VEDA-CNF-000001")
        return value


class RuleOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_id: str
    outcome_type: OutcomeType
    target: OperandReference | None = None
    value: Any | None = None
    value_entity_id: str | None = None
    value_entity_ids: list[str] = Field(default_factory=list)
    description: str

    @field_validator("outcome_id", "description")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()

    @field_validator("value_entity_id")
    @classmethod
    def _validate_value_entity_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("value_entity_id must use a stable VEDA identifier")
        return value

    @field_validator("value_entity_ids")
    @classmethod
    def _validate_value_entity_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _ENTITY_ID_RE.fullmatch(item):
                raise ValueError("value_entity_ids must use stable VEDA identifiers")
        return value


class AstrologyRuleRecord(VersionedAstrologyArtifact):
    rule_id: str
    title: str
    domain: str
    subdomain: str | None = None
    rule_type: RuleType
    status: RuleLifecycleStatus
    source_class: SourceClass
    approval_status: ApprovalStatus
    evidence_types: list[EvidenceType] = Field(default_factory=list)
    high_stakes: bool = False
    requires_safety_review: bool = False
    allowed_output_mode: AllowedOutputMode = AllowedOutputMode.STANDARD
    authority: RuleAuthorityProfile
    provenance: RuleProvenance
    conditions: RuleConditionSet
    modifiers: list[RuleModifier] = Field(default_factory=list)
    exceptions: list[RuleException] = Field(default_factory=list)
    confirmations: list[RuleConfirmation] = Field(default_factory=list)
    activations: list[RuleActivation] = Field(default_factory=list)
    outcomes: list[RuleOutcome] = Field(default_factory=list)
    depends_on_rule_ids: list[str] = Field(default_factory=list)
    cancelled_by_rule_ids: list[str] = Field(default_factory=list)

    @field_validator("rule_id")
    @classmethod
    def _validate_rule_id(cls, value: str) -> str:
        if not _RULE_ID_RE.fullmatch(value):
            raise ValueError("rule_id must match VEDA-RUL-AREA-000001")
        return value

    @field_validator("title", "domain")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()

    @field_validator("subdomain")
    @classmethod
    def _normalize_subdomain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("depends_on_rule_ids", "cancelled_by_rule_ids")
    @classmethod
    def _validate_rule_refs(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _RULE_ID_RE.fullmatch(item):
                raise ValueError("rule references must match VEDA-RUL-AREA-000001")
        return value

    @model_validator(mode="after")
    def _validate_provenance_policy(self) -> "AstrologyRuleRecord":
        approved_states = {
            RuleLifecycleStatus.SOURCE_VALIDATED,
            RuleLifecycleStatus.APPROVED,
            RuleLifecycleStatus.APPROVED_WITH_CONDITIONS,
            RuleLifecycleStatus.IMPLEMENTATION_READY,
            RuleLifecycleStatus.IMPLEMENTED,
            RuleLifecycleStatus.VALIDATED,
        }
        approved_statuses = {
            ApprovalStatus.APPROVED,
            ApprovalStatus.APPROVED_WITH_CONDITIONS,
            ApprovalStatus.IMPLEMENTATION_READY,
        }
        has_governed_refs = bool(
            self.provenance.source_ids
            or self.provenance.passage_ids
            or self.provenance.claim_ids
            or self.provenance.conflict_ids
        )
        if (self.status in approved_states or self.approval_status in approved_statuses) and not has_governed_refs:
            raise ValueError("approved or implementation-ready rules must include governed provenance references")
        if self.approval_status in approved_statuses and self.provenance.legacy_provenance_status is not None:
            raise ValueError("approved rules cannot rely on legacy_provenance_status in place of governed provenance")
        return self


class LegacyKnowledgeMappingRecord(VersionedAstrologyArtifact):
    legacy_mapping_id: str
    legacy_location: str
    legacy_function: str
    legacy_behavior: str
    target_rule_ids: list[str] = Field(default_factory=list)
    mapping_status: LegacyMappingStatus
    semantic_match: SemanticMatch
    known_differences: list[str] = Field(default_factory=list)
    source_status: LegacyMappingStatus
    migration_recommendation: str

    @field_validator("legacy_mapping_id")
    @classmethod
    def _validate_mapping_id(cls, value: str) -> str:
        if not _LEGACY_MAPPING_ID_RE.fullmatch(value):
            raise ValueError("legacy_mapping_id must match VEDA-LMP-000001")
        return value

    @field_validator("legacy_location", "legacy_function", "legacy_behavior", "migration_recommendation")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()

    @field_validator("target_rule_ids")
    @classmethod
    def _validate_target_rules(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("target_rule_ids must contain at least one rule id")
        for item in value:
            if not _RULE_ID_RE.fullmatch(item):
                raise ValueError("target_rule_ids must match VEDA-RUL-AREA-000001")
        return value


class LagnaFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    longitude: float | None = None

    @field_validator("entity_id")
    @classmethod
    def _validate_entity_id(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("entity_id must use a stable VEDA identifier")
        return value


class PlanetFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    longitude: float
    rashi: str
    bhava: str
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    retrograde: bool
    dignity: str

    @field_validator("entity_id", "rashi", "bhava", "nakshatra", "dignity")
    @classmethod
    def _validate_entity_ref(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("field must use a stable VEDA identifier")
        return value


class HouseFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    rashi: str
    lord: str
    occupants: list[str] = Field(default_factory=list)

    @field_validator("entity_id", "rashi", "lord")
    @classmethod
    def _validate_entity_ref(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("field must use a stable VEDA identifier")
        return value

    @field_validator("occupants")
    @classmethod
    def _validate_occupants(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _ENTITY_ID_RE.fullmatch(item):
                raise ValueError("occupants must use stable VEDA identifiers")
        return value


class VargaFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    chart_signs: dict[str, str] = Field(default_factory=dict)

    @field_validator("entity_id")
    @classmethod
    def _validate_entity_id(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("entity_id must use a stable VEDA identifier")
        return value

    @field_validator("chart_signs")
    @classmethod
    def _validate_chart_signs(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not _ENTITY_ID_RE.fullmatch(key) or not _ENTITY_ID_RE.fullmatch(item):
                raise ValueError("chart_signs must map entity ids to entity ids")
        return value


class DashaFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    sequence_order: list[str] = Field(default_factory=list)
    birth_balance_basis: str | None = None

    @field_validator("entity_id")
    @classmethod
    def _validate_entity_id(cls, value: str) -> str:
        if not _ENTITY_ID_RE.fullmatch(value):
            raise ValueError("entity_id must use a stable VEDA identifier")
        return value

    @field_validator("sequence_order")
    @classmethod
    def _validate_sequence_order(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _ENTITY_ID_RE.fullmatch(item):
                raise ValueError("sequence_order must contain stable VEDA identifiers")
        return value


class ChartFactsContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = CONTRACT_VERSION
    chart_id: str
    chart_type: ContractChartType
    lagna: LagnaFact
    planets: list[PlanetFact] = Field(default_factory=list)
    houses: list[HouseFact] = Field(default_factory=list)
    vargas: list[VargaFact] = Field(default_factory=list)
    dashas: list[DashaFact] = Field(default_factory=list)
    relationships: dict[str, dict[str, Any]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("chart_id")
    @classmethod
    def _validate_chart_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chart_id is required")
        return value.strip()


class EvaluationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_ids: list[str] = Field(default_factory=list)
    passage_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)

    @field_validator("claim_ids")
    @classmethod
    def _validate_claim_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CLM-\d{6}", item):
                raise ValueError("claim_ids must match VEDA-CLM-000001")
        return value

    @field_validator("passage_ids")
    @classmethod
    def _validate_passage_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-PSG-\d{6}", item):
                raise ValueError("passage_ids must match VEDA-PSG-000001")
        return value

    @field_validator("source_ids")
    @classmethod
    def _validate_source_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-SRC-\d{6}", item):
                raise ValueError("source_ids must match VEDA-SRC-000001")
        return value

    @field_validator("conflict_ids")
    @classmethod
    def _validate_conflict_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CNF-\d{6}", item):
                raise ValueError("conflict_ids must match VEDA-CNF-000001")
        return value


class RuleEvaluationResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation_id: str
    rule_id: str
    matched: bool
    conditions_met: list[str] = Field(default_factory=list)
    conditions_failed: list[str] = Field(default_factory=list)
    modifiers_applied: list[str] = Field(default_factory=list)
    exceptions_triggered: list[str] = Field(default_factory=list)
    activation: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: EvaluationEvidence
    outputs: list[RuleOutcome] = Field(default_factory=list)

    @field_validator("evaluation_id")
    @classmethod
    def _validate_evaluation_id(cls, value: str) -> str:
        if not _EVALUATION_ID_RE.fullmatch(value):
            raise ValueError("evaluation_id must match VEDA-EVL-000001")
        return value

    @field_validator("rule_id")
    @classmethod
    def _validate_rule_id(cls, value: str) -> str:
        if not _RULE_ID_RE.fullmatch(value):
            raise ValueError("rule_id must match VEDA-RUL-AREA-000001")
        return value


@dataclass(slots=True)
class OntologyValidationReport:
    entity_count: int = 0
    relation_count: int = 0
    approved_rule_count: int = 0
    draft_rule_count: int = 0
    legacy_mapping_count: int = 0
    chart_contract_count: int = 0
    evaluation_contract_count: int = 0
    broken_references: list[str] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    invalid_operators: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def rule_count(self) -> int:
        return self.approved_rule_count + self.draft_rule_count

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def assert_valid(self) -> None:
        if self.errors:
            raise AssertionError("Ontology validation failed:\n- " + "\n- ".join(self.errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "approved_rule_count": self.approved_rule_count,
            "draft_rule_count": self.draft_rule_count,
            "rule_count": self.rule_count,
            "legacy_mapping_count": self.legacy_mapping_count,
            "chart_contract_count": self.chart_contract_count,
            "evaluation_contract_count": self.evaluation_contract_count,
            "broken_references": list(self.broken_references),
            "duplicate_ids": list(self.duplicate_ids),
            "invalid_operators": list(self.invalid_operators),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "is_valid": self.is_valid,
        }


def _artifact_meta(change_reason: str, notes: str | None = None) -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "created_at": _DEFAULT_TS,
        "created_by": _DEFAULT_ACTOR,
        "updated_at": _DEFAULT_TS,
        "updated_by": _DEFAULT_ACTOR,
        "change_reason": change_reason,
        "supersedes": None,
        "superseded_by": None,
        "notes": notes,
        "contract_version": CONTRACT_VERSION,
    }


def _entity(
    *,
    entity_id: str,
    canonical_name: str,
    entity_type: EntityType,
    description: str,
    sanskrit_name: str | None = None,
    transliteration: str | None = None,
    aliases: list[str] | None = None,
    deprecated_aliases: list[str] | None = None,
    source_status: EntitySourceStatus = EntitySourceStatus.CURATED_CANONICAL,
    status: OntologyRecordStatus = OntologyRecordStatus.ACTIVE,
) -> dict[str, Any]:
    return EntityRecord.model_validate(
        {
            "entity_id": entity_id,
            "canonical_name": canonical_name,
            "entity_type": entity_type,
            "sanskrit_name": sanskrit_name,
            "transliteration": transliteration,
            "aliases": aliases or [],
            "description": description,
            "source_status": source_status,
            "deprecated_aliases": deprecated_aliases or [],
            "status": status,
            **_artifact_meta("Initial P003 canonical ontology registration."),
        }
    ).model_dump(mode="json")


def _relation(
    *,
    relation_id: str,
    subject_entity_id: str,
    relation_type: RelationType,
    object_entity_id: str,
    description: str,
    source_status: EntitySourceStatus = EntitySourceStatus.CURATED_CANONICAL,
    status: OntologyRecordStatus = OntologyRecordStatus.ACTIVE,
) -> dict[str, Any]:
    return RelationRecord.model_validate(
        {
            "relation_id": relation_id,
            "subject_entity_id": subject_entity_id,
            "relation_type": relation_type,
            "object_entity_id": object_entity_id,
            "description": description,
            "source_status": source_status,
            "status": status,
            **_artifact_meta("Initial P003 canonical ontology relationship registration."),
        }
    ).model_dump(mode="json")


def _operand(ref: str, ref_type: OperandKind, property_name: str | None = None) -> dict[str, Any]:
    return OperandReference(ref=ref, ref_type=ref_type, property_name=property_name).model_dump(mode="json")


def _conditions(**kwargs: Any) -> dict[str, Any]:
    return RuleConditionSet.model_validate(kwargs).model_dump(mode="json")


def _condition_node(**kwargs: Any) -> dict[str, Any]:
    return ConditionNode.model_validate(kwargs).model_dump(mode="json")


def _rule(
    *,
    rule_id: str,
    title: str,
    domain: str,
    subdomain: str | None,
    rule_type: RuleType,
    status: RuleLifecycleStatus,
    source_class: SourceClass,
    approval_status: ApprovalStatus,
    evidence_types: list[EvidenceType],
    authority: dict[str, Any],
    provenance: dict[str, Any],
    conditions: dict[str, Any],
    modifiers: list[dict[str, Any]] | None = None,
    exceptions: list[dict[str, Any]] | None = None,
    confirmations: list[dict[str, Any]] | None = None,
    activations: list[dict[str, Any]] | None = None,
    outcomes: list[dict[str, Any]] | None = None,
    depends_on_rule_ids: list[str] | None = None,
    cancelled_by_rule_ids: list[str] | None = None,
    high_stakes: bool = False,
    requires_safety_review: bool = False,
    allowed_output_mode: AllowedOutputMode = AllowedOutputMode.STANDARD,
    notes: str | None = None,
) -> dict[str, Any]:
    return AstrologyRuleRecord.model_validate(
        {
            "rule_id": rule_id,
            "title": title,
            "domain": domain,
            "subdomain": subdomain,
            "rule_type": rule_type,
            "status": status,
            "source_class": source_class,
            "approval_status": approval_status,
            "evidence_types": evidence_types,
            "high_stakes": high_stakes,
            "requires_safety_review": requires_safety_review,
            "allowed_output_mode": allowed_output_mode,
            "authority": authority,
            "provenance": provenance,
            "conditions": conditions,
            "modifiers": modifiers or [],
            "exceptions": exceptions or [],
            "confirmations": confirmations or [],
            "activations": activations or [],
            "outcomes": outcomes or [],
            "depends_on_rule_ids": depends_on_rule_ids or [],
            "cancelled_by_rule_ids": cancelled_by_rule_ids or [],
            **_artifact_meta("Initial P003 pilot rule registration.", notes=notes),
        }
    ).model_dump(mode="json")


def _legacy_mapping(
    *,
    legacy_mapping_id: str,
    legacy_location: str,
    legacy_function: str,
    legacy_behavior: str,
    target_rule_ids: list[str],
    mapping_status: LegacyMappingStatus,
    semantic_match: SemanticMatch,
    known_differences: list[str],
    source_status: LegacyMappingStatus,
    migration_recommendation: str,
    notes: str | None = None,
) -> dict[str, Any]:
    return LegacyKnowledgeMappingRecord.model_validate(
        {
            "legacy_mapping_id": legacy_mapping_id,
            "legacy_location": legacy_location,
            "legacy_function": legacy_function,
            "legacy_behavior": legacy_behavior,
            "target_rule_ids": target_rule_ids,
            "mapping_status": mapping_status,
            "semantic_match": semantic_match,
            "known_differences": known_differences,
            "source_status": source_status,
            "migration_recommendation": migration_recommendation,
            **_artifact_meta("Initial P003 legacy knowledge mapping pilot.", notes=notes),
        }
    ).model_dump(mode="json")


def _rule_authority(
    textual: int,
    traditional: int,
    cross_source: int,
    empirical: int,
    implementation: int,
    notes: str | None = None,
) -> dict[str, Any]:
    return RuleAuthorityProfile(
        textual=textual,
        traditional=traditional,
        cross_source=cross_source,
        empirical=empirical,
        implementation=implementation,
        notes=notes,
    ).model_dump(mode="json")


def _rule_provenance(
    *,
    source_ids: list[str] | None = None,
    passage_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
    conflict_ids: list[str] | None = None,
    legacy_provenance_status: LegacyMappingStatus | None = None,
) -> dict[str, Any]:
    return RuleProvenance(
        source_ids=source_ids or [],
        passage_ids=passage_ids or [],
        claim_ids=claim_ids or [],
        conflict_ids=conflict_ids or [],
        legacy_provenance_status=legacy_provenance_status,
    ).model_dump(mode="json")


def _rule_outcome(
    *,
    outcome_id: str,
    outcome_type: OutcomeType,
    description: str,
    target: dict[str, Any] | None = None,
    value: Any | None = None,
    value_entity_id: str | None = None,
    value_entity_ids: list[str] | None = None,
) -> dict[str, Any]:
    return RuleOutcome(
        outcome_id=outcome_id,
        outcome_type=outcome_type,
        target=target,
        value=value,
        value_entity_id=value_entity_id,
        value_entity_ids=value_entity_ids or [],
        description=description,
    ).model_dump(mode="json")


def default_documents() -> dict[str, Any]:
    graha_ids = {
        "Sun": "VEDA-GRAHA-SUN",
        "Moon": "VEDA-GRAHA-MOON",
        "Mars": "VEDA-GRAHA-MARS",
        "Mercury": "VEDA-GRAHA-MERCURY",
        "Jupiter": "VEDA-GRAHA-JUPITER",
        "Venus": "VEDA-GRAHA-VENUS",
        "Saturn": "VEDA-GRAHA-SATURN",
        "Rahu": "VEDA-GRAHA-RAHU",
        "Ketu": "VEDA-GRAHA-KETU",
        "Uranus": "VEDA-GRAHA-URANUS",
        "Neptune": "VEDA-GRAHA-NEPTUNE",
        "Pluto": "VEDA-GRAHA-PLUTO",
    }
    rashi_ids = {
        "Aries": "VEDA-RASHI-ARIES",
        "Taurus": "VEDA-RASHI-TAURUS",
        "Gemini": "VEDA-RASHI-GEMINI",
        "Cancer": "VEDA-RASHI-CANCER",
        "Leo": "VEDA-RASHI-LEO",
        "Virgo": "VEDA-RASHI-VIRGO",
        "Libra": "VEDA-RASHI-LIBRA",
        "Scorpio": "VEDA-RASHI-SCORPIO",
        "Sagittarius": "VEDA-RASHI-SAGITTARIUS",
        "Capricorn": "VEDA-RASHI-CAPRICORN",
        "Aquarius": "VEDA-RASHI-AQUARIUS",
        "Pisces": "VEDA-RASHI-PISCES",
    }
    bhava_ids = {str(i): f"VEDA-BHAVA-{i:02d}" for i in range(1, 13)}
    nak_ids = {
        "Ashwini": "VEDA-NAK-ASHWINI",
        "Bharani": "VEDA-NAK-BHARANI",
        "Krittika": "VEDA-NAK-KRITTIKA",
        "Rohini": "VEDA-NAK-ROHINI",
        "Mrigashira": "VEDA-NAK-MRIGASHIRA",
        "Ardra": "VEDA-NAK-ARDRA",
        "Punarvasu": "VEDA-NAK-PUNARVASU",
        "Pushya": "VEDA-NAK-PUSHYA",
        "Ashlesha": "VEDA-NAK-ASHLESHA",
        "Magha": "VEDA-NAK-MAGHA",
        "Purva Phalguni": "VEDA-NAK-PURVA_PHALGUNI",
        "Uttara Phalguni": "VEDA-NAK-UTTARA_PHALGUNI",
        "Hasta": "VEDA-NAK-HASTA",
        "Chitra": "VEDA-NAK-CHITRA",
        "Swati": "VEDA-NAK-SWATI",
        "Vishakha": "VEDA-NAK-VISHAKHA",
        "Anuradha": "VEDA-NAK-ANURADHA",
        "Jyeshtha": "VEDA-NAK-JYESHTHA",
        "Mula": "VEDA-NAK-MULA",
        "Purva Ashadha": "VEDA-NAK-PURVA_ASHADHA",
        "Uttara Ashadha": "VEDA-NAK-UTTARA_ASHADHA",
        "Shravana": "VEDA-NAK-SHRAVANA",
        "Dhanishtha": "VEDA-NAK-DHANISHTHA",
        "Shatabhisha": "VEDA-NAK-SHATABHISHA",
        "Purva Bhadra": "VEDA-NAK-PURVA_BHADRA",
        "Uttara Bhadra": "VEDA-NAK-UTTARA_BHADRA",
        "Revati": "VEDA-NAK-REVATI",
    }
    varga_ids = {
        "D1": "VEDA-VARGA-D01",
        "D2": "VEDA-VARGA-D02",
        "D3": "VEDA-VARGA-D03",
        "D4": "VEDA-VARGA-D04",
        "D7": "VEDA-VARGA-D07",
        "D9": "VEDA-VARGA-D09",
        "D10": "VEDA-VARGA-D10",
        "D12": "VEDA-VARGA-D12",
        "D16": "VEDA-VARGA-D16",
        "D20": "VEDA-VARGA-D20",
        "D24": "VEDA-VARGA-D24",
        "D27": "VEDA-VARGA-D27",
        "D30": "VEDA-VARGA-D30",
        "D40": "VEDA-VARGA-D40",
        "D45": "VEDA-VARGA-D45",
        "D60": "VEDA-VARGA-D60",
    }
    dasha_ids = {
        "Vimshottari": "VEDA-DASHA-VIMSHOTTARI",
        "Mahadasha": "VEDA-DASHA-MAHADASHA",
        "Antardasha": "VEDA-DASHA-ANTARDASHA",
        "Pratyantardasha": "VEDA-DASHA-PRATYANTARDASHA",
        "Transit": "VEDA-TIMING-TRANSIT",
        "Gochara": "VEDA-TIMING-GOCHARA",
    }

    documents: dict[str, Any] = {}

    documents["ontology/grahas/grahas.json"] = [
        _entity(
            entity_id=graha_ids["Sun"],
            canonical_name="Sun",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Surya",
            transliteration="Surya",
            aliases=["Sun", "Surya", "Ravi"],
            description="Solar graha used across natal, dasha, transit, and interpretation layers.",
        ),
        _entity(
            entity_id=graha_ids["Moon"],
            canonical_name="Moon",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Chandra",
            transliteration="Chandra",
            aliases=["Moon", "Chandra", "Soma"],
            description="Lunar graha used for Janma Nakshatra, Vimshottari initialization, and mind-related interpretation.",
        ),
        _entity(
            entity_id=graha_ids["Mars"],
            canonical_name="Mars",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Mangala",
            transliteration="Mangala",
            aliases=["Mars", "Kuja", "Mangala"],
            description="Fiery graha used in lordship, aspect, dignity, and yoga evaluation.",
        ),
        _entity(
            entity_id=graha_ids["Mercury"],
            canonical_name="Mercury",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Budha",
            transliteration="Budha",
            aliases=["Mercury", "Budha"],
            description="Mercurial graha used in analytical, trade, and communications interpretation.",
        ),
        _entity(
            entity_id=graha_ids["Jupiter"],
            canonical_name="Jupiter",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Guru",
            transliteration="Guru",
            aliases=["Jupiter", "Guru", "Brihaspati"],
            description="Benefic graha central to Gaja Kesari and many strength- and wisdom-related rules.",
        ),
        _entity(
            entity_id=graha_ids["Venus"],
            canonical_name="Venus",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Shukra",
            transliteration="Shukra",
            aliases=["Venus", "Shukra"],
            description="Graha associated with pleasures, partnerships, luxuries, and several financial interpretations.",
        ),
        _entity(
            entity_id=graha_ids["Saturn"],
            canonical_name="Saturn",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Shani",
            transliteration="Shani",
            aliases=["Saturn", "Shani"],
            description="Slow graha important for delay, endurance, karmic weight, and current transit analysis.",
        ),
        _entity(
            entity_id=graha_ids["Rahu"],
            canonical_name="Rahu",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Rahu",
            transliteration="Rahu",
            aliases=["Rahu", "North Node", "True Node"],
            description="North lunar node used in Vedic calculations, Kala Sarpa logic, and specialized aspects.",
        ),
        _entity(
            entity_id=graha_ids["Ketu"],
            canonical_name="Ketu",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Ketu",
            transliteration="Ketu",
            aliases=["Ketu", "South Node"],
            description="South lunar node used in Vedic calculations, Vimshottari order, and Kala Sarpa logic.",
        ),
        _entity(
            entity_id=graha_ids["Uranus"],
            canonical_name="Uranus",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Uranus",
            transliteration="Uranus",
            aliases=["Uranus"],
            description="Optional outer planet preserved as an ontology concept because current code references it in exclusions.",
            source_status=EntitySourceStatus.LEGACY_UNGOVERNED,
        ),
        _entity(
            entity_id=graha_ids["Neptune"],
            canonical_name="Neptune",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Neptune",
            transliteration="Neptune",
            aliases=["Neptune"],
            description="Optional outer planet preserved as an ontology concept because current code references it in exclusions.",
            source_status=EntitySourceStatus.LEGACY_UNGOVERNED,
        ),
        _entity(
            entity_id=graha_ids["Pluto"],
            canonical_name="Pluto",
            entity_type=EntityType.GRAHA,
            sanskrit_name="Pluto",
            transliteration="Pluto",
            aliases=["Pluto"],
            description="Outer planet included only as an extensibility concept for future compatibility, not as a current VEDA runtime requirement.",
            source_status=EntitySourceStatus.UNKNOWN,
        ),
    ]

    documents["ontology/rashis/rashis.json"] = [
        _entity(entity_id=rashi_ids["Aries"], canonical_name="Aries", entity_type=EntityType.RASHI, sanskrit_name="Mesha", transliteration="Mesha", aliases=["Aries", "Mesha"], description="First sign of the zodiac."),
        _entity(entity_id=rashi_ids["Taurus"], canonical_name="Taurus", entity_type=EntityType.RASHI, sanskrit_name="Vrishabha", transliteration="Vrishabha", aliases=["Taurus", "Vrishabha"], description="Second sign of the zodiac."),
        _entity(entity_id=rashi_ids["Gemini"], canonical_name="Gemini", entity_type=EntityType.RASHI, sanskrit_name="Mithuna", transliteration="Mithuna", aliases=["Gemini", "Mithuna"], description="Third sign of the zodiac."),
        _entity(entity_id=rashi_ids["Cancer"], canonical_name="Cancer", entity_type=EntityType.RASHI, sanskrit_name="Karka", transliteration="Karka", aliases=["Cancer", "Karka"], description="Fourth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Leo"], canonical_name="Leo", entity_type=EntityType.RASHI, sanskrit_name="Simha", transliteration="Simha", aliases=["Leo", "Simha"], description="Fifth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Virgo"], canonical_name="Virgo", entity_type=EntityType.RASHI, sanskrit_name="Kanya", transliteration="Kanya", aliases=["Virgo", "Kanya"], description="Sixth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Libra"], canonical_name="Libra", entity_type=EntityType.RASHI, sanskrit_name="Tula", transliteration="Tula", aliases=["Libra", "Tula"], description="Seventh sign of the zodiac."),
        _entity(entity_id=rashi_ids["Scorpio"], canonical_name="Scorpio", entity_type=EntityType.RASHI, sanskrit_name="Vrischika", transliteration="Vrischika", aliases=["Scorpio", "Vrischika"], description="Eighth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Sagittarius"], canonical_name="Sagittarius", entity_type=EntityType.RASHI, sanskrit_name="Dhanu", transliteration="Dhanu", aliases=["Sagittarius", "Dhanu"], description="Ninth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Capricorn"], canonical_name="Capricorn", entity_type=EntityType.RASHI, sanskrit_name="Makara", transliteration="Makara", aliases=["Capricorn", "Makara"], description="Tenth sign of the zodiac."),
        _entity(entity_id=rashi_ids["Aquarius"], canonical_name="Aquarius", entity_type=EntityType.RASHI, sanskrit_name="Kumbha", transliteration="Kumbha", aliases=["Aquarius", "Kumbha"], description="Eleventh sign of the zodiac."),
        _entity(entity_id=rashi_ids["Pisces"], canonical_name="Pisces", entity_type=EntityType.RASHI, sanskrit_name="Meena", transliteration="Meena", aliases=["Pisces", "Meena"], description="Twelfth sign of the zodiac."),
    ]

    documents["ontology/bhavas/bhavas.json"] = [
        _entity(entity_id=bhava_ids["1"], canonical_name="First House", entity_type=EntityType.BHAVA, sanskrit_name="Tanu Bhava", transliteration="Tanu Bhava", aliases=["1H", "First House", "House 1"], description="Identity, body, and baseline orientation."),
        _entity(entity_id=bhava_ids["2"], canonical_name="Second House", entity_type=EntityType.BHAVA, sanskrit_name="Dhana Bhava", transliteration="Dhana Bhava", aliases=["2H", "Second House", "House 2"], description="Accumulated wealth, speech, and stored resources."),
        _entity(entity_id=bhava_ids["3"], canonical_name="Third House", entity_type=EntityType.BHAVA, sanskrit_name="Sahaja Bhava", transliteration="Sahaja Bhava", aliases=["3H", "Third House", "House 3"], description="Courage, initiative, siblings, and effort."),
        _entity(entity_id=bhava_ids["4"], canonical_name="Fourth House", entity_type=EntityType.BHAVA, sanskrit_name="Sukha Bhava", transliteration="Sukha Bhava", aliases=["4H", "Fourth House", "House 4"], description="Home, mother, emotional grounding, and assets."),
        _entity(entity_id=bhava_ids["5"], canonical_name="Fifth House", entity_type=EntityType.BHAVA, sanskrit_name="Putra Bhava", transliteration="Putra Bhava", aliases=["5H", "Fifth House", "House 5"], description="Intelligence, creativity, children, and speculation."),
        _entity(entity_id=bhava_ids["6"], canonical_name="Sixth House", entity_type=EntityType.BHAVA, sanskrit_name="Roga Bhava", transliteration="Roga Bhava", aliases=["6H", "Sixth House", "House 6"], description="Debts, disease, disputes, and service."),
        _entity(entity_id=bhava_ids["7"], canonical_name="Seventh House", entity_type=EntityType.BHAVA, sanskrit_name="Yuvati Bhava", transliteration="Yuvati Bhava", aliases=["7H", "Seventh House", "House 7"], description="Marriage, partnerships, and open counterparts."),
        _entity(entity_id=bhava_ids["8"], canonical_name="Eighth House", entity_type=EntityType.BHAVA, sanskrit_name="Randhra Bhava", transliteration="Randhra Bhava", aliases=["8H", "Eighth House", "House 8"], description="Longevity, transformation, secrecy, and volatility."),
        _entity(entity_id=bhava_ids["9"], canonical_name="Ninth House", entity_type=EntityType.BHAVA, sanskrit_name="Dharma Bhava", transliteration="Dharma Bhava", aliases=["9H", "Ninth House", "House 9"], description="Fortune, dharma, teachers, and higher guidance."),
        _entity(entity_id=bhava_ids["10"], canonical_name="Tenth House", entity_type=EntityType.BHAVA, sanskrit_name="Karma Bhava", transliteration="Karma Bhava", aliases=["10H", "Tenth House", "House 10"], description="Career, profession, work output, and status."),
        _entity(entity_id=bhava_ids["11"], canonical_name="Eleventh House", entity_type=EntityType.BHAVA, sanskrit_name="Labha Bhava", transliteration="Labha Bhava", aliases=["11H", "Eleventh House", "House 11"], description="Gains, income, networks, and fulfillment of desires."),
        _entity(entity_id=bhava_ids["12"], canonical_name="Twelfth House", entity_type=EntityType.BHAVA, sanskrit_name="Vyaya Bhava", transliteration="Vyaya Bhava", aliases=["12H", "Twelfth House", "House 12"], description="Loss, expenditure, isolation, and liberation-related themes."),
    ]

    documents["ontology/nakshatras/nakshatras.json"] = [
        _entity(entity_id=nak_ids["Ashwini"], canonical_name="Ashwini", entity_type=EntityType.NAKSHATRA, sanskrit_name="Ashvini", transliteration="Ashvini", aliases=["Ashwini", "Ashvini"], description="First lunar mansion; in runtime it initializes the Vimshottari sequence with Ketu."),
        _entity(entity_id=nak_ids["Bharani"], canonical_name="Bharani", entity_type=EntityType.NAKSHATRA, sanskrit_name="Bharani", transliteration="Bharani", aliases=["Bharani"], description="Second lunar mansion."),
        _entity(entity_id=nak_ids["Krittika"], canonical_name="Krittika", entity_type=EntityType.NAKSHATRA, sanskrit_name="Krittika", transliteration="Krittika", aliases=["Krittika"], description="Third lunar mansion."),
        _entity(entity_id=nak_ids["Rohini"], canonical_name="Rohini", entity_type=EntityType.NAKSHATRA, sanskrit_name="Rohini", transliteration="Rohini", aliases=["Rohini"], description="Fourth lunar mansion."),
        _entity(entity_id=nak_ids["Mrigashira"], canonical_name="Mrigashira", entity_type=EntityType.NAKSHATRA, sanskrit_name="Mrigashira", transliteration="Mrigashira", aliases=["Mrigashira"], description="Fifth lunar mansion."),
        _entity(entity_id=nak_ids["Ardra"], canonical_name="Ardra", entity_type=EntityType.NAKSHATRA, sanskrit_name="Ardra", transliteration="Ardra", aliases=["Ardra"], description="Sixth lunar mansion."),
        _entity(entity_id=nak_ids["Punarvasu"], canonical_name="Punarvasu", entity_type=EntityType.NAKSHATRA, sanskrit_name="Punarvasu", transliteration="Punarvasu", aliases=["Punarvasu"], description="Seventh lunar mansion."),
        _entity(entity_id=nak_ids["Pushya"], canonical_name="Pushya", entity_type=EntityType.NAKSHATRA, sanskrit_name="Pushya", transliteration="Pushya", aliases=["Pushya"], description="Eighth lunar mansion."),
        _entity(entity_id=nak_ids["Ashlesha"], canonical_name="Ashlesha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Ashlesha", transliteration="Ashlesha", aliases=["Ashlesha"], description="Ninth lunar mansion."),
        _entity(entity_id=nak_ids["Magha"], canonical_name="Magha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Magha", transliteration="Magha", aliases=["Magha"], description="Tenth lunar mansion."),
        _entity(entity_id=nak_ids["Purva Phalguni"], canonical_name="Purva Phalguni", entity_type=EntityType.NAKSHATRA, sanskrit_name="Purva Phalguni", transliteration="Purva Phalguni", aliases=["Purva Phalguni"], description="Eleventh lunar mansion."),
        _entity(entity_id=nak_ids["Uttara Phalguni"], canonical_name="Uttara Phalguni", entity_type=EntityType.NAKSHATRA, sanskrit_name="Uttara Phalguni", transliteration="Uttara Phalguni", aliases=["Uttara Phalguni"], description="Twelfth lunar mansion."),
        _entity(entity_id=nak_ids["Hasta"], canonical_name="Hasta", entity_type=EntityType.NAKSHATRA, sanskrit_name="Hasta", transliteration="Hasta", aliases=["Hasta"], description="Thirteenth lunar mansion."),
        _entity(entity_id=nak_ids["Chitra"], canonical_name="Chitra", entity_type=EntityType.NAKSHATRA, sanskrit_name="Chitra", transliteration="Chitra", aliases=["Chitra"], description="Fourteenth lunar mansion."),
        _entity(entity_id=nak_ids["Swati"], canonical_name="Swati", entity_type=EntityType.NAKSHATRA, sanskrit_name="Swati", transliteration="Swati", aliases=["Swati"], description="Fifteenth lunar mansion."),
        _entity(entity_id=nak_ids["Vishakha"], canonical_name="Vishakha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Vishakha", transliteration="Vishakha", aliases=["Vishakha"], description="Sixteenth lunar mansion."),
        _entity(entity_id=nak_ids["Anuradha"], canonical_name="Anuradha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Anuradha", transliteration="Anuradha", aliases=["Anuradha"], description="Seventeenth lunar mansion."),
        _entity(entity_id=nak_ids["Jyeshtha"], canonical_name="Jyeshtha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Jyeshtha", transliteration="Jyeshtha", aliases=["Jyeshtha"], description="Eighteenth lunar mansion."),
        _entity(entity_id=nak_ids["Mula"], canonical_name="Mula", entity_type=EntityType.NAKSHATRA, sanskrit_name="Mula", transliteration="Mula", aliases=["Mula"], description="Nineteenth lunar mansion."),
        _entity(entity_id=nak_ids["Purva Ashadha"], canonical_name="Purva Ashadha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Purva Ashadha", transliteration="Purva Ashadha", aliases=["Purva Ashadha"], description="Twentieth lunar mansion."),
        _entity(entity_id=nak_ids["Uttara Ashadha"], canonical_name="Uttara Ashadha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Uttara Ashadha", transliteration="Uttara Ashadha", aliases=["Uttara Ashadha"], description="Twenty-first lunar mansion."),
        _entity(entity_id=nak_ids["Shravana"], canonical_name="Shravana", entity_type=EntityType.NAKSHATRA, sanskrit_name="Shravana", transliteration="Shravana", aliases=["Shravana"], description="Twenty-second lunar mansion."),
        _entity(entity_id=nak_ids["Dhanishtha"], canonical_name="Dhanishtha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Dhanishtha", transliteration="Dhanishtha", aliases=["Dhanishtha"], description="Twenty-third lunar mansion."),
        _entity(entity_id=nak_ids["Shatabhisha"], canonical_name="Shatabhisha", entity_type=EntityType.NAKSHATRA, sanskrit_name="Shatabhisha", transliteration="Shatabhisha", aliases=["Shatabhisha"], description="Twenty-fourth lunar mansion."),
        _entity(entity_id=nak_ids["Purva Bhadra"], canonical_name="Purva Bhadra", entity_type=EntityType.NAKSHATRA, sanskrit_name="Purva Bhadrapada", transliteration="Purva Bhadrapada", aliases=["Purva Bhadra", "Purva Bhadrapada"], description="Twenty-fifth lunar mansion."),
        _entity(entity_id=nak_ids["Uttara Bhadra"], canonical_name="Uttara Bhadra", entity_type=EntityType.NAKSHATRA, sanskrit_name="Uttara Bhadrapada", transliteration="Uttara Bhadrapada", aliases=["Uttara Bhadra", "Uttara Bhadrapada"], description="Twenty-sixth lunar mansion."),
        _entity(entity_id=nak_ids["Revati"], canonical_name="Revati", entity_type=EntityType.NAKSHATRA, sanskrit_name="Revati", transliteration="Revati", aliases=["Revati"], description="Twenty-seventh lunar mansion and current runtime edge-case fallback at the 360-degree boundary."),
    ]

    documents["ontology/vargas/vargas.json"] = [
        _entity(entity_id=varga_ids["D1"], canonical_name="D1", entity_type=EntityType.VARGA, sanskrit_name="Rashi", transliteration="Rashi", aliases=["D1", "Rashi"], description="Primary natal chart."),
        _entity(entity_id=varga_ids["D2"], canonical_name="D2", entity_type=EntityType.VARGA, sanskrit_name="Hora", transliteration="Hora", aliases=["D2", "Hora"], description="Divisional chart traditionally related to wealth and sustenance."),
        _entity(entity_id=varga_ids["D3"], canonical_name="D3", entity_type=EntityType.VARGA, sanskrit_name="Drekkana", transliteration="Drekkana", aliases=["D3", "Drekkana"], description="Divisional chart for courage, co-borns, and related themes."),
        _entity(entity_id=varga_ids["D4"], canonical_name="D4", entity_type=EntityType.VARGA, sanskrit_name="Chaturthamsha", transliteration="Chaturthamsha", aliases=["D4"], description="Divisional chart related to property and assets."),
        _entity(entity_id=varga_ids["D7"], canonical_name="D7", entity_type=EntityType.VARGA, sanskrit_name="Saptamsha", transliteration="Saptamsha", aliases=["D7"], description="Divisional chart related to children and lineage."),
        _entity(entity_id=varga_ids["D9"], canonical_name="D9", entity_type=EntityType.VARGA, sanskrit_name="Navamsha", transliteration="Navamsha", aliases=["D9", "Navamsa", "Navamsha"], description="Divisional chart central to dharma, marriage, and refinement."),
        _entity(entity_id=varga_ids["D10"], canonical_name="D10", entity_type=EntityType.VARGA, sanskrit_name="Dashamsha", transliteration="Dashamsha", aliases=["D10"], description="Divisional chart tied to profession and public action."),
        _entity(entity_id=varga_ids["D12"], canonical_name="D12", entity_type=EntityType.VARGA, sanskrit_name="Dwadashamsha", transliteration="Dwadashamsha", aliases=["D12"], description="Divisional chart tied to ancestry and elders."),
        _entity(entity_id=varga_ids["D16"], canonical_name="D16", entity_type=EntityType.VARGA, sanskrit_name="Shodashamsha", transliteration="Shodashamsha", aliases=["D16"], description="Divisional chart used for comforts and vehicles."),
        _entity(entity_id=varga_ids["D20"], canonical_name="D20", entity_type=EntityType.VARGA, sanskrit_name="Vimshamsha", transliteration="Vimshamsha", aliases=["D20"], description="Divisional chart used for spirituality and worship."),
        _entity(entity_id=varga_ids["D24"], canonical_name="D24", entity_type=EntityType.VARGA, sanskrit_name="Siddhamsha", transliteration="Siddhamsha", aliases=["D24"], description="Divisional chart used for learning and scholarship."),
        _entity(entity_id=varga_ids["D27"], canonical_name="D27", entity_type=EntityType.VARGA, sanskrit_name="Nakshatramsha", transliteration="Nakshatramsha", aliases=["D27"], description="Divisional chart used for strengths and weaknesses."),
        _entity(entity_id=varga_ids["D30"], canonical_name="D30", entity_type=EntityType.VARGA, sanskrit_name="Trimshamsha", transliteration="Trimshamsha", aliases=["D30"], description="Divisional chart used for misfortunes and defects."),
        _entity(entity_id=varga_ids["D40"], canonical_name="D40", entity_type=EntityType.VARGA, sanskrit_name="Khavedamsha", transliteration="Khavedamsha", aliases=["D40"], description="Divisional chart reserved for advanced analysis."),
        _entity(entity_id=varga_ids["D45"], canonical_name="D45", entity_type=EntityType.VARGA, sanskrit_name="Akshavedamsha", transliteration="Akshavedamsha", aliases=["D45"], description="Divisional chart reserved for advanced analysis."),
        _entity(entity_id=varga_ids["D60"], canonical_name="D60", entity_type=EntityType.VARGA, sanskrit_name="Shashtyamsha", transliteration="Shashtyamsha", aliases=["D60"], description="Divisional chart tied to subtle karmic residue."),
    ]

    documents["ontology/dashas/dashas.json"] = [
        _entity(entity_id=dasha_ids["Vimshottari"], canonical_name="Vimshottari Dasha", entity_type=EntityType.DASHA, sanskrit_name="Vimshottari Dasha", transliteration="Vimshottari Dasha", aliases=["Vimshottari"], description="Current primary dasha system implemented by VEDA runtime and governed by the P002 pilot."),
        _entity(entity_id=dasha_ids["Mahadasha"], canonical_name="Mahadasha", entity_type=EntityType.DASHA, sanskrit_name="Mahadasha", transliteration="Mahadasha", aliases=["Mahadasha"], description="Major dasha level."),
        _entity(entity_id=dasha_ids["Antardasha"], canonical_name="Antardasha", entity_type=EntityType.DASHA, sanskrit_name="Antardasha", transliteration="Antardasha", aliases=["Antardasha"], description="Sub-period inside a Mahadasha."),
        _entity(entity_id=dasha_ids["Pratyantardasha"], canonical_name="Pratyantardasha", entity_type=EntityType.DASHA, sanskrit_name="Pratyantardasha", transliteration="Pratyantardasha", aliases=["Pratyantardasha"], description="Third-level subdivision inside a Mahadasha."),
        _entity(entity_id=dasha_ids["Transit"], canonical_name="Transit", entity_type=EntityType.TIMING, sanskrit_name="Gochara", transliteration="Gochara", aliases=["Transit"], description="Movement-based timing layer separate from period systems."),
        _entity(entity_id=dasha_ids["Gochara"], canonical_name="Gochara", entity_type=EntityType.TIMING, sanskrit_name="Gochara", transliteration="Gochara", aliases=["Gochara"], description="Sanskritic label for transit-based timing analysis."),
    ]

    documents["ontology/relationships/relationships.json"] = [
        _entity(entity_id="VEDA-RELTYPE-CONJUNCTION", canonical_name="Conjunction", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Yuti", transliteration="Yuti", aliases=["Conjunction", "Yuti"], description="Two grahas occupying the same sign or house context."),
        _entity(entity_id="VEDA-RELTYPE-ASPECT", canonical_name="Aspect", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Drishti", transliteration="Drishti", aliases=["Aspect", "Drishti"], description="General aspect relationship."),
        _entity(entity_id="VEDA-RELTYPE-GRAHA_DRISHTI", canonical_name="Graha Drishti", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Graha Drishti", transliteration="Graha Drishti", aliases=["Graha Drishti"], description="Planetary aspect relationship."),
        _entity(entity_id="VEDA-RELTYPE-RASHI_DRISHTI", canonical_name="Rashi Drishti", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Rashi Drishti", transliteration="Rashi Drishti", aliases=["Rashi Drishti"], description="Sign-aspect relationship."),
        _entity(entity_id="VEDA-RELTYPE-LORDSHIP", canonical_name="Lordship", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Adhipatya", transliteration="Adhipatya", aliases=["Lordship"], description="Rulership relation between graha and sign or house."),
        _entity(entity_id="VEDA-RELTYPE-DISPOSITOR", canonical_name="Dispositor", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Dispositor", transliteration="Dispositor", aliases=["Dispositor"], description="Planet owning the sign occupied by another planet."),
        _entity(entity_id="VEDA-RELTYPE-MUTUAL_ASPECT", canonical_name="Mutual Aspect", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Paraspara Drishti", transliteration="Paraspara Drishti", aliases=["Mutual Aspect"], description="Mutual aspectual relationship."),
        _entity(entity_id="VEDA-RELTYPE-SIGN_EXCHANGE", canonical_name="Sign Exchange", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Parivartana", transliteration="Parivartana", aliases=["Sign Exchange", "Parivartana"], description="Two grahas occupying each other's signs."),
        _entity(entity_id="VEDA-RELTYPE-HOUSE_EXCHANGE", canonical_name="House Exchange", entity_type=EntityType.RELATIONSHIP, sanskrit_name="Bhava Parivartana", transliteration="Bhava Parivartana", aliases=["House Exchange"], description="House-lord exchange relationship."),
    ]

    documents["ontology/dignities/dignities.json"] = [
        _entity(entity_id="VEDA-DIGNITY-EXALTATION", canonical_name="Exaltation", entity_type=EntityType.DIGNITY, sanskrit_name="Uccha", transliteration="Uccha", aliases=["Exaltation", "Exalted"], description="High dignity state."),
        _entity(entity_id="VEDA-DIGNITY-EXALTED_EXACT", canonical_name="Exalted Exact", entity_type=EntityType.DIGNITY, sanskrit_name="Uccha Exact", transliteration="Uccha Exact", aliases=["Exalted Exact"], description="Exact exaltation window used by current runtime."),
        _entity(entity_id="VEDA-DIGNITY-DEBILITATION", canonical_name="Debilitation", entity_type=EntityType.DIGNITY, sanskrit_name="Neecha", transliteration="Neecha", aliases=["Debilitation", "Debilitated"], description="Low dignity state."),
        _entity(entity_id="VEDA-DIGNITY-MOOLATRIKONA", canonical_name="Moolatrikona", entity_type=EntityType.DIGNITY, sanskrit_name="Moolatrikona", transliteration="Moolatrikona", aliases=["Moolatrikona"], description="Special sign-based strength state."),
        _entity(entity_id="VEDA-DIGNITY-OWN_SIGN", canonical_name="Own Sign", entity_type=EntityType.DIGNITY, sanskrit_name="Swa Rashi", transliteration="Swa Rashi", aliases=["Own Sign"], description="Planet occupying its own sign."),
        _entity(entity_id="VEDA-DIGNITY-FRIEND_SIGN", canonical_name="Friend Sign", entity_type=EntityType.DIGNITY, sanskrit_name="Mitra Rashi", transliteration="Mitra Rashi", aliases=["Friendly"], description="Planet occupying a friendly sign."),
        _entity(entity_id="VEDA-DIGNITY-ENEMY_SIGN", canonical_name="Enemy Sign", entity_type=EntityType.DIGNITY, sanskrit_name="Shatru Rashi", transliteration="Shatru Rashi", aliases=["Enemy"], description="Planet occupying an enemy sign."),
        _entity(entity_id="VEDA-DIGNITY-NEUTRAL_SIGN", canonical_name="Neutral Sign", entity_type=EntityType.DIGNITY, sanskrit_name="Sama Rashi", transliteration="Sama Rashi", aliases=["Neutral"], description="Planet occupying a neutral sign."),
    ]

    documents["ontology/house_classifications/house_classifications.json"] = [
        _entity(entity_id="VEDA-HCLASS-KENDRA", canonical_name="Kendra", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Kendra", transliteration="Kendra", aliases=["Kendra"], description="Angular house classification."),
        _entity(entity_id="VEDA-HCLASS-TRIKONA", canonical_name="Trikona", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Trikona", transliteration="Trikona", aliases=["Trikona"], description="Trinal house classification."),
        _entity(entity_id="VEDA-HCLASS-DUSTHANA", canonical_name="Dusthana", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Dusthana", transliteration="Dusthana", aliases=["Dusthana"], description="Difficult house classification."),
        _entity(entity_id="VEDA-HCLASS-UPACHAYA", canonical_name="Upachaya", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Upachaya", transliteration="Upachaya", aliases=["Upachaya"], description="Growth-oriented house classification."),
        _entity(entity_id="VEDA-HCLASS-MARAKA", canonical_name="Maraka", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Maraka", transliteration="Maraka", aliases=["Maraka"], description="Killer-house classification used in longevity-related reasoning."),
        _entity(entity_id="VEDA-HCLASS-ARTHA", canonical_name="Artha", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Artha", transliteration="Artha", aliases=["Artha"], description="Material-purpose house grouping."),
        _entity(entity_id="VEDA-HCLASS-DHARMA", canonical_name="Dharma", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Dharma", transliteration="Dharma", aliases=["Dharma"], description="Duty-purpose house grouping."),
        _entity(entity_id="VEDA-HCLASS-KAMA", canonical_name="Kama", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Kama", transliteration="Kama", aliases=["Kama"], description="Desire-purpose house grouping."),
        _entity(entity_id="VEDA-HCLASS-MOKSHA", canonical_name="Moksha", entity_type=EntityType.HOUSE_CLASSIFICATION, sanskrit_name="Moksha", transliteration="Moksha", aliases=["Moksha"], description="Liberation-purpose house grouping."),
    ]

    documents["ontology/domains/domains.json"] = [
        _entity(entity_id="VEDA-DOMAIN-MARRIAGE", canonical_name="Marriage", entity_type=EntityType.DOMAIN, aliases=["Marriage"], description="Marriage and spousal matters."),
        _entity(entity_id="VEDA-DOMAIN-FINANCE", canonical_name="Finance", entity_type=EntityType.DOMAIN, aliases=["Finance"], description="Finance and money management."),
        _entity(entity_id="VEDA-DOMAIN-WEALTH", canonical_name="Wealth", entity_type=EntityType.DOMAIN, aliases=["Wealth"], description="Accumulated assets and wealth-building."),
        _entity(entity_id="VEDA-DOMAIN-CAREER", canonical_name="Career", entity_type=EntityType.DOMAIN, aliases=["Career", "Profession"], description="Career, public action, and profession."),
        _entity(entity_id="VEDA-DOMAIN-CHILDREN", canonical_name="Children", entity_type=EntityType.DOMAIN, aliases=["Children"], description="Children, fertility, and lineage topics."),
        _entity(entity_id="VEDA-DOMAIN-HEALTH", canonical_name="Health", entity_type=EntityType.DOMAIN, aliases=["Health"], description="Health and illness topics."),
        _entity(entity_id="VEDA-DOMAIN-LONGEVITY", canonical_name="Longevity", entity_type=EntityType.DOMAIN, aliases=["Longevity", "Ayurdaya"], description="Longevity-related topics.", source_status=EntitySourceStatus.CURATED_CANONICAL),
        _entity(entity_id="VEDA-DOMAIN-REMEDIES", canonical_name="Remedies", entity_type=EntityType.DOMAIN, aliases=["Remedies"], description="Remedial prescriptions and guidance."),
        _entity(entity_id="VEDA-DOMAIN-COMPATIBILITY", canonical_name="Compatibility", entity_type=EntityType.DOMAIN, aliases=["Compatibility"], description="Relationship compatibility and matching."),
        _entity(entity_id="VEDA-DOMAIN-ASTROFINANCE", canonical_name="AstroFinance", entity_type=EntityType.DOMAIN, aliases=["AstroFinance"], description="Non-classical finance-market experimentation kept separate from classical Jyotisha evidence.", source_status=EntitySourceStatus.LEGACY_UNGOVERNED),
    ]

    documents["ontology/yogas/yogas.json"] = [
        _entity(entity_id="VEDA-YOGA-GAJA_KESARI", canonical_name="Gaja Kesari", entity_type=EntityType.YOGA, aliases=["Gaja Kesari"], description="Yoga currently detected by runtime when Jupiter is in a kendra from the Moon."),
        _entity(entity_id="VEDA-YOGA-DHANA_YOGA", canonical_name="Dhana Yoga", entity_type=EntityType.YOGA, aliases=["Dhana Yoga"], description="Yoga category related to wealth combinations."),
        _entity(entity_id="VEDA-YOGA-RAJA_YOGA", canonical_name="Raja Yoga", entity_type=EntityType.YOGA, aliases=["Raja Yoga"], description="Yoga category related to prominence and elevation."),
        _entity(entity_id="VEDA-YOGA-VIPARITA_RAJA", canonical_name="Viparita Raja", entity_type=EntityType.YOGA, aliases=["Viparita Raja"], description="Yoga category related to reversal and gain through adversity."),
        _entity(entity_id="VEDA-YOGA-NEECHA_BHANGA", canonical_name="Neecha Bhanga", entity_type=EntityType.YOGA, aliases=["Neecha Bhanga"], description="Cancellation of debility yoga currently detected by runtime."),
        _entity(entity_id="VEDA-YOGA-KALA_SARPA", canonical_name="Kala Sarpa", entity_type=EntityType.YOGA, aliases=["Kala Sarpa"], description="Node-bound yoga currently detected by runtime."),
        _entity(entity_id="VEDA-YOGA-PARIVARTANA", canonical_name="Parivartana", entity_type=EntityType.YOGA, aliases=["Parivartana"], description="Sign-exchange yoga currently detected by runtime."),
        _entity(entity_id="VEDA-YOGA-KEMDRUM", canonical_name="Kemdrum", entity_type=EntityType.YOGA, aliases=["Kemdrum"], description="Legacy runtime yoga label preserved in ontology for mapping continuity.", source_status=EntitySourceStatus.LEGACY_UNGOVERNED),
        _entity(entity_id="VEDA-YOGA-GRAHA_YUDDHA", canonical_name="Graha Yuddha", entity_type=EntityType.YOGA, aliases=["Graha Yuddha"], description="Legacy runtime label preserved in ontology for mapping continuity.", source_status=EntitySourceStatus.LEGACY_UNGOVERNED),
        _entity(entity_id="VEDA-YOGA-MAHABHAGYA", canonical_name="Mahabhagya", entity_type=EntityType.YOGA, aliases=["Mahabhagya"], description="Legacy runtime label preserved in ontology for mapping continuity.", source_status=EntitySourceStatus.LEGACY_UNGOVERNED),
    ]

    documents["ontology/relations/core_relations.json"] = [
        _relation(relation_id="VEDA-REL-000001", subject_entity_id=graha_ids["Mars"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Aries"], description="Mars rules Aries in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000002", subject_entity_id=graha_ids["Venus"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Taurus"], description="Venus rules Taurus in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000003", subject_entity_id=graha_ids["Mercury"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Gemini"], description="Mercury rules Gemini in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000004", subject_entity_id=graha_ids["Moon"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Cancer"], description="Moon rules Cancer in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000005", subject_entity_id=graha_ids["Sun"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Leo"], description="Sun rules Leo in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000006", subject_entity_id=graha_ids["Mercury"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Virgo"], description="Mercury rules Virgo in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000007", subject_entity_id=graha_ids["Venus"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Libra"], description="Venus rules Libra in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000008", subject_entity_id=graha_ids["Mars"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Scorpio"], description="Mars rules Scorpio in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000009", subject_entity_id=graha_ids["Jupiter"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Sagittarius"], description="Jupiter rules Sagittarius in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000010", subject_entity_id=graha_ids["Saturn"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Capricorn"], description="Saturn rules Capricorn in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000011", subject_entity_id=graha_ids["Saturn"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Aquarius"], description="Saturn rules Aquarius in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000012", subject_entity_id=graha_ids["Jupiter"], relation_type=RelationType.RULES, object_entity_id=rashi_ids["Pisces"], description="Jupiter rules Pisces in the canonical ontology."),
        _relation(relation_id="VEDA-REL-000013", subject_entity_id=bhava_ids["2"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-WEALTH", description="Second house contributes to wealth ontology."),
        _relation(relation_id="VEDA-REL-000014", subject_entity_id=bhava_ids["5"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-FINANCE", description="Fifth house contributes to speculative finance ontology."),
        _relation(relation_id="VEDA-REL-000015", subject_entity_id=bhava_ids["7"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-MARRIAGE", description="Seventh house contributes to marriage ontology."),
        _relation(relation_id="VEDA-REL-000016", subject_entity_id=bhava_ids["8"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-LONGEVITY", description="Eighth house contributes to longevity ontology."),
        _relation(relation_id="VEDA-REL-000017", subject_entity_id=bhava_ids["10"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-CAREER", description="Tenth house contributes to career ontology."),
        _relation(relation_id="VEDA-REL-000018", subject_entity_id=bhava_ids["11"], relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-FINANCE", description="Eleventh house contributes to finance ontology."),
        _relation(relation_id="VEDA-REL-000019", subject_entity_id=varga_ids["D9"], relation_type=RelationType.SPECIALIZES, object_entity_id="VEDA-DOMAIN-MARRIAGE", description="Navamsha specializes marriage and dharma analysis."),
        _relation(relation_id="VEDA-REL-000020", subject_entity_id=varga_ids["D10"], relation_type=RelationType.SPECIALIZES, object_entity_id="VEDA-DOMAIN-CAREER", description="Dashamsha specializes career analysis."),
        _relation(relation_id="VEDA-REL-000021", subject_entity_id=varga_ids["D7"], relation_type=RelationType.SPECIALIZES, object_entity_id="VEDA-DOMAIN-CHILDREN", description="Saptamsha specializes children analysis."),
        _relation(relation_id="VEDA-REL-000022", subject_entity_id=varga_ids["D2"], relation_type=RelationType.SPECIALIZES, object_entity_id="VEDA-DOMAIN-WEALTH", description="Hora specializes wealth analysis."),
        _relation(relation_id="VEDA-REL-000023", subject_entity_id=dasha_ids["Mahadasha"], relation_type=RelationType.PART_OF, object_entity_id=dasha_ids["Vimshottari"], description="Mahadasha is part of the Vimshottari system."),
        _relation(relation_id="VEDA-REL-000024", subject_entity_id=dasha_ids["Antardasha"], relation_type=RelationType.PART_OF, object_entity_id=dasha_ids["Vimshottari"], description="Antardasha is part of the Vimshottari system."),
        _relation(relation_id="VEDA-REL-000025", subject_entity_id=dasha_ids["Pratyantardasha"], relation_type=RelationType.PART_OF, object_entity_id=dasha_ids["Vimshottari"], description="Pratyantardasha is part of the Vimshottari system."),
        _relation(relation_id="VEDA-REL-000026", subject_entity_id=graha_ids["Ketu"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Venus"], description="Ketu is followed by Venus in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000027", subject_entity_id=graha_ids["Venus"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Sun"], description="Venus is followed by Sun in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000028", subject_entity_id=graha_ids["Sun"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Moon"], description="Sun is followed by Moon in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000029", subject_entity_id=graha_ids["Moon"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Mars"], description="Moon is followed by Mars in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000030", subject_entity_id=graha_ids["Mars"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Rahu"], description="Mars is followed by Rahu in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000031", subject_entity_id=graha_ids["Rahu"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Jupiter"], description="Rahu is followed by Jupiter in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000032", subject_entity_id=graha_ids["Jupiter"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Saturn"], description="Jupiter is followed by Saturn in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000033", subject_entity_id=graha_ids["Saturn"], relation_type=RelationType.NEXT_IN_SEQUENCE, object_entity_id=graha_ids["Mercury"], description="Saturn is followed by Mercury in current Vimshottari order."),
        _relation(relation_id="VEDA-REL-000034", subject_entity_id="VEDA-YOGA-GAJA_KESARI", relation_type=RelationType.BELONGS_TO_DOMAIN, object_entity_id="VEDA-DOMAIN-FINANCE", description="Current runtime associates Gaja Kesari with positive institutional-trust and growth language in finance contexts.", source_status=EntitySourceStatus.LEGACY_UNGOVERNED),
    ]

    documents["rules/approved/VEDA-RUL-DASHA-000001.json"] = _rule(
        rule_id="VEDA-RUL-DASHA-000001",
        title="Vimshottari sequence and birth-balance baseline",
        domain="DASHA",
        subdomain="VIMSHOTTARI_DASHA_FOUNDATIONS",
        rule_type=RuleType.FOUNDATIONAL_ALGORITHM,
        status=RuleLifecycleStatus.IMPLEMENTATION_READY,
        source_class=SourceClass.CLASSICAL_PRIMARY,
        approval_status=ApprovalStatus.IMPLEMENTATION_READY,
        evidence_types=[EvidenceType.CLASSICAL_TEXTUAL],
        authority=_rule_authority(4, 4, 4, 0, 3, "P002 pilot sources establish order and Moon-based balance without migrating runtime logic."),
        provenance=_rule_provenance(
            source_ids=["VEDA-SRC-000001", "VEDA-SRC-000003"],
            passage_ids=["VEDA-PSG-000001", "VEDA-PSG-000002", "VEDA-PSG-000003"],
            claim_ids=["VEDA-CLM-000001", "VEDA-CLM-000002"],
        ),
        conditions=_conditions(
            all=[
                _condition_node(
                    condition_id="COND-DASHA-000001",
                    subject=_operand("chart.dashas.primary.entity_id", OperandKind.FACT_PATH),
                    operator=ConditionOperator.EQUALS,
                    value_entity_id=dasha_ids["Vimshottari"],
                ),
                _condition_node(
                    condition_id="COND-DASHA-000002",
                    subject=_operand("chart.dashas.primary.sequence_order", OperandKind.FACT_PATH),
                    operator=ConditionOperator.EQUALS,
                    value_entity_ids=[
                        graha_ids["Ketu"],
                        graha_ids["Venus"],
                        graha_ids["Sun"],
                        graha_ids["Moon"],
                        graha_ids["Mars"],
                        graha_ids["Rahu"],
                        graha_ids["Jupiter"],
                        graha_ids["Saturn"],
                        graha_ids["Mercury"],
                    ],
                ),
                _condition_node(
                    condition_id="COND-DASHA-000003",
                    subject=_operand("chart.dashas.primary.birth_balance_basis", OperandKind.FACT_PATH),
                    operator=ConditionOperator.EQUALS,
                    value="MOON_NAKSHATRA_REMAINDER",
                ),
            ]
        ),
        outcomes=[
            _rule_outcome(
                outcome_id="OUT-DASHA-000001",
                outcome_type=OutcomeType.CONTRACT_METADATA,
                target=_operand("chart.dashas.primary.sequence_order", OperandKind.FACT_PATH),
                value_entity_ids=[
                    graha_ids["Ketu"],
                    graha_ids["Venus"],
                    graha_ids["Sun"],
                    graha_ids["Moon"],
                    graha_ids["Mars"],
                    graha_ids["Rahu"],
                    graha_ids["Jupiter"],
                    graha_ids["Saturn"],
                    graha_ids["Mercury"],
                ],
                description="The governed rule preserves the current Vimshottari order without altering runtime calculation code.",
            ),
            _rule_outcome(
                outcome_id="OUT-DASHA-000002",
                outcome_type=OutcomeType.CONTRACT_METADATA,
                target=_operand("chart.dashas.primary.birth_balance_basis", OperandKind.FACT_PATH),
                value="MOON_NAKSHATRA_REMAINDER",
                description="Birth balance is derived from the unelapsed portion of the Moon's Janma Nakshatra.",
            ),
        ],
        notes="Governed rule captures the research-approved baseline for the current Vimshottari implementation path.",
    )

    documents["rules/approved/VEDA-RUL-DASHA-000002.json"] = _rule(
        rule_id="VEDA-RUL-DASHA-000002",
        title="Vimshottari default-path governance with coexistence metadata",
        domain="DASHA",
        subdomain="VIMSHOTTARI_DASHA_FOUNDATIONS",
        rule_type=RuleType.DASHA,
        status=RuleLifecycleStatus.APPROVED_WITH_CONDITIONS,
        source_class=SourceClass.CLASSICAL_PRIMARY,
        approval_status=ApprovalStatus.APPROVED_WITH_CONDITIONS,
        evidence_types=[EvidenceType.CLASSICAL_TEXTUAL, EvidenceType.TRADITIONAL_INTERPRETIVE],
        authority=_rule_authority(4, 4, 3, 0, 2, "P002 preserved a scoped contradiction between defaulting and coexistence."),
        provenance=_rule_provenance(
            source_ids=["VEDA-SRC-000001", "VEDA-SRC-000002"],
            passage_ids=["VEDA-PSG-000004", "VEDA-PSG-000005"],
            claim_ids=["VEDA-CLM-000005", "VEDA-CLM-000006"],
            conflict_ids=["VEDA-CNF-000001"],
        ),
        conditions=_conditions(
            all=[
                _condition_node(
                    condition_id="COND-DASHA-000004",
                    subject=_operand("chart.dashas.primary.entity_id", OperandKind.FACT_PATH),
                    operator=ConditionOperator.EQUALS,
                    value_entity_id=dasha_ids["Vimshottari"],
                )
            ]
        ),
        exceptions=[
            RuleException.model_validate(
                {
                    "exception_id": "EXC-DASHA-000001",
                    "conditions": _condition_node(
                        condition_id="COND-DASHA-000005",
                        subject=_operand("chart.context.alternate_dasha_scope", OperandKind.FACT_PATH),
                        operator=ConditionOperator.EQUALS,
                        value=True,
                    ),
                    "result": {
                        "suppress_rule": True,
                        "override_value": "COEXIST",
                        "note": "Alternate dasha scope remains preserved rather than erased by a universal default.",
                    },
                }
            ).model_dump(mode="json")
        ],
        outcomes=[
            _rule_outcome(
                outcome_id="OUT-DASHA-000003",
                outcome_type=OutcomeType.CONTRACT_METADATA,
                target=_operand("chart.dashas.primary.scope_policy", OperandKind.FACT_PATH),
                value="GENERAL_DEFAULT_NON_EXCLUSIVE",
                description="The governed ontology marks Vimshottari as the current default path without flattening alternate dasha evidence.",
            )
        ],
        notes="This rule demonstrates direct conflict linkage from rule to claim to conflict record.",
    )

    documents["rules/draft/VEDA-RUL-DIGNITY-000001.json"] = _rule(
        rule_id="VEDA-RUL-DIGNITY-000001",
        title="Jupiter exaltation sample mapping from current runtime dignity engine",
        domain="DIGNITY",
        subdomain="GRAHA_DIGNITY",
        rule_type=RuleType.DIGNITY,
        status=RuleLifecycleStatus.DRAFT,
        source_class=SourceClass.DERIVED_INTERNAL,
        approval_status=ApprovalStatus.NOT_SUBMITTED,
        evidence_types=[],
        authority=_rule_authority(0, 0, 0, 0, 2, "Legacy runtime mapping only; no approved P002 provenance attached in P003."),
        provenance=_rule_provenance(legacy_provenance_status=LegacyMappingStatus.LEGACY_UNSOURCED),
        conditions=_conditions(
            all=[
                _condition_node(
                    condition_id="COND-DIGNITY-000001",
                    subject=_operand("chart.planets.jupiter.rashi", OperandKind.FACT_PATH),
                    operator=ConditionOperator.EQUALS,
                    value_entity_id=rashi_ids["Cancer"],
                )
            ]
        ),
        modifiers=[
            RuleModifier.model_validate(
                {
                    "modifier_id": "MOD-DIGNITY-000001",
                    "condition": _condition_node(
                        condition_id="COND-DIGNITY-000002",
                        subject=_operand("chart.planets.jupiter.degrees_in_sign", OperandKind.FACT_PATH),
                        operator=ConditionOperator.BETWEEN,
                        value=[3.0, 7.0],
                    ),
                    "effect": {
                        "type": ModifierType.AMPLIFY,
                        "weight": 1.2,
                        "value": "EXALTED_EXACT",
                        "note": "Matches current runtime window of exact exaltation within two degrees of the canonical point.",
                    },
                }
            ).model_dump(mode="json")
        ],
        outcomes=[
            _rule_outcome(
                outcome_id="OUT-DIGNITY-000001",
                outcome_type=OutcomeType.CLASSIFICATION,
                target=_operand("chart.planets.jupiter.dignity", OperandKind.FACT_PATH),
                value_entity_id="VEDA-DIGNITY-EXALTATION",
                description="Pilot mapping of Jupiter exaltation in Cancer from the legacy dignity routine.",
            )
        ],
        notes="Draft rule exists to prove schema expressiveness for legacy dignity logic without inventing provenance.",
    )

    documents["rules/draft/VEDA-RUL-YOGA-000001.json"] = _rule(
        rule_id="VEDA-RUL-YOGA-000001",
        title="Gaja Kesari yoga sample mapping from current runtime",
        domain="YOGA",
        subdomain="GAJA_KESARI",
        rule_type=RuleType.YOGA,
        status=RuleLifecycleStatus.DRAFT,
        source_class=SourceClass.DERIVED_INTERNAL,
        approval_status=ApprovalStatus.NOT_SUBMITTED,
        evidence_types=[],
        authority=_rule_authority(0, 0, 0, 0, 3, "Legacy runtime mapping only; no approved P002 yoga provenance attached in P003."),
        provenance=_rule_provenance(legacy_provenance_status=LegacyMappingStatus.LEGACY_UNSOURCED),
        conditions=_conditions(
            all=[
                _condition_node(
                    any=[
                        _condition_node(
                            condition_id="COND-YOGA-000001",
                            subject=_operand("chart.relationships.jupiter_from_moon.house_distance", OperandKind.FACT_PATH),
                            operator=ConditionOperator.EQUALS,
                            value=0,
                        ),
                        _condition_node(
                            condition_id="COND-YOGA-000002",
                            subject=_operand("chart.relationships.jupiter_from_moon.house_distance", OperandKind.FACT_PATH),
                            operator=ConditionOperator.EQUALS,
                            value=3,
                        ),
                        _condition_node(
                            condition_id="COND-YOGA-000003",
                            subject=_operand("chart.relationships.jupiter_from_moon.house_distance", OperandKind.FACT_PATH),
                            operator=ConditionOperator.EQUALS,
                            value=6,
                        ),
                        _condition_node(
                            condition_id="COND-YOGA-000004",
                            subject=_operand("chart.relationships.jupiter_from_moon.house_distance", OperandKind.FACT_PATH),
                            operator=ConditionOperator.EQUALS,
                            value=9,
                        ),
                    ]
                )
            ]
        ),
        modifiers=[
            RuleModifier.model_validate(
                {
                    "modifier_id": "MOD-YOGA-000001",
                    "condition": _condition_node(
                        condition_id="COND-YOGA-000005",
                        subject=_operand("chart.relationships.jupiter_from_moon.house_distance", OperandKind.FACT_PATH),
                        operator=ConditionOperator.EQUALS,
                        value=0,
                    ),
                    "effect": {
                        "type": ModifierType.AMPLIFY,
                        "weight": 1.2,
                        "value": "STRONG",
                        "note": "Current runtime tags same-house Gaja Kesari as strong and other kendras as moderate.",
                    },
                }
            ).model_dump(mode="json")
        ],
        outcomes=[
            _rule_outcome(
                outcome_id="OUT-YOGA-000001",
                outcome_type=OutcomeType.DETECTION,
                target=_operand("chart.results.detected_yogas", OperandKind.FACT_PATH),
                value_entity_id="VEDA-YOGA-GAJA_KESARI",
                description="Pilot mapping of the Gaja Kesari yoga currently detected by kundli_engine._detect_yogas.",
            )
        ],
        notes="Draft rule demonstrates nested condition groups and modifier support without changing production yoga detection.",
    )

    documents["rules/legacy_mappings/VEDA-LMP-000001.json"] = _legacy_mapping(
        legacy_mapping_id="VEDA-LMP-000001",
        legacy_location="engines/intelligence/kundli_engine.py",
        legacy_function="KundliEngine._vimshottari_dasha",
        legacy_behavior="Current runtime derives Mahadasha, Antardasha, and Pratyantardasha using the Moon's Janma Nakshatra, the hard-coded Vimshottari sequence, and a remaining-portion birth-balance calculation.",
        target_rule_ids=["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"],
        mapping_status=LegacyMappingStatus.MAPPED_TO_SCHEMA,
        semantic_match=SemanticMatch.PARTIAL,
        known_differences=[
            "The runtime does not currently persist governed claim/source identifiers.",
            "The runtime does not currently surface coexistence metadata for alternate dasha scopes.",
        ],
        source_status=LegacyMappingStatus.SOURCE_VALIDATED,
        migration_recommendation="Retain the current deterministic implementation and add an adapter in a later phase rather than rewriting the engine.",
        notes="This mapping anchors the strongest governed rule pilot to the protected Vimshottari runtime path.",
    )

    documents["rules/legacy_mappings/VEDA-LMP-000002.json"] = _legacy_mapping(
        legacy_mapping_id="VEDA-LMP-000002",
        legacy_location="engines/intelligence/kundli_engine.py",
        legacy_function="KundliEngine._dignity",
        legacy_behavior="Current runtime computes exalted, exalted_exact, debilitated, moolatrikona, own_sign, friendly, enemy, and neutral states using hard-coded sign and degree tables.",
        target_rule_ids=["VEDA-RUL-DIGNITY-000001"],
        mapping_status=LegacyMappingStatus.MAPPED_TO_SCHEMA,
        semantic_match=SemanticMatch.PARTIAL,
        known_differences=[
            "The pilot rule maps only one dignity branch and does not yet model the full dignity table.",
            "No governed P002 claim provenance is attached yet for the legacy dignity table.",
        ],
        source_status=LegacyMappingStatus.LEGACY_UNSOURCED,
        migration_recommendation="Keep the current dignity table untouched until P004/P005 validate or replace each branch with governed source evidence.",
        notes="This record proves that legacy dignity logic can be represented without falsely claiming provenance.",
    )

    documents["rules/legacy_mappings/VEDA-LMP-000003.json"] = _legacy_mapping(
        legacy_mapping_id="VEDA-LMP-000003",
        legacy_location="engines/intelligence/kundli_engine.py",
        legacy_function="KundliEngine._detect_yogas",
        legacy_behavior="Current runtime detects Gaja Kesari when Jupiter is in a kendra from the Moon and labels same-house cases as strong.",
        target_rule_ids=["VEDA-RUL-YOGA-000001"],
        mapping_status=LegacyMappingStatus.MAPPED_TO_SCHEMA,
        semantic_match=SemanticMatch.EXACT,
        known_differences=[
            "The pilot rule preserves runtime logic only and does not yet attach governed classical yoga provenance.",
        ],
        source_status=LegacyMappingStatus.LEGACY_UNSOURCED,
        migration_recommendation="Use this mapping as the bridge for future yoga-source validation instead of rewriting the live detector now.",
        notes="This record demonstrates that compound legacy yoga logic can be mapped into nested conditions and modifiers.",
    )

    # P014 extends the approved-core foundation baseline with governed Graha/Bhava/Dignity rules.
    from engines.ai.knowledge.astrology_foundation_migration import (
        foundation_legacy_mappings as _p014_legacy_mappings,
        foundation_rules as _p014_rules,
    )

    for payload in _p014_rules():
        documents[f"rules/approved/{payload['rule_id']}.json"] = payload
    for payload in _p014_legacy_mappings():
        documents[f"rules/legacy_mappings/{payload['legacy_mapping_id']}.json"] = payload

    documents["rules/contracts/chart_facts_contract.sample.json"] = ChartFactsContract.model_validate(
        {
            "contract_version": CONTRACT_VERSION,
            "chart_id": "VEDA-CHART-SAMPLE-000001",
            "chart_type": ContractChartType.GENERIC,
            "lagna": {"entity_id": rashi_ids["Libra"], "longitude": 195.2},
            "planets": [
                {
                    "entity_id": graha_ids["Moon"],
                    "longitude": 102.4,
                    "rashi": rashi_ids["Cancer"],
                    "bhava": bhava_ids["10"],
                    "nakshatra": nak_ids["Pushya"],
                    "pada": 2,
                    "retrograde": False,
                    "dignity": "VEDA-DIGNITY-NEUTRAL_SIGN",
                },
                {
                    "entity_id": graha_ids["Jupiter"],
                    "longitude": 105.1,
                    "rashi": rashi_ids["Cancer"],
                    "bhava": bhava_ids["10"],
                    "nakshatra": nak_ids["Pushya"],
                    "pada": 3,
                    "retrograde": False,
                    "dignity": "VEDA-DIGNITY-EXALTATION",
                },
            ],
            "houses": [
                {
                    "entity_id": bhava_ids["10"],
                    "rashi": rashi_ids["Cancer"],
                    "lord": graha_ids["Moon"],
                    "occupants": [graha_ids["Moon"], graha_ids["Jupiter"]],
                }
            ],
            "vargas": [
                {
                    "entity_id": varga_ids["D9"],
                    "chart_signs": {
                        graha_ids["Moon"]: rashi_ids["Cancer"],
                        graha_ids["Jupiter"]: rashi_ids["Pisces"],
                    },
                }
            ],
            "dashas": [
                {
                    "entity_id": dasha_ids["Vimshottari"],
                    "sequence_order": [
                        graha_ids["Ketu"],
                        graha_ids["Venus"],
                        graha_ids["Sun"],
                        graha_ids["Moon"],
                        graha_ids["Mars"],
                        graha_ids["Rahu"],
                        graha_ids["Jupiter"],
                        graha_ids["Saturn"],
                        graha_ids["Mercury"],
                    ],
                    "birth_balance_basis": "MOON_NAKSHATRA_REMAINDER",
                }
            ],
            "relationships": {
                "jupiter_from_moon": {
                    "house_distance": 0,
                    "relationship_entity_id": "VEDA-RELTYPE-GRAHA_DRISHTI",
                }
            },
            "metadata": {
                "adapter_status": "P003_CONTRACT_SAMPLE",
                "legacy_paths": [
                    "engines/intelligence/kundli_engine.py::compute_human",
                    "engines/intelligence/kundli_engine.py::_vimshottari_dasha",
                    "engines/intelligence/kundli_engine.py::_detect_yogas",
                ],
            },
        }
    ).model_dump(mode="json")

    documents["rules/contracts/evaluation_result_contract.sample.json"] = RuleEvaluationResultRecord.model_validate(
        {
            "evaluation_id": "VEDA-EVL-000001",
            "rule_id": "VEDA-RUL-YOGA-000001",
            "matched": True,
            "conditions_met": ["COND-YOGA-000001"],
            "conditions_failed": [],
            "modifiers_applied": ["MOD-YOGA-000001"],
            "exceptions_triggered": [],
            "activation": ["NATAL"],
            "confidence": 0.82,
            "evidence": {
                "claim_ids": [],
                "passage_ids": [],
                "source_ids": [],
                "conflict_ids": [],
            },
            "outputs": [
                _rule_outcome(
                    outcome_id="OUT-EVAL-000001",
                    outcome_type=OutcomeType.DETECTION,
                    target=_operand("chart.results.detected_yogas", OperandKind.FACT_PATH),
                    value_entity_id="VEDA-YOGA-GAJA_KESARI",
                    description="Sample evaluation output showing why a future rule engine would report Gaja Kesari.",
                )
            ],
        }
    ).model_dump(mode="json")

    return documents


def write_default_documents(target_root: Path) -> list[Path]:
    written: list[Path] = []
    for relative_path, payload in default_documents().items():
        path = target_root / relative_path
        _write_json(path, payload)
        written.append(path)
    return written


def schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "entity.schema.json": EntityRecord.model_json_schema(),
        "relation.schema.json": RelationRecord.model_json_schema(),
        "rule.schema.json": AstrologyRuleRecord.model_json_schema(),
        "condition.schema.json": ConditionNode.model_json_schema(),
        "modifier.schema.json": RuleModifier.model_json_schema(),
        "exception.schema.json": RuleException.model_json_schema(),
        "legacy_mapping.schema.json": LegacyKnowledgeMappingRecord.model_json_schema(),
        "chart_facts.schema.json": ChartFactsContract.model_json_schema(),
        "evaluation_result.schema.json": RuleEvaluationResultRecord.model_json_schema(),
    }


def write_json_schemas(target_dir: Path) -> list[Path]:
    written: list[Path] = []
    for name, payload in schema_documents().items():
        path = target_dir / name
        _write_json(path, payload)
        written.append(path)
    return written


def _load_entity_records(ontology_root: Path, report: OntologyValidationReport) -> list[EntityRecord]:
    entities: list[EntityRecord] = []
    for path in sorted(ontology_root.rglob("*.json")):
        if "relations" in path.parts:
            continue
        try:
            payload = _load_json(path)
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                entities.append(EntityRecord.model_validate(item))
        except Exception as exc:  # pragma: no cover - exercised via invalid-payload tests
            report.errors.append(f"{path}: {exc}")
    return entities


def _load_relation_records(relation_root: Path, report: OntologyValidationReport) -> list[RelationRecord]:
    relations: list[RelationRecord] = []
    if not relation_root.exists():
        report.warnings.append(f"Missing relation directory: {relation_root}")
        return relations
    for path in sorted(relation_root.rglob("*.json")):
        try:
            payload = _load_json(path)
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                relations.append(RelationRecord.model_validate(item))
        except Exception as exc:  # pragma: no cover - exercised via invalid-payload tests
            report.errors.append(f"{path}: {exc}")
    return relations


def _load_rule_records(rule_root: Path, report: OntologyValidationReport) -> tuple[list[AstrologyRuleRecord], list[AstrologyRuleRecord]]:
    approved: list[AstrologyRuleRecord] = []
    draft: list[AstrologyRuleRecord] = []
    for directory, bucket in ((rule_root / "approved", approved), (rule_root / "draft", draft)):
        if not directory.exists():
            report.warnings.append(f"Missing rule directory: {directory}")
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                bucket.append(AstrologyRuleRecord.model_validate(_load_json(path)))
            except Exception as exc:  # pragma: no cover - exercised via invalid-payload tests
                report.errors.append(f"{path}: {exc}")
    return approved, draft


def _collect_condition_refs(node: ConditionNode, refs: list[OperandReference]) -> None:
    if node.subject is not None:
        refs.append(node.subject)
    if node.object is not None:
        refs.append(node.object)
    for child in node.all:
        _collect_condition_refs(child, refs)
    for child in node.any:
        _collect_condition_refs(child, refs)
    for child in node.none:
        _collect_condition_refs(child, refs)


def _validate_operand_reference(
    owner: str,
    operand: OperandReference,
    entity_ids: set[str],
    rule_ids: set[str],
    claim_ids: set[str],
    passage_ids: set[str],
    source_ids: set[str],
    conflict_ids: set[str],
    report: OntologyValidationReport,
) -> None:
    if operand.ref_type == OperandKind.ENTITY and operand.ref not in entity_ids:
        report.broken_references.append(f"{owner}: missing entity reference {operand.ref}")
    elif operand.ref_type == OperandKind.RULE and operand.ref not in rule_ids:
        report.broken_references.append(f"{owner}: missing rule reference {operand.ref}")
    elif operand.ref_type == OperandKind.CLAIM and operand.ref not in claim_ids:
        report.broken_references.append(f"{owner}: missing claim reference {operand.ref}")
    elif operand.ref_type == OperandKind.PASSAGE and operand.ref not in passage_ids:
        report.broken_references.append(f"{owner}: missing passage reference {operand.ref}")
    elif operand.ref_type == OperandKind.SOURCE and operand.ref not in source_ids:
        report.broken_references.append(f"{owner}: missing source reference {operand.ref}")
    elif operand.ref_type == OperandKind.CONFLICT and operand.ref not in conflict_ids:
        report.broken_references.append(f"{owner}: missing conflict reference {operand.ref}")
    elif operand.ref_type == OperandKind.FACT_PATH and not operand.ref.startswith("chart."):
        report.errors.append(f"{owner}: invalid fact-path operand {operand.ref}")


def _validate_condition_tree(
    owner: str,
    node: ConditionNode,
    entity_ids: set[str],
    rule_ids: set[str],
    claim_ids: set[str],
    passage_ids: set[str],
    source_ids: set[str],
    conflict_ids: set[str],
    report: OntologyValidationReport,
) -> None:
    refs: list[OperandReference] = []
    _collect_condition_refs(node, refs)
    for operand in refs:
        _validate_operand_reference(
            owner,
            operand,
            entity_ids,
            rule_ids,
            claim_ids,
            passage_ids,
            source_ids,
            conflict_ids,
            report,
        )
    if node.value_entity_id and node.value_entity_id not in entity_ids:
        report.broken_references.append(f"{owner}: missing value_entity_id reference {node.value_entity_id}")
    for entity_id in node.value_entity_ids:
        if entity_id not in entity_ids:
            report.broken_references.append(f"{owner}: missing value_entity_ids reference {entity_id}")
    for child in node.all:
        _validate_condition_tree(owner, child, entity_ids, rule_ids, claim_ids, passage_ids, source_ids, conflict_ids, report)
    for child in node.any:
        _validate_condition_tree(owner, child, entity_ids, rule_ids, claim_ids, passage_ids, source_ids, conflict_ids, report)
    for child in node.none:
        _validate_condition_tree(owner, child, entity_ids, rule_ids, claim_ids, passage_ids, source_ids, conflict_ids, report)


def _validate_rule_dependencies(rules: list[AstrologyRuleRecord], report: OntologyValidationReport) -> None:
    graph = {rule.rule_id: list(rule.depends_on_rule_ids) for rule in rules}
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            report.errors.append(f"circular rule dependency detected at {node}")
            return
        visiting.add(node)
        for neighbor in graph.get(node, []):
            walk(neighbor)
        visiting.remove(node)
        visited.add(node)

    for rule_id in graph:
        walk(rule_id)


def validate_ontology_directory(
    root: Path | None = None,
    research_root: Path | None = None,
) -> OntologyValidationReport:
    base_root = Path(root or cfg.VEDA_CACHE_DIR)
    ontology_root = base_root / "ontology"
    relation_root = cfg.VEDA_ASTROLOGY_RELATION_DIR if root is None else ontology_root / "relations"
    rule_root = base_root / "rules"
    research_dir = Path(research_root or cfg.VEDA_ASTROLOGY_RESEARCH_DIR)

    report = OntologyValidationReport()

    governance = load_governance_registry(research_dir)
    source_ids = {item.source_id for item in governance["sources"] if hasattr(item, "source_id")}
    passage_ids = {item.passage_id for item in governance["passages"] if hasattr(item, "passage_id")}
    claim_ids = {item.claim_id for item in governance["claims"] if hasattr(item, "claim_id")}
    conflict_ids = {item.conflict_id for item in governance["conflicts"] if hasattr(item, "conflict_id")}

    entities = _load_entity_records(ontology_root, report)
    relations = _load_relation_records(relation_root, report)
    approved_rules, draft_rules = _load_rule_records(rule_root, report)

    entity_ids: set[str] = set()
    for entity in entities:
        if entity.entity_id in entity_ids:
            report.duplicate_ids.append(entity.entity_id)
        entity_ids.add(entity.entity_id)

    relation_ids: set[str] = set()
    for relation in relations:
        if relation.relation_id in relation_ids:
            report.duplicate_ids.append(relation.relation_id)
        relation_ids.add(relation.relation_id)
        if relation.subject_entity_id not in entity_ids:
            report.broken_references.append(
                f"{relation.relation_id}: missing subject entity reference {relation.subject_entity_id}"
            )
        if relation.object_entity_id not in entity_ids:
            report.broken_references.append(
                f"{relation.relation_id}: missing object entity reference {relation.object_entity_id}"
            )

    rules = approved_rules + draft_rules
    all_rule_ids = {rule.rule_id for rule in rules}
    rule_ids: set[str] = set()
    for rule in rules:
        if rule.rule_id in rule_ids:
            report.duplicate_ids.append(rule.rule_id)
        rule_ids.add(rule.rule_id)
        for source_id in rule.provenance.source_ids:
            if source_id not in source_ids:
                report.broken_references.append(f"{rule.rule_id}: missing source reference {source_id}")
        for passage_id in rule.provenance.passage_ids:
            if passage_id not in passage_ids:
                report.broken_references.append(f"{rule.rule_id}: missing passage reference {passage_id}")
        for claim_id in rule.provenance.claim_ids:
            if claim_id not in claim_ids:
                report.broken_references.append(f"{rule.rule_id}: missing claim reference {claim_id}")
        for conflict_id in rule.provenance.conflict_ids:
            if conflict_id not in conflict_ids:
                report.broken_references.append(f"{rule.rule_id}: missing conflict reference {conflict_id}")

        for node in rule.conditions.all + rule.conditions.any + rule.conditions.none:
            _validate_condition_tree(
                rule.rule_id,
                node,
                entity_ids,
                all_rule_ids,
                claim_ids,
                passage_ids,
                source_ids,
                conflict_ids,
                report,
            )
        for modifier in rule.modifiers:
            _validate_condition_tree(
                f"{rule.rule_id}:{modifier.modifier_id}",
                modifier.condition,
                entity_ids,
                all_rule_ids,
                claim_ids,
                passage_ids,
                source_ids,
                conflict_ids,
                report,
            )
        for exception in rule.exceptions:
            _validate_condition_tree(
                f"{rule.rule_id}:{exception.exception_id}",
                exception.conditions,
                entity_ids,
                all_rule_ids,
                claim_ids,
                passage_ids,
                source_ids,
                conflict_ids,
                report,
            )
        for confirmation in rule.confirmations:
            _validate_condition_tree(
                f"{rule.rule_id}:{confirmation.confirmation_id}",
                confirmation.condition,
                entity_ids,
                all_rule_ids,
                claim_ids,
                passage_ids,
                source_ids,
                conflict_ids,
                report,
            )
        for activation in rule.activations:
            _validate_condition_tree(
                f"{rule.rule_id}:{activation.activation_id}",
                activation.condition,
                entity_ids,
                all_rule_ids,
                claim_ids,
                passage_ids,
                source_ids,
                conflict_ids,
                report,
            )
        for outcome in rule.outcomes:
            if outcome.target is not None:
                _validate_operand_reference(
                    f"{rule.rule_id}:{outcome.outcome_id}",
                    outcome.target,
                    entity_ids,
                    all_rule_ids,
                    claim_ids,
                    passage_ids,
                    source_ids,
                    conflict_ids,
                    report,
                )
            if outcome.value_entity_id and outcome.value_entity_id not in entity_ids:
                report.broken_references.append(
                    f"{rule.rule_id}:{outcome.outcome_id}: missing value_entity_id reference {outcome.value_entity_id}"
                )
            for entity_id in outcome.value_entity_ids:
                if entity_id not in entity_ids:
                    report.broken_references.append(
                        f"{rule.rule_id}:{outcome.outcome_id}: missing value_entity_ids reference {entity_id}"
                    )
        for ref_id in rule.depends_on_rule_ids + rule.cancelled_by_rule_ids:
            if ref_id not in all_rule_ids:
                report.broken_references.append(f"{rule.rule_id}: missing rule dependency reference {ref_id}")

    _validate_rule_dependencies(rules, report)

    legacy_mappings: list[LegacyKnowledgeMappingRecord] = []
    mapping_dir = rule_root / "legacy_mappings"
    if not mapping_dir.exists():
        report.warnings.append(f"Missing legacy mapping directory: {mapping_dir}")
    else:
        for path in sorted(mapping_dir.glob("*.json")):
            try:
                mapping = LegacyKnowledgeMappingRecord.model_validate(_load_json(path))
                legacy_mappings.append(mapping)
                for rule_id in mapping.target_rule_ids:
                    if rule_id not in all_rule_ids:
                        report.broken_references.append(
                            f"{mapping.legacy_mapping_id}: missing target rule reference {rule_id}"
                        )
            except Exception as exc:  # pragma: no cover - exercised via invalid-payload tests
                report.errors.append(f"{path}: {exc}")

    contract_dir = rule_root / "contracts"
    chart_contracts: list[ChartFactsContract] = []
    evaluation_contracts: list[RuleEvaluationResultRecord] = []
    if not contract_dir.exists():
        report.warnings.append(f"Missing contract directory: {contract_dir}")
    else:
        for path in sorted(contract_dir.glob("*.json")):
            try:
                payload = _load_json(path)
                if "chart_facts_contract" in path.name or "chart_facts" in path.name:
                    contract = ChartFactsContract.model_validate(payload)
                    chart_contracts.append(contract)
                    if contract.lagna.entity_id not in entity_ids:
                        report.broken_references.append(
                            f"{contract.chart_id}: missing lagna entity reference {contract.lagna.entity_id}"
                        )
                    for planet in contract.planets:
                        for entity_id in (planet.entity_id, planet.rashi, planet.bhava, planet.nakshatra, planet.dignity):
                            if entity_id not in entity_ids:
                                report.broken_references.append(
                                    f"{contract.chart_id}: missing planet contract entity reference {entity_id}"
                                )
                    for house in contract.houses:
                        refs = [house.entity_id, house.rashi, house.lord, *house.occupants]
                        for entity_id in refs:
                            if entity_id not in entity_ids:
                                report.broken_references.append(
                                    f"{contract.chart_id}: missing house contract entity reference {entity_id}"
                                )
                    for varga in contract.vargas:
                        if varga.entity_id not in entity_ids:
                            report.broken_references.append(
                                f"{contract.chart_id}: missing varga entity reference {varga.entity_id}"
                            )
                        for key, value in varga.chart_signs.items():
                            for entity_id in (key, value):
                                if entity_id not in entity_ids:
                                    report.broken_references.append(
                                        f"{contract.chart_id}: missing varga chart-sign entity reference {entity_id}"
                                    )
                    for dasha in contract.dashas:
                        if dasha.entity_id not in entity_ids:
                            report.broken_references.append(
                                f"{contract.chart_id}: missing dasha entity reference {dasha.entity_id}"
                            )
                        for entity_id in dasha.sequence_order:
                            if entity_id not in entity_ids:
                                report.broken_references.append(
                                    f"{contract.chart_id}: missing dasha sequence entity reference {entity_id}"
                                )
                else:
                    evaluation = RuleEvaluationResultRecord.model_validate(payload)
                    evaluation_contracts.append(evaluation)
                    if evaluation.rule_id not in rule_ids:
                        report.broken_references.append(
                            f"{evaluation.evaluation_id}: missing evaluated rule reference {evaluation.rule_id}"
                        )
                    for claim_id in evaluation.evidence.claim_ids:
                        if claim_id not in claim_ids:
                            report.broken_references.append(
                                f"{evaluation.evaluation_id}: missing evidence claim reference {claim_id}"
                            )
                    for passage_id in evaluation.evidence.passage_ids:
                        if passage_id not in passage_ids:
                            report.broken_references.append(
                                f"{evaluation.evaluation_id}: missing evidence passage reference {passage_id}"
                            )
                    for source_id in evaluation.evidence.source_ids:
                        if source_id not in source_ids:
                            report.broken_references.append(
                                f"{evaluation.evaluation_id}: missing evidence source reference {source_id}"
                            )
                    for conflict_id in evaluation.evidence.conflict_ids:
                        if conflict_id not in conflict_ids:
                            report.broken_references.append(
                                f"{evaluation.evaluation_id}: missing evidence conflict reference {conflict_id}"
                            )
                    for outcome in evaluation.outputs:
                        if outcome.target is not None:
                            _validate_operand_reference(
                                f"{evaluation.evaluation_id}:{outcome.outcome_id}",
                                outcome.target,
                                entity_ids,
                                rule_ids,
                                claim_ids,
                                passage_ids,
                                source_ids,
                                conflict_ids,
                                report,
                            )
                        if outcome.value_entity_id and outcome.value_entity_id not in entity_ids:
                            report.broken_references.append(
                                f"{evaluation.evaluation_id}:{outcome.outcome_id}: missing output entity reference {outcome.value_entity_id}"
                            )
            except Exception as exc:  # pragma: no cover - exercised via invalid-payload tests
                report.errors.append(f"{path}: {exc}")

    report.entity_count = len(entity_ids)
    report.relation_count = len(relations)
    report.approved_rule_count = len(approved_rules)
    report.draft_rule_count = len(draft_rules)
    report.legacy_mapping_count = len(legacy_mappings)
    report.chart_contract_count = len(chart_contracts)
    report.evaluation_contract_count = len(evaluation_contracts)

    if report.broken_references:
        report.errors.extend(report.broken_references)
    if report.duplicate_ids:
        report.errors.extend([f"duplicate identifier detected: {value}" for value in report.duplicate_ids])

    return report


__all__ = [
    "AstrologyRuleRecord",
    "ChartFactsContract",
    "ConditionNode",
    "EntityRecord",
    "LegacyKnowledgeMappingRecord",
    "OntologyValidationReport",
    "RelationRecord",
    "RuleEvaluationResultRecord",
    "RuleModifier",
    "RuleException",
    "default_documents",
    "schema_documents",
    "validate_ontology_directory",
    "write_default_documents",
    "write_json_schemas",
]
