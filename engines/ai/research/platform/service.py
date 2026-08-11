from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engines.ai.research.platform.contracts import (
    AdminAction,
    ActorType,
    ApprovalStatus,
    CadenceType,
    CandidateReviewRecord,
    CandidateType,
    ConfidenceDimensions,
    ConflictResolutionStatus,
    ContradictionStatus,
    KnowledgeZone,
    LedgerEventType,
    MisfirePolicy,
    MissionPriority,
    MissionStatus,
    NoveltyStatus,
    OverlapPolicy,
    PlatformHealth,
    PromotionState,
    ResearchApprovalRecord,
    ResearchBudget,
    ResearchCandidateRecord,
    ResearchConflictRecord,
    ResearchDashboardRecord,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchLedgerEventRecord,
    ResearchMissionRecord,
    ResearchRunRecord,
    ResearchScheduleRecord,
    ResearchValidationRecord,
    RunStatus,
    SafetyClass,
    SourceAccessStatus,
    SourceObservationRecord,
    TriggerType,
    ValidationStage,
    ValidationStatus,
)
from engines.ai.research.platform.providers import BasePlatformResearchProvider, SyntheticFixtureProvider
from engines.ai.research.platform.security import content_hash, detect_prompt_injection, is_safe_uri, normalize_uri, sanitize_external_text
from engines.ai.research.platform.store import ResearchPlatformStore
from engines.ai.research.platform.synthetic import SyntheticResearchDomainPlugin
from engines.ai.research.domains.vedic_astrology import VedicAstrologyCorpusProvider, VedicAstrologyResearchDomain
from engines.common import config as cfg


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def blank_confidence() -> ConfidenceDimensions:
    return ConfidenceDimensions(
        source_confidence=0.0,
        authority_confidence=0.0,
        cross_source_confidence=0.0,
        provenance_confidence=0.0,
        novelty_confidence=0.0,
        contradiction_confidence=0.0,
        domain_confidence=0.0,
    )


