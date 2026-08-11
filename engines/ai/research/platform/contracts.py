from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engines.common import config as cfg

CONTRACT_VERSION = getattr(cfg, "VEDA_RESEARCH_PLATFORM_VERSION", "2026-08-10")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")

DOMAIN_ID_RE = re.compile(r"^VEDA-DOMAIN-[A-Z0-9_-]+$")
MISSION_ID_RE = re.compile(r"^VEDA-RM-\d{6}$")
SCHEDULE_ID_RE = re.compile(r"^VEDA-RSCH-\d{6}$")
RUN_ID_RE = re.compile(r"^VEDA-RUN-\d{6}$")
OBSERVATION_ID_RE = re.compile(r"^VEDA-OBS-\d{6}$")
EVIDENCE_ID_RE = re.compile(r"^VEDA-EVD-\d{6}$")
CANDIDATE_ID_RE = re.compile(r"^VEDA-RCND-\d{6}$")
VALIDATION_ID_RE = re.compile(r"^VEDA-RVAL-\d{6}$")
CONFLICT_ID_RE = re.compile(r"^VEDA-RCNF-\d{6}$")
APPROVAL_ID_RE = re.compile(r"^VEDA-RAPR-\d{6}$")
LEDGER_ID_RE = re.compile(r"^VEDA-LED-\d{6}$")
CORE_ID_RE = re.compile(r"^VEDA-RCORE-\d{6}$")


