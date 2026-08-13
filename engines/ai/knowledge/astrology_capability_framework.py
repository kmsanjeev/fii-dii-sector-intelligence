from __future__ import annotations

import json
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from engines.ai.research.platform.contracts import MissionPriority, ResearchType, SafetyClass
from engines.common import config as cfg

try:  # pragma: no cover - optional dependency in lean environments
    import jsonschema
except Exception:  # pragma: no cover - optional dependency in lean environments
    jsonschema = None


ROOT = Path(__file__).resolve().parents[3]
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
_CAPABILITY_ID_RE = re.compile(r"^VEDA-CAP-[A-Z0-9_]+-\d{6}$")
_DEPENDENCY_ID_RE = re.compile(r"^VEDA-CDEP-\d{6}$")
_LIFECYCLE_ID_RE = re.compile(r"^VEDA-CLFC-\d{6}$")
_VALIDATION_ID_RE = re.compile(r"^VEDA-CVAL-\d{6}$")
_ACTIVATION_ID_RE = re.compile(r"^VEDA-CACT-\d{6}$")
_ROLLBACK_ID_RE = re.compile(r"^VEDA-CRBK-\d{6}$")
_PACKAGE_ID_RE = re.compile(r"^VEDA-CPKG-\d{6}$")
_MISSION_ID_RE = re.compile(r"^VEDA-CMIS-\d{6}$")

_DEFAULT_TS = "2026-08-11T00:00:00Z"
_DEFAULT_ACTOR = "codex"
_CONTRACT_VERSION = "2026-08-11"