class ResearchPlatformService:
    def __init__(
        self,
        *,
        db_path: Path | None = None,
        fixture_path: Path | None = None,
        providers: dict[str, BasePlatformResearchProvider] | None = None,
        domain_plugins: dict[str, Any] | None = None,
    ):
        self.store = ResearchPlatformStore(db_path=db_path)
        self.fixture_path = Path(fixture_path or (cfg.VEDA_RESEARCH_PLATFORM_FIXTURE_DIR / "synthetic_research_fixture.json"))
        self.synthetic_plugin = SyntheticResearchDomainPlugin(self.fixture_path)
        self.vedic_astrology_plugin = VedicAstrologyResearchDomain()
        default_provider = SyntheticFixtureProvider(self.fixture_path)
        astrology_provider = VedicAstrologyCorpusProvider(self.vedic_astrology_plugin)
        self.providers: dict[str, BasePlatformResearchProvider] = {
            default_provider.descriptor().provider_id: default_provider,
            astrology_provider.descriptor().provider_id: astrology_provider,
        }
        if providers:
            self.providers.update(providers)
        self.domain_plugins = {
            self.synthetic_plugin.domain_id: self.synthetic_plugin,
            self.vedic_astrology_plugin.domain_id: self.vedic_astrology_plugin,
        }
        if domain_plugins:
            self.domain_plugins.update(domain_plugins)
        self.store.recover_stale_runs()
        self._bootstrap_defaults()

    def _bootstrap_defaults(self) -> None:
        for plugin in self.domain_plugins.values():
            self.store.upsert_domain(plugin.domain_record())
            for record in plugin.seed_core_knowledge():
                self.store.upsert_core_knowledge(record)

    def list_domains(self) -> list[ResearchDomainRecord]:
        return self.store.list_domains()

    def health(self) -> dict[str, Any]:
        failed_runs = sum(1 for run in self.store.list_runs() if run.status == RunStatus.FAILED)
        providers = {name: provider.health_check() for name, provider in self.providers.items()}
        if failed_runs:
            status = PlatformHealth.DEGRADED
        elif not all(item.get("status") in {"ACTIVE", "HEALTHY"} for item in providers.values()):
            status = PlatformHealth.DEGRADED
        else:
            status = PlatformHealth.HEALTHY
        return {
            "status": status.value,
            "providers": providers,
            "failed_runs": failed_runs,
            "db_path": str(self.store.db_path),
        }

    def dashboard(self) -> ResearchDashboardRecord:
        runs = self.store.list_runs()
        now = utc_now()[:10]
        metrics = self.store.dashboard_metrics()
        last_by_cadence = {"HOURLY": None, "DAILY": None, "WEEKLY": None}
        for schedule in self.store.list_schedules():
            value = schedule.last_run_at
            if schedule.cadence_type.value in last_by_cadence and value:
                last_by_cadence[schedule.cadence_type.value] = value
        return ResearchDashboardRecord(
            research_status=PlatformHealth(self.health()["status"]),
            active_missions=metrics["missions_active"],
            runs_today=sum(1 for run in runs if run.started_at.startswith(now)),
            sources_today=sum(1 for obs in self.store.list_observations() if obs.retrieved_at.startswith(now)),
            new_candidates=sum(1 for candidate in self.store.list_candidates() if candidate.created_at.startswith(now)),
            pending_approvals=metrics["pending_reviews"],
            high_priority_conflicts=sum(
                1 for candidate in self.store.list_candidates()
                if candidate.priority == MissionPriority.P0 and candidate.contradiction_status != ContradictionStatus.NONE
            ),
            failed_runs=metrics["runs_failed"],
            last_hourly=last_by_cadence["HOURLY"],
            last_daily=last_by_cadence["DAILY"],
            last_weekly=last_by_cadence["WEEKLY"],
            metrics=metrics,
        )

    def create_mission(self, payload: dict[str, Any]) -> ResearchMissionRecord:
        now = utc_now()
        budget = ResearchBudget.model_validate(payload.get("research_budget", {}))
        record = ResearchMissionRecord(
            mission_id=self.store.next_id("mission", "VEDA-RM-"),
            domain_id=payload["domain_id"],
            title=payload["title"],
            objective=payload["objective"],
            research_type=payload["research_type"],
            priority=payload.get("priority", MissionPriority.P2),
            status=payload.get("status", MissionStatus.QUEUED),
            created_by=payload.get("created_by", "admin"),
            created_at=now,
            updated_at=now,
            schedule_id=payload.get("schedule_id"),
            query_strategy=dict(payload.get("query_strategy", {})),
            required_source_classes=list(payload.get("required_source_classes", [])),
            minimum_independent_sources=int(payload.get("minimum_independent_sources", 1)),
            known_claim_ids=list(payload.get("known_claim_ids", [])),
            known_conflict_ids=list(payload.get("known_conflict_ids", [])),
            known_gap_ids=list(payload.get("known_gap_ids", [])),
            safety_class=payload.get("safety_class", SafetyClass.LOW),
            completion_policy=dict(payload.get("completion_policy", {})),
            research_budget=budget,
            notes=payload.get("notes"),
            follow_up_depth=int(payload.get("follow_up_depth", 0)),
            parent_candidate_id=payload.get("parent_candidate_id"),
            parent_mission_id=payload.get("parent_mission_id"),
            last_run_at=payload.get("last_run_at"),
        )
        self.store.create_mission(record)
        self._append_ledger(
            event_type=LedgerEventType.MISSION_CREATED,
            actor_type=ActorType.ADMIN,
            actor_id=record.created_by,
            action="create_mission",
            domain_id=record.domain_id,
            mission_id=record.mission_id,
            after_state=record.model_dump(mode="json"),
            reason=record.objective,
        )
        return record

    def pause_mission(self, mission_id: str, *, actor_id: str = "admin") -> ResearchMissionRecord:
        mission = self._require_mission(mission_id)
        updated = mission.model_copy(update={"status": MissionStatus.PAUSED, "updated_at": utc_now()})
        self.store.update_mission(updated)
        self._append_ledger(
            event_type=LedgerEventType.MISSION_PAUSED,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="pause_mission",
            domain_id=updated.domain_id,
            mission_id=updated.mission_id,
            before_state=mission.model_dump(mode="json"),
            after_state=updated.model_dump(mode="json"),
        )
        return updated

    def resume_mission(self, mission_id: str, *, actor_id: str = "admin") -> ResearchMissionRecord:
        mission = self._require_mission(mission_id)
        updated = mission.model_copy(update={"status": MissionStatus.ACTIVE, "updated_at": utc_now()})
        self.store.update_mission(updated)
        self._append_ledger(
            event_type=LedgerEventType.MISSION_STARTED,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="resume_mission",
            domain_id=updated.domain_id,
            mission_id=updated.mission_id,
            before_state=mission.model_dump(mode="json"),
            after_state=updated.model_dump(mode="json"),
        )
        return updated

    def list_missions(self) -> list[ResearchMissionRecord]:
        return self.store.list_missions()

    def get_mission(self, mission_id: str) -> ResearchMissionRecord | None:
        return self.store.get_mission(mission_id)

    def create_schedule(self, payload: dict[str, Any]) -> ResearchScheduleRecord:
        now = utc_now()
        record = ResearchScheduleRecord(
            schedule_id=self.store.next_id("schedule", "VEDA-RSCH-"),
            domain_id=payload["domain_id"],
            mission_id=payload["mission_id"],
            cadence_type=payload.get("cadence_type", "MANUAL_ONLY"),
            timezone=payload.get("timezone", "Asia/Calcutta"),
            enabled=bool(payload.get("enabled", True)),
            next_run_at=payload.get("next_run_at"),
            last_run_at=payload.get("last_run_at"),
            misfire_policy=payload.get("misfire_policy", "RUN_ONCE"),
            overlap_policy=payload.get("overlap_policy", "SKIP"),
            priority=payload.get("priority", MissionPriority.P2),
            created_at=now,
            updated_at=now,
        )
        self.store.upsert_schedule(record)
        return record

    def update_schedule(self, schedule_id: str, updates: dict[str, Any]) -> ResearchScheduleRecord:
        schedule = self.store.get_schedule(schedule_id)
        if schedule is None:
            raise KeyError(f"Unknown schedule: {schedule_id}")
        updated = ResearchScheduleRecord.model_validate(
            {
                **schedule.model_dump(mode="json"),
                "enabled": bool(updates.get("enabled", schedule.enabled)),
                "cadence_type": CadenceType(updates.get("cadence_type", schedule.cadence_type)),
                "next_run_at": updates.get("next_run_at", schedule.next_run_at),
                "last_run_at": updates.get("last_run_at", schedule.last_run_at),
                "misfire_policy": MisfirePolicy(updates.get("misfire_policy", schedule.misfire_policy)),
                "overlap_policy": OverlapPolicy(updates.get("overlap_policy", schedule.overlap_policy)),
                "priority": MissionPriority(updates.get("priority", schedule.priority)),
                "updated_at": utc_now(),
            }
        )
        self.store.upsert_schedule(updated)
        return updated

    def list_schedules(self) -> list[ResearchScheduleRecord]:
        return self.store.list_schedules()

    def trigger_manual_run(self, mission_id: str, *, actor_id: str = "admin", trigger_type: TriggerType = TriggerType.MANUAL) -> ResearchRunRecord:
        mission = self._require_mission(mission_id)
        if mission.status in {MissionStatus.CANCELLED, MissionStatus.ARCHIVED, MissionStatus.PAUSED}:
            raise RuntimeError(f"Mission {mission_id} is not runnable from state {mission.status.value}")
        domain = self._require_domain(mission.domain_id)
        provider = self._resolve_provider(mission, domain)
        prior_runs = self.store.list_runs_for_mission(mission_id)
        now = utc_now()

        run = ResearchRunRecord(
            run_id=self.store.next_id("run", "VEDA-RUN-"),
            mission_id=mission.mission_id,
            domain_id=mission.domain_id,
            trigger_type=trigger_type,
            started_at=now,
            status=RunStatus.RUNNING,
        )
        self.store.insert_run(run)
        self._append_ledger(
            event_type=LedgerEventType.RUN_STARTED,
            actor_type=ActorType.ADMIN if trigger_type == TriggerType.MANUAL else ActorType.SYSTEM,
            actor_id=actor_id,
            action="start_run",
            domain_id=run.domain_id,
            mission_id=run.mission_id,
            run_id=run.run_id,
            after_state=run.model_dump(mode="json"),
        )

        try:
            batch = provider.search(mission, prior_run_count=len(prior_runs))
            run.provider_calls += 1
            run.queries_executed += 1
            self._append_ledger(
                event_type=LedgerEventType.QUERY_EXECUTED,
                actor_type=ActorType.PROVIDER,
                actor_id=provider.descriptor().provider_id,
                action="provider_search",
                domain_id=run.domain_id,
                mission_id=run.mission_id,
                run_id=run.run_id,
                metadata={
                    "query": batch.query,
                    "continuation_hint": batch.continuation_hint,
                    **dict(batch.search_metadata),
                },
            )
            for document in batch.documents[: mission.research_budget.max_sources]:
                self._process_document(provider, mission, run, document)
            run.continuation_required = bool(batch.continuation_hint)
            run.continuation_hint = batch.continuation_hint
            run.status = RunStatus.PARTIAL if run.errors else RunStatus.SUCCESS
        except Exception as exc:
            run.errors.append(str(exc))
            run.status = RunStatus.FAILED
            self._append_ledger(
                event_type=LedgerEventType.RUN_FAILED,
                actor_type=ActorType.SYSTEM,
                actor_id="system",
                action="run_failed",
                domain_id=run.domain_id,
                mission_id=run.mission_id,
                run_id=run.run_id,
                reason=str(exc),
            )
        finally:
            finished_at = utc_now()
            run = run.model_copy(update={"completed_at": finished_at})
            self.store.update_run(run)
            mission_update = mission.model_copy(
                update={
                    "status": MissionStatus.ACTIVE if mission.status != MissionStatus.PAUSED else mission.status,
                    "updated_at": finished_at,
                    "last_run_at": finished_at,
                }
            )
            self.store.update_mission(mission_update)
            if mission.schedule_id:
                schedule = self.store.get_schedule(mission.schedule_id)
                if schedule:
                    self.store.upsert_schedule(
                        schedule.model_copy(update={"last_run_at": finished_at, "updated_at": finished_at})
                    )
        return run

    def _process_document(
        self,
        provider: BasePlatformResearchProvider,
        mission: ResearchMissionRecord,
        run: ResearchRunRecord,
        document,
    ) -> None:
        descriptor = provider.descriptor()
        retrieved_at = utc_now()
        raw_content = provider.retrieve(document)
        prompt_injection = detect_prompt_injection(raw_content)
        canonical_uri = normalize_uri(document.source_uri)
        safe, unsafe_reason = is_safe_uri(document.source_uri, allowed_schemes=set(descriptor.allowed_uri_schemes))
        observation = SourceObservationRecord(
            observation_id=self.store.next_id("observation", "VEDA-OBS-"),
            run_id=run.run_id,
            provider_id=descriptor.provider_id,
            source_uri=document.source_uri,
            canonical_uri=canonical_uri,
            source_title=document.source_title,
            source_type=document.source_type,
            published_at=document.published_at,
            retrieved_at=retrieved_at,
            last_checked_at=retrieved_at,
            author=document.author,
            publisher=document.publisher,
            content_hash=content_hash(raw_content),
            content_version=document.metadata.get("content_version"),
            access_status=SourceAccessStatus.ACCEPTED if safe else SourceAccessStatus.UNSAFE,
            trust_metadata={
                "prompt_injection_detected": prompt_injection,
                "unsafe_reason": unsafe_reason,
                "authority_score": document.metadata.get("authority_score", 0.5),
            },
            raw_reference=provider.fetch_metadata(document),
            domain_metadata=dict(document.metadata),
        )

        accepted, reject_reason = self.domain_plugins[mission.domain_id].validate_source(observation)
        if not safe or not accepted:
            observation = observation.model_copy(
                update={
                    "access_status": SourceAccessStatus.UNSAFE if not safe else SourceAccessStatus.REJECTED,
                    "trust_metadata": {
                        **observation.trust_metadata,
                        "reject_reason": reject_reason or unsafe_reason,
                    },
                }
            )
            self.store.insert_observation(observation)
            run.sources_discovered += 1
            run.sources_rejected += 1
            self._append_ledger(
                event_type=LedgerEventType.SOURCE_REJECTED,
                actor_type=ActorType.VALIDATOR,
                actor_id="source_gate",
                action="reject_source",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                reason=reject_reason or unsafe_reason,
                metadata={"source_uri": document.source_uri},
            )
            return

        self.store.insert_observation(observation)
        run.sources_discovered += 1
        run.sources_accepted += 1
        self._append_ledger(
            event_type=LedgerEventType.SOURCE_DISCOVERED,
            actor_type=ActorType.PROVIDER,
            actor_id=descriptor.provider_id,
            action="accept_source",
            domain_id=mission.domain_id,
            mission_id=mission.mission_id,
            run_id=run.run_id,
            metadata={"observation_id": observation.observation_id, "source_uri": observation.source_uri},
        )

        for hint in provider.extract(document, content=raw_content):
            normalized_text = sanitize_external_text(hint.normalized_text or hint.passage or hint.claim_hint)
            evidence_metadata = {
                **hint.metadata,
                "authority_score": document.metadata.get("authority_score", 0.5),
                "prompt_injection_detected": prompt_injection,
            }
            evidence = ResearchEvidenceRecord(
                evidence_id=self.store.next_id("evidence", "VEDA-EVD-"),
                observation_id=observation.observation_id,
                run_id=run.run_id,
                mission_id=mission.mission_id,
                domain_id=mission.domain_id,
                location=hint.location,
                passage=hint.passage,
                normalized_text=normalized_text or hint.claim_hint.lower(),
                claim_hint=hint.claim_hint,
                evidence_type=observation.source_type,
                language="en",
                content_hash=content_hash(hint.passage),
                extraction_method=descriptor.provider_id,
                confidence=hint.confidence,
                domain_metadata=evidence_metadata,
                created_at=utc_now(),
            )
            self.store.insert_evidence(evidence)
            run.evidence_created += 1
            self._append_ledger(
                event_type=LedgerEventType.EVIDENCE_CREATED,
                actor_type=ActorType.PROVIDER,
                actor_id=descriptor.provider_id,
                action="extract_evidence",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                metadata={"evidence_id": evidence.evidence_id, "observation_id": observation.observation_id},
            )
            self._upsert_candidate_from_evidence(mission, run, observation, evidence)

    def _upsert_candidate_from_evidence(
        self,
        mission: ResearchMissionRecord,
        run: ResearchRunRecord,
        observation: SourceObservationRecord,
        evidence: ResearchEvidenceRecord,
    ) -> ResearchCandidateRecord:
        plugin = self.domain_plugins[mission.domain_id]
        draft = plugin.normalize_candidate(evidence, observation, mission)
        existing = self.store.find_candidate_by_normalized_claim(
            mission.domain_id,
            draft["normalized_claim"],
            exclude_archived=False,
        )
        source_key = observation.domain_metadata.get("source_id") or observation.canonical_uri

        if existing is not None:
            before = existing.model_dump(mode="json")
            evidence_ids = sorted({*existing.evidence_ids, evidence.evidence_id})
            source_ids = sorted({*existing.source_ids, source_key})
            updated = existing.model_copy(
                update={
                    "mission_id": mission.mission_id,
                    "run_id": run.run_id,
                    "evidence_ids": evidence_ids,
                    "source_ids": source_ids,
                    "support_count": len(source_ids),
                    "updated_at": utc_now(),
                }
            )
            updated = self._apply_validations(updated, mission)
            self.store.upsert_candidate(updated)
            run.duplicates_detected += 1
            self._append_ledger(
                event_type=LedgerEventType.CANDIDATE_MERGED,
                actor_type=ActorType.SYSTEM,
                actor_id="dedupe",
                action="merge_candidate",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                candidate_id=updated.candidate_id,
                before_state=before,
                after_state=updated.model_dump(mode="json"),
                metadata={"evidence_id": evidence.evidence_id},
            )
            return updated

        core_records = self.store.list_core_knowledge(mission.domain_id)
        comparison = plugin.compare_to_core(draft, core_records)
        pending_candidates = self.store.find_candidates_by_topic(mission.domain_id, draft["topic_key"])
        conflict_payload = plugin.detect_domain_conflict(draft, core_records, pending_candidates)
        candidate = ResearchCandidateRecord(
            candidate_id=self.store.next_id("candidate", "VEDA-RCND-"),
            domain_id=mission.domain_id,
            mission_id=mission.mission_id,
            run_id=run.run_id,
            title=draft["title"],
            candidate_type=CandidateType(draft["candidate_type"]),
            claim=draft["claim"],
            normalized_claim=draft["normalized_claim"],
            topic_key=draft["topic_key"],
            stance=draft["stance"],
            evidence_ids=[evidence.evidence_id],
            source_ids=[source_key],
            existing_knowledge_matches=list(comparison.get("existing_knowledge_matches", [])),
            novelty_status=NoveltyStatus(comparison.get("novelty_status", NoveltyStatus.UNKNOWN.value)),
            contradiction_status=ContradictionStatus(conflict_payload.get("contradiction_status", ContradictionStatus.NONE.value)),
            validation_status=ValidationStatus.UNKNOWN,
            confidence=blank_confidence(),
            priority=MissionPriority(draft.get("priority", MissionPriority.P2.value)),
            safety_class=plugin.classify_safety(draft),
            approval_status=ApprovalStatus.PENDING,
            knowledge_zone=KnowledgeZone.RESEARCH_CANDIDATE,
            promotion_state=PromotionState.NONE,
            created_at=utc_now(),
            updated_at=utc_now(),
            support_count=1,
            metadata={
                **dict(draft.get("metadata", {})),
                "current_knowledge_comparison": comparison,
                "conflict_analysis": conflict_payload.get("analysis"),
            },
        )
        candidate = self._apply_validations(candidate, mission)
        self.store.upsert_candidate(candidate)
        run.candidates_created += 1
        self._append_ledger(
            event_type=LedgerEventType.CANDIDATE_CREATED,
            actor_type=ActorType.SYSTEM,
            actor_id="candidate_builder",
            action="create_candidate",
            domain_id=mission.domain_id,
            mission_id=mission.mission_id,
            run_id=run.run_id,
            candidate_id=candidate.candidate_id,
            after_state=candidate.model_dump(mode="json"),
        )
        if candidate.contradiction_status != ContradictionStatus.NONE:
            conflict = ResearchConflictRecord(
                conflict_id=self.store.next_id("conflict", "VEDA-RCNF-"),
                topic=candidate.topic_key,
                candidate_id=candidate.candidate_id,
                conflicting_candidate_id=conflict_payload.get("conflicting_candidate_id"),
                conflicting_core_id=conflict_payload.get("conflicting_core_id"),
                conflict_type=candidate.contradiction_status,
                analysis=conflict_payload.get("analysis", "Conflict detected."),
                implementation_impact="Requires explicit admin review before promotion.",
                resolution_status=ConflictResolutionStatus.UNRESOLVED,
                confidence=0.8,
                created_at=utc_now(),
            )
            self.store.insert_conflict(conflict)
            run.conflicts_created += 1
            self._append_ledger(
                event_type=LedgerEventType.CONTRADICTION_FOUND,
                actor_type=ActorType.VALIDATOR,
                actor_id="contradiction_checker",
                action="record_conflict",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                candidate_id=candidate.candidate_id,
                metadata={"conflict_id": conflict.conflict_id},
            )
        return candidate

    def _apply_validations(self, candidate: ResearchCandidateRecord, mission: ResearchMissionRecord) -> ResearchCandidateRecord:
        evidence_records = [self.store.get_evidence(evidence_id) for evidence_id in candidate.evidence_ids]
        evidence_records = [item for item in evidence_records if item is not None]
        source_count = max(1, len(set(candidate.source_ids)))
        source_confidence = min(1.0, source_count / max(1, mission.minimum_independent_sources))
        authority_scores = [float(item.domain_metadata.get("authority_score", 0.5)) for item in evidence_records] or [0.0]
        authority_confidence = sum(authority_scores) / len(authority_scores)
        provenance_needs_review = any(
            item.domain_metadata.get("verification_status") in {"REFERENCE_NOT_VERIFIED", "UNVERIFIED"}
            or bool(item.domain_metadata.get("discovery_only"))
            for item in evidence_records
        )
        provenance_confidence = 1.0 if evidence_records else 0.0
        if provenance_needs_review and provenance_confidence:
            provenance_confidence = 0.65
        cross_source_confidence = min(1.0, source_count / max(1, mission.minimum_independent_sources))
        ontology_matches = list(candidate.metadata.get("ontology_matches", []))
        ontology_gaps = list(candidate.metadata.get("ontology_gaps", []))
        if ontology_matches and not ontology_gaps:
            ontology_confidence = 1.0
        elif ontology_matches and ontology_gaps:
            ontology_confidence = 0.7
        elif ontology_gaps:
            ontology_confidence = 0.35
        else:
            ontology_confidence = 0.8
        novelty_confidence = {
            NoveltyStatus.NEW: 0.9,
            NoveltyStatus.KNOWN: 0.7,
            NoveltyStatus.DUPLICATE: 0.6,
            NoveltyStatus.POSSIBLE_UPDATE: 0.75,
            NoveltyStatus.PARTIAL_EXTENSION: 0.8,
            NoveltyStatus.REFINEMENT: 0.8,
            NoveltyStatus.UNKNOWN: 0.2,
        }[candidate.novelty_status]
        contradiction_confidence = 1.0 if candidate.contradiction_status == ContradictionStatus.NONE else 0.3
        domain_confidence = round(
            (source_confidence + authority_confidence + provenance_confidence + cross_source_confidence + novelty_confidence + contradiction_confidence) / 6,
            4,
        )
        confidence = ConfidenceDimensions(
            source_confidence=round(source_confidence, 4),
            authority_confidence=round(authority_confidence, 4),
            cross_source_confidence=round(cross_source_confidence, 4),
            provenance_confidence=round(provenance_confidence, 4),
            novelty_confidence=round(novelty_confidence, 4),
            contradiction_confidence=round(contradiction_confidence, 4),
            domain_confidence=domain_confidence,
        )

        validations = [
            (ValidationStage.V1_SOURCE_VALIDATION, ValidationStatus.PASS, source_confidence, "Accepted sources attached.", False),
            (
                ValidationStage.V2_AUTHORITY_VALIDATION,
                ValidationStatus.PASS if authority_confidence >= 0.7 else ValidationStatus.PASS_WITH_CONDITIONS,
                authority_confidence,
                "Authority based on source metadata.",
                False,
            ),
            (
                ValidationStage.V3_PROVENANCE_VALIDATION,
                ValidationStatus.PASS if evidence_records and not provenance_needs_review else (
                    ValidationStatus.PASS_WITH_CONDITIONS if evidence_records else ValidationStatus.FAIL
                ),
                provenance_confidence,
                "Evidence linkage present." if not provenance_needs_review else "Evidence linkage present, but source verification remains partial.",
                provenance_needs_review,
            ),
            (ValidationStage.V4_EXISTING_KNOWLEDGE_CHECK, ValidationStatus.PASS, novelty_confidence, "Existing knowledge comparison completed.", False),
            (
                ValidationStage.V5_CONTRADICTION_CHECK,
                ValidationStatus.PASS if candidate.contradiction_status == ContradictionStatus.NONE else ValidationStatus.PASS_WITH_CONDITIONS,
                contradiction_confidence,
                f"Contradiction status is {candidate.contradiction_status.value}.",
                candidate.contradiction_status != ContradictionStatus.NONE,
            ),
            (
                ValidationStage.V6_CROSS_SOURCE_SUPPORT,
                ValidationStatus.PASS if source_count >= mission.minimum_independent_sources else ValidationStatus.PASS_WITH_CONDITIONS,
                cross_source_confidence,
                "Independent source count evaluated.",
                source_count < mission.minimum_independent_sources,
            ),
            (
                ValidationStage.V7_ONTOLOGY_COMPATIBILITY,
                ValidationStatus.PASS if not ontology_gaps else ValidationStatus.PASS_WITH_CONDITIONS,
                ontology_confidence,
                "Ontology mapping completed." if not ontology_gaps else f"Ontology gaps remain: {', '.join(ontology_gaps[:4])}",
                bool(ontology_gaps),
            ),
            (ValidationStage.V8_RULE_IMPACT, ValidationStatus.NOT_APPLICABLE, 0.0, "No rule impact promotion occurs in P006.", False),
            (
                ValidationStage.V9_SAFETY_CLASSIFICATION,
                ValidationStatus.PASS_WITH_CONDITIONS if candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES} else ValidationStatus.PASS,
                1.0,
                f"Safety class is {candidate.safety_class.value}.",
                candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES},
            ),
            (ValidationStage.V10_NOVELTY_ASSESSMENT, ValidationStatus.PASS, novelty_confidence, "Novelty assessment completed.", False),
        ]

        for stage, status, score, reason, requires_follow_up in validations:
            validation = ResearchValidationRecord(
                validation_id=self.store.next_id("validation", "VEDA-RVAL-"),
                candidate_id=candidate.candidate_id,
                validator=stage,
                result=stage.value,
                score=float(round(score, 4)),
                status=status,
                evidence={
                    "evidence_ids": candidate.evidence_ids,
                    "source_ids": candidate.source_ids,
                    "support_count": candidate.support_count,
                },
                reason=reason,
                requires_follow_up=requires_follow_up,
                created_at=utc_now(),
            )
            self.store.insert_validation(validation)
            self._append_ledger(
                event_type=LedgerEventType.VALIDATION_COMPLETED,
                actor_type=ActorType.VALIDATOR,
                actor_id=stage.value,
                action="validation_completed",
                domain_id=candidate.domain_id,
                mission_id=candidate.mission_id,
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                metadata={"validation_id": validation.validation_id, "status": validation.status.value},
            )

        aggregate_status = ValidationStatus.PASS
        if any(stage_status == ValidationStatus.FAIL for _, stage_status, *_ in validations):
            aggregate_status = ValidationStatus.FAIL
        elif any(stage_status == ValidationStatus.PASS_WITH_CONDITIONS for _, stage_status, *_ in validations):
            aggregate_status = ValidationStatus.PASS_WITH_CONDITIONS

        updated = candidate.model_copy(
            update={
                "confidence": confidence,
                "validation_status": aggregate_status,
                "updated_at": utc_now(),
            }
        )
        return updated

    def list_runs(self) -> list[ResearchRunRecord]:
        return self.store.list_runs()

    def get_run(self, run_id: str) -> ResearchRunRecord | None:
        return self.store.get_run(run_id)

    def list_candidates(self) -> list[ResearchCandidateRecord]:
        return self.store.list_candidates()

    def get_candidate(self, candidate_id: str) -> ResearchCandidateRecord | None:
        return self.store.get_candidate(candidate_id)

    def get_candidate_review(self, candidate_id: str) -> CandidateReviewRecord:
        candidate = self._require_candidate(candidate_id)
        evidence_summary = [self.store.get_evidence(evidence_id) for evidence_id in candidate.evidence_ids]
        evidence_summary = [item for item in evidence_summary if item is not None]
        validation_summary = self.store.list_validations_for_candidate(candidate_id)
        mission = self._require_mission(candidate.mission_id)
        run = self._require_run(candidate.run_id)
        return CandidateReviewRecord(
            candidate=candidate,
            evidence_summary=evidence_summary,
            validation_summary=validation_summary,
            novelty=candidate.novelty_status,
            contradiction=candidate.contradiction_status,
            confidence=candidate.confidence,
            current_knowledge_comparison=dict(candidate.metadata.get("current_knowledge_comparison", {})),
            mission=mission,
            run=run,
            status=candidate.approval_status,
        )

    def decide_candidate(
        self,
        candidate_id: str,
        *,
        action: AdminAction,
        actor_id: str,
        reason: str,
        conditions: list[str] | None = None,
    ) -> ResearchApprovalRecord:
        action = action if isinstance(action, AdminAction) else AdminAction(action)
        candidate = self._require_candidate(candidate_id)
        before = candidate.model_dump(mode="json")

        updates: dict[str, Any] = {"updated_at": utc_now()}
        if action == AdminAction.APPROVE:
            updates["approval_status"] = ApprovalStatus.APPROVED
            updates["promotion_state"] = PromotionState.PROMOTION_READY
            event_type = LedgerEventType.ADMIN_APPROVED
        elif action == AdminAction.APPROVE_WITH_CONDITIONS:
            updates["approval_status"] = ApprovalStatus.APPROVED_WITH_CONDITIONS
            updates["promotion_state"] = PromotionState.PROMOTION_READY
            event_type = LedgerEventType.ADMIN_APPROVED
        elif action == AdminAction.REJECT:
            updates["approval_status"] = ApprovalStatus.REJECTED
            updates["knowledge_zone"] = KnowledgeZone.RESEARCH_ARCHIVE
            event_type = LedgerEventType.ADMIN_REJECTED
        elif action == AdminAction.REQUEST_MORE_RESEARCH:
            updates["approval_status"] = ApprovalStatus.NEEDS_MORE_RESEARCH
            event_type = LedgerEventType.MORE_RESEARCH_REQUESTED
        elif action == AdminAction.MERGE:
            updates["approval_status"] = ApprovalStatus.MERGE_REQUIRED
            event_type = LedgerEventType.MORE_RESEARCH_REQUESTED
        elif action == AdminAction.SUPERSEDE:
            updates["approval_status"] = ApprovalStatus.SUPERSEDE_APPROVED
            event_type = LedgerEventType.ADMIN_APPROVED
        elif action == AdminAction.ARCHIVE:
            updates["approval_status"] = ApprovalStatus.ARCHIVED
            updates["knowledge_zone"] = KnowledgeZone.RESEARCH_ARCHIVE
            event_type = LedgerEventType.ADMIN_REJECTED
        else:
            raise RuntimeError(f"Unsupported action: {action.value}")

        updated = candidate.model_copy(update=updates)
        self.store.upsert_candidate(updated)

        approval = ResearchApprovalRecord(
            approval_id=self.store.next_id("approval", "VEDA-RAPR-"),
            candidate_id=candidate_id,
            action=action,
            status=updated.approval_status,
            decided_by=actor_id,
            decided_at=utc_now(),
            reason=reason,
            conditions=list(conditions or []),
            promotion_state=updated.promotion_state,
        )
        self.store.insert_approval(approval)
        self._append_ledger(
            event_type=event_type,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action=action.value,
            domain_id=updated.domain_id,
            mission_id=updated.mission_id,
            run_id=updated.run_id,
            candidate_id=updated.candidate_id,
            before_state=before,
            after_state=updated.model_dump(mode="json"),
            reason=reason,
            metadata={"approval_id": approval.approval_id},
        )

        if action == AdminAction.REQUEST_MORE_RESEARCH:
            self._create_follow_up_mission(updated, reason=reason, actor_id=actor_id)

        return approval

    def _create_follow_up_mission(self, candidate: ResearchCandidateRecord, *, reason: str, actor_id: str) -> ResearchMissionRecord | None:
        existing = self.store.find_follow_up_mission(candidate.candidate_id)
        if existing is not None:
            return existing
        plugin = self.domain_plugins[candidate.domain_id]
        payload = plugin.create_follow_up(candidate, reason)
        if payload is None:
            return None
        if payload.get("follow_up_depth", 0) > candidate.metadata.get("max_follow_up_depth", 2):
            return None
        follow_up = self.create_mission(payload)
        self._append_ledger(
            event_type=LedgerEventType.FOLLOW_UP_CREATED,
            actor_type=ActorType.SYSTEM,
            actor_id=actor_id,
            action="create_follow_up_mission",
            domain_id=follow_up.domain_id,
            mission_id=follow_up.mission_id,
            candidate_id=candidate.candidate_id,
            reason=reason,
        )
        return follow_up

    def list_ledger_events(self) -> list[ResearchLedgerEventRecord]:
        return self.store.list_ledger_events()

    def export_snapshot(self, export_dir: Path | None = None) -> dict[str, Path]:
        base_dir = Path(export_dir or cfg.VEDA_RESEARCH_PLATFORM_EXPORT_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        payloads = self.store.export_records()
        written: dict[str, Path] = {}
        file_map = {
            "research_domains": "research_domain.json",
            "research_core_knowledge": "research_core_knowledge.json",
            "research_missions": "research_missions.json",
            "research_schedules": "research_schedule.json",
            "research_runs": "research_run.json",
            "source_observations": "source_observation.json",
            "research_evidence": "research_evidence.json",
            "research_candidates": "research_candidate.json",
            "research_validations": "research_validation.json",
            "research_conflicts": "research_conflict.json",
            "research_approvals": "research_approval.json",
            "research_ledger_events": "research_ledger_event.json",
        }
        for key, filename in file_map.items():
            path = base_dir / filename
            path.write_text(json.dumps(payloads[key], indent=2) + "\n", encoding="utf-8")
            written[key] = path
        (base_dir / "research_dashboard.json").write_text(
            json.dumps(self.dashboard().model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        written["research_dashboard"] = base_dir / "research_dashboard.json"
        return written

    def _resolve_provider(self, mission: ResearchMissionRecord, domain: ResearchDomainRecord) -> BasePlatformResearchProvider:
        provider_id = mission.query_strategy.get("provider_id") or domain.provider_policy.get("default_provider_id")
        provider = self.providers.get(provider_id)
        if provider is None:
            raise KeyError(f"Unknown research provider: {provider_id}")
        return provider

    def _append_ledger(
        self,
        *,
        event_type: LedgerEventType,
        actor_type: ActorType,
        actor_id: str,
        action: str,
        domain_id: str | None = None,
        mission_id: str | None = None,
        run_id: str | None = None,
        candidate_id: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = ResearchLedgerEventRecord(
            event_id=self.store.next_id("ledger", "VEDA-LED-"),
            timestamp=utc_now(),
            event_type=event_type,
            domain_id=domain_id,
            mission_id=mission_id,
            run_id=run_id,
            candidate_id=candidate_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            metadata=dict(metadata or {}),
        )
        self.store.append_ledger_event(record)

    def _require_domain(self, domain_id: str) -> ResearchDomainRecord:
        domain = self.store.get_domain(domain_id)
        if domain is None:
            raise KeyError(f"Unknown domain: {domain_id}")
        return domain

    def _require_mission(self, mission_id: str) -> ResearchMissionRecord:
        mission = self.store.get_mission(mission_id)
        if mission is None:
            raise KeyError(f"Unknown mission: {mission_id}")
        return mission

    def _require_candidate(self, candidate_id: str) -> ResearchCandidateRecord:
        candidate = self.store.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(f"Unknown candidate: {candidate_id}")
        return candidate

    def _require_run(self, run_id: str) -> ResearchRunRecord:
        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(f"Unknown run: {run_id}")
        return run


_SERVICE: ResearchPlatformService | None = None


def get_research_platform_service() -> ResearchPlatformService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ResearchPlatformService()
    return _SERVICE
