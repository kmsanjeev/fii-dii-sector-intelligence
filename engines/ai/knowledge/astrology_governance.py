from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from engines.common import config as cfg

CONTRACT_VERSION = getattr(cfg, "VEDA_ASTROLOGY_GOVERNANCE_VERSION", "2026-08-10")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _is_iso_datetime(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class SourceClass(str, Enum):
    CLASSICAL_PRIMARY = "CLASSICAL_PRIMARY"
    CLASSICAL_COMMENTARY = "CLASSICAL_COMMENTARY"
    TRADITIONAL_SECONDARY = "TRADITIONAL_SECONDARY"
    MODERN_PRACTITIONER = "MODERN_PRACTITIONER"
    ACADEMIC_SECONDARY = "ACADEMIC_SECONDARY"
    EMPIRICAL_RESEARCH = "EMPIRICAL_RESEARCH"
    REFERENCE_EDITION = "REFERENCE_EDITION"
    DERIVED_INTERNAL = "DERIVED_INTERNAL"
    HYPOTHESIS = "HYPOTHESIS"
    FOLKLORE_OR_UNVERIFIED = "FOLKLORE_OR_UNVERIFIED"


class AuthorityTier(str, Enum):
    TIER_A = "TIER_A"
    TIER_B = "TIER_B"
    TIER_C = "TIER_C"
    TIER_D = "TIER_D"
    TIER_E = "TIER_E"
    TIER_F = "TIER_F"
    TIER_U = "TIER_U"


class EvidenceType(str, Enum):
    CLASSICAL_TEXTUAL = "CLASSICAL_TEXTUAL"
    TRADITIONAL_INTERPRETIVE = "TRADITIONAL_INTERPRETIVE"
    MODERN_ASTROLOGY = "MODERN_ASTROLOGY"
    EMPIRICAL_MARKET = "EMPIRICAL_MARKET"
    INTERNAL_HYPOTHESIS = "INTERNAL_HYPOTHESIS"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PASSAGE_VERIFIED = "PASSAGE_VERIFIED"
    METADATA_VERIFIED = "METADATA_VERIFIED"
    PARTIAL = "PARTIAL"
    REFERENCE_NOT_VERIFIED = "REFERENCE_NOT_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNKNOWN"


class LegalAccessStatus(str, Enum):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    LICENSED_OR_COPYRIGHTED = "LICENSED_OR_COPYRIGHTED"
    LIMITED_QUOTATION_ONLY = "LIMITED_QUOTATION_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    UNKNOWN = "UNKNOWN"


class PrimarySecondaryStatus(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"
    UNKNOWN = "UNKNOWN"


class QualityGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    U = "U"


class ArtifactStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PILOT = "PILOT"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class WorkflowState(str, Enum):
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    EXTRACTED = "EXTRACTED"
    CROSS_REFERENCED = "CROSS_REFERENCED"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVIEWED = "REVIEWED"
    CONFLICT_FOUND = "CONFLICT_FOUND"
    NEEDS_MORE_RESEARCH = "NEEDS_MORE_RESEARCH"
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    REJECTED = "REJECTED"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"
    IMPLEMENTED = "IMPLEMENTED"
    VALIDATED = "VALIDATED"
    SUPERSEDED = "SUPERSEDED"


class InterpretationType(str, Enum):
    TEXTUAL_LITERAL = "TEXTUAL_LITERAL"
    COMMENTARIAL = "COMMENTARIAL"
    DERIVED_RULE = "DERIVED_RULE"
    IMPLEMENTATION_NOTE = "IMPLEMENTATION_NOTE"
    HYPOTHESIS = "HYPOTHESIS"


class SupportLevel(str, Enum):
    SINGLE_SOURCE = "SINGLE_SOURCE"
    MULTI_SOURCE = "MULTI_SOURCE"
    CROSS_VERIFIED = "CROSS_VERIFIED"
    CONFLICTED = "CONFLICTED"
    HYPOTHETICAL = "HYPOTHETICAL"


class ConflictType(str, Enum):
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
    PARTIAL_CONTRADICTION = "PARTIAL_CONTRADICTION"
    DIFFERENT_SCOPE = "DIFFERENT_SCOPE"
    DIFFERENT_CONDITION = "DIFFERENT_CONDITION"
    DIFFERENT_SCHOOL = "DIFFERENT_SCHOOL"
    TRANSLATION_VARIANCE = "TRANSLATION_VARIANCE"
    COMMENTARIAL_VARIANCE = "COMMENTARIAL_VARIANCE"
    TEMPORAL_OR_TRADITION_VARIANCE = "TEMPORAL_OR_TRADITION_VARIANCE"
    APPARENT_ONLY = "APPARENT_ONLY"
    UNRESOLVED = "UNRESOLVED"


class ConflictResolutionStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    COEXIST = "COEXIST"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    SOURCE_A_PREFERRED = "SOURCE_A_PREFERRED"
    SOURCE_B_PREFERRED = "SOURCE_B_PREFERRED"
    COMPOSITE_RULE = "COMPOSITE_RULE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ApprovalRole(str, Enum):
    RESEARCHER = "RESEARCHER"
    REVIEWER = "REVIEWER"
    DOMAIN_APPROVER = "DOMAIN_APPROVER"
    ENGINEERING_APPROVER = "ENGINEERING_APPROVER"
    VALIDATION_APPROVER = "VALIDATION_APPROVER"


class ApprovalStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    REJECTED = "REJECTED"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"


class AllowedOutputMode(str, Enum):
    STANDARD = "STANDARD"
    TRADITIONAL_INTERPRETATION_ONLY = "TRADITIONAL_INTERPRETATION_ONLY"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    NO_END_USER_OUTPUT = "NO_END_USER_OUTPUT"


class LegacyRuleStatus(str, Enum):
    LEGACY_UNSOURCED = "LEGACY_UNSOURCED"
    LEGACY_PARTIALLY_SOURCED = "LEGACY_PARTIALLY_SOURCED"
    SOURCE_VALIDATED = "SOURCE_VALIDATED"
    RULE_MIGRATED = "RULE_MIGRATED"
    SUPERSEDED = "SUPERSEDED"


class ArtifactType(str, Enum):
    SOURCE = "SOURCE"
    PASSAGE = "PASSAGE"
    CLAIM = "CLAIM"
    CONFLICT = "CONFLICT"
    CLAIM_SET = "CLAIM_SET"
    PILOT_TOPIC = "PILOT_TOPIC"
    LEGACY_RULE_SET = "LEGACY_RULE_SET"


class GovernedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "1.0.0"
    status: ArtifactStatus = ArtifactStatus.ACTIVE
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
            raise ValueError("version must use semantic version format, for example 1.0.0")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_datetime(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value

    @field_validator("created_by", "updated_by", "change_reason")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("field must be a non-empty string")
        return value.strip()


class AuthorityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authority_tier: AuthorityTier
    textual_authority: int = Field(ge=0, le=5)
    traditional_authority: int = Field(ge=0, le=5)
    translation_reliability: int = Field(ge=0, le=5)
    cross_source_support: int = Field(ge=0, le=5)
    empirical_support: int = Field(ge=0, le=5)
    implementation_confidence: int = Field(ge=0, le=5)
    notes: str | None = None


class AstrologySourceRecord(GovernedArtifact):
    source_id: str
    title_original: str | None = None
    title_normalized: str
    source_class: SourceClass
    author_attributed: str | None = None
    author_normalized: str | None = None
    historical_period: str | None = None
    language_original: str | None = None
    edition: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    translator: str | None = None
    commentator: str | None = None
    isbn_or_identifier: str | None = None
    digital_source: str | None = None
    legal_access_status: LegalAccessStatus = LegalAccessStatus.UNKNOWN
    primary_or_secondary: PrimarySecondaryStatus = PrimarySecondaryStatus.UNKNOWN
    tradition: str | None = None
    school: str | None = None
    domains: list[str] = Field(default_factory=list)
    quality_grade: QualityGrade = QualityGrade.U
    authority_score: int | None = Field(default=None, ge=0, le=100)
    authority_profile: AuthorityProfile
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence_type: EvidenceType = EvidenceType.CLASSICAL_TEXTUAL

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-SRC-\d{6}", value):
            raise ValueError("source_id must match VEDA-SRC-000001")
        return value

    @field_validator("title_normalized")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title_normalized is required")
        return value.strip()

    @field_validator("domains")
    @classmethod
    def _validate_domains(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in value if isinstance(item, str) and item.strip()]
        if not cleaned:
            raise ValueError("domains must contain at least one value")
        return cleaned


class PassageRecord(GovernedArtifact):
    passage_id: str
    source_id: str
    work: str
    chapter: str | None = None
    section: str | None = None
    verse_start: str | None = None
    verse_end: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    original_language: str | None = None
    original_text: str | None = None
    transliteration: str | None = None
    translation: str | None = None
    translator: str | None = None
    commentator: str | None = None
    context_before: str | None = None
    context_after: str | None = None
    topics: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    citation_label: str

    @field_validator("passage_id")
    @classmethod
    def _validate_passage_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-PSG-\d{6}", value):
            raise ValueError("passage_id must match VEDA-PSG-000001")
        return value

    @field_validator("source_id")
    @classmethod
    def _validate_source_ref(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-SRC-\d{6}", value):
            raise ValueError("source_id must match VEDA-SRC-000001")
        return value

    @field_validator("topics", "domains")
    @classmethod
    def _normalize_lists(cls, value: list[str]) -> list[str]:
        return [item.strip().upper() for item in value if isinstance(item, str) and item.strip()]

    @field_validator("citation_label")
    @classmethod
    def _validate_citation_label(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("citation_label is required")
        return value.strip()


class ClaimRecord(GovernedArtifact):
    claim_id: str
    claim_text: str
    domain: str
    subdomain: str | None = None
    source_passages: list[str] = Field(default_factory=list)
    interpretation_type: InterpretationType
    support_level: SupportLevel
    evidence_types: list[EvidenceType] = Field(default_factory=list)
    conflicting_claims: list[str] = Field(default_factory=list)
    research_status: WorkflowState
    approval_status: ApprovalStatus = ApprovalStatus.NOT_SUBMITTED
    high_stakes: bool = False
    requires_safety_review: bool = False
    allowed_output_mode: AllowedOutputMode = AllowedOutputMode.STANDARD

    @field_validator("claim_id")
    @classmethod
    def _validate_claim_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-CLM-\d{6}", value):
            raise ValueError("claim_id must match VEDA-CLM-000001")
        return value

    @field_validator("claim_text")
    @classmethod
    def _validate_claim_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim_text is required")
        return value.strip()

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("domain is required")
        return value.strip().upper()

    @field_validator("subdomain")
    @classmethod
    def _validate_subdomain(cls, value: str | None) -> str | None:
        return value.strip().upper() if isinstance(value, str) and value.strip() else None

    @field_validator("source_passages")
    @classmethod
    def _validate_passages(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("source_passages must contain at least one passage id")
        for item in value:
            if not re.fullmatch(r"VEDA-PSG-\d{6}", item):
                raise ValueError("source_passages entries must match VEDA-PSG-000001")
        return value

    @field_validator("conflicting_claims")
    @classmethod
    def _validate_conflicts(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CLM-\d{6}", item):
                raise ValueError("conflicting_claims entries must match VEDA-CLM-000001")
        return value

    @field_validator("requires_safety_review")
    @classmethod
    def _validate_safety_boolean(cls, value: bool) -> bool:
        return bool(value)


class ConflictRecord(GovernedArtifact):
    conflict_id: str
    topic: str
    claim_a: str
    claim_b: str
    source_a: str | None = None
    source_b: str | None = None
    conflict_type: ConflictType
    analysis: str
    possible_reconciliation: str | None = None
    school_context: str | None = None
    implementation_impact: str
    resolution_status: ConflictResolutionStatus
    approved_resolution: str | None = None
    confidence: int = Field(ge=0, le=5)

    @field_validator("conflict_id")
    @classmethod
    def _validate_conflict_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-CNF-\d{6}", value):
            raise ValueError("conflict_id must match VEDA-CNF-000001")
        return value

    @field_validator("claim_a", "claim_b")
    @classmethod
    def _validate_claim_ref(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-CLM-\d{6}", value):
            raise ValueError("claim references must match VEDA-CLM-000001")
        return value

    @field_validator("source_a", "source_b")
    @classmethod
    def _validate_source_ref_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch(r"VEDA-SRC-\d{6}", value):
            raise ValueError("source references must match VEDA-SRC-000001")
        return value


class RoleDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: ApprovalRole
    actor: str
    decision: ApprovalStatus
    decided_at: str
    note: str | None = None

    @field_validator("actor")
    @classmethod
    def _validate_actor(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("actor is required")
        return value.strip()

    @field_validator("decided_at")
    @classmethod
    def _validate_decided_at(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("decided_at must be ISO-8601")
        return value


class ApprovalRecord(GovernedArtifact):
    approval_id: str
    artifact_type: ArtifactType
    artifact_ids: list[str] = Field(default_factory=list)
    pilot_domain: str | None = None
    workflow_state: WorkflowState
    approval_status: ApprovalStatus
    role_decisions: list[RoleDecision] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    implementation_ready: bool = False
    validated_against_runtime: bool = False

    @field_validator("approval_id")
    @classmethod
    def _validate_approval_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-APR-\d{6}", value):
            raise ValueError("approval_id must match VEDA-APR-000001")
        return value

    @field_validator("artifact_ids")
    @classmethod
    def _validate_artifact_ids(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("artifact_ids must contain at least one identifier")
        return value

    @field_validator("pilot_domain")
    @classmethod
    def _validate_pilot_domain(cls, value: str | None) -> str | None:
        return value.strip().upper() if isinstance(value, str) and value.strip() else None


class DomainPolicyRecord(GovernedArtifact):
    policy_id: str
    domain: str
    subdomain: str | None = None
    high_stakes: bool
    requires_safety_review: bool
    allowed_output_mode: AllowedOutputMode
    review_requirements: list[str] = Field(default_factory=list)

    @field_validator("policy_id")
    @classmethod
    def _validate_policy_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-PLC-\d{6}", value):
            raise ValueError("policy_id must match VEDA-PLC-000001")
        return value

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("domain is required")
        return value.strip().upper()

    @field_validator("subdomain")
    @classmethod
    def _validate_subdomain(cls, value: str | None) -> str | None:
        return value.strip().upper() if isinstance(value, str) and value.strip() else None


class LegacyRuleEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legacy_rule_id: str
    capability: str
    module_path: str
    status: LegacyRuleStatus
    mapped_claim_ids: list[str] = Field(default_factory=list)
    provenance_note: str
    migration_strategy: str

    @field_validator("legacy_rule_id")
    @classmethod
    def _validate_legacy_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-LRY-\d{6}", value):
            raise ValueError("legacy_rule_id must match VEDA-LRY-000001")
        return value

    @field_validator("mapped_claim_ids")
    @classmethod
    def _validate_mapped_claim_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"VEDA-CLM-\d{6}", item):
                raise ValueError("mapped_claim_ids entries must match VEDA-CLM-000001")
        return value


class LegacyRuleRegister(GovernedArtifact):
    register_id: str
    scope: str
    entries: list[LegacyRuleEntry] = Field(default_factory=list)

    @field_validator("register_id")
    @classmethod
    def _validate_register_id(cls, value: str) -> str:
        if not re.fullmatch(r"VEDA-LGC-\d{6}", value):
            raise ValueError("register_id must match VEDA-LGC-000001")
        return value

    @field_validator("entries")
    @classmethod
    def _validate_entries(cls, value: list[LegacyRuleEntry]) -> list[LegacyRuleEntry]:
        if not value:
            raise ValueError("entries must contain at least one legacy rule entry")
        return value


@dataclass(slots=True)
class RegistryValidationReport:
    source_count: int = 0
    passage_count: int = 0
    claim_count: int = 0
    conflict_count: int = 0
    approval_count: int = 0
    policy_count: int = 0
    legacy_register_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def assert_valid(self) -> None:
        if self.errors:
            raise AssertionError("Registry validation failed:\n- " + "\n- ".join(self.errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_count": self.source_count,
            "passage_count": self.passage_count,
            "claim_count": self.claim_count,
            "conflict_count": self.conflict_count,
            "approval_count": self.approval_count,
            "policy_count": self.policy_count,
            "legacy_register_count": self.legacy_register_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "is_valid": self.is_valid,
        }


def schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "source.schema.json": AstrologySourceRecord.model_json_schema(),
        "passage.schema.json": PassageRecord.model_json_schema(),
        "claim.schema.json": ClaimRecord.model_json_schema(),
        "conflict.schema.json": ConflictRecord.model_json_schema(),
        "approval.schema.json": ApprovalRecord.model_json_schema(),
        "domain_policy.schema.json": DomainPolicyRecord.model_json_schema(),
        "legacy_rule_register.schema.json": LegacyRuleRegister.model_json_schema(),
    }


def write_json_schemas(target_dir: Path) -> list[Path]:
    written: list[Path] = []
    for name, payload in schema_documents().items():
        path = target_dir / name
        _write_json(path, payload)
        written.append(path)
    return written


def load_registry(root: Path | None = None) -> dict[str, list[BaseModel]]:
    base_dir = Path(root or cfg.VEDA_ASTROLOGY_RESEARCH_DIR)
    directories = {
        "sources": (base_dir / "sources", AstrologySourceRecord),
        "passages": (base_dir / "passages", PassageRecord),
        "claims": (base_dir / "claims", ClaimRecord),
        "conflicts": (base_dir / "conflicts", ConflictRecord),
        "approvals": (base_dir / "approvals", ApprovalRecord),
        "policies": (base_dir / "policies", DomainPolicyRecord),
        "legacy": (base_dir / "legacy", LegacyRuleRegister),
    }
    loaded: dict[str, list[BaseModel]] = {}
    for key, (directory, model_cls) in directories.items():
        items: list[BaseModel] = []
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                items.append(model_cls.model_validate(_load_json(path)))
        loaded[key] = items
    return loaded


def validate_registry_directory(root: Path | None = None) -> RegistryValidationReport:
    base_dir = Path(root or cfg.VEDA_ASTROLOGY_RESEARCH_DIR)
    report = RegistryValidationReport()
    directories = {
        "sources": (base_dir / "sources", AstrologySourceRecord),
        "passages": (base_dir / "passages", PassageRecord),
        "claims": (base_dir / "claims", ClaimRecord),
        "conflicts": (base_dir / "conflicts", ConflictRecord),
        "approvals": (base_dir / "approvals", ApprovalRecord),
        "policies": (base_dir / "policies", DomainPolicyRecord),
        "legacy": (base_dir / "legacy", LegacyRuleRegister),
    }

    loaded: dict[str, list[BaseModel]] = {key: [] for key in directories}

    for key, (directory, model_cls) in directories.items():
        if not directory.exists():
            report.warnings.append(f"Missing directory: {directory}")
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                loaded[key].append(model_cls.model_validate(_load_json(path)))
            except Exception as exc:  # pragma: no cover - exercised in tests with invalid payloads
                report.errors.append(f"{path}: {exc}")

    sources = {item.source_id: item for item in loaded["sources"] if isinstance(item, AstrologySourceRecord)}
    passages = {item.passage_id: item for item in loaded["passages"] if isinstance(item, PassageRecord)}
    claims = {item.claim_id: item for item in loaded["claims"] if isinstance(item, ClaimRecord)}
    conflicts = {item.conflict_id: item for item in loaded["conflicts"] if isinstance(item, ConflictRecord)}
    approvals = {item.approval_id: item for item in loaded["approvals"] if isinstance(item, ApprovalRecord)}
    policies = {item.policy_id: item for item in loaded["policies"] if isinstance(item, DomainPolicyRecord)}
    legacy_registers = {
        item.register_id: item for item in loaded["legacy"] if isinstance(item, LegacyRuleRegister)
    }

    report.source_count = len(sources)
    report.passage_count = len(passages)
    report.claim_count = len(claims)
    report.conflict_count = len(conflicts)
    report.approval_count = len(approvals)
    report.policy_count = len(policies)
    report.legacy_register_count = len(legacy_registers)

    for passage in passages.values():
        if passage.source_id not in sources:
            report.errors.append(
                f"{passage.passage_id}: missing source reference {passage.source_id}"
            )

    for claim in claims.values():
        for passage_id in claim.source_passages:
            if passage_id not in passages:
                report.errors.append(
                    f"{claim.claim_id}: missing passage reference {passage_id}"
                )
        for claim_id in claim.conflicting_claims:
            if claim_id not in claims:
                report.errors.append(
                    f"{claim.claim_id}: missing conflicting claim reference {claim_id}"
                )
        if claim.high_stakes:
            matching_policy = [
                policy
                for policy in policies.values()
                if policy.domain == claim.domain and policy.high_stakes
            ]
            if not matching_policy:
                report.warnings.append(
                    f"{claim.claim_id}: high-stakes claim has no matching domain policy"
                )

    for conflict in conflicts.values():
        if conflict.claim_a not in claims:
            report.errors.append(
                f"{conflict.conflict_id}: missing claim_a reference {conflict.claim_a}"
            )
        if conflict.claim_b not in claims:
            report.errors.append(
                f"{conflict.conflict_id}: missing claim_b reference {conflict.claim_b}"
            )
        if conflict.source_a and conflict.source_a not in sources:
            report.errors.append(
                f"{conflict.conflict_id}: missing source_a reference {conflict.source_a}"
            )
        if conflict.source_b and conflict.source_b not in sources:
            report.errors.append(
                f"{conflict.conflict_id}: missing source_b reference {conflict.source_b}"
            )

    valid_artifact_ids = set(sources) | set(passages) | set(claims) | set(conflicts) | set(legacy_registers)
    for approval in approvals.values():
        for artifact_id in approval.artifact_ids:
            if artifact_id not in valid_artifact_ids:
                report.errors.append(
                    f"{approval.approval_id}: missing approved artifact reference {artifact_id}"
                )
        if approval.implementation_ready and approval.approval_status not in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.APPROVED_WITH_CONDITIONS,
            ApprovalStatus.IMPLEMENTATION_READY,
        }:
            report.errors.append(
                f"{approval.approval_id}: implementation_ready requires an approved approval_status"
            )

    for register in legacy_registers.values():
        for entry in register.entries:
            for claim_id in entry.mapped_claim_ids:
                if claim_id not in claims:
                    report.errors.append(
                        f"{register.register_id}: missing mapped claim reference {claim_id}"
                    )

    return report


__all__ = [
    "CONTRACT_VERSION",
    "AllowedOutputMode",
    "ApprovalRecord",
    "ApprovalRole",
    "ApprovalStatus",
    "ArtifactType",
    "AstrologySourceRecord",
    "AuthorityProfile",
    "ClaimRecord",
    "ConflictRecord",
    "ConflictResolutionStatus",
    "ConflictType",
    "DomainPolicyRecord",
    "EvidenceType",
    "GovernedArtifact",
    "LegacyRuleEntry",
    "LegacyRuleRegister",
    "LegacyRuleStatus",
    "PassageRecord",
    "PrimarySecondaryStatus",
    "QualityGrade",
    "RegistryValidationReport",
    "RoleDecision",
    "SourceClass",
    "VerificationStatus",
    "WorkflowState",
    "load_registry",
    "schema_documents",
    "validate_registry_directory",
    "write_json_schemas",
]