def _is_iso_datetime(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if not _ISO_TS_RE.match(value):
        return False
    try:
        from datetime import datetime

        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CapabilityType(str, Enum):
    CALCULATION = "CALCULATION"
    DERIVED_FACT = "DERIVED_FACT"
    DETECTION = "DETECTION"
    TIMING = "TIMING"
    INTERPRETATION = "INTERPRETATION"
    COMPOSITE_ANALYSIS = "COMPOSITE_ANALYSIS"
    REMEDY = "REMEDY"
    HIGH_STAKES = "HIGH_STAKES"


class CapabilityStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    RESEARCHING = "RESEARCHING"
    KNOWLEDGE_APPROVED = "KNOWLEDGE_APPROVED"
    RULE_ENGINEERING = "RULE_ENGINEERING"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"
    IMPLEMENTING = "IMPLEMENTING"
    VALIDATING = "VALIDATING"
    SHADOW = "SHADOW"
    ACTIVATION_READY = "ACTIVATION_READY"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    SUPERSEDED = "SUPERSEDED"
    BLOCKED = "BLOCKED"


class ActivationState(str, Enum):
    INACTIVE = "INACTIVE"
    SHADOW = "SHADOW"
    LIMITED = "LIMITED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ROLLED_BACK = "ROLLED_BACK"


class ChangeClass(str, Enum):
    ASTRONOMICAL_CALCULATION = "ASTRONOMICAL_CALCULATION"
    DERIVED_CHART_FACT = "DERIVED_CHART_FACT"
    RULE_DETECTION = "RULE_DETECTION"
    INTERPRETATION = "INTERPRETATION"
    USER_PRESENTATION = "USER_PRESENTATION"


class GateDecision(str, Enum):
    PASS = "PASS"
    RESEARCH_MORE = "RESEARCH_MORE"
    BLOCKED = "BLOCKED"
    BLOCKED_BY_CONFLICT = "BLOCKED_BY_CONFLICT"
    BLOCKED_BY_ONTOLOGY = "BLOCKED_BY_ONTOLOGY"
    BLOCKED_BY_CALCULATION = "BLOCKED_BY_CALCULATION"
    WAITING_FOR_VALIDATION = "WAITING_FOR_VALIDATION"
    WAITING_FOR_SHADOW = "WAITING_FOR_SHADOW"
    WAITING_FOR_ADMIN = "WAITING_FOR_ADMIN"


class DependencyKind(str, Enum):
    CAPABILITY = "CAPABILITY"
    APPROVED_RULE = "APPROVED_RULE"
    APPROVED_CLAIM = "APPROVED_CLAIM"
    CHART_FACT = "CHART_FACT"
    RUNTIME_PROFILE = "RUNTIME_PROFILE"
    SAFETY_POLICY = "SAFETY_POLICY"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_CONDITIONS = "PASS_WITH_CONDITIONS"
    BLOCKED = "BLOCKED"
    NOT_STARTED = "NOT_STARTED"


class CapabilityConfidenceDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_confidence: float = 0.0
    source_confidence: float = 0.0
    implementation_confidence: float = 0.0
    calculation_confidence: float = 0.0
    validation_confidence: float = 0.0
    production_confidence: float = 0.0

    @field_validator(
        "research_confidence",
        "source_confidence",
        "implementation_confidence",
        "calculation_confidence",
        "validation_confidence",
        "production_confidence",
    )
    @classmethod
    def _validate_range(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("confidence dimensions must be between 0 and 1")
        return round(float(value), 3)


class CapabilityRegistryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str
    name: str
    domain: str
    subdomain: str
    capability_type: CapabilityType
    status: CapabilityStatus
    research_status: str
    knowledge_status: str
    implementation_status: str
    validation_status: str
    activation_status: ActivationState
    safety_class: SafetyClass
    dependencies: list[str] = Field(default_factory=list)
    required_chart_facts: list[str] = Field(default_factory=list)
    required_rules: list[str] = Field(default_factory=list)
    required_sources: list[str] = Field(default_factory=list)
    runtime_profile_support: list[str] = Field(default_factory=list)
    approved_claim_ids: list[str] = Field(default_factory=list)
    approved_rule_ids: list[str] = Field(default_factory=list)
    draft_rule_ids: list[str] = Field(default_factory=list)
    legacy_mapping_ids: list[str] = Field(default_factory=list)
    coverage_category: str
    change_classes: list[ChangeClass] = Field(default_factory=list)
    confidence: CapabilityConfidenceDimensions
    version: str = "1.0.0"
    notes: str | None = None

    @field_validator("capability_id")
    @classmethod
    def _validate_capability_id(cls, value: str) -> str:
        if not _CAPABILITY_ID_RE.fullmatch(value):
            raise ValueError("capability_id must use a stable VEDA-CAP identifier")
        return value

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not _SEMVER_RE.fullmatch(value):
            raise ValueError("version must use semantic versioning")
        return value


class CapabilityDependencyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dependency_id: str
    capability_id: str
    depends_on: str
    dependency_kind: DependencyKind
    minimum_status: str
    rationale: str
    blocking: bool = True

    @field_validator("dependency_id")
    @classmethod
    def _validate_dependency_id(cls, value: str) -> str:
        if not _DEPENDENCY_ID_RE.fullmatch(value):
            raise ValueError("dependency_id must match VEDA-CDEP-000001")
        return value


class CapabilityGateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate: str
    decision: GateDecision
    reason: str
    evidence: list[str] = Field(default_factory=list)
    next_action: str | None = None


class CapabilityTransitionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_status: CapabilityStatus
    to_status: CapabilityStatus
    allowed: bool
    reason: str


class CapabilityLifecycleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lifecycle_id: str
    capability_id: str
    current_status: CapabilityStatus
    allowed_next_statuses: list[CapabilityStatus] = Field(default_factory=list)
    research_gate: CapabilityGateRecord
    knowledge_gate: CapabilityGateRecord
    rule_engineering_gate: CapabilityGateRecord
    dependency_gate: CapabilityGateRecord
    validation_gate: CapabilityGateRecord
    shadow_gate: CapabilityGateRecord
    activation_gate: CapabilityGateRecord
    rollback_supported: bool = True
    blocked_reason: str | None = None

    @field_validator("lifecycle_id")
    @classmethod
    def _validate_lifecycle_id(cls, value: str) -> str:
        if not _LIFECYCLE_ID_RE.fullmatch(value):
            raise ValueError("lifecycle_id must match VEDA-CLFC-000001")
        return value


class CapabilityValidationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    capability_id: str
    status: ValidationStatus
    required_suites: list[str] = Field(default_factory=list)
    completed_suites: list[str] = Field(default_factory=list)
    boundary_cases: list[str] = Field(default_factory=list)
    negative_cases: list[str] = Field(default_factory=list)
    regression_suites: list[str] = Field(default_factory=list)
    shadow_required: bool = True
    notes: str | None = None

    @field_validator("validation_id")
    @classmethod
    def _validate_validation_id(cls, value: str) -> str:
        if not _VALIDATION_ID_RE.fullmatch(value):
            raise ValueError("validation_id must match VEDA-CVAL-000001")
        return value


class CapabilityActivationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activation_id: str
    capability_id: str
    activation_state: ActivationState
    admin_activation_required: bool = True
    validation_passed: bool = False
    shadow_complete: bool = False
    dependencies_satisfied: bool = False
    approval_required: bool = True
    production_enabled: bool = False
    notes: str | None = None

    @field_validator("activation_id")
    @classmethod
    def _validate_activation_id(cls, value: str) -> str:
        if not _ACTIVATION_ID_RE.fullmatch(value):
            raise ValueError("activation_id must match VEDA-CACT-000001")
        return value


class CapabilityRollbackRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rollback_id: str
    capability_id: str
    supported: bool
    restore_target: str
    preserves_evidence: bool = True
    preserves_history: bool = True
    notes: str | None = None

    @field_validator("rollback_id")
    @classmethod
    def _validate_rollback_id(cls, value: str) -> str:
        if not _ROLLBACK_ID_RE.fullmatch(value):
            raise ValueError("rollback_id must match VEDA-CRBK-000001")
        return value


class CapabilityCoverageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    total_capabilities: int
    active_capabilities: int
    researching_capabilities: int
    blocked_capabilities: int
    implementation_ready_capabilities: int
    activation_ready_capabilities: int
    high_stakes_capabilities: int
    coverage_percent: float


class CapabilityImplementationPackageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: str
    capability_id: str
    approved_claim_ids: list[str] = Field(default_factory=list)
    approved_rule_ids: list[str] = Field(default_factory=list)
    calculation_dependencies: list[str] = Field(default_factory=list)
    implementation_module: str
    validation_datasets: list[str] = Field(default_factory=list)
    shadow_policy: str
    activation_policy: str
    documentation: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("package_id")
    @classmethod
    def _validate_package_id(cls, value: str) -> str:
        if not _PACKAGE_ID_RE.fullmatch(value):
            raise ValueError("package_id must match VEDA-CPKG-000001")
        return value


class CapabilityMissionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    capability_id: str
    title: str
    objective: str
    research_type: ResearchType
    priority: MissionPriority
    reason: str
    query_strategy: dict[str, Any] = Field(default_factory=dict)
    required_source_classes: list[str] = Field(default_factory=list)

    @field_validator("mission_id")
    @classmethod
    def _validate_mission_id(cls, value: str) -> str:
        if not _MISSION_ID_RE.fullmatch(value):
            raise ValueError("mission_id must match VEDA-CMIS-000001")
        return value


class CapabilityBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str
    name: str
    domain: str
    subdomain: str
    capability_type: CapabilityType
    safety_class: SafetyClass
    coverage_category: str
    initial_status: CapabilityStatus
    activation_state: ActivationState
    research_status: str
    knowledge_status: str
    implementation_status: str
    validation_status: str
    required_chart_facts: list[str] = Field(default_factory=list)
    required_rules: list[str] = Field(default_factory=list)
    required_sources: list[str] = Field(default_factory=list)
    runtime_profile_support: list[str] = Field(default_factory=list)
    approved_claim_ids: list[str] = Field(default_factory=list)
    approved_rule_ids: list[str] = Field(default_factory=list)
    draft_rule_ids: list[str] = Field(default_factory=list)
    legacy_mapping_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    change_classes: list[ChangeClass] = Field(default_factory=list)
    confidence: CapabilityConfidenceDimensions
    notes: str | None = None
    implementation_module: str = "UNASSIGNED"


def _artifact_meta() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "created_at": _DEFAULT_TS,
        "created_by": _DEFAULT_ACTOR,
        "updated_at": _DEFAULT_TS,
        "updated_by": _DEFAULT_ACTOR,
        "change_reason": "P013 capability governance bundle export.",
        "contract_version": _CONTRACT_VERSION,
    }


def _load_records(directory: Path) -> dict[str, dict[str, Any]]:
    if not directory.exists():
        return {}
    payload: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        row = _load_json(path)
        key = str(
            row.get("rule_id")
            or row.get("claim_id")
            or row.get("legacy_mapping_id")
            or row.get("approval_id")
            or path.stem
        )
        payload[key] = row
    return payload


class JyotishaCapabilityLifecycleService:
    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.runtime_summary = self._load_runtime_summary()
        self.runtime_profiles = self._load_runtime_profiles()
        self.approved_rules = _load_records(self.root / "data" / "veda" / "rules" / "approved")
        self.draft_rules = _load_records(self.root / "data" / "veda" / "rules" / "draft")
        self.claims = _load_records(self.root / "data" / "veda" / "research" / "astrology" / "claims")
        self.legacy_mappings = _load_records(self.root / "data" / "veda" / "rules" / "legacy_mappings")

    def _load_runtime_summary(self) -> dict[str, Any]:
        path = self.root / "data" / "veda" / "validation" / "runtime" / "p012_summary.json"
        if not path.exists():
            return {}
        return _load_json(path).get("summary", {})

    def _load_runtime_profiles(self) -> list[dict[str, Any]]:
        path = self.root / "data" / "veda" / "validation" / "runtime" / "p012_runtime_profiles.json"
        if not path.exists():
            return []
        return list(_load_json(path))

    def blueprints(self) -> list[CapabilityBlueprint]:
        return [
            CapabilityBlueprint(
                capability_id="VEDA-CAP-FOUNDATION-000001",
                name="D1 canonical chart calculation",
                domain="FOUNDATION",
                subdomain="D1",
                capability_type=CapabilityType.CALCULATION,
                safety_class=SafetyClass.LOW,
                coverage_category="FOUNDATION",
                initial_status=CapabilityStatus.ACTIVE,
                activation_state=ActivationState.ACTIVE,
                research_status="P004_VALIDATED_DETERMINISTIC_BASELINE",
                knowledge_status="P004_CANONICAL_CALCULATION_APPROVED",
                implementation_status="P012_RUNTIME_FACADE_ROUTED",
                validation_status="P004_AND_P012_VALIDATED",
                required_chart_facts=["normalized_datetime", "julian_day", "ayanamsha", "lagna", "graha_longitudes"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD", "STOCK_MARKET", "COUNTRY_EVENT"],
                change_classes=[ChangeClass.ASTRONOMICAL_CALCULATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.95,
                    source_confidence=0.95,
                    implementation_confidence=0.92,
                    calculation_confidence=0.98,
                    validation_confidence=0.98,
                    production_confidence=0.95,
                ),
                notes="Existing deterministic calculation capability governed by P004 and routed through the P012 runtime boundary.",
                implementation_module="engines/intelligence/jyotisha_runtime.py",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-FOUNDATION-000002",
                name="Canonical graha and lagna chart facts",
                domain="FOUNDATION",
                subdomain="GRAHA_LAGNA_FACTS",
                capability_type=CapabilityType.DERIVED_FACT,
                safety_class=SafetyClass.LOW,
                coverage_category="FOUNDATION",
                initial_status=CapabilityStatus.ACTIVE,
                activation_state=ActivationState.ACTIVE,
                research_status="P012_CANONICAL_FACT_CONTRACT_ESTABLISHED",
                knowledge_status="P003_ONTOLOGY_FACT_IDS_GOVERNED",
                implementation_status="P012_FACT_NORMALIZATION_ACTIVE",
                validation_status="P004_AND_P012_VALIDATED",
                required_chart_facts=["graha_longitudes", "rashi", "bhava", "nakshatra", "pada", "retrograde"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD", "STOCK_MARKET", "COUNTRY_EVENT"],
                dependencies=["VEDA-CAP-FOUNDATION-000001"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.9,
                    source_confidence=0.9,
                    implementation_confidence=0.92,
                    calculation_confidence=0.96,
                    validation_confidence=0.96,
                    production_confidence=0.94,
                ),
                notes="Canonical fact contract is active and exposed through the Jyotisha runtime facade.",
                implementation_module="engines/intelligence/jyotisha_runtime.py",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-TIMING-000001",
                name="Vimshottari runtime baseline",
                domain="TIMING",
                subdomain="VIMSHOTTARI",
                capability_type=CapabilityType.TIMING,
                safety_class=SafetyClass.LOW,
                coverage_category="TIMING",
                initial_status=CapabilityStatus.ACTIVE,
                activation_state=ActivationState.ACTIVE,
                research_status="P002_P010_GOVERNED_FOUNDATION_AVAILABLE",
                knowledge_status="APPROVED_RULES_PRESENT",
                implementation_status="LEGACY_RUNTIME_PROTECTED",
                validation_status="P001_P004_P012_RUNTIME_PROTECTED",
                required_chart_facts=["janma_nakshatra", "moon_longitude", "dasha_sequence"],
                required_rules=["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                approved_claim_ids=["VEDA-CLM-000001", "VEDA-CLM-000002", "VEDA-CLM-000005", "VEDA-CLM-000006"],
                approved_rule_ids=["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.RULE_DETECTION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.88,
                    source_confidence=0.87,
                    implementation_confidence=0.86,
                    calculation_confidence=0.9,
                    validation_confidence=0.9,
                    production_confidence=0.88,
                ),
                notes="Production timing exists but future expansions must follow the P013 lifecycle rather than bypassing governed rules.",
                implementation_module="engines/intelligence/jyotisha_runtime.py",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DIGNITY-000001",
                name="Graha dignity governed rule migration",
                domain="STRENGTH",
                subdomain="DIGNITY",
                capability_type=CapabilityType.DETECTION,
                safety_class=SafetyClass.LOW,
                coverage_category="Dignity",
                initial_status=CapabilityStatus.ACTIVATION_READY,
                activation_state=ActivationState.INACTIVE,
                research_status="P014_FOUNDATION_RESEARCH_COMPLETE",
                knowledge_status="APPROVED_CORE_AVAILABLE_WITH_CONDITIONAL_VARIANCE",
                implementation_status="GOVERNED_RULE_EVALUATOR_AVAILABLE",
                validation_status="P014_VALIDATED_WITH_SHADOW_VARIANCE_EXPLICIT",
                required_chart_facts=["graha_longitudes", "rashi", "degrees_in_sign"],
                required_rules=["VEDA-RUL-DIGNITY-000002"],
                required_sources=["CLASSICAL_PRIMARY", "TRADITIONAL_SECONDARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD", "STOCK_MARKET", "COUNTRY_EVENT"],
                approved_claim_ids=["VEDA-CLM-000007", "VEDA-CLM-000008", "VEDA-CLM-000009", "VEDA-CLM-000010"],
                approved_rule_ids=["VEDA-RUL-DIGNITY-000002"],
                draft_rule_ids=["VEDA-RUL-DIGNITY-000001"],
                legacy_mapping_ids=["VEDA-LMP-000002", "VEDA-LMP-000004"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.RULE_DETECTION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.82,
                    source_confidence=0.74,
                    implementation_confidence=0.85,
                    calculation_confidence=0.92,
                    validation_confidence=0.84,
                    production_confidence=0.61,
                ),
                notes="P014 closes the approved-core blocker with governed dignity foundations. Production activation remains separate because planetary friendship/enmity and node-dignity branches still need wider source governance.",
                implementation_module="engines/ai/knowledge/astrology_foundation_migration.py::evaluate_dignity",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-INTERPRETATION-000001",
                name="Graha and bhava interpretive rules",
                domain="FOUNDATION",
                subdomain="GRAHA_BHAVA_INTERPRETATION",
                capability_type=CapabilityType.INTERPRETATION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Graha",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_TRACEABILITY_GAPS_OPEN",
                knowledge_status="PARTIAL_APPROVED_CORE_ONLY",
                implementation_status="LEGACY_INTERPRETATION_PATH_ACTIVE",
                validation_status="NOT_GOVERNED_FOR_MIGRATION",
                required_chart_facts=["graha_longitudes", "bhava", "lordship", "dignity"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000002", "VEDA-CAP-DIGNITY-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.5,
                    source_confidence=0.32,
                    implementation_confidence=0.48,
                    calculation_confidence=0.88,
                    validation_confidence=0.28,
                    production_confidence=0.24,
                ),
                notes="Interpretation remains downstream from calculation and should migrate only after dignity and house-rule provenance is governed.",
                implementation_module="engines/intelligence/kundli_interpretator.py",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-VARGA-000001",
                name="Navamsha (D9) calculation",
                domain="DIVISIONAL_CHARTS",
                subdomain="D9",
                capability_type=CapabilityType.CALCULATION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="D9",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "rashi"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000001"],
                change_classes=[ChangeClass.ASTRONOMICAL_CALCULATION, ChangeClass.DERIVED_CHART_FACT],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.2,
                    source_confidence=0.15,
                    implementation_confidence=0.1,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                notes="D9 is listed as a governed future capability but is not activated by P013.",
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-VARGA-000002",
                name="Navamsha (D9) interpretation",
                domain="DIVISIONAL_CHARTS",
                subdomain="D9_INTERPRETATION",
                capability_type=CapabilityType.INTERPRETATION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="D9",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="BLOCKED_BY_D9_CALCULATION",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["d9_chart", "graha_longitudes", "bhava"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-VARGA-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.15,
                    source_confidence=0.12,
                    implementation_confidence=0.05,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-VARGA-000003",
                name="Dashamsha (D10) calculation",
                domain="DIVISIONAL_CHARTS",
                subdomain="D10",
                capability_type=CapabilityType.CALCULATION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="D10",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "rashi"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000001"],
                change_classes=[ChangeClass.ASTRONOMICAL_CALCULATION, ChangeClass.DERIVED_CHART_FACT],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.15,
                    source_confidence=0.12,
                    implementation_confidence=0.05,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-VARGA-000004",
                name="Dashamsha (D10) interpretation",
                domain="DIVISIONAL_CHARTS",
                subdomain="D10_INTERPRETATION",
                capability_type=CapabilityType.INTERPRETATION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="D10",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="BLOCKED_BY_D10_CALCULATION",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["d10_chart", "graha_longitudes", "bhava"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-VARGA-000003", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.15,
                    source_confidence=0.12,
                    implementation_confidence=0.05,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-RULE-000001",
                name="Yoga governed detection framework",
                domain="RULE_SYSTEMS",
                subdomain="YOGA",
                capability_type=CapabilityType.DETECTION,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Yoga",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_CONFLICTS_AND_SOURCE_GAPS_OPEN",
                knowledge_status="INSUFFICIENT_APPROVED_CORE",
                implementation_status="LEGACY_LOGIC_NOT_MIGRATED",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "bhava", "lordship", "aspects"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000002", "VEDA-CAP-DIGNITY-000001"],
                change_classes=[ChangeClass.RULE_DETECTION, ChangeClass.INTERPRETATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.35,
                    source_confidence=0.25,
                    implementation_confidence=0.2,
                    calculation_confidence=0.82,
                    validation_confidence=0.1,
                    production_confidence=0.08,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-RULE-000002",
                name="Dosha governed detection framework",
                domain="RULE_SYSTEMS",
                subdomain="DOSHA",
                capability_type=CapabilityType.DETECTION,
                safety_class=SafetyClass.HIGH,
                coverage_category="Dosha",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_SOURCE_GAPS_OPEN",
                knowledge_status="INSUFFICIENT_APPROVED_CORE",
                implementation_status="LEGACY_LOGIC_NOT_MIGRATED",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "bhava", "lordship", "aspects"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000002", "VEDA-CAP-DIGNITY-000001"],
                change_classes=[ChangeClass.RULE_DETECTION, ChangeClass.INTERPRETATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.32,
                    source_confidence=0.21,
                    implementation_confidence=0.18,
                    calculation_confidence=0.8,
                    validation_confidence=0.08,
                    production_confidence=0.05,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-TIMING-000002",
                name="Yogini Dasha expansion",
                domain="TIMING",
                subdomain="YOGINI_DASHA",
                capability_type=CapabilityType.TIMING,
                safety_class=SafetyClass.MODERATE,
                coverage_category="TIMING",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["janma_nakshatra", "moon_longitude"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000001"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.RULE_DETECTION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.1,
                    source_confidence=0.1,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-TIMING-000003",
                name="Ashtottari Dasha expansion",
                domain="TIMING",
                subdomain="ASHTOTTARI_DASHA",
                capability_type=CapabilityType.TIMING,
                safety_class=SafetyClass.MODERATE,
                coverage_category="TIMING",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["janma_nakshatra", "moon_longitude"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-FOUNDATION-000001"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.RULE_DETECTION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.1,
                    source_confidence=0.1,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-TIMING-000004",
                name="Transit / gochar structural comparison",
                domain="TIMING",
                subdomain="GOCHAR",
                capability_type=CapabilityType.TIMING,
                safety_class=SafetyClass.MODERATE,
                coverage_category="TIMING",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="P019_FOUNDATION_RESEARCH_COMPLETE",
                knowledge_status="RESEARCH_ONLY_STRUCTURAL_BASELINE",
                implementation_status="P019_READ_ONLY_RUNTIME_AVAILABLE",
                validation_status="IMPLEMENTED_UNVALIDATED",
                required_chart_facts=["transit", "lagna", "moon_longitude", "graha_longitudes"],
                required_sources=["CLASSICAL_PRIMARY", "TRADITIONAL_SECONDARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD", "STOCK_MARKET", "COUNTRY_EVENT"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002", "VEDA-CAP-TIMING-000001"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.RULE_DETECTION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.35,
                    source_confidence=0.3,
                    implementation_confidence=0.55,
                    calculation_confidence=0.6,
                    validation_confidence=0.25,
                    production_confidence=0.1,
                ),
                notes="Read-only transit comparison is available through the new gochar router and should remain unactivated until provenance and rule coverage are expanded.",
                implementation_module="engines/transit_gochar.py",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-STRENGTH-000001",
                name="Shadbala governed strength system",
                domain="STRENGTH",
                subdomain="SHADBALA",
                capability_type=CapabilityType.DERIVED_FACT,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Shadbala",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "declination", "time_of_birth"],
                required_sources=["CLASSICAL_PRIMARY", "TRADITIONAL_SECONDARY"],
                runtime_profile_support=["PERSONAL"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.08,
                    source_confidence=0.08,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-STRENGTH-000002",
                name="Ashtakavarga governed strength system",
                domain="STRENGTH",
                subdomain="ASHTAKAVARGA",
                capability_type=CapabilityType.DERIVED_FACT,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Ashtakavarga",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["graha_longitudes", "rashi"],
                required_sources=["CLASSICAL_PRIMARY", "TRADITIONAL_SECONDARY"],
                runtime_profile_support=["PERSONAL"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.08,
                    source_confidence=0.08,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000001",
                name="Marriage intelligence",
                domain="LIFE_DOMAINS",
                subdomain="MARRIAGE",
                capability_type=CapabilityType.COMPOSITE_ANALYSIS,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Marriage",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_DOMAIN_GAPS_OPEN",
                knowledge_status="DEPENDENCY_GAPS_OPEN",
                implementation_status="LEGACY_HEURISTICS_NOT_MIGRATED",
                validation_status="NOT_STARTED",
                required_chart_facts=["d1_chart", "seventh_house", "lordship", "venus", "jupiter", "d9_chart", "dasha"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-VARGA-000001", "VEDA-CAP-VARGA-000002", "VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001", "VEDA-CAP-RULE-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.22,
                    source_confidence=0.18,
                    implementation_confidence=0.05,
                    calculation_confidence=0.78,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000002",
                name="Career and education intelligence",
                domain="LIFE_DOMAINS",
                subdomain="CAREER",
                capability_type=CapabilityType.COMPOSITE_ANALYSIS,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Career",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_DOMAIN_GAPS_OPEN",
                knowledge_status="DEPENDENCY_GAPS_OPEN",
                implementation_status="LEGACY_HEURISTICS_NOT_MIGRATED",
                validation_status="NOT_STARTED",
                required_chart_facts=["tenth_house", "lordship", "saturn", "sun", "d10_chart", "dasha"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-VARGA-000003", "VEDA-CAP-VARGA-000004", "VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.22,
                    source_confidence=0.18,
                    implementation_confidence=0.05,
                    calculation_confidence=0.78,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000003",
                name="Finance intelligence",
                domain="LIFE_DOMAINS",
                subdomain="FINANCE",
                capability_type=CapabilityType.HIGH_STAKES,
                safety_class=SafetyClass.HIGH_STAKES,
                coverage_category="Finance",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_R1_SAFETY_BOUNDARY_ACTIVE",
                knowledge_status="HIGH_STAKES_APPROVED_CORE_REQUIRED",
                implementation_status="LEGACY_HEURISTICS_SAFETY_BOUNDED",
                validation_status="NOT_STARTED",
                required_chart_facts=["second_house", "eleventh_house", "lordship", "dasha", "yogas"],
                required_sources=["CLASSICAL_PRIMARY", "TRADITIONAL_SECONDARY", "EMPIRICAL_RESEARCH"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD", "STOCK_MARKET"],
                dependencies=["VEDA-CAP-TIMING-000001", "VEDA-CAP-RULE-000001", "VEDA-CAP-DIGNITY-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.18,
                    source_confidence=0.12,
                    implementation_confidence=0.04,
                    calculation_confidence=0.75,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000004",
                name="Children and family intelligence",
                domain="LIFE_DOMAINS",
                subdomain="CHILDREN",
                capability_type=CapabilityType.COMPOSITE_ANALYSIS,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Children",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_DOMAIN_GAPS_OPEN",
                knowledge_status="DEPENDENCY_GAPS_OPEN",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["fifth_house", "jupiter", "d7_chart", "dasha"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.16,
                    source_confidence=0.12,
                    implementation_confidence=0.03,
                    calculation_confidence=0.72,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000005",
                name="Health intelligence",
                domain="LIFE_DOMAINS",
                subdomain="HEALTH",
                capability_type=CapabilityType.HIGH_STAKES,
                safety_class=SafetyClass.HIGH_STAKES,
                coverage_category="Health",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_P1_RESEARCH_DEBT",
                knowledge_status="HIGH_STAKES_APPROVED_CORE_REQUIRED",
                implementation_status="SAFETY_REMEDIATED_ONLY",
                validation_status="NOT_STARTED",
                required_chart_facts=["sixth_house", "eighth_house", "twelfth_house", "dasha"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL", "REST_STANDARD"],
                dependencies=["VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.12,
                    source_confidence=0.1,
                    implementation_confidence=0.02,
                    calculation_confidence=0.7,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000006",
                name="Longevity intelligence",
                domain="ADVANCED",
                subdomain="AYURDAYA",
                capability_type=CapabilityType.HIGH_STAKES,
                safety_class=SafetyClass.HIGH_STAKES,
                coverage_category="Longevity",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_R1_LONGEVITY_OUTPUT_BLOCKED",
                knowledge_status="HIGH_STAKES_APPROVED_CORE_REQUIRED",
                implementation_status="USER_OUTPUT_DISABLED_FOR_DETERMINISTIC_USE",
                validation_status="NOT_STARTED",
                required_chart_facts=["eighth_house", "maraka_factors", "dasha", "ayurdaya_method"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                runtime_profile_support=["PERSONAL"],
                dependencies=["VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.1,
                    source_confidence=0.08,
                    implementation_confidence=0.0,
                    calculation_confidence=0.65,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-DOMAIN-000007",
                name="Remedy governance",
                domain="ADVANCED",
                subdomain="REMEDIES",
                capability_type=CapabilityType.REMEDY,
                safety_class=SafetyClass.HIGH_STAKES,
                coverage_category="Remedies",
                initial_status=CapabilityStatus.RESEARCHING,
                activation_state=ActivationState.INACTIVE,
                research_status="P005_P1_RESEARCH_DEBT",
                knowledge_status="HIGH_STAKES_APPROVED_CORE_REQUIRED",
                implementation_status="NO_GOVERNED_RUNTIME",
                validation_status="NOT_STARTED",
                required_chart_facts=["chart_context", "dasha", "benefic_malefic_context"],
                required_sources=["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY", "TRADITIONAL_SECONDARY"],
                runtime_profile_support=["PERSONAL"],
                dependencies=["VEDA-CAP-TIMING-000001", "VEDA-CAP-INTERPRETATION-000001"],
                change_classes=[ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.08,
                    source_confidence=0.08,
                    implementation_confidence=0.0,
                    calculation_confidence=0.6,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-ADVANCED-000001",
                name="Jaimini systems",
                domain="ADVANCED",
                subdomain="JAIMINI",
                capability_type=CapabilityType.COMPOSITE_ANALYSIS,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Jaimini",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["chara_karakas", "argala", "arudha"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["PERSONAL"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.RULE_DETECTION, ChangeClass.INTERPRETATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.05,
                    source_confidence=0.05,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
            CapabilityBlueprint(
                capability_id="VEDA-CAP-ADVANCED-000002",
                name="Muhurta and electional astrology",
                domain="ADVANCED",
                subdomain="MUHURTA",
                capability_type=CapabilityType.COMPOSITE_ANALYSIS,
                safety_class=SafetyClass.MODERATE,
                coverage_category="Muhurta",
                initial_status=CapabilityStatus.IDENTIFIED,
                activation_state=ActivationState.INACTIVE,
                research_status="KNOWLEDGE_GAP_IDENTIFIED",
                knowledge_status="NOT_YET_GOVERNED",
                implementation_status="NO_P013_PACKAGE",
                validation_status="NOT_STARTED",
                required_chart_facts=["transit", "lagna", "tithi", "nakshatra"],
                required_sources=["CLASSICAL_PRIMARY"],
                runtime_profile_support=["EVENT", "MARKET"],
                dependencies=["VEDA-CAP-FOUNDATION-000001", "VEDA-CAP-FOUNDATION-000002"],
                change_classes=[ChangeClass.DERIVED_CHART_FACT, ChangeClass.INTERPRETATION, ChangeClass.USER_PRESENTATION],
                confidence=CapabilityConfidenceDimensions(
                    research_confidence=0.05,
                    source_confidence=0.05,
                    implementation_confidence=0.0,
                    calculation_confidence=0.0,
                    validation_confidence=0.0,
                    production_confidence=0.0,
                ),
                implementation_module="UNASSIGNED",
            ),
        ]

    def registry_records(self) -> list[CapabilityRegistryRecord]:
        return [
            CapabilityRegistryRecord(
                capability_id=blueprint.capability_id,
                name=blueprint.name,
                domain=blueprint.domain,
                subdomain=blueprint.subdomain,
                capability_type=blueprint.capability_type,
                status=blueprint.initial_status,
                research_status=blueprint.research_status,
                knowledge_status=blueprint.knowledge_status,
                implementation_status=blueprint.implementation_status,
                validation_status=blueprint.validation_status,
                activation_status=blueprint.activation_state,
                safety_class=blueprint.safety_class,
                dependencies=blueprint.dependencies,
                required_chart_facts=blueprint.required_chart_facts,
                required_rules=blueprint.required_rules,
                required_sources=blueprint.required_sources,
                runtime_profile_support=blueprint.runtime_profile_support,
                approved_claim_ids=blueprint.approved_claim_ids,
                approved_rule_ids=blueprint.approved_rule_ids,
                draft_rule_ids=blueprint.draft_rule_ids,
                legacy_mapping_ids=blueprint.legacy_mapping_ids,
                coverage_category=blueprint.coverage_category,
                change_classes=blueprint.change_classes,
                confidence=blueprint.confidence,
                notes=blueprint.notes,
            )
            for blueprint in self.blueprints()
        ]

    def dependency_records(self) -> list[CapabilityDependencyRecord]:
        records: list[CapabilityDependencyRecord] = []
        counter = 1
        registry = {item.capability_id: item for item in self.registry_records()}
        for capability in registry.values():
            for dependency in capability.dependencies:
                dependency_name = registry[dependency].name if dependency in registry else dependency
                records.append(
                    CapabilityDependencyRecord(
                        dependency_id=f"VEDA-CDEP-{counter:06d}",
                        capability_id=capability.capability_id,
                        depends_on=dependency,
                        dependency_kind=DependencyKind.CAPABILITY,
                        minimum_status="ACTIVE_OR_ACTIVATION_READY",
                        rationale=f"{capability.name} depends on {dependency_name}.",
                        blocking=True,
                    )
                )
                counter += 1
            for rule_id in capability.required_rules:
                records.append(
                    CapabilityDependencyRecord(
                        dependency_id=f"VEDA-CDEP-{counter:06d}",
                        capability_id=capability.capability_id,
                        depends_on=rule_id,
                        dependency_kind=DependencyKind.APPROVED_RULE,
                        minimum_status="APPROVED_RULE_REQUIRED",
                        rationale=f"{capability.name} requires governed rule {rule_id} before activation.",
                        blocking=True,
                    )
                )
                counter += 1
            for fact in capability.required_chart_facts:
                records.append(
                    CapabilityDependencyRecord(
                        dependency_id=f"VEDA-CDEP-{counter:06d}",
                        capability_id=capability.capability_id,
                        depends_on=fact,
                        dependency_kind=DependencyKind.CHART_FACT,
                        minimum_status="FACT_AVAILABLE",
                        rationale=f"{capability.name} needs canonical fact `{fact}` from the P012 runtime boundary.",
                        blocking=False,
                    )
                )
                counter += 1
        return records

    def _allowed_next_statuses(self, status: CapabilityStatus) -> list[CapabilityStatus]:
        transition_map = {
            CapabilityStatus.IDENTIFIED: [CapabilityStatus.RESEARCHING, CapabilityStatus.BLOCKED],
            CapabilityStatus.RESEARCHING: [CapabilityStatus.KNOWLEDGE_APPROVED, CapabilityStatus.BLOCKED],
            CapabilityStatus.KNOWLEDGE_APPROVED: [CapabilityStatus.RULE_ENGINEERING, CapabilityStatus.BLOCKED],
            CapabilityStatus.RULE_ENGINEERING: [CapabilityStatus.IMPLEMENTATION_READY, CapabilityStatus.BLOCKED],
            CapabilityStatus.IMPLEMENTATION_READY: [CapabilityStatus.IMPLEMENTING, CapabilityStatus.BLOCKED],
            CapabilityStatus.IMPLEMENTING: [CapabilityStatus.VALIDATING, CapabilityStatus.BLOCKED],
            CapabilityStatus.VALIDATING: [CapabilityStatus.SHADOW, CapabilityStatus.BLOCKED],
            CapabilityStatus.SHADOW: [CapabilityStatus.ACTIVATION_READY, CapabilityStatus.BLOCKED],
            CapabilityStatus.ACTIVATION_READY: [CapabilityStatus.ACTIVE, CapabilityStatus.BLOCKED],
            CapabilityStatus.ACTIVE: [CapabilityStatus.SUPERSEDED, CapabilityStatus.DEPRECATED, CapabilityStatus.BLOCKED],
            CapabilityStatus.BLOCKED: [CapabilityStatus.RESEARCHING, CapabilityStatus.RULE_ENGINEERING],
            CapabilityStatus.SUPERSEDED: [],
            CapabilityStatus.DEPRECATED: [],
        }
        return transition_map.get(status, [])

    def _dependency_satisfied(self, dependency_id: str, registry: dict[str, CapabilityRegistryRecord]) -> bool:
        dependency = registry.get(dependency_id)
        if dependency is None:
            return False
        return dependency.status in {
            CapabilityStatus.ACTIVE,
            CapabilityStatus.ACTIVATION_READY,
            CapabilityStatus.SHADOW,
            CapabilityStatus.IMPLEMENTATION_READY,
        }

    def _evaluate_research_gate(self, record: CapabilityRegistryRecord) -> CapabilityGateRecord:
        if record.capability_type == CapabilityType.CALCULATION and "P004" in record.research_status:
            return CapabilityGateRecord(
                gate="research",
                decision=GateDecision.PASS,
                reason="Existing deterministic calculation capability is already governed by the P004 baseline.",
                evidence=["P004 validated baseline", "P012 runtime boundary"],
                next_action="Maintain regression protection through P014+.",
            )
        if record.approved_claim_ids or record.approved_rule_ids:
            return CapabilityGateRecord(
                gate="research",
                decision=GateDecision.PASS,
                reason="Approved or implementation-ready governed knowledge is already linked.",
                evidence=[*record.approved_claim_ids, *record.approved_rule_ids],
                next_action="Continue through knowledge sufficiency and rule-engineering checks.",
            )
        if record.draft_rule_ids or record.legacy_mapping_ids:
            return CapabilityGateRecord(
                gate="research",
                decision=GateDecision.RESEARCH_MORE,
                reason="A legacy-unsourced mapping or draft rule exists, but no approved-core knowledge supports implementation yet.",
                evidence=[*record.draft_rule_ids, *record.legacy_mapping_ids],
                next_action="Open or continue a provenance-recovery mission until approved-core dignity support exists.",
            )
        return CapabilityGateRecord(
            gate="research",
            decision=GateDecision.RESEARCH_MORE,
            reason="No approved-core evidence is linked to this capability yet.",
            next_action="Create a knowledge-gap research mission.",
        )

    def _evaluate_knowledge_gate(self, record: CapabilityRegistryRecord, research_gate: CapabilityGateRecord) -> CapabilityGateRecord:
        if research_gate.decision != GateDecision.PASS:
            return CapabilityGateRecord(
                gate="knowledge",
                decision=GateDecision.RESEARCH_MORE,
                reason="Approved knowledge is not yet sufficient for rule engineering.",
                evidence=research_gate.evidence,
                next_action=research_gate.next_action,
            )
        if record.knowledge_status.startswith("BLOCKED_BY"):
            blocked = GateDecision.BLOCKED_BY_CALCULATION
            if "ONTOLOGY" in record.knowledge_status:
                blocked = GateDecision.BLOCKED_BY_ONTOLOGY
            elif "CONFLICT" in record.knowledge_status:
                blocked = GateDecision.BLOCKED_BY_CONFLICT
            return CapabilityGateRecord(
                gate="knowledge",
                decision=blocked,
                reason=record.knowledge_status.replace("_", " ").title(),
                next_action="Resolve the blocking condition before implementation.",
            )
        return CapabilityGateRecord(
            gate="knowledge",
            decision=GateDecision.PASS,
            reason="Knowledge linkage is sufficient to enter ruled engineering under P003 contracts.",
            evidence=[*record.approved_claim_ids, *record.approved_rule_ids],
            next_action="Create or refine the machine-readable rule package.",
        )

    def _evaluate_rule_gate(self, record: CapabilityRegistryRecord, knowledge_gate: CapabilityGateRecord) -> CapabilityGateRecord:
        if knowledge_gate.decision != GateDecision.PASS:
            return CapabilityGateRecord(
                gate="rule_engineering",
                decision=GateDecision.BLOCKED,
                reason="Rule engineering cannot begin until knowledge sufficiency passes.",
                evidence=knowledge_gate.evidence,
                next_action=knowledge_gate.next_action,
            )
        if record.required_rules and not record.approved_rule_ids:
            return CapabilityGateRecord(
                gate="rule_engineering",
                decision=GateDecision.BLOCKED,
                reason="The capability declares required rules, but no governed approved rule artifact is linked.",
                evidence=record.required_rules,
                next_action="Create a P003 rule artifact from approved core knowledge.",
            )
        return CapabilityGateRecord(
            gate="rule_engineering",
            decision=GateDecision.PASS,
            reason="Machine-readable rule packaging can proceed under existing governed contracts.",
            evidence=record.approved_rule_ids or record.approved_claim_ids,
            next_action="Assemble the implementation package and validation fixtures.",
        )

    def _evaluate_dependency_gate(self, record: CapabilityRegistryRecord, registry: dict[str, CapabilityRegistryRecord]) -> CapabilityGateRecord:
        missing = [item for item in record.dependencies if not self._dependency_satisfied(item, registry)]
        if missing:
            return CapabilityGateRecord(
                gate="dependencies",
                decision=GateDecision.BLOCKED_BY_CALCULATION,
                reason="One or more prerequisite capabilities are not yet active or activation-ready.",
                evidence=missing,
                next_action="Advance the prerequisite capabilities first.",
            )
        return CapabilityGateRecord(
            gate="dependencies",
            decision=GateDecision.PASS,
            reason="Declared dependencies are satisfied or already active.",
            evidence=record.dependencies,
            next_action="Proceed to validation.",
        )

    def _evaluate_validation_gate(
        self,
        record: CapabilityRegistryRecord,
        rule_gate: CapabilityGateRecord,
        dependency_gate: CapabilityGateRecord,
    ) -> CapabilityGateRecord:
        if rule_gate.decision != GateDecision.PASS or dependency_gate.decision != GateDecision.PASS:
            return CapabilityGateRecord(
                gate="validation",
                decision=GateDecision.WAITING_FOR_VALIDATION if rule_gate.decision == GateDecision.PASS else GateDecision.BLOCKED,
                reason="Validation cannot complete until rule engineering and dependency gates pass.",
                next_action="Finish upstream gates before validation.",
            )
        if record.status in {CapabilityStatus.ACTIVE, CapabilityStatus.ACTIVATION_READY} and "VALIDATED" in record.validation_status:
            return CapabilityGateRecord(
                gate="validation",
                decision=GateDecision.PASS,
                reason="Validation evidence already exists for this capability.",
                evidence=[record.validation_status],
                next_action="Maintain regression suites and proceed to shadow/activation policy.",
            )
        if record.status == CapabilityStatus.BLOCKED:
            return CapabilityGateRecord(
                gate="validation",
                decision=GateDecision.BLOCKED,
                reason="Validation is blocked because the capability has not reached an implementation-ready state.",
                next_action="Resolve upstream governance gates first.",
            )
        return CapabilityGateRecord(
            gate="validation",
            decision=GateDecision.WAITING_FOR_VALIDATION,
            reason="A governed implementation package exists conceptually, but validation execution is still pending.",
            next_action="Run unit, rule-fixture, boundary, and regression validation suites.",
        )

    def _evaluate_shadow_gate(self, record: CapabilityRegistryRecord, validation_gate: CapabilityGateRecord) -> CapabilityGateRecord:
        if record.status == CapabilityStatus.ACTIVE:
            return CapabilityGateRecord(
                gate="shadow",
                decision=GateDecision.PASS,
                reason="Existing foundation capability is already active and protected by current-production regression suites.",
                next_action="Keep shadow comparison available for future migrations.",
            )
        if validation_gate.decision != GateDecision.PASS:
            return CapabilityGateRecord(
                gate="shadow",
                decision=GateDecision.WAITING_FOR_VALIDATION,
                reason="Shadow deployment is only allowed after validation passes.",
                next_action="Complete validation before entering shadow mode.",
            )
        if record.status in {CapabilityStatus.SHADOW, CapabilityStatus.ACTIVATION_READY}:
            return CapabilityGateRecord(
                gate="shadow",
                decision=GateDecision.PASS,
                reason="Shadow policy requirements are satisfied for this capability.",
                next_action="Continue monitoring or proceed to Admin activation review.",
            )
        return CapabilityGateRecord(
            gate="shadow",
            decision=GateDecision.WAITING_FOR_SHADOW,
            reason="The capability has not yet completed a governed shadow period.",
            next_action="Run shadow comparison against the current production path.",
        )

    def _evaluate_activation_gate(self, record: CapabilityRegistryRecord, shadow_gate: CapabilityGateRecord) -> CapabilityGateRecord:
        if record.status == CapabilityStatus.ACTIVE:
            return CapabilityGateRecord(
                gate="activation",
                decision=GateDecision.PASS,
                reason="The capability is already active in production and remains under regression protection.",
                next_action="Do not bypass P013 for any future changes.",
            )
        if shadow_gate.decision != GateDecision.PASS:
            return CapabilityGateRecord(
                gate="activation",
                decision=GateDecision.WAITING_FOR_SHADOW,
                reason="Activation cannot proceed before shadow completion.",
                next_action="Complete validation and shadow review first.",
            )
        if record.status == CapabilityStatus.ACTIVATION_READY:
            return CapabilityGateRecord(
                gate="activation",
                decision=GateDecision.WAITING_FOR_ADMIN,
                reason="Capability is activation-ready but still requires an explicit Admin activation decision.",
                next_action="Admin may approve LIMITED or ACTIVE rollout after reviewing shadow evidence.",
            )
        return CapabilityGateRecord(
            gate="activation",
            decision=GateDecision.WAITING_FOR_ADMIN,
            reason="Activation remains intentionally separate from implementation and validation.",
            next_action="Keep the capability inactive until an Admin decision is recorded.",
        )

    def lifecycle_records(self) -> list[CapabilityLifecycleRecord]:
        registry = {item.capability_id: item for item in self.registry_records()}
        records: list[CapabilityLifecycleRecord] = []
        for index, capability in enumerate(registry.values(), start=1):
            research_gate = self._evaluate_research_gate(capability)
            knowledge_gate = self._evaluate_knowledge_gate(capability, research_gate)
            rule_gate = self._evaluate_rule_gate(capability, knowledge_gate)
            dependency_gate = self._evaluate_dependency_gate(capability, registry)
            validation_gate = self._evaluate_validation_gate(capability, rule_gate, dependency_gate)
            shadow_gate = self._evaluate_shadow_gate(capability, validation_gate)
            activation_gate = self._evaluate_activation_gate(capability, shadow_gate)
            blocked_reason = None
            for gate in (
                research_gate,
                knowledge_gate,
                rule_gate,
                dependency_gate,
                validation_gate,
                shadow_gate,
                activation_gate,
            ):
                if gate.decision not in {GateDecision.PASS, GateDecision.WAITING_FOR_ADMIN}:
                    blocked_reason = gate.reason
                    break
            records.append(
                CapabilityLifecycleRecord(
                    lifecycle_id=f"VEDA-CLFC-{index:06d}",
                    capability_id=capability.capability_id,
                    current_status=capability.status,
                    allowed_next_statuses=self._allowed_next_statuses(capability.status),
                    research_gate=research_gate,
                    knowledge_gate=knowledge_gate,
                    rule_engineering_gate=rule_gate,
                    dependency_gate=dependency_gate,
                    validation_gate=validation_gate,
                    shadow_gate=shadow_gate,
                    activation_gate=activation_gate,
                    rollback_supported=True,
                    blocked_reason=blocked_reason,
                )
            )
        return records

    def validation_records(self) -> list[CapabilityValidationRecord]:
        lifecycle = {item.capability_id: item for item in self.lifecycle_records()}
        records: list[CapabilityValidationRecord] = []
        for index, capability in enumerate(self.registry_records(), start=1):
            suites = ["unit_validation", "rule_fixtures", "boundary_cases", "negative_cases", "regression_suites"]
            completed: list[str] = []
            if capability.status == CapabilityStatus.ACTIVE:
                completed = ["unit_validation", "regression_suites"]
                if capability.capability_type == CapabilityType.CALCULATION:
                    completed.append("rule_fixtures")
            status = ValidationStatus.NOT_STARTED
            if capability.status == CapabilityStatus.ACTIVE:
                status = ValidationStatus.PASS
            elif lifecycle[capability.capability_id].blocked_reason:
                status = ValidationStatus.BLOCKED
            records.append(
                CapabilityValidationRecord(
                    validation_id=f"VEDA-CVAL-{index:06d}",
                    capability_id=capability.capability_id,
                    status=status,
                    required_suites=suites,
                    completed_suites=completed,
                    boundary_cases=["lagna_boundary", "timezone_normalization", "ontology_id_integrity"],
                    negative_cases=["unsupported_claim_block", "missing_dependency_block", "direct_activation_block"],
                    regression_suites=["P001", "P004", "P011", "P012"],
                    shadow_required=capability.status not in {CapabilityStatus.ACTIVE},
                    notes="Interpretive capabilities compare structural activation and evidence trace rather than exact prose.",
                )
            )
        return records

    def activation_records(self) -> list[CapabilityActivationRecord]:
        lifecycle = {item.capability_id: item for item in self.lifecycle_records()}
        validations = {item.capability_id: item for item in self.validation_records()}
        records: list[CapabilityActivationRecord] = []
        for index, capability in enumerate(self.registry_records(), start=1):
            validation_passed = validations[capability.capability_id].status == ValidationStatus.PASS
            shadow_complete = lifecycle[capability.capability_id].shadow_gate.decision == GateDecision.PASS
            dependencies_satisfied = lifecycle[capability.capability_id].dependency_gate.decision == GateDecision.PASS
            records.append(
                CapabilityActivationRecord(
                    activation_id=f"VEDA-CACT-{index:06d}",
                    capability_id=capability.capability_id,
                    activation_state=capability.activation_status,
                    admin_activation_required=True,
                    validation_passed=validation_passed,
                    shadow_complete=shadow_complete,
                    dependencies_satisfied=dependencies_satisfied,
                    approval_required=True,
                    production_enabled=capability.activation_status == ActivationState.ACTIVE,
                    notes="Activation remains separate from implementation and requires an explicit Admin action.",
                )
            )
        return records

    def rollback_records(self) -> list[CapabilityRollbackRecord]:
        records: list[CapabilityRollbackRecord] = []
        for index, capability in enumerate(self.registry_records(), start=1):
            restore_target = "PREVIOUS_ACTIVE_VERSION" if capability.activation_status == ActivationState.ACTIVE else "INACTIVE"
            records.append(
                CapabilityRollbackRecord(
                    rollback_id=f"VEDA-CRBK-{index:06d}",
                    capability_id=capability.capability_id,
                    supported=True,
                    restore_target=restore_target,
                    notes="Rollback disables the governed capability path while preserving evidence, validation logs, and activation history.",
                )
            )
        return records

    def implementation_packages(self) -> list[CapabilityImplementationPackageRecord]:
        records: list[CapabilityImplementationPackageRecord] = []
        for index, capability in enumerate(self.registry_records(), start=1):
            records.append(
                CapabilityImplementationPackageRecord(
                    package_id=f"VEDA-CPKG-{index:06d}",
                    capability_id=capability.capability_id,
                    approved_claim_ids=capability.approved_claim_ids,
                    approved_rule_ids=capability.approved_rule_ids or capability.required_rules,
                    calculation_dependencies=capability.required_chart_facts,
                    implementation_module=next(
                        blueprint.implementation_module
                        for blueprint in self.blueprints()
                        if blueprint.capability_id == capability.capability_id
                    ),
                    validation_datasets=["P001 fixtures", "P004 fixtures", "P012 runtime fixtures"],
                    shadow_policy="Shadow against the legacy/runtime-protected path before any production activation.",
                    activation_policy="Admin activation required after validation and shadow acceptance.",
                    documentation=[
                        "VEDA-P013-06_IMPLEMENTATION_PACKAGE_STANDARD.md",
                        "VEDA-P013-07_VALIDATION_STANDARD.md",
                        "VEDA-P013-08_SHADOW_DEPLOYMENT.md",
                    ],
                    notes="Package references governed knowledge and runtime dependencies without activating the capability.",
                )
            )
        return records

    def coverage_matrix(self) -> list[CapabilityCoverageRecord]:
        registry = self.registry_records()
        categories = [
            "FOUNDATION",
            "Graha",
            "Bhava",
            "Lagna",
            "Nakshatra",
            "D1",
            "Vimshottari",
            "D2",
            "D3",
            "D4",
            "D7",
            "D9",
            "D10",
            "D12",
            "D16",
            "D20",
            "D24",
            "D27",
            "D30",
            "D40",
            "D45",
            "D60",
            "Dignity",
            "Shadbala",
            "Ashtakavarga",
            "Yoga",
            "Dosha",
            "Marriage",
            "Career",
            "Finance",
            "Children",
            "Health",
            "Education",
            "Property",
            "Spirituality",
            "Longevity",
            "Remedies",
            "Jaimini",
            "Muhurta",
        ]
        rows: list[CapabilityCoverageRecord] = []
        for category in categories:
            matches = [item for item in registry if item.coverage_category == category or item.subdomain == category or item.domain == category]
            total = len(matches)
            active = sum(1 for item in matches if item.status == CapabilityStatus.ACTIVE)
            researching = sum(1 for item in matches if item.status == CapabilityStatus.RESEARCHING)
            blocked = sum(1 for item in matches if item.status == CapabilityStatus.BLOCKED)
            implementation_ready = sum(1 for item in matches if item.status == CapabilityStatus.IMPLEMENTATION_READY)
            activation_ready = sum(1 for item in matches if item.status == CapabilityStatus.ACTIVATION_READY)
            high_stakes = sum(1 for item in matches if item.safety_class == SafetyClass.HIGH_STAKES)
            coverage = round(((active + implementation_ready + activation_ready) / total) * 100, 2) if total else 0.0
            rows.append(
                CapabilityCoverageRecord(
                    category=category,
                    total_capabilities=total,
                    active_capabilities=active,
                    researching_capabilities=researching,
                    blocked_capabilities=blocked,
                    implementation_ready_capabilities=implementation_ready,
                    activation_ready_capabilities=activation_ready,
                    high_stakes_capabilities=high_stakes,
                    coverage_percent=coverage,
                )
            )
        return rows

    def mission_proposals(self) -> list[CapabilityMissionProposal]:
        lifecycle = {item.capability_id: item for item in self.lifecycle_records()}
        proposals: list[CapabilityMissionProposal] = []
        for index, capability in enumerate(self.registry_records(), start=1):
            research_gate = lifecycle[capability.capability_id].research_gate
            if research_gate.decision != GateDecision.RESEARCH_MORE:
                continue
            proposals.append(
                CapabilityMissionProposal(
                    mission_id=f"VEDA-CMIS-{index:06d}",
                    capability_id=capability.capability_id,
                    title=f"Capability gap research: {capability.name}",
                    objective=(
                        f"Recover or validate approved-core knowledge for {capability.name} "
                        f"before rule engineering and implementation."
                    ),
                    research_type=ResearchType.KNOWLEDGE_GAP,
                    priority=MissionPriority.P0 if capability.safety_class == SafetyClass.HIGH_STAKES else MissionPriority.P1,
                    reason=research_gate.reason,
                    query_strategy={
                        "domain": capability.domain,
                        "subdomain": capability.subdomain,
                        "required_rules": capability.required_rules,
                        "runtime_profiles": capability.runtime_profile_support,
                    },
                    required_source_classes=capability.required_sources,
                )
            )
        return proposals

    def pilot_capability(self) -> dict[str, Any]:
        capability = next(item for item in self.registry_records() if item.capability_id == "VEDA-CAP-DIGNITY-000001")
        lifecycle = next(item for item in self.lifecycle_records() if item.capability_id == capability.capability_id)
        package = next(item for item in self.implementation_packages() if item.capability_id == capability.capability_id)
        mission = next((item for item in self.mission_proposals() if item.capability_id == capability.capability_id), None)
        draft_rule = self.draft_rules.get("VEDA-RUL-DIGNITY-000001", {})
        legacy_mapping = self.legacy_mappings.get("VEDA-LMP-000002", {})
        return {
            **_artifact_meta(),
            "capability_id": capability.capability_id,
            "name": capability.name,
            "legacy_behavior": legacy_mapping.get("legacy_behavior"),
            "legacy_location": legacy_mapping.get("legacy_function"),
            "draft_rule_id": "VEDA-RUL-DIGNITY-000001",
            "draft_rule_status": draft_rule.get("status"),
            "approved_rule_ids": capability.approved_rule_ids,
            "approved_core_available": bool(capability.approved_claim_ids or capability.approved_rule_ids),
            "research_gate": lifecycle.research_gate.model_dump(mode="json"),
            "knowledge_gate": lifecycle.knowledge_gate.model_dump(mode="json"),
            "dependency_gate": lifecycle.dependency_gate.model_dump(mode="json"),
            "validation_gate": lifecycle.validation_gate.model_dump(mode="json"),
            "shadow_gate": lifecycle.shadow_gate.model_dump(mode="json"),
            "activation_gate": lifecycle.activation_gate.model_dump(mode="json"),
            "implementation_package": package.model_dump(mode="json"),
            "recommended_research_mission": mission.model_dump(mode="json") if mission else None,
            "final_status": capability.status.value,
            "blocked_reason": lifecycle.blocked_reason,
            "activation_ready": capability.status == CapabilityStatus.ACTIVATION_READY,
            "governance_outcome": "ACTIVATION_READY" if capability.status == CapabilityStatus.ACTIVATION_READY else "BLOCKED_WITH_EXPLICIT_REASON",
        }

    def roadmap(self) -> list[dict[str, Any]]:
        return [
            {
                "phase": "P014",
                "title": "Core Rule Migration & Graha/Bhava/Dignity",
                "depends_on": ["VEDA-CAP-DIGNITY-000001", "VEDA-CAP-INTERPRETATION-000001"],
                "rationale": "Dignity and foundational interpretive rules are the lowest-risk governed migration target after P013.",
            },
            {
                "phase": "P015",
                "title": "Varga Calculation & Interpretation Programme",
                "depends_on": ["VEDA-CAP-VARGA-000001", "VEDA-CAP-VARGA-000002", "VEDA-CAP-VARGA-000003", "VEDA-CAP-VARGA-000004"],
                "rationale": "Marriage, career, and other domain expansions depend on governed divisional-chart capability.",
            },
            {
                "phase": "P016",
                "title": "Yoga / Dosha Knowledge Programme",
                "depends_on": ["VEDA-CAP-RULE-000001", "VEDA-CAP-RULE-000002"],
                "rationale": "Composite analyses should not activate until Yoga and Dosha provenance is governed.",
            },
            {
                "phase": "P017",
                "title": "Dasha Expansion & Timing Intelligence",
                "depends_on": ["VEDA-CAP-TIMING-000002", "VEDA-CAP-TIMING-000003"],
                "rationale": "Timing expansion comes after the foundational Vimshottari path and governed lifecycle are stable.",
            },
            {
                "phase": "P018",
                "title": "Strength Systems",
                "depends_on": ["VEDA-CAP-STRENGTH-000001", "VEDA-CAP-STRENGTH-000002"],
                "rationale": "Shadbala and Ashtakavarga are downstream from foundation runtime and ontology coverage.",
            },
            {
                "phase": "P019",
                "title": "Relationship & Marriage Intelligence",
                "depends_on": ["VEDA-CAP-DOMAIN-000001", "VEDA-CAP-VARGA-000001", "VEDA-CAP-VARGA-000002", "VEDA-CAP-RULE-000001"],
                "rationale": "Marriage intelligence depends on D9, foundational interpretation, and governed Yoga support.",
            },
            {
                "phase": "P020",
                "title": "Career / Education / Wealth Intelligence",
                "depends_on": ["VEDA-CAP-DOMAIN-000002", "VEDA-CAP-DOMAIN-000003", "VEDA-CAP-VARGA-000003", "VEDA-CAP-VARGA-000004"],
                "rationale": "Career and finance require D10 plus high-stakes and safety governance.",
            },
            {
                "phase": "P021",
                "title": "Children / Family / Property",
                "depends_on": ["VEDA-CAP-DOMAIN-000004"],
                "rationale": "Family-domain work depends on the same governed lifecycle and likely additional Vargas.",
            },
            {
                "phase": "P022",
                "title": "Health / Longevity Research Governance",
                "depends_on": ["VEDA-CAP-DOMAIN-000005", "VEDA-CAP-DOMAIN-000006"],
                "rationale": "High-stakes domains require the stricter lifecycle created in P013 before any runtime activation.",
            },
            {
                "phase": "P023",
                "title": "Remedies Governance",
                "depends_on": ["VEDA-CAP-DOMAIN-000007"],
                "rationale": "Remedies remain separately governed and cannot ride on interpretive phases.",
            },
            {
                "phase": "P024",
                "title": "Muhurta / Electional Astrology",
                "depends_on": ["VEDA-CAP-ADVANCED-000002"],
                "rationale": "Event-time and electional capabilities need dedicated runtime semantics and governed sources.",
            },
            {
                "phase": "P025",
                "title": "Jaimini Systems",
                "depends_on": ["VEDA-CAP-ADVANCED-000001"],
                "rationale": "Jaimini requires separate ontology, runtime facts, and evidence policy.",
            },
            {
                "phase": "P026",
                "title": "Advanced Synthesis & Multi-Chart Reasoning",
                "depends_on": ["P019", "P020", "P022", "P025"],
                "rationale": "Multi-chart reasoning should only follow after major governed sub-capabilities exist.",
            },
        ]

    def summary(self) -> dict[str, Any]:
        registry = self.registry_records()
        lifecycle = self.lifecycle_records()
        pilot = self.pilot_capability()
        return {
            "capabilities_registered": len(registry),
            "active_capabilities": sum(1 for item in registry if item.status == CapabilityStatus.ACTIVE),
            "researching_capabilities": sum(1 for item in registry if item.status == CapabilityStatus.RESEARCHING),
            "blocked_capabilities": sum(1 for item in registry if item.status == CapabilityStatus.BLOCKED),
            "activation_ready_capabilities": sum(1 for item in registry if item.status == CapabilityStatus.ACTIVATION_READY),
            "high_stakes_capabilities": sum(1 for item in registry if item.safety_class == SafetyClass.HIGH_STAKES),
            "mission_proposals": len(self.mission_proposals()),
            "dependency_edges": len(self.dependency_records()),
            "pilot_capability_id": pilot["capability_id"],
            "pilot_status": pilot["final_status"],
            "pilot_blocked_reason": pilot["blocked_reason"],
            "next_recommended_phase": "P014 - Core Rule Migration & Graha/Bhava/Dignity",
            "p012_runtime_integration": "YES",
            "p011_rag_integration": "YES",
            "p010_promotion_integration": "YES",
            "p009_research_integration": "YES",
            "production_capabilities_activated": 0,
            "production_calculation_semantics_changed": "NO",
            "production_interpretation_semantics_changed": "NO",
            "approved_core_automatically_modified": "NO",
            "runtime_surfaces_from_p012": self.runtime_summary.get("runtime_surfaces_identified", 0),
            "p001_fixture_pass_count": self.runtime_summary.get("p001_pass_count", 0),
            "p004_fixture_pass_count": self.runtime_summary.get("p004_pass_count", 0),
            "lifecycle_fail_closed": all(
                item.activation_gate.decision != GateDecision.PASS or item.current_status == CapabilityStatus.ACTIVE
                for item in lifecycle
            ),
        }

    def list_capability_rows(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        safety_class: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        rows = self.registry_records()
        if category:
            needle = category.strip().lower()
            rows = [row for row in rows if row.coverage_category.lower() == needle or row.domain.lower() == needle or row.subdomain.lower() == needle]
        if status:
            normalized = status.strip().upper()
            rows = [row for row in rows if row.status.value == normalized]
        if safety_class:
            normalized = safety_class.strip().upper()
            rows = [row for row in rows if row.safety_class.value == normalized]
        if search:
            needle = search.strip().lower()
            rows = [
                row for row in rows
                if needle in row.name.lower()
                or needle in row.capability_id.lower()
                or needle in row.domain.lower()
                or needle in row.subdomain.lower()
            ]
        total = len(rows)
        start = max(page - 1, 0) * per_page
        end = start + per_page
        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "returned": max(min(total - start, per_page), 0),
            "capabilities": [row.model_dump(mode="json") for row in rows[start:end]],
        }

    def get_capability_detail(self, capability_id: str) -> dict[str, Any]:
        registry = {item.capability_id: item for item in self.registry_records()}
        if capability_id not in registry:
            raise KeyError(capability_id)
        lifecycle = {item.capability_id: item for item in self.lifecycle_records()}
        validations = {item.capability_id: item for item in self.validation_records()}
        activations = {item.capability_id: item for item in self.activation_records()}
        rollbacks = {item.capability_id: item for item in self.rollback_records()}
        packages = {item.capability_id: item for item in self.implementation_packages()}
        proposal = next((item for item in self.mission_proposals() if item.capability_id == capability_id), None)
        transitions = {
            target.value: self.preview_transition(capability_id, target, actor_is_admin=True).model_dump(mode="json")
            for target in CapabilityStatus
            if target != registry[capability_id].status
        }
        return {
            "capability": registry[capability_id].model_dump(mode="json"),
            "lifecycle": lifecycle[capability_id].model_dump(mode="json"),
            "validation": validations[capability_id].model_dump(mode="json"),
            "activation": activations[capability_id].model_dump(mode="json"),
            "rollback": rollbacks[capability_id].model_dump(mode="json"),
            "implementation_package": packages[capability_id].model_dump(mode="json"),
            "research_mission_proposal": proposal.model_dump(mode="json") if proposal else None,
            "transition_preview": transitions,
        }

    def create_research_mission(self, research_service: Any, capability_id: str, *, actor_id: str = "admin") -> dict[str, Any]:
        proposal = next((item for item in self.mission_proposals() if item.capability_id == capability_id), None)
        if proposal is None:
            raise ValueError(f"No research mission proposal is available for {capability_id}.")
        existing = next(
            (
                mission for mission in research_service.list_missions()
                if mission.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY" and mission.title == proposal.title
            ),
            None,
        )
        if existing is not None:
            return {"duplicate": True, "mission": existing.model_dump(mode="json"), "proposal": proposal.model_dump(mode="json")}
        mission = research_service.create_mission(
            {
                "domain_id": "VEDA-DOMAIN-VEDIC-ASTROLOGY",
                "title": proposal.title,
                "objective": proposal.objective,
                "research_type": proposal.research_type.value,
                "priority": proposal.priority.value,
                "status": "QUEUED",
                "created_by": actor_id,
                "query_strategy": proposal.query_strategy,
                "required_source_classes": proposal.required_source_classes,
                "known_gap_ids": [capability_id],
                "notes": f"P013 capability-driven mission for {capability_id}. Reason: {proposal.reason}",
            }
        )
        return {"duplicate": False, "mission": mission.model_dump(mode="json"), "proposal": proposal.model_dump(mode="json")}

    def preview_transition(
        self,
        capability_id: str,
        target_status: CapabilityStatus | str,
        *,
        actor_is_admin: bool = False,
    ) -> CapabilityTransitionRecord:
        normalized = CapabilityStatus(target_status)
        lifecycle = {item.capability_id: item for item in self.lifecycle_records()}
        registry = {item.capability_id: item for item in self.registry_records()}
        if capability_id not in lifecycle:
            raise KeyError(capability_id)
        current = lifecycle[capability_id]
        capability = registry[capability_id]
        allowed = normalized in current.allowed_next_statuses
        if not allowed:
            return CapabilityTransitionRecord(
                from_status=current.current_status,
                to_status=normalized,
                allowed=False,
                reason=f"Transition {current.current_status.value} -> {normalized.value} is not allowed by the P013 lifecycle.",
            )
        if normalized == CapabilityStatus.ACTIVE:
            if not actor_is_admin:
                return CapabilityTransitionRecord(
                    from_status=current.current_status,
                    to_status=normalized,
                    allowed=False,
                    reason="Only an Admin can activate a capability after shadow and validation complete.",
                )
            if current.activation_gate.decision != GateDecision.PASS and current.current_status != CapabilityStatus.ACTIVATION_READY:
                return CapabilityTransitionRecord(
                    from_status=current.current_status,
                    to_status=normalized,
                    allowed=False,
                    reason=current.activation_gate.reason,
                )
        if normalized == CapabilityStatus.SHADOW and current.validation_gate.decision != GateDecision.PASS:
            return CapabilityTransitionRecord(
                from_status=current.current_status,
                to_status=normalized,
                allowed=False,
                reason=current.validation_gate.reason,
            )
        if normalized == CapabilityStatus.RULE_ENGINEERING and current.knowledge_gate.decision != GateDecision.PASS:
            return CapabilityTransitionRecord(
                from_status=current.current_status,
                to_status=normalized,
                allowed=False,
                reason=current.knowledge_gate.reason,
            )
        return CapabilityTransitionRecord(
            from_status=capability.status,
            to_status=normalized,
            allowed=True,
            reason="Transition is structurally allowed under the P013 lifecycle contract.",
        )


def _schema_documents() -> dict[str, Any]:
    return {
        "capability_registry.schema.json": CapabilityRegistryRecord.model_json_schema(),
        "capability_dependency.schema.json": CapabilityDependencyRecord.model_json_schema(),
        "capability_lifecycle.schema.json": CapabilityLifecycleRecord.model_json_schema(),
        "capability_validation.schema.json": CapabilityValidationRecord.model_json_schema(),
        "capability_activation.schema.json": CapabilityActivationRecord.model_json_schema(),
        "capability_rollback.schema.json": CapabilityRollbackRecord.model_json_schema(),
        "capability_coverage.schema.json": CapabilityCoverageRecord.model_json_schema(),
        "capability_package.schema.json": CapabilityImplementationPackageRecord.model_json_schema(),
    }


def write_json_schemas(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    target = root / "schemas" / "astrology"
    written: list[Path] = []
    for name, schema in _schema_documents().items():
        path = target / name
        _write_json(path, schema)
        written.append(path)
    return written


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    service = JyotishaCapabilityLifecycleService(root=root)
    return {
        "meta": _artifact_meta(),
        "capability_registry": [item.model_dump(mode="json") for item in service.registry_records()],
        "capability_dependencies": [item.model_dump(mode="json") for item in service.dependency_records()],
        "capability_lifecycle": [item.model_dump(mode="json") for item in service.lifecycle_records()],
        "capability_validation": [item.model_dump(mode="json") for item in service.validation_records()],
        "capability_activation": [item.model_dump(mode="json") for item in service.activation_records()],
        "capability_rollback": [item.model_dump(mode="json") for item in service.rollback_records()],
        "coverage_matrix": [item.model_dump(mode="json") for item in service.coverage_matrix()],
        "implementation_packages": [item.model_dump(mode="json") for item in service.implementation_packages()],
        "research_gap_missions": [item.model_dump(mode="json") for item in service.mission_proposals()],
        "pilot_capability": service.pilot_capability(),
        "expansion_roadmap": service.roadmap(),
        "summary": service.summary(),
    }


def export_phase_bundle(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    write_json_schemas(root)
    target = Path(cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR)
    files = {
        "p013_capability_registry.json": bundle["capability_registry"],
        "p013_capability_dependencies.json": bundle["capability_dependencies"],
        "p013_capability_lifecycle.json": bundle["capability_lifecycle"],
        "p013_capability_validation.json": bundle["capability_validation"],
        "p013_capability_activation.json": bundle["capability_activation"],
        "p013_capability_rollback.json": bundle["capability_rollback"],
        "p013_coverage_matrix.json": bundle["coverage_matrix"],
        "p013_implementation_packages.json": bundle["implementation_packages"],
        "p013_research_gap_missions.json": bundle["research_gap_missions"],
        "p013_pilot_capability.json": bundle["pilot_capability"],
        "p013_expansion_roadmap.json": bundle["expansion_roadmap"],
        "p013_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = target / name
        _write_json(path, payload)
        written.append(path)
    written.extend(render_phase_docs(root))
    return written


def render_phase_docs(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    summary = bundle["summary"]
    registry = bundle["capability_registry"]
    lifecycle = bundle["capability_lifecycle"]
    dependencies = bundle["capability_dependencies"]
    coverage = bundle["coverage_matrix"]
    missions = bundle["research_gap_missions"]
    roadmap = bundle["expansion_roadmap"]
    pilot = bundle["pilot_capability"]

    registry_lines = "\n".join(
        f"| `{row['capability_id']}` | {row['name']} | {row['status']} | {row['domain']} | {row['subdomain']} | {row['safety_class']} |"
        for row in registry
    )
    lifecycle_lines = "\n".join(
        f"| `{row['capability_id']}` | {row['current_status']} | {row['research_gate']['decision']} | {row['knowledge_gate']['decision']} | {row['validation_gate']['decision']} | {row['activation_gate']['decision']} |"
        for row in lifecycle
    )
    dependency_lines = "\n".join(
        f"| `{row['capability_id']}` | `{row['depends_on']}` | {row['dependency_kind']} | {row['minimum_status']} |"
        for row in dependencies[:24]
    )
    coverage_lines = "\n".join(
        f"| {row['category']} | {row['total_capabilities']} | {row['active_capabilities']} | {row['researching_capabilities']} | {row['blocked_capabilities']} | {row['coverage_percent']} |"
        for row in coverage
        if row["total_capabilities"] > 0
    )
    mission_lines = "\n".join(
        f"| `{row['capability_id']}` | {row['title']} | {row['research_type']} | {row['priority']} |"
        for row in missions
    )
    roadmap_lines = "\n".join(
        f"| {row['phase']} | {row['title']} | {', '.join(row['depends_on'])} |"
        for row in roadmap
    )

    docs = {
        "VEDA-P013-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P013 Executive Summary

P013 establishes a governed capability-engineering lifecycle on top of the existing research, approved-core, runtime, and rule infrastructure.

Key outcomes:

- Capabilities registered: `{summary['capabilities_registered']}`
- Dependency edges recorded: `{summary['dependency_edges']}`
- Research mission proposals generated: `{summary['mission_proposals']}`
- Pilot capability: `{summary['pilot_capability_id']}` -> `{summary['pilot_status']}`
- Lifecycle fail-closed: `{summary['lifecycle_fail_closed']}`

Production expectations remain unchanged:

- Production capabilities activated: `{summary['production_capabilities_activated']}`
- Production calculation semantics changed: `{summary['production_calculation_semantics_changed']}`
- Production interpretation semantics changed: `{summary['production_interpretation_semantics_changed']}`
- Approved Core automatically modified: `{summary['approved_core_automatically_modified']}`
""",
        "VEDA-P013-01_CAPABILITY_ARCHITECTURE.md": f"""# Capability Architecture

The capability registry is machine-readable and links every future Jyotisha capability to:

- required runtime facts from P012
- approved-core claims and rules from P010/P011
- lifecycle gates
- validation/shadow/activation policy

| Capability ID | Name | Status | Domain | Subdomain | Safety |
| --- | --- | --- | --- | --- | --- |
{registry_lines}
""",
        "VEDA-P013-02_CAPABILITY_LIFECYCLE.md": f"""# Capability Lifecycle

| Capability | Current | Research Gate | Knowledge Gate | Validation Gate | Activation Gate |
| --- | --- | --- | --- | --- | --- |
{lifecycle_lines}
""",
        "VEDA-P013-03_RESEARCH_KNOWLEDGE_GATES.md": f"""# Research & Knowledge Gates

Research cannot jump directly to production implementation. The current gap-driven mission proposals are:

| Capability | Proposed Mission | Research Type | Priority |
| --- | --- | --- | --- |
{mission_lines}
""",
        "VEDA-P013-04_RULE_ENGINEERING_STANDARD.md": """# Rule Engineering Standard

Approved knowledge does not become Python logic directly.

P013 requires:

1. Approved Core knowledge or a validated deterministic-calculation exception.
2. P003 machine-readable rule modeling.
3. Explicit conditions, exceptions, confirmations, and activation status.
4. Traceability from capability -> rule -> claim -> passage -> source.
""",
        "VEDA-P013-05_DEPENDENCY_GRAPH.md": f"""# Dependency Graph

| Capability | Depends On | Kind | Minimum Status |
| --- | --- | --- | --- |
{dependency_lines}
""",
        "VEDA-P013-06_IMPLEMENTATION_PACKAGE_STANDARD.md": """# Implementation Package Standard

Each capability package references:

- approved claim IDs
- approved rule IDs
- canonical chart-fact dependencies
- implementation module
- validation datasets
- shadow policy
- activation policy
""",
        "VEDA-P013-07_VALIDATION_STANDARD.md": """# Validation Standard

Required validation classes:

- unit validation
- rule fixtures
- cross-source validation
- boundary cases
- negative cases
- regression suites

Interpretive capabilities compare structural activation and evidence trace, not exact prose wording.
""",
        "VEDA-P013-08_SHADOW_DEPLOYMENT.md": """# Shadow Deployment

Shadow deployment is a mandatory stage before activation for new governed capabilities.

P013 keeps shadow output internal/admin-only and never displays it to normal users by default.
""",
        "VEDA-P013-09_ACTIVATION_ROLLBACK.md": """# Activation & Rollback

Activation remains separate from implementation. Only an Admin may move a capability from `ACTIVATION_READY` to `ACTIVE`.

Rollback restores the prior active version or returns the governed capability to `INACTIVE` while preserving:

- evidence
- validation history
- shadow history
- activation history
""",
        "VEDA-P013-10_CAPABILITY_CONFIDENCE.md": """# Capability Confidence

P013 preserves separate confidence dimensions:

- research_confidence
- source_confidence
- implementation_confidence
- calculation_confidence
- validation_confidence
- production_confidence

This avoids collapsing provenance, engineering quality, and runtime certainty into one misleading score.
""",
        "VEDA-P013-11_ADMIN_CAPABILITY_CONTROL.md": """# Admin Capability Control

The framework is designed so Admin control can supervise:

- research start / continuation
- shadow entry
- activation
- pause
- rollback

P013 keeps the implementation fail-closed: non-Admin callers cannot mark a capability active by bypassing lifecycle gates.
""",
        "VEDA-P013-12_COVERAGE_MATRIX.md": f"""# Coverage Matrix

| Category | Total | Active | Researching | Blocked | Coverage % |
| --- | ---: | ---: | ---: | ---: | ---: |
{coverage_lines}
""",
        "VEDA-P013-13_PILOT_CAPABILITY.md": f"""# Pilot Capability

Pilot capability: `{pilot['capability_id']}`.

- Final status: `{pilot['final_status']}`
- Governance outcome: `{pilot['governance_outcome']}`
- Blocked reason: `{pilot['blocked_reason']}`
- Draft rule: `{pilot['draft_rule_id']}` (`{pilot['draft_rule_status']}`)
- Approved Core available: `{pilot['approved_core_available']}`

This is the intended P013 proof point: the lifecycle blocks legacy dignity migration until provenance reaches approved-core quality.
""",
        "VEDA-P013-14_EXPANSION_ROADMAP.md": f"""# Expansion Roadmap

| Phase | Title | Depends On |
| --- | --- | --- |
{roadmap_lines}
""",
        "VEDA-P013-15_SECURITY_GOVERNANCE.md": """# Security Governance

P013 prevents manual or code-level lifecycle bypass:

- no direct `RESEARCHING -> ACTIVE`
- no activation without Admin
- no implementation without governed knowledge
- no capability rollout without validation and shadow policy
- no high-stakes activation without stricter evidence and review
""",
        "VEDA-P013-16_REGRESSION_REPORT.md": """# Regression Report

P013 is designed to preserve:

- P001 runtime and security protections
- P004 calculation validation
- P010 approved-core governance
- P011 citation-aware retrieval
- P012 runtime boundary isolation

The framework itself does not activate new runtime behaviour.
""",
        "VEDA-P013-17_FINAL_ACCEPTANCE.md": f"""# Final Acceptance

- Next recommended phase: `{summary['next_recommended_phase']}`
- Production capabilities activated: `{summary['production_capabilities_activated']}`
- Production calculation semantics changed: `{summary['production_calculation_semantics_changed']}`
- Production interpretation semantics changed: `{summary['production_interpretation_semantics_changed']}`
- Approved Core automatically modified: `{summary['approved_core_automatically_modified']}`
""",
    }

    written: list[Path] = []
    for name, content in docs.items():
        path = root / "docs" / "current-state" / "p013" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def validate_exported_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    expected = {
        "p013_capability_registry.json": bundle["capability_registry"],
        "p013_capability_dependencies.json": bundle["capability_dependencies"],
        "p013_capability_lifecycle.json": bundle["capability_lifecycle"],
        "p013_capability_validation.json": bundle["capability_validation"],
        "p013_capability_activation.json": bundle["capability_activation"],
        "p013_capability_rollback.json": bundle["capability_rollback"],
        "p013_coverage_matrix.json": bundle["coverage_matrix"],
        "p013_implementation_packages.json": bundle["implementation_packages"],
        "p013_research_gap_missions.json": bundle["research_gap_missions"],
        "p013_pilot_capability.json": bundle["pilot_capability"],
        "p013_expansion_roadmap.json": bundle["expansion_roadmap"],
        "p013_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    target = Path(cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR)
    missing: list[str] = []
    mismatched: list[str] = []
    for name, payload in expected.items():
        path = target / name
        if not path.exists():
            missing.append(name)
            continue
        if _load_json(path) != payload:
            mismatched.append(name)

    schema_errors: list[str] = []
    if jsonschema is not None:
        schemas = _schema_documents()
        checks: list[tuple[str, Any]] = []
        checks.extend(("capability_registry.schema.json", row) for row in bundle["capability_registry"])
        checks.extend(("capability_dependency.schema.json", row) for row in bundle["capability_dependencies"])
        checks.extend(("capability_lifecycle.schema.json", row) for row in bundle["capability_lifecycle"])
        checks.extend(("capability_validation.schema.json", row) for row in bundle["capability_validation"])
        checks.extend(("capability_activation.schema.json", row) for row in bundle["capability_activation"])
        checks.extend(("capability_rollback.schema.json", row) for row in bundle["capability_rollback"])
        checks.extend(("capability_coverage.schema.json", row) for row in bundle["coverage_matrix"])
        checks.extend(("capability_package.schema.json", row) for row in bundle["implementation_packages"])
        for schema_name, payload in checks:
            try:
                jsonschema.validate(payload, schemas[schema_name])
            except Exception as exc:  # pragma: no cover - error reporting only
                schema_errors.append(f"{schema_name}: {exc}")

    return {
        "is_valid": not missing and not mismatched and not schema_errors,
        "missing_files": missing,
        "mismatched_files": mismatched,
        "schema_errors": schema_errors,
    }


@lru_cache(maxsize=1)
def get_jyotisha_capability_lifecycle_service() -> JyotishaCapabilityLifecycleService:
    return JyotishaCapabilityLifecycleService()


__all__ = [
    "ActivationState",
    "CapabilityStatus",
    "CapabilityType",
    "ChangeClass",
    "GateDecision",
    "JyotishaCapabilityLifecycleService",
    "build_phase_bundle",
    "export_phase_bundle",
    "get_jyotisha_capability_lifecycle_service",
    "render_phase_docs",
    "validate_exported_bundle",
    "write_json_schemas",
]