def _is_iso_datetime(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if not ISO_TS_RE.match(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class DomainStatus(str, Enum):
    DISABLED = "DISABLED"
    TEST = "TEST"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class ResearchType(str, Enum):
    DISCOVERY = "DISCOVERY"
    SOURCE_VERIFICATION = "SOURCE_VERIFICATION"
    CLAIM_VALIDATION = "CLAIM_VALIDATION"
    CROSS_SOURCE_VALIDATION = "CROSS_SOURCE_VALIDATION"
    CONTRADICTION_RESOLUTION = "CONTRADICTION_RESOLUTION"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    PROVENANCE_RECOVERY = "PROVENANCE_RECOVERY"
    UPDATE_MONITORING = "UPDATE_MONITORING"
    NOVELTY_SEARCH = "NOVELTY_SEARCH"
    EMPIRICAL_VALIDATION = "EMPIRICAL_VALIDATION"
    LEGACY_RULE_PROVENANCE = "LEGACY_RULE_PROVENANCE"
    CLASSICAL_RULE_EXTRACTION = "CLASSICAL_RULE_EXTRACTION"
    TRANSLATION_VARIANCE = "TRANSLATION_VARIANCE"
    ONTOLOGY_EXPANSION = "ONTOLOGY_EXPANSION"
    DOMAIN_DEEP_RESEARCH = "DOMAIN_DEEP_RESEARCH"


class MissionPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class MissionStatus(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class TriggerType(str, Enum):
    MANUAL = "MANUAL"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    FOLLOW_UP = "FOLLOW_UP"
    ADMIN_REQUEST = "ADMIN_REQUEST"
    SYSTEM_RETRY = "SYSTEM_RETRY"


class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERABLE = "RECOVERABLE"


class EvidenceType(str, Enum):
    PRIMARY_SOURCE = "PRIMARY_SOURCE"
    SECONDARY_SOURCE = "SECONDARY_SOURCE"
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    ACADEMIC_SOURCE = "ACADEMIC_SOURCE"
    NEWS = "NEWS"
    DATASET = "DATASET"
    WEB_REFERENCE = "WEB_REFERENCE"
    INTERNAL_KNOWLEDGE = "INTERNAL_KNOWLEDGE"
    ARCHIVED_RESEARCH = "ARCHIVED_RESEARCH"
    USER_PROVIDED = "USER_PROVIDED"
    UNKNOWN = "UNKNOWN"


class SourceAccessStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"
    UNSAFE = "UNSAFE"


class CandidateType(str, Enum):
    NEW_CLAIM = "NEW_CLAIM"
    CLAIM_UPDATE = "CLAIM_UPDATE"
    SOURCE_ADDITION = "SOURCE_ADDITION"
    SOURCE_CORRECTION = "SOURCE_CORRECTION"
    CONTRADICTION = "CONTRADICTION"
    RULE_CANDIDATE = "RULE_CANDIDATE"
    PROVENANCE_CANDIDATE = "PROVENANCE_CANDIDATE"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    DEPRECATION_CANDIDATE = "DEPRECATION_CANDIDATE"
    EMPIRICAL_FINDING = "EMPIRICAL_FINDING"
    ONTOLOGY_EXTENSION = "ONTOLOGY_EXTENSION"


class NoveltyStatus(str, Enum):
    NEW = "NEW"
    KNOWN = "KNOWN"
    DUPLICATE = "DUPLICATE"
    PARTIAL_EXTENSION = "PARTIAL_EXTENSION"
    REFINEMENT = "REFINEMENT"
    POSSIBLE_UPDATE = "POSSIBLE_UPDATE"
    UNKNOWN = "UNKNOWN"


class ContradictionStatus(str, Enum):
    NONE = "NONE"
    POSSIBLE = "POSSIBLE"
    DIRECT = "DIRECT"
    PARTIAL = "PARTIAL"
    CONTEXTUAL = "CONTEXTUAL"
    SOURCE_VARIANCE = "SOURCE_VARIANCE"
    UNRESOLVED = "UNRESOLVED"


class ValidationStage(str, Enum):
    V1_SOURCE_VALIDATION = "V1_SOURCE_VALIDATION"
    V2_AUTHORITY_VALIDATION = "V2_AUTHORITY_VALIDATION"
    V3_PROVENANCE_VALIDATION = "V3_PROVENANCE_VALIDATION"
    V4_EXISTING_KNOWLEDGE_CHECK = "V4_EXISTING_KNOWLEDGE_CHECK"
    V5_CONTRADICTION_CHECK = "V5_CONTRADICTION_CHECK"
    V6_CROSS_SOURCE_SUPPORT = "V6_CROSS_SOURCE_SUPPORT"
    V7_ONTOLOGY_COMPATIBILITY = "V7_ONTOLOGY_COMPATIBILITY"
    V8_RULE_IMPACT = "V8_RULE_IMPACT"
    V9_SAFETY_CLASSIFICATION = "V9_SAFETY_CLASSIFICATION"
    V10_NOVELTY_ASSESSMENT = "V10_NOVELTY_ASSESSMENT"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_CONDITIONS = "PASS_WITH_CONDITIONS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    REJECTED = "REJECTED"
    NEEDS_MORE_RESEARCH = "NEEDS_MORE_RESEARCH"
    MERGE_REQUIRED = "MERGE_REQUIRED"
    SUPERSEDE_APPROVED = "SUPERSEDE_APPROVED"
    ARCHIVED = "ARCHIVED"


class AdminAction(str, Enum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REJECT = "REJECT"
    REQUEST_MORE_RESEARCH = "REQUEST_MORE_RESEARCH"
    MERGE = "MERGE"
    SUPERSEDE = "SUPERSEDE"
    ARCHIVE = "ARCHIVE"


class PromotionState(str, Enum):
    NONE = "NONE"
    PROMOTION_READY = "PROMOTION_READY"


class KnowledgeZone(str, Enum):
    APPROVED_CORE = "APPROVED_CORE"
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"
    RESEARCH_ARCHIVE = "RESEARCH_ARCHIVE"


class ConflictResolutionStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    COEXIST = "COEXIST"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    SOURCE_A_PREFERRED = "SOURCE_A_PREFERRED"
    SOURCE_B_PREFERRED = "SOURCE_B_PREFERRED"
    COMPOSITE_RULE = "COMPOSITE_RULE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CadenceType(str, Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    CUSTOM = "CUSTOM"
    MANUAL_ONLY = "MANUAL_ONLY"


class OverlapPolicy(str, Enum):
    SKIP = "SKIP"
    QUEUE = "QUEUE"
    COALESCE = "COALESCE"
    ALLOW = "ALLOW"


class MisfirePolicy(str, Enum):
    RUN_ONCE = "RUN_ONCE"
    SKIP = "SKIP"
    RESCHEDULE = "RESCHEDULE"


class ProviderType(str, Enum):
    WEB_SEARCH = "WEB_SEARCH"
    DIRECT_WEB = "DIRECT_WEB"
    LOCAL_DOCUMENTS = "LOCAL_DOCUMENTS"
    INTERNAL_KNOWLEDGE = "INTERNAL_KNOWLEDGE"
    ACADEMIC_SEARCH = "ACADEMIC_SEARCH"
    DATABASE = "DATABASE"
    API = "API"
    CONNECTOR = "CONNECTOR"
    FIXTURE = "FIXTURE"


class ProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"


class SafetyClass(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    HIGH_STAKES = "HIGH_STAKES"


class PlatformHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    MODEL = "MODEL"
    ADMIN = "ADMIN"
    SCHEDULER = "SCHEDULER"
    PROVIDER = "PROVIDER"
    VALIDATOR = "VALIDATOR"


class LedgerEventType(str, Enum):
    MISSION_CREATED = "MISSION_CREATED"
    MISSION_STARTED = "MISSION_STARTED"
    MISSION_PAUSED = "MISSION_PAUSED"
    RUN_STARTED = "RUN_STARTED"
    QUERY_EXECUTED = "QUERY_EXECUTED"
    SOURCE_DISCOVERED = "SOURCE_DISCOVERED"
    SOURCE_REJECTED = "SOURCE_REJECTED"
    EVIDENCE_CREATED = "EVIDENCE_CREATED"
    CANDIDATE_CREATED = "CANDIDATE_CREATED"
    CANDIDATE_MERGED = "CANDIDATE_MERGED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    CONTRADICTION_FOUND = "CONTRADICTION_FOUND"
    FOLLOW_UP_CREATED = "FOLLOW_UP_CREATED"
    ADMIN_APPROVED = "ADMIN_APPROVED"
    ADMIN_REJECTED = "ADMIN_REJECTED"
    MORE_RESEARCH_REQUESTED = "MORE_RESEARCH_REQUESTED"
    RUN_FAILED = "RUN_FAILED"
    RUN_RECOVERED = "RUN_RECOVERED"


class RetentionClass(str, Enum):
    PERMANENT = "PERMANENT"
    LONG_TERM = "LONG_TERM"
    TEMPORARY = "TEMPORARY"
    CACHE = "CACHE"


class PlatformArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = CONTRACT_VERSION


class ConfidenceDimensions(PlatformArtifact):
    source_confidence: float = Field(ge=0, le=1)
    authority_confidence: float = Field(ge=0, le=1)
    cross_source_confidence: float = Field(ge=0, le=1)
    provenance_confidence: float = Field(ge=0, le=1)
    novelty_confidence: float = Field(ge=0, le=1)
    contradiction_confidence: float = Field(ge=0, le=1)
    domain_confidence: float = Field(ge=0, le=1)


class ResearchBudget(PlatformArtifact):
    max_queries: int = Field(default=5, ge=1)
    max_sources: int = Field(default=10, ge=1)
    max_provider_calls: int = Field(default=3, ge=1)
    max_runtime_seconds: int = Field(default=60, ge=1)
    max_model_calls: int = Field(default=0, ge=0)
    max_cost: float = Field(default=0, ge=0)
    max_follow_up_depth: int = Field(default=2, ge=0)
    max_retries: int = Field(default=2, ge=0)
    cooldown_seconds: int = Field(default=0, ge=0)


class ResearchProviderDescriptor(PlatformArtifact):
    provider_id: str
    provider_type: ProviderType
    capabilities: list[str] = Field(default_factory=list)
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    cost_model: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = False
    supports_search: bool = True
    supports_fetch: bool = True
    supports_documents: bool = True
    status: ProviderStatus = ProviderStatus.ACTIVE
    allowed_uri_schemes: list[str] = Field(default_factory=lambda: ["https", "http"])

    @field_validator("provider_id")
    @classmethod
    def _validate_provider_id(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("provider_id is required")
        return cleaned


class ResearchDomainRecord(PlatformArtifact):
    domain_id: str
    name: str
    version: str
    status: DomainStatus
    description: str
    ontology_namespace: str
    source_policy: dict[str, Any]
    validation_policy: dict[str, Any]
    safety_policy: dict[str, Any]
    approval_policy: dict[str, Any]
    provider_policy: dict[str, Any]
    schedule_policy: dict[str, Any]
    plugin_entrypoint: str
    created_at: str
    updated_at: str

    @field_validator("domain_id")
    @classmethod
    def _validate_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not SEMVER_RE.fullmatch(value):
            raise ValueError("version must use semantic versioning")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_datetime(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class ResearchScheduleRecord(PlatformArtifact):
    schedule_id: str
    domain_id: str
    mission_id: str
    cadence_type: CadenceType
    timezone: str
    enabled: bool = True
    next_run_at: str | None = None
    last_run_at: str | None = None
    misfire_policy: MisfirePolicy = MisfirePolicy.RUN_ONCE
    overlap_policy: OverlapPolicy = OverlapPolicy.SKIP
    priority: MissionPriority = MissionPriority.P2
    created_at: str
    updated_at: str

    @field_validator("schedule_id")
    @classmethod
    def _validate_schedule_id(cls, value: str) -> str:
        if not SCHEDULE_ID_RE.fullmatch(value):
            raise ValueError("schedule_id must match VEDA-RSCH-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_schedule_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("mission_id")
    @classmethod
    def _validate_schedule_mission_id(cls, value: str) -> str:
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("next_run_at", "last_run_at", "created_at", "updated_at")
    @classmethod
    def _validate_schedule_times(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class ResearchMissionRecord(PlatformArtifact):
    mission_id: str
    domain_id: str
    title: str
    objective: str
    research_type: ResearchType
    priority: MissionPriority
    status: MissionStatus
    created_by: str
    created_at: str
    updated_at: str
    schedule_id: str | None = None
    query_strategy: dict[str, Any] = Field(default_factory=dict)
    required_source_classes: list[str] = Field(default_factory=list)
    minimum_independent_sources: int = Field(default=1, ge=1)
    known_claim_ids: list[str] = Field(default_factory=list)
    known_conflict_ids: list[str] = Field(default_factory=list)
    known_gap_ids: list[str] = Field(default_factory=list)
    safety_class: SafetyClass = SafetyClass.LOW
    completion_policy: dict[str, Any] = Field(default_factory=dict)
    research_budget: ResearchBudget = Field(default_factory=ResearchBudget)
    notes: str | None = None
    follow_up_depth: int = Field(default=0, ge=0)
    parent_candidate_id: str | None = None
    parent_mission_id: str | None = None
    last_run_at: str | None = None

    @field_validator("mission_id")
    @classmethod
    def _validate_mission_id(cls, value: str) -> str:
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_mission_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("schedule_id")
    @classmethod
    def _validate_schedule_ref(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not SCHEDULE_ID_RE.fullmatch(value):
            raise ValueError("schedule_id must match VEDA-RSCH-000001")
        return value

    @field_validator("created_at", "updated_at", "last_run_at")
    @classmethod
    def _validate_mission_times(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class ResearchRunRecord(PlatformArtifact):
    run_id: str
    mission_id: str
    domain_id: str
    trigger_type: TriggerType
    started_at: str
    completed_at: str | None = None
    status: RunStatus
    provider_calls: int = Field(default=0, ge=0)
    queries_executed: int = Field(default=0, ge=0)
    sources_discovered: int = Field(default=0, ge=0)
    sources_accepted: int = Field(default=0, ge=0)
    sources_rejected: int = Field(default=0, ge=0)
    evidence_created: int = Field(default=0, ge=0)
    candidates_created: int = Field(default=0, ge=0)
    duplicates_detected: int = Field(default=0, ge=0)
    conflicts_created: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
    cost_metrics: dict[str, Any] = Field(default_factory=dict)
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    continuation_required: bool = False
    continuation_hint: str | None = None

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        if not RUN_ID_RE.fullmatch(value):
            raise ValueError("run_id must match VEDA-RUN-000001")
        return value

    @field_validator("mission_id")
    @classmethod
    def _validate_run_mission_id(cls, value: str) -> str:
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_run_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("started_at", "completed_at")
    @classmethod
    def _validate_run_times(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class SourceObservationRecord(PlatformArtifact):
    observation_id: str
    run_id: str
    provider_id: str
    source_uri: str
    canonical_uri: str
    source_title: str
    source_type: EvidenceType
    published_at: str | None = None
    retrieved_at: str
    last_checked_at: str
    author: str | None = None
    publisher: str | None = None
    content_hash: str
    content_version: str | None = None
    access_status: SourceAccessStatus = SourceAccessStatus.ACCEPTED
    trust_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_reference: dict[str, Any] = Field(default_factory=dict)
    domain_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observation_id")
    @classmethod
    def _validate_observation_id(cls, value: str) -> str:
        if not OBSERVATION_ID_RE.fullmatch(value):
            raise ValueError("observation_id must match VEDA-OBS-000001")
        return value

    @field_validator("run_id")
    @classmethod
    def _validate_observation_run_id(cls, value: str) -> str:
        if not RUN_ID_RE.fullmatch(value):
            raise ValueError("run_id must match VEDA-RUN-000001")
        return value

    @field_validator("retrieved_at", "last_checked_at", "published_at")
    @classmethod
    def _validate_observation_times(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class ResearchEvidenceRecord(PlatformArtifact):
    evidence_id: str
    observation_id: str
    run_id: str
    mission_id: str
    domain_id: str
    location: str | None = None
    passage: str
    normalized_text: str
    claim_hint: str
    evidence_type: EvidenceType
    language: str = "en"
    content_hash: str
    extraction_method: str
    confidence: float = Field(ge=0, le=1)
    domain_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str

    @field_validator("evidence_id")
    @classmethod
    def _validate_evidence_id(cls, value: str) -> str:
        if not EVIDENCE_ID_RE.fullmatch(value):
            raise ValueError("evidence_id must match VEDA-EVD-000001")
        return value

    @field_validator("observation_id")
    @classmethod
    def _validate_evidence_observation_id(cls, value: str) -> str:
        if not OBSERVATION_ID_RE.fullmatch(value):
            raise ValueError("observation_id must match VEDA-OBS-000001")
        return value

    @field_validator("run_id")
    @classmethod
    def _validate_evidence_run_id(cls, value: str) -> str:
        if not RUN_ID_RE.fullmatch(value):
            raise ValueError("run_id must match VEDA-RUN-000001")
        return value

    @field_validator("mission_id")
    @classmethod
    def _validate_evidence_mission_id(cls, value: str) -> str:
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_evidence_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_evidence_created_at(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("created_at must be ISO-8601")
        return value


class ResearchCandidateRecord(PlatformArtifact):
    candidate_id: str
    domain_id: str
    mission_id: str
    run_id: str
    title: str
    candidate_type: CandidateType
    claim: str
    normalized_claim: str
    topic_key: str
    stance: str
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    existing_knowledge_matches: list[str] = Field(default_factory=list)
    novelty_status: NoveltyStatus = NoveltyStatus.UNKNOWN
    contradiction_status: ContradictionStatus = ContradictionStatus.NONE
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    confidence: ConfidenceDimensions
    priority: MissionPriority = MissionPriority.P2
    safety_class: SafetyClass = SafetyClass.LOW
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    knowledge_zone: KnowledgeZone = KnowledgeZone.RESEARCH_CANDIDATE
    promotion_state: PromotionState = PromotionState.NONE
    created_at: str
    updated_at: str
    merged_into_candidate_id: str | None = None
    support_count: int = Field(default=1, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("candidate_id")
    @classmethod
    def _validate_candidate_id(cls, value: str) -> str:
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("candidate_id must match VEDA-RCND-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_candidate_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("mission_id")
    @classmethod
    def _validate_candidate_mission_id(cls, value: str) -> str:
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("run_id")
    @classmethod
    def _validate_candidate_run_id(cls, value: str) -> str:
        if not RUN_ID_RE.fullmatch(value):
            raise ValueError("run_id must match VEDA-RUN-000001")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def _validate_candidate_evidence_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if not EVIDENCE_ID_RE.fullmatch(item):
                raise ValueError("evidence_ids must use VEDA-EVD identifiers")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_candidate_times(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value

    @field_validator("merged_into_candidate_id")
    @classmethod
    def _validate_merged_into_candidate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("merged_into_candidate_id must match VEDA-RCND-000001")
        return value


class ResearchValidationRecord(PlatformArtifact):
    validation_id: str
    candidate_id: str
    validator: ValidationStage
    result: str
    score: float = Field(ge=0, le=1)
    status: ValidationStatus
    evidence: dict[str, Any] = Field(default_factory=dict)
    reason: str
    requires_follow_up: bool = False
    created_at: str

    @field_validator("validation_id")
    @classmethod
    def _validate_validation_id(cls, value: str) -> str:
        if not VALIDATION_ID_RE.fullmatch(value):
            raise ValueError("validation_id must match VEDA-RVAL-000001")
        return value

    @field_validator("candidate_id")
    @classmethod
    def _validate_validation_candidate_id(cls, value: str) -> str:
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("candidate_id must match VEDA-RCND-000001")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_validation_created_at(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("created_at must be ISO-8601")
        return value


class ResearchConflictRecord(PlatformArtifact):
    conflict_id: str
    topic: str
    candidate_id: str
    conflicting_candidate_id: str | None = None
    conflicting_core_id: str | None = None
    conflict_type: ContradictionStatus
    analysis: str
    possible_reconciliation: str | None = None
    school_context: str | None = None
    implementation_impact: str
    resolution_status: ConflictResolutionStatus = ConflictResolutionStatus.UNRESOLVED
    approved_resolution: str | None = None
    confidence: float = Field(ge=0, le=1)
    created_at: str

    @field_validator("conflict_id")
    @classmethod
    def _validate_conflict_id(cls, value: str) -> str:
        if not CONFLICT_ID_RE.fullmatch(value):
            raise ValueError("conflict_id must match VEDA-RCNF-000001")
        return value

    @field_validator("candidate_id")
    @classmethod
    def _validate_conflict_candidate_id(cls, value: str) -> str:
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("candidate_id must match VEDA-RCND-000001")
        return value

    @field_validator("conflicting_candidate_id")
    @classmethod
    def _validate_conflicting_candidate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("conflicting_candidate_id must match VEDA-RCND-000001")
        return value

    @field_validator("conflicting_core_id")
    @classmethod
    def _validate_conflicting_core_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not CORE_ID_RE.fullmatch(value):
            raise ValueError("conflicting_core_id must match VEDA-RCORE-000001")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_conflict_created_at(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("created_at must be ISO-8601")
        return value


class ResearchApprovalRecord(PlatformArtifact):
    approval_id: str
    candidate_id: str
    action: AdminAction
    status: ApprovalStatus
    decided_by: str
    decided_at: str
    reason: str
    conditions: list[str] = Field(default_factory=list)
    promotion_state: PromotionState = PromotionState.NONE

    @field_validator("approval_id")
    @classmethod
    def _validate_approval_id(cls, value: str) -> str:
        if not APPROVAL_ID_RE.fullmatch(value):
            raise ValueError("approval_id must match VEDA-RAPR-000001")
        return value

    @field_validator("candidate_id")
    @classmethod
    def _validate_approval_candidate_id(cls, value: str) -> str:
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("candidate_id must match VEDA-RCND-000001")
        return value

    @field_validator("decided_at")
    @classmethod
    def _validate_decided_at(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("decided_at must be ISO-8601")
        return value


class ResearchLedgerEventRecord(PlatformArtifact):
    event_id: str
    timestamp: str
    event_type: LedgerEventType
    domain_id: str | None = None
    mission_id: str | None = None
    run_id: str | None = None
    candidate_id: str | None = None
    actor_type: ActorType
    actor_id: str
    action: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id")
    @classmethod
    def _validate_event_id(cls, value: str) -> str:
        if not LEDGER_ID_RE.fullmatch(value):
            raise ValueError("event_id must match VEDA-LED-000001")
        return value

    @field_validator("timestamp")
    @classmethod
    def _validate_event_timestamp(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("timestamp must be ISO-8601")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_event_domain_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("mission_id")
    @classmethod
    def _validate_event_mission_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-RM-000001")
        return value

    @field_validator("run_id")
    @classmethod
    def _validate_event_run_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not RUN_ID_RE.fullmatch(value):
            raise ValueError("run_id must match VEDA-RUN-000001")
        return value

    @field_validator("candidate_id")
    @classmethod
    def _validate_event_candidate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not CANDIDATE_ID_RE.fullmatch(value):
            raise ValueError("candidate_id must match VEDA-RCND-000001")
        return value


class ResearchCoreKnowledgeRecord(PlatformArtifact):
    core_id: str
    domain_id: str
    title: str
    claim: str
    normalized_claim: str
    topic_key: str
    stance: str
    source_ids: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.APPROVED
    knowledge_zone: KnowledgeZone = KnowledgeZone.APPROVED_CORE
    confidence: ConfidenceDimensions
    created_at: str
    updated_at: str

    @field_validator("core_id")
    @classmethod
    def _validate_core_id(cls, value: str) -> str:
        if not CORE_ID_RE.fullmatch(value):
            raise ValueError("core_id must match VEDA-RCORE-000001")
        return value

    @field_validator("domain_id")
    @classmethod
    def _validate_core_domain_id(cls, value: str) -> str:
        if not DOMAIN_ID_RE.fullmatch(value):
            raise ValueError("domain_id must match VEDA-DOMAIN-...")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_core_times(cls, value: str) -> str:
        if not _is_iso_datetime(value):
            raise ValueError("datetime fields must be ISO-8601 strings")
        return value


class ResearchDashboardRecord(PlatformArtifact):
    research_status: PlatformHealth
    active_missions: int = 0
    runs_today: int = 0
    sources_today: int = 0
    new_candidates: int = 0
    pending_approvals: int = 0
    high_priority_conflicts: int = 0
    failed_runs: int = 0
    last_hourly: str | None = None
    last_daily: str | None = None
    last_weekly: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class CandidateReviewRecord(PlatformArtifact):
    candidate: ResearchCandidateRecord
    evidence_summary: list[ResearchEvidenceRecord]
    validation_summary: list[ResearchValidationRecord]
    novelty: NoveltyStatus
    contradiction: ContradictionStatus
    confidence: ConfidenceDimensions
    current_knowledge_comparison: dict[str, Any] = Field(default_factory=dict)
    mission: ResearchMissionRecord
    run: ResearchRunRecord
    status: ApprovalStatus


class ResearchDomainPlugin(ABC):
    domain_id: str
    ontology_namespace: str
    source_policy: dict[str, Any]
    authority_policy: dict[str, Any]
    validation_policy: dict[str, Any]
    safety_policy: dict[str, Any]

    @abstractmethod
    def domain_record(self) -> ResearchDomainRecord:
        raise NotImplementedError

    @abstractmethod
    def seed_core_knowledge(self) -> list[ResearchCoreKnowledgeRecord]:
        raise NotImplementedError

    @abstractmethod
    def normalize_candidate(
        self,
        evidence: ResearchEvidenceRecord,
        observation: SourceObservationRecord,
        mission: ResearchMissionRecord,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate_source(self, observation: SourceObservationRecord) -> tuple[bool, str | None]:
        raise NotImplementedError

    @abstractmethod
    def compare_to_core(self, candidate_payload: dict[str, Any], core_records: list[ResearchCoreKnowledgeRecord]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def detect_domain_conflict(
        self,
        candidate_payload: dict[str, Any],
        core_records: list[ResearchCoreKnowledgeRecord],
        pending_candidates: list[ResearchCandidateRecord],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def classify_safety(self, candidate_payload: dict[str, Any]) -> SafetyClass:
        raise NotImplementedError

    @abstractmethod
    def create_follow_up(self, candidate: ResearchCandidateRecord, reason: str) -> dict[str, Any] | None:
        raise NotImplementedError


def schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "research_domain.schema.json": ResearchDomainRecord.model_json_schema(),
        "research_mission.schema.json": ResearchMissionRecord.model_json_schema(),
        "research_schedule.schema.json": ResearchScheduleRecord.model_json_schema(),
        "research_run.schema.json": ResearchRunRecord.model_json_schema(),
        "source_observation.schema.json": SourceObservationRecord.model_json_schema(),
        "research_evidence.schema.json": ResearchEvidenceRecord.model_json_schema(),
        "research_candidate.schema.json": ResearchCandidateRecord.model_json_schema(),
        "research_validation.schema.json": ResearchValidationRecord.model_json_schema(),
        "research_conflict.schema.json": ResearchConflictRecord.model_json_schema(),
        "research_approval.schema.json": ResearchApprovalRecord.model_json_schema(),
        "research_ledger_event.schema.json": ResearchLedgerEventRecord.model_json_schema(),
    }


def write_json_schemas(target_dir: Path) -> list[Path]:
    written: list[Path] = []
    for filename, document in schema_documents().items():
        path = target_dir / filename
        _write_json(path, document)
        written.append(path)
    return written


__all__ = [
    "AdminAction",
    "ApprovalStatus",
    "CandidateReviewRecord",
    "CandidateType",
    "CadenceType",
    "ConfidenceDimensions",
    "ConflictResolutionStatus",
    "ContradictionStatus",
    "DomainStatus",
    "EvidenceType",
    "KnowledgeZone",
    "LedgerEventType",
    "MissionPriority",
    "MissionStatus",
    "MisfirePolicy",
    "NoveltyStatus",
    "OverlapPolicy",
    "PlatformHealth",
    "PromotionState",
    "ProviderStatus",
    "ProviderType",
    "ResearchApprovalRecord",
    "ResearchBudget",
    "ResearchCandidateRecord",
    "ResearchConflictRecord",
    "ResearchCoreKnowledgeRecord",
    "ResearchDashboardRecord",
    "ResearchDomainPlugin",
    "ResearchDomainRecord",
    "ResearchEvidenceRecord",
    "ResearchLedgerEventRecord",
    "ResearchMissionRecord",
    "ResearchProviderDescriptor",
    "ResearchRunRecord",
    "ResearchScheduleRecord",
    "ResearchType",
    "ResearchValidationRecord",
    "RunStatus",
    "SafetyClass",
    "SourceAccessStatus",
    "SourceObservationRecord",
    "TriggerType",
    "ValidationStage",
    "ValidationStatus",
    "schema_documents",
    "write_json_schemas",
]
