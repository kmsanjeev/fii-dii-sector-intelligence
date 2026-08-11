from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.ai.knowledge.astrology_governance import (
    AllowedOutputMode,
    ApprovalRecord,
    ApprovalRole,
    ApprovalStatus as GovernanceApprovalStatus,
    ArtifactStatus,
    ArtifactType,
    AstrologySourceRecord,
    AuthorityProfile,
    AuthorityTier,
    ClaimRecord,
    ConflictRecord,
    ConflictResolutionStatus,
    ConflictType,
    EvidenceType,
    InterpretationType,
    LegalAccessStatus,
    PassageRecord,
    PrimarySecondaryStatus,
    QualityGrade,
    RoleDecision,
    SourceClass,
    SupportLevel,
    VerificationStatus,
    WorkflowState,
)
from engines.ai.knowledge.astrology_ontology import (
    AllowedOutputMode as OntologyOutputMode,
    ApprovalStatus as OntologyApprovalStatus,
    AstrologyRuleRecord,
    ConditionNode,
    ConditionOperator,
    LegacyKnowledgeMappingRecord,
    LegacyMappingStatus,
    OperandKind,
    OperandReference,
    OutcomeType,
    RuleAuthorityProfile,
    RuleConditionSet,
    RuleLifecycleStatus,
    RuleOutcome,
    RuleProvenance,
    RuleType,
    SemanticMatch,
)
from engines.ai.research.platform.contracts import (
    ApprovalStatus,
    CoreVersionState,
    PromotionPreflightStatus,
    ResearchApprovalRecord,
    ResearchCandidateRecord,
    ResearchConflictRecord,
    ResearchCoreKnowledgeRecord,
    ResearchEvidenceRecord,
    SourceObservationRecord,
)
from engines.common import config as cfg


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _title_token(value: str, *, fallback: str = "GENERIC") -> str:
    cleaned = re.sub(r"[^A-Z0-9]+", "_", str(value or "").upper()).strip("_")
    return cleaned[:24] or fallback


def _enum_or(enum_cls, value: Any, default):
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    raw = str(value).strip()
    if not raw:
        return default
    try:
        return enum_cls(raw)
    except Exception:
        try:
            return enum_cls(raw.upper())
        except Exception:
            return default


def _artifact_meta(actor_id: str, change_reason: str, *, notes: str | None = None, status: str | None = None) -> dict[str, Any]:
    now = _utc_now()
    payload = {
        "version": "1.0.0",
        "created_at": now,
        "created_by": actor_id,
        "updated_at": now,
        "updated_by": actor_id,
        "change_reason": change_reason,
        "supersedes": None,
        "superseded_by": None,
        "notes": notes,
    }
    if status is not None:
        payload["status"] = status
    return payload


def _increment_semver(value: str | None) -> str:
    raw = str(value or "1.0.0").strip() or "1.0.0"
    try:
        major, minor, patch = [int(part) for part in raw.split(".", 2)]
    except Exception:
        return "1.0.0"
    return f"{major}.{minor}.{patch + 1}"


@dataclass(slots=True)
class PromotionMaterializationResult:
    source_ids: list[str]
    passage_ids: list[str]
    claim_ids: list[str]
    conflict_ids: list[str]
    approval_ids: list[str]
    rule_ids: list[str]
    core_records: list[ResearchCoreKnowledgeRecord]
    current_core_docs: list[dict[str, Any]]
    previous_core_ids: list[str]
    created_files: list[str]
    updated_files: list[str]
    warnings: list[str]
    file_snapshot: dict[str, str | None] = field(default_factory=dict)


class VedicAstrologyPromotionMaterializer:
    def __init__(self) -> None:
        self.source_dir = Path(cfg.VEDA_ASTROLOGY_SOURCE_DIR)
        self.passage_dir = Path(cfg.VEDA_ASTROLOGY_PASSAGE_DIR)
        self.claim_dir = Path(cfg.VEDA_ASTROLOGY_CLAIM_DIR)
        self.conflict_dir = Path(cfg.VEDA_ASTROLOGY_CONFLICT_DIR)
        self.approval_dir = Path(cfg.VEDA_ASTROLOGY_APPROVAL_DIR)
        self.rule_dir = Path(cfg.VEDA_ASTROLOGY_RULE_APPROVED_DIR)
        self.legacy_dir = Path(cfg.VEDA_ASTROLOGY_RULE_LEGACY_MAPPING_DIR)
        self.core_docs_path = Path(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS)

    def materialize(
        self,
        *,
        candidate: ResearchCandidateRecord,
        approval: ResearchApprovalRecord,
        evidence_rows: list[ResearchEvidenceRecord],
        observations: list[SourceObservationRecord],
        conflicts: list[ResearchConflictRecord],
        existing_core_matches: list[ResearchCoreKnowledgeRecord],
        promotion_id: str,
        core_id: str,
        actor_id: str,
        promotion_notes: str | None = None,
    ) -> PromotionMaterializationResult:
        source_records_by_observation: dict[str, AstrologySourceRecord] = {}
        source_ids: list[str] = []
        passage_ids: list[str] = []
        claim_ids: list[str] = []
        conflict_ids: list[str] = []
        approval_ids: list[str] = []
        rule_ids: list[str] = []
        warnings: list[str] = []
        previous_core_ids = [item.core_id for item in existing_core_matches]
        created_files: list[str] = []
        updated_files: list[str] = []
        writes: dict[Path, str] = {}

        existing_sources = self._load_models(self.source_dir, AstrologySourceRecord)
        existing_passages = self._load_models(self.passage_dir, PassageRecord)
        current_core_docs = self._load_core_docs()
        source_records_by_id = {item.source_id: item for item in existing_sources}

        for observation in observations:
            source_record, created = self._resolve_source_record(
                observation=observation,
                candidate=candidate,
                actor_id=actor_id,
                existing_records=existing_sources,
                change_reason=f"P010 promotion source materialization for {candidate.candidate_id}.",
            )
            source_records_by_observation[observation.observation_id] = source_record
            source_records_by_id[source_record.source_id] = source_record
            if source_record.source_id not in source_ids:
                source_ids.append(source_record.source_id)
            if created:
                path = self._source_path(source_record.source_id)
                writes[path] = json.dumps(source_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
                created_files.append(str(path))

        for evidence in evidence_rows:
            observation = next((item for item in observations if item.observation_id == evidence.observation_id), None)
            if observation is None:
                warnings.append(f"Evidence {evidence.evidence_id} could not resolve observation {evidence.observation_id}.")
                continue
            source_record = source_records_by_observation.get(observation.observation_id)
            if source_record is None:
                warnings.append(f"Observation {observation.observation_id} did not resolve to a governed source record.")
                continue
            passage_record, created = self._resolve_passage_record(
                evidence=evidence,
                observation=observation,
                candidate=candidate,
                source_id=source_record.source_id,
                actor_id=actor_id,
                existing_records=existing_passages,
                change_reason=f"P010 promotion passage materialization for {candidate.candidate_id}.",
            )
            if passage_record.passage_id not in passage_ids:
                passage_ids.append(passage_record.passage_id)
            if created:
                path = self._passage_path(passage_record.passage_id)
                writes[path] = json.dumps(passage_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
                created_files.append(str(path))

        claim_record = self._create_claim_record(
            candidate=candidate,
            passage_ids=passage_ids,
            actor_id=actor_id,
            change_reason=f"P010 promotion claim materialization for {candidate.candidate_id}.",
            notes=promotion_notes,
        )
        claim_ids.append(claim_record.claim_id)
        claim_path = self._claim_path(claim_record.claim_id)
        writes[claim_path] = json.dumps(claim_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
        created_files.append(str(claim_path))

        matched_claim_id = next((item.claim_ids[0] for item in existing_core_matches if item.claim_ids), None)
        for research_conflict in conflicts:
            if not matched_claim_id:
                warnings.append(
                    f"Conflict {research_conflict.conflict_id} preserved in core lineage only because no opposing governed claim is available."
                )
                continue
            conflict_record = self._create_conflict_record(
                candidate=candidate,
                research_conflict=research_conflict,
                new_claim_id=claim_record.claim_id,
                existing_claim_id=matched_claim_id,
                source_ids=source_ids,
                actor_id=actor_id,
                change_reason=f"P010 promotion conflict preservation for {candidate.candidate_id}.",
            )
            conflict_ids.append(conflict_record.conflict_id)
            conflict_path = self._conflict_path(conflict_record.conflict_id)
            writes[conflict_path] = json.dumps(conflict_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
            created_files.append(str(conflict_path))

        approval_record = self._create_approval_record(
            candidate=candidate,
            approval=approval,
            source_ids=source_ids,
            passage_ids=passage_ids,
            claim_ids=claim_ids,
            conflict_ids=conflict_ids,
            actor_id=actor_id,
            change_reason=f"P010 promotion approval materialization for {candidate.candidate_id}.",
        )
        approval_ids.append(approval_record.approval_id)
        approval_path = self._approval_path(approval_record.approval_id)
        writes[approval_path] = json.dumps(approval_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
        created_files.append(str(approval_path))

        rule_record = self._create_rule_record(
            candidate=candidate,
            source_ids=source_ids,
            passage_ids=passage_ids,
            claim_ids=claim_ids,
            conflict_ids=conflict_ids,
            actor_id=actor_id,
            change_reason=f"P010 promotion rule materialization for {candidate.candidate_id}.",
            notes=promotion_notes,
        )
        if rule_record is not None:
            rule_ids.append(rule_record.rule_id)
            rule_path = self._rule_path(rule_record.rule_id)
            writes[rule_path] = json.dumps(rule_record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
            created_files.append(str(rule_path))

        legacy_updates = self._update_legacy_mappings(
            candidate=candidate,
            rule_ids=rule_ids,
            actor_id=actor_id,
        )
        for path, payload in legacy_updates.items():
            writes[path] = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            updated_files.append(str(path))

        supersede_updates = self._supersede_previous_core_artifacts(
            existing_core_matches=existing_core_matches,
            claim_ids=claim_ids,
            rule_ids=rule_ids,
            actor_id=actor_id,
        )
        for path, payload in supersede_updates.items():
            writes[path] = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            if str(path) not in updated_files:
                updated_files.append(str(path))

        new_core_record = self._create_core_record(
            core_id=core_id,
            candidate=candidate,
            approval=approval,
            promotion_id=promotion_id,
            source_ids=source_ids,
            passage_ids=passage_ids,
            claim_ids=claim_ids,
            conflict_ids=conflict_ids,
            rule_ids=rule_ids,
            existing_core_matches=existing_core_matches,
            actor_id=actor_id,
            promotion_notes=promotion_notes,
        )
        current_core_docs = self._merge_core_docs(
            docs=current_core_docs,
            new_doc=self._core_doc_from_record(new_core_record, candidate, source_records_by_id),
            superseded_core_ids=previous_core_ids,
        )
        writes[self.core_docs_path] = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in current_core_docs)

        snapshot = self._write_transaction(writes)
        return PromotionMaterializationResult(
            source_ids=sorted(set(source_ids)),
            passage_ids=sorted(set(passage_ids)),
            claim_ids=claim_ids,
            conflict_ids=conflict_ids,
            approval_ids=approval_ids,
            rule_ids=rule_ids,
            core_records=[new_core_record],
            current_core_docs=current_core_docs,
            previous_core_ids=previous_core_ids,
            created_files=created_files,
            updated_files=updated_files,
            warnings=warnings,
            file_snapshot=snapshot,
        )

    def rollback(self, result: PromotionMaterializationResult | None) -> None:
        if result is None:
            return
        self._restore_transaction(result.file_snapshot)

    def _write_transaction(self, writes: dict[Path, str]) -> dict[str, str | None]:
        snapshot: dict[str, str | None] = {}
        applied: list[Path] = []
        try:
            for path, content in writes.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                key = str(path)
                if key not in snapshot:
                    snapshot[key] = path.read_text(encoding="utf-8") if path.exists() else None
                path.write_text(content, encoding="utf-8")
                applied.append(path)
            return snapshot
        except Exception:
            self._restore_transaction(snapshot)
            raise

    def _restore_transaction(self, snapshot: dict[str, str | None]) -> None:
        for raw_path, original in snapshot.items():
            path = Path(raw_path)
            if original is None:
                if path.exists():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(original, encoding="utf-8")

    def _load_models(self, directory: Path, model_cls) -> list[Any]:
        if not directory.exists():
            return []
        records: list[Any] = []
        for path in sorted(directory.glob("*.json")):
            try:
                records.append(model_cls.model_validate(_read_json(path)))
            except Exception:
                continue
        return records

    def _load_core_docs(self) -> list[dict[str, Any]]:
        if not self.core_docs_path.exists():
            return []
        docs: list[dict[str, Any]] = []
        for line in self.core_docs_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                docs.append(json.loads(line))
        return docs

    def _source_path(self, source_id: str) -> Path:
        return self.source_dir / f"{source_id}.json"

    def _passage_path(self, passage_id: str) -> Path:
        return self.passage_dir / f"{passage_id}.json"

    def _claim_path(self, claim_id: str) -> Path:
        return self.claim_dir / f"{claim_id}.json"

    def _conflict_path(self, conflict_id: str) -> Path:
        return self.conflict_dir / f"{conflict_id}.json"

    def _approval_path(self, approval_id: str) -> Path:
        return self.approval_dir / f"{approval_id}.json"

    def _rule_path(self, rule_id: str) -> Path:
        return self.rule_dir / f"{rule_id}.json"

    def _next_artifact_id(self, directory: Path, prefix: str) -> str:
        pattern = re.compile(rf"^{re.escape(prefix)}(\d{{6}})\.json$")
        highest = 0
        if directory.exists():
            for path in directory.glob("*.json"):
                match = pattern.match(path.name)
                if match:
                    highest = max(highest, int(match.group(1)))
        return f"{prefix}{highest + 1:06d}"

    def _normalized_source_title(self, value: str) -> str:
        return " ".join(str(value or "").strip().split())

    def _resolve_source_record(
        self,
        *,
        observation: SourceObservationRecord,
        candidate: ResearchCandidateRecord,
        actor_id: str,
        existing_records: list[AstrologySourceRecord],
        change_reason: str,
    ) -> tuple[AstrologySourceRecord, bool]:
        metadata = dict(observation.domain_metadata or {})
        requested_id = str(metadata.get("source_id") or "").strip() or None
        if requested_id:
            existing = next((item for item in existing_records if item.source_id == requested_id), None)
            if existing is not None:
                return existing, False
        existing = next(
            (
                item
                for item in existing_records
                if (item.digital_source and item.digital_source == observation.canonical_uri)
                or self._normalized_source_title(item.title_normalized) == self._normalized_source_title(
                    metadata.get("title_normalized") or observation.source_title
                )
            ),
            None,
        )
        if existing is not None:
            return existing, False

        authority_input = dict(metadata.get("authority_profile") or {})
        record = AstrologySourceRecord(
            source_id=requested_id or self._next_artifact_id(self.source_dir, "VEDA-SRC-"),
            title_original=str(metadata.get("title_original") or observation.source_title or "").strip() or None,
            title_normalized=self._normalized_source_title(metadata.get("title_normalized") or observation.source_title or candidate.title),
            source_class=_enum_or(SourceClass, metadata.get("source_class"), SourceClass.REFERENCE_EDITION),
            author_attributed=str(observation.author or metadata.get("author_attributed") or "").strip() or None,
            author_normalized=str(metadata.get("author_normalized") or observation.author or "").strip() or None,
            historical_period=str(metadata.get("historical_period") or "").strip() or None,
            language_original=str(metadata.get("language_original") or metadata.get("language") or "").strip() or None,
            edition=str(metadata.get("edition") or "").strip() or None,
            publisher=str(observation.publisher or metadata.get("publisher") or "").strip() or None,
            publication_year=_safe_int(metadata.get("publication_year")) or None,
            translator=str(metadata.get("translator") or "").strip() or None,
            commentator=str(metadata.get("commentator") or "").strip() or None,
            isbn_or_identifier=str(metadata.get("isbn_or_identifier") or metadata.get("identifier") or "").strip() or None,
            digital_source=observation.canonical_uri,
            legal_access_status=_enum_or(LegalAccessStatus, metadata.get("legal_access_status"), LegalAccessStatus.LIMITED_QUOTATION_ONLY),
            primary_or_secondary=_enum_or(PrimarySecondaryStatus, metadata.get("primary_or_secondary"), PrimarySecondaryStatus.UNKNOWN),
            tradition=str(metadata.get("tradition") or "").strip() or None,
            school=str(metadata.get("school") or "").strip() or None,
            domains=sorted(
                {
                    str(metadata.get("domain") or candidate.metadata.get("domain") or "ASTROLOGY").upper(),
                    *[str(item).upper() for item in metadata.get("domains", []) if str(item).strip()],
                }
            ),
            quality_grade=_enum_or(QualityGrade, metadata.get("quality_grade"), QualityGrade.C),
            authority_score=max(
                0,
                min(
                    100,
                    _safe_int(
                        metadata.get("authority_score"),
                        int(round(_safe_float(candidate.confidence.authority_confidence, 0.5) * 100)),
                    ),
                ),
            ),
            authority_profile=AuthorityProfile(
                authority_tier=_enum_or(AuthorityTier, authority_input.get("authority_tier"), AuthorityTier.TIER_C),
                textual_authority=max(0, min(5, _safe_int(authority_input.get("textual_authority"), 3))),
                traditional_authority=max(0, min(5, _safe_int(authority_input.get("traditional_authority"), 3))),
                translation_reliability=max(0, min(5, _safe_int(authority_input.get("translation_reliability"), 3))),
                cross_source_support=max(0, min(5, _safe_int(authority_input.get("cross_source_support"), 2))),
                empirical_support=max(0, min(5, _safe_int(authority_input.get("empirical_support"), 0))),
                implementation_confidence=max(0, min(5, _safe_int(authority_input.get("implementation_confidence"), 3))),
                notes=str(authority_input.get("notes") or "Promoted from governed research evidence.").strip() or None,
            ),
            verification_status=_enum_or(VerificationStatus, metadata.get("verification_status"), VerificationStatus.METADATA_VERIFIED),
            evidence_type=_enum_or(
                EvidenceType,
                metadata.get("evidence_type") or metadata.get("evidence_class"),
                EvidenceType.CLASSICAL_TEXTUAL,
            ),
            **_artifact_meta(actor_id, change_reason, notes=str(metadata.get("notes") or "").strip() or None, status=ArtifactStatus.APPROVED.value),
        )
        return record, True

    def _resolve_passage_record(
        self,
        *,
        evidence: ResearchEvidenceRecord,
        observation: SourceObservationRecord,
        candidate: ResearchCandidateRecord,
        source_id: str,
        actor_id: str,
        existing_records: list[PassageRecord],
        change_reason: str,
    ) -> tuple[PassageRecord, bool]:
        metadata = dict(evidence.domain_metadata or {})
        requested_id = str(metadata.get("passage_id") or "").strip() or None
        if requested_id:
            existing = next((item for item in existing_records if item.passage_id == requested_id), None)
            if existing is not None:
                return existing, False

        translation = str(metadata.get("translation") or evidence.passage or evidence.claim_hint or "").strip()
        citation_label = str(metadata.get("citation_label") or f"{observation.source_title} [{observation.observation_id}]").strip()
        existing = next(
            (
                item
                for item in existing_records
                if item.source_id == source_id
                and item.citation_label == citation_label
                and (item.translation or "") == translation
            ),
            None,
        )
        if existing is not None:
            return existing, False

        record = PassageRecord(
            passage_id=requested_id or self._next_artifact_id(self.passage_dir, "VEDA-PSG-"),
            source_id=source_id,
            work=str(metadata.get("work") or observation.source_title or candidate.title).strip(),
            chapter=str(metadata.get("chapter") or "").strip() or None,
            section=str(metadata.get("section") or "").strip() or None,
            verse_start=str(metadata.get("verse_start") or "").strip() or None,
            verse_end=str(metadata.get("verse_end") or "").strip() or None,
            page_start=_safe_int(metadata.get("page_start")) or None,
            page_end=_safe_int(metadata.get("page_end")) or None,
            original_language=str(metadata.get("original_language") or metadata.get("language") or "").strip() or None,
            original_text=str(metadata.get("original_text") or observation.raw_reference.get("original_text") or "").strip() or None,
            transliteration=str(metadata.get("transliteration") or "").strip() or None,
            translation=translation or None,
            translator=str(metadata.get("translator") or "").strip() or None,
            commentator=str(metadata.get("commentator") or "").strip() or None,
            context_before=str(metadata.get("context_before") or "").strip() or None,
            context_after=str(metadata.get("context_after") or "").strip() or None,
            topics=[str(item).upper() for item in (metadata.get("topics") or [candidate.topic_key]) if str(item).strip()],
            domains=[str(item).upper() for item in (metadata.get("domains") or [candidate.metadata.get("domain") or "ASTROLOGY"]) if str(item).strip()],
            verification_status=_enum_or(VerificationStatus, metadata.get("verification_status"), VerificationStatus.PASSAGE_VERIFIED),
            citation_label=citation_label,
            **_artifact_meta(actor_id, change_reason, notes=str(metadata.get("notes") or "").strip() or None, status=ArtifactStatus.APPROVED.value),
        )
        return record, True

    def _candidate_evidence_types(self, candidate: ResearchCandidateRecord) -> list[EvidenceType]:
        raw_values = list(candidate.metadata.get("evidence_types") or [])
        if not raw_values:
            raw_values = [candidate.metadata.get("evidence_class") or EvidenceType.CLASSICAL_TEXTUAL.value]
        values: list[EvidenceType] = []
        for raw in raw_values:
            value = _enum_or(EvidenceType, raw, None)
            if value and value not in values:
                values.append(value)
        return values or [EvidenceType.CLASSICAL_TEXTUAL]

    def _create_claim_record(
        self,
        *,
        candidate: ResearchCandidateRecord,
        passage_ids: list[str],
        actor_id: str,
        change_reason: str,
        notes: str | None,
    ) -> ClaimRecord:
        support_level = SupportLevel.CROSS_VERIFIED if len(set(passage_ids)) >= 2 else SupportLevel.SINGLE_SOURCE
        if candidate.contradiction_status.value != "NONE":
            support_level = SupportLevel.CONFLICTED
        approval_status = (
            GovernanceApprovalStatus.APPROVED_WITH_CONDITIONS
            if candidate.approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS
            else GovernanceApprovalStatus.APPROVED
        )
        research_status = (
            WorkflowState.APPROVED_WITH_CONDITIONS
            if approval_status == GovernanceApprovalStatus.APPROVED_WITH_CONDITIONS
            else WorkflowState.APPROVED
        )
        high_stakes = candidate.safety_class.value in {"HIGH", "HIGH_STAKES", "CRITICAL"}
        record = ClaimRecord(
            claim_id=self._next_artifact_id(self.claim_dir, "VEDA-CLM-"),
            claim_text=candidate.claim,
            domain=str(candidate.metadata.get("domain") or "ASTROLOGY").upper(),
            subdomain=str(candidate.metadata.get("subdomain") or "").strip().upper() or None,
            source_passages=passage_ids,
            interpretation_type=_enum_or(
                InterpretationType,
                candidate.metadata.get("interpretation_type"),
                InterpretationType.DERIVED_RULE,
            ),
            support_level=support_level,
            evidence_types=self._candidate_evidence_types(candidate),
            conflicting_claims=[],
            research_status=research_status,
            approval_status=approval_status,
            high_stakes=high_stakes,
            requires_safety_review=high_stakes,
            allowed_output_mode=AllowedOutputMode.TRADITIONAL_INTERPRETATION_ONLY if high_stakes else AllowedOutputMode.STANDARD,
            **_artifact_meta(actor_id, change_reason, notes=notes, status=ArtifactStatus.APPROVED.value),
        )
        return record

    def _create_conflict_record(
        self,
        *,
        candidate: ResearchCandidateRecord,
        research_conflict: ResearchConflictRecord,
        new_claim_id: str,
        existing_claim_id: str,
        source_ids: list[str],
        actor_id: str,
        change_reason: str,
    ) -> ConflictRecord:
        return ConflictRecord(
            conflict_id=self._next_artifact_id(self.conflict_dir, "VEDA-CNF-"),
            topic=research_conflict.topic,
            claim_a=new_claim_id,
            claim_b=existing_claim_id,
            source_a=source_ids[0] if source_ids else None,
            source_b=None,
            conflict_type=_enum_or(ConflictType, research_conflict.conflict_type.value, ConflictType.UNRESOLVED),
            analysis=research_conflict.analysis,
            possible_reconciliation=research_conflict.possible_reconciliation,
            school_context=research_conflict.school_context,
            implementation_impact=research_conflict.implementation_impact,
            resolution_status=ConflictResolutionStatus.UNRESOLVED,
            approved_resolution=None,
            confidence=max(0, min(5, round(research_conflict.confidence * 5))),
            **_artifact_meta(
                actor_id,
                change_reason,
                notes=f"Derived from research conflict {research_conflict.conflict_id}.",
                status=ArtifactStatus.APPROVED.value,
            ),
        )

    def _create_approval_record(
        self,
        *,
        candidate: ResearchCandidateRecord,
        approval: ResearchApprovalRecord,
        source_ids: list[str],
        passage_ids: list[str],
        claim_ids: list[str],
        conflict_ids: list[str],
        actor_id: str,
        change_reason: str,
    ) -> ApprovalRecord:
        decision = (
            GovernanceApprovalStatus.APPROVED_WITH_CONDITIONS
            if approval.status == ApprovalStatus.APPROVED_WITH_CONDITIONS
            else GovernanceApprovalStatus.APPROVED
        )
        workflow_state = (
            WorkflowState.APPROVED_WITH_CONDITIONS
            if decision == GovernanceApprovalStatus.APPROVED_WITH_CONDITIONS
            else WorkflowState.APPROVED
        )
        return ApprovalRecord(
            approval_id=self._next_artifact_id(self.approval_dir, "VEDA-APR-"),
            artifact_type=ArtifactType.CLAIM_SET,
            artifact_ids=[*source_ids, *passage_ids, *claim_ids, *conflict_ids],
            pilot_domain=str(candidate.metadata.get("subdomain") or candidate.metadata.get("domain") or "").strip().upper() or None,
            workflow_state=workflow_state,
            approval_status=decision,
            role_decisions=[
                RoleDecision(
                    role=ApprovalRole.DOMAIN_APPROVER,
                    actor=actor_id,
                    decision=decision,
                    decided_at=_utc_now(),
                    note=approval.reason,
                )
            ],
            conditions=list(approval.conditions),
            implementation_ready=True,
            validated_against_runtime=False,
            **_artifact_meta(actor_id, change_reason, notes=approval.reason, status=ArtifactStatus.APPROVED.value),
        )

    def _create_rule_record(
        self,
        *,
        candidate: ResearchCandidateRecord,
        source_ids: list[str],
        passage_ids: list[str],
        claim_ids: list[str],
        conflict_ids: list[str],
        actor_id: str,
        change_reason: str,
        notes: str | None,
    ) -> AstrologyRuleRecord | None:
        if candidate.candidate_type.value in {"KNOWLEDGE_GAP", "ONTOLOGY_EXTENSION"}:
            return None

        domain = str(candidate.metadata.get("domain") or "ASTROLOGY").upper()
        subdomain = str(candidate.metadata.get("subdomain") or "").strip().upper() or None
        if "DASHA" in domain or "DASHA" in (subdomain or ""):
            rule_type = RuleType.DASHA
        elif "DIGNITY" in domain or "DIGNITY" in (subdomain or ""):
            rule_type = RuleType.DIGNITY
        elif "YOGA" in domain or "YOGA" in (subdomain or ""):
            rule_type = RuleType.YOGA
        elif "DOSHA" in domain or "DOSHA" in (subdomain or ""):
            rule_type = RuleType.DOSHA
        elif "FINANCE" in domain:
            rule_type = RuleType.ASTROFINANCE_HYPOTHESIS
        else:
            rule_type = RuleType.INTERPRETATION

        high_stakes = candidate.safety_class.value in {"HIGH", "HIGH_STAKES", "CRITICAL"}
        rule_status = (
            RuleLifecycleStatus.APPROVED_WITH_CONDITIONS
            if candidate.approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS
            else RuleLifecycleStatus.IMPLEMENTATION_READY
        )
        approval_status = (
            OntologyApprovalStatus.APPROVED_WITH_CONDITIONS
            if candidate.approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS
            else OntologyApprovalStatus.IMPLEMENTATION_READY
        )
        return AstrologyRuleRecord(
            rule_id=self._next_artifact_id(self.rule_dir, f"VEDA-RUL-{_title_token(subdomain or domain, fallback='GENERIC')}-"),
            title=candidate.title,
            domain=domain,
            subdomain=subdomain,
            rule_type=rule_type,
            status=rule_status,
            source_class=_enum_or(SourceClass, candidate.metadata.get("source_class"), SourceClass.REFERENCE_EDITION),
            approval_status=approval_status,
            evidence_types=self._candidate_evidence_types(candidate),
            high_stakes=high_stakes,
            requires_safety_review=high_stakes,
            allowed_output_mode=OntologyOutputMode.TRADITIONAL_INTERPRETATION_ONLY if high_stakes else OntologyOutputMode.STANDARD,
            authority=RuleAuthorityProfile(
                textual=max(0, min(5, round(candidate.confidence.source_confidence * 5))),
                traditional=max(0, min(5, round(candidate.confidence.authority_confidence * 5))),
                cross_source=max(0, min(5, round(candidate.confidence.cross_source_confidence * 5))),
                empirical=max(0, min(5, round(_safe_float(candidate.metadata.get("empirical_confidence"), 0.0) * 5))),
                implementation=max(0, min(5, round(candidate.confidence.domain_confidence * 5))),
                notes="Promoted by P010 from human-approved research candidate.",
            ),
            provenance=RuleProvenance(
                source_ids=source_ids,
                passage_ids=passage_ids,
                claim_ids=claim_ids,
                conflict_ids=conflict_ids,
                legacy_provenance_status=None,
            ),
            conditions=RuleConditionSet(
                all=[
                    ConditionNode(
                        condition_id=f"COND-{candidate.candidate_id}",
                        subject=OperandReference(
                            ref="chart.metadata.promotion_candidate_id",
                            ref_type=OperandKind.FACT_PATH,
                        ),
                        operator=ConditionOperator.EQUALS,
                        value=candidate.candidate_id,
                        notes="P010 promotion placeholder condition. Governed rule stored for future activation only.",
                    )
                ],
                any=[],
                none=[],
            ),
            modifiers=[],
            exceptions=[],
            confirmations=[],
            activations=[],
            outcomes=[
                RuleOutcome(
                    outcome_id=f"OUT-{_title_token(domain, fallback='GENERIC')}-{len(claim_ids):06d}",
                    outcome_type=OutcomeType.EXPLANATION,
                    description=candidate.claim,
                )
            ],
            depends_on_rule_ids=[],
            cancelled_by_rule_ids=[],
            **_artifact_meta(actor_id, change_reason, notes=notes),
        )

    def _create_core_record(
        self,
        *,
        core_id: str,
        candidate: ResearchCandidateRecord,
        approval: ResearchApprovalRecord,
        promotion_id: str,
        source_ids: list[str],
        passage_ids: list[str],
        claim_ids: list[str],
        conflict_ids: list[str],
        rule_ids: list[str],
        existing_core_matches: list[ResearchCoreKnowledgeRecord],
        actor_id: str,
        promotion_notes: str | None,
    ) -> ResearchCoreKnowledgeRecord:
        previous = existing_core_matches[0] if existing_core_matches else None
        return ResearchCoreKnowledgeRecord(
            core_id=core_id,
            domain_id=candidate.domain_id,
            title=candidate.title,
            claim=candidate.claim,
            normalized_claim=candidate.normalized_claim,
            topic_key=candidate.topic_key,
            stance=candidate.stance,
            source_ids=sorted(set(source_ids)),
            passage_ids=sorted(set(passage_ids)),
            claim_ids=sorted(set(claim_ids)),
            conflict_ids=sorted(set(conflict_ids)),
            rule_ids=sorted(set(rule_ids)),
            approval_status=approval.status,
            confidence=candidate.confidence,
            candidate_id=candidate.candidate_id,
            approval_id=approval.approval_id,
            promotion_id=promotion_id,
            version=_increment_semver(previous.version if previous else None),
            version_state=CoreVersionState.CURRENT,
            supersedes_core_id=previous.core_id if previous else None,
            retrieval_classification="APPROVED_CORE",
            high_stakes=candidate.safety_class.value in {"HIGH", "HIGH_STAKES", "CRITICAL"},
            created_by=actor_id,
            updated_by=actor_id,
            change_reason=promotion_notes or f"P010 promotion from candidate {candidate.candidate_id}.",
            lineage={
                "candidate_id": candidate.candidate_id,
                "approval_id": approval.approval_id,
                "promotion_id": promotion_id,
                "mission_id": candidate.mission_id,
                "run_id": candidate.run_id,
                "evidence_ids": list(candidate.evidence_ids),
                "source_observation_ids": list(candidate.source_ids),
                "predecessor_core_ids": [item.core_id for item in existing_core_matches],
            },
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    def _core_doc_from_record(
        self,
        core_record: ResearchCoreKnowledgeRecord,
        candidate: ResearchCandidateRecord,
        source_records: dict[str, AstrologySourceRecord],
    ) -> dict[str, Any]:
        research_sources = []
        for source_id in core_record.source_ids:
            source = source_records.get(source_id)
            if source is None:
                continue
            research_sources.append(
                {
                    "title": source.title_normalized,
                    "url": source.digital_source,
                    "published_at": str(source.publication_year) if source.publication_year else None,
                    "excerpt": source.notes,
                    "source_class": source.source_class.value,
                    "verification_status": source.verification_status.value,
                }
            )
        latest_source_date = max((item["published_at"] for item in research_sources if item.get("published_at")), default=None)
        return {
            "doc_id": f"veda_core_{core_record.core_id.lower().replace('-', '_')}",
            "domain": str(candidate.metadata.get("knowledge_domain") or candidate.metadata.get("domain") or "ASTRO"),
            "entity": core_record.title,
            "text": core_record.claim,
            "meta": {
                "memory_type": "approved_core",
                "governance_zone": "APPROVED_CORE",
                "saved_at": core_record.updated_at,
                "promoted_at": core_record.updated_at,
                "summary": core_record.claim,
                "intent": str(candidate.metadata.get("domain") or "ASTRO"),
                "topic_key": core_record.topic_key,
                "core_id": core_record.core_id,
                "candidate_id": core_record.candidate_id,
                "approval_id": core_record.approval_id,
                "promotion_id": core_record.promotion_id,
                "source_ids": core_record.source_ids,
                "passage_ids": core_record.passage_ids,
                "claim_ids": core_record.claim_ids,
                "rule_ids": core_record.rule_ids,
                "conflict_ids": core_record.conflict_ids,
                "research_sources": research_sources,
                "latest_source_date": latest_source_date,
                "version": core_record.version,
                "version_state": core_record.version_state.value,
                "high_stakes": core_record.high_stakes,
                "tags": [str(candidate.metadata.get("domain") or "astro").lower(), "approved_core"],
            },
        }

    def _merge_core_docs(
        self,
        *,
        docs: list[dict[str, Any]],
        new_doc: dict[str, Any],
        superseded_core_ids: list[str],
    ) -> list[dict[str, Any]]:
        survivors = []
        superseded = set(superseded_core_ids)
        for doc in docs:
            meta = doc.get("meta", {}) if isinstance(doc.get("meta"), dict) else {}
            core_id = str(meta.get("core_id") or "").strip()
            if core_id and core_id in superseded:
                continue
            if doc.get("doc_id") == new_doc.get("doc_id"):
                continue
            survivors.append(doc)
        survivors.append(new_doc)
        survivors.sort(key=lambda item: str((item.get("meta") or {}).get("saved_at") or ""))
        return survivors

    def _supersede_previous_core_artifacts(
        self,
        *,
        existing_core_matches: list[ResearchCoreKnowledgeRecord],
        claim_ids: list[str],
        rule_ids: list[str],
        actor_id: str,
    ) -> dict[Path, dict[str, Any]]:
        payloads: dict[Path, dict[str, Any]] = {}
        new_claim_id = claim_ids[0] if claim_ids else None
        new_rule_id = rule_ids[0] if rule_ids else None
        for core in existing_core_matches:
            for claim_id in core.claim_ids:
                path = self._claim_path(claim_id)
                if not path.exists():
                    continue
                payload = _read_json(path)
                payload["status"] = ArtifactStatus.SUPERSEDED.value
                payload["superseded_by"] = new_claim_id
                payload["updated_at"] = _utc_now()
                payload["updated_by"] = actor_id
                payload["change_reason"] = "Superseded by P010 promoted core update."
                payloads[path] = payload
            for rule_id in core.rule_ids:
                path = self._rule_path(rule_id)
                if not path.exists():
                    continue
                payload = _read_json(path)
                payload["status"] = RuleLifecycleStatus.SUPERSEDED.value
                payload["superseded_by"] = new_rule_id
                payload["updated_at"] = _utc_now()
                payload["updated_by"] = actor_id
                payload["change_reason"] = "Superseded by P010 promoted core update."
                payloads[path] = payload
        return payloads

    def _update_legacy_mappings(
        self,
        *,
        candidate: ResearchCandidateRecord,
        rule_ids: list[str],
        actor_id: str,
    ) -> dict[Path, dict[str, Any]]:
        payloads: dict[Path, dict[str, Any]] = {}
        legacy_rule_id = str(candidate.metadata.get("legacy_rule_id") or "").strip()
        if not legacy_rule_id or not self.legacy_dir.exists() or not rule_ids:
            return payloads
        for path in sorted(self.legacy_dir.glob("*.json")):
            raw = _read_json(path)
            try:
                record = LegacyKnowledgeMappingRecord.model_validate(raw)
            except Exception:
                continue
            haystack = " ".join(
                [
                    record.legacy_behavior,
                    record.legacy_function,
                    record.legacy_location,
                    record.notes or "",
                ]
            )
            if legacy_rule_id not in haystack:
                continue
            updated = record.model_copy(
                update={
                    "target_rule_ids": sorted(set([*record.target_rule_ids, *rule_ids])),
                    "mapping_status": LegacyMappingStatus.MAPPED_TO_SCHEMA,
                    "source_status": LegacyMappingStatus.SOURCE_VALIDATED,
                    "semantic_match": SemanticMatch.EXACT if record.semantic_match == SemanticMatch.EXACT else SemanticMatch.PARTIAL,
                    "updated_at": _utc_now(),
                    "updated_by": actor_id,
                    "change_reason": "Updated by P010 promotion pipeline.",
                }
            )
            payloads[path] = updated.model_dump(mode="json")
        return payloads
