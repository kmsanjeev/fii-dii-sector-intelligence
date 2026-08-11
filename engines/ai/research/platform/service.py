from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from engines.ai.research.platform.contracts import (
    AdminAction,
    ActorType,
    ApprovalStatus,
    CadenceType,
    CandidateReviewRecord,
    CandidateType,
    ConfidenceDimensions,
    ConflictResolutionStatus,
    CoreVersionState,
    ContradictionStatus,
    DomainStatus,
    IndexSyncStatus,
    KnowledgeZone,
    LedgerEventType,
    MisfirePolicy,
    MissionPriority,
    MissionStatus,
    NoveltyStatus,
    OverlapPolicy,
    PlatformHealth,
    PromotionPreflightStatus,
    PromotionStatus,
    PromotionState,
    ResearchApprovalRecord,
    ResearchBudget,
    ResearchCandidateRecord,
    ResearchConflictRecord,
    ResearchCoreKnowledgeRecord,
    ResearchDashboardRecord,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchIndexSyncRecord,
    ResearchLedgerEventRecord,
    ResearchMissionRecord,
    ResearchPromotionPreflightRecord,
    ResearchPromotionRecord,
    ResearchRollbackRecord,
    ResearchRunRecord,
    ResearchScheduleRecord,
    ResearchType,
    ResearchValidationRecord,
    RunStatus,
    SafetyClass,
    SourceAccessStatus,
    SourceObservationRecord,
    TriggerType,
    ValidationStage,
    ValidationStatus,
    ProviderStatus,
)
from engines.ai.knowledge.unified_runtime_sync import refresh_unified_retrieval_assets
from engines.ai.research.platform.external_providers import DDGSPlatformSearchProvider, RequestsDirectRetrievalProvider
from engines.ai.research.platform.promotion import PromotionMaterializationResult, VedicAstrologyPromotionMaterializer
from engines.ai.research.platform.providers import (
    BasePlatformResearchProvider,
    ResearchProviderAuthError,
    ResearchProviderTemporaryError,
    SyntheticFixtureProvider,
)
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
        ddgs_provider = DDGSPlatformSearchProvider()
        requests_provider = RequestsDirectRetrievalProvider()
        self.providers: dict[str, BasePlatformResearchProvider] = {
            default_provider.descriptor().provider_id: default_provider,
            astrology_provider.descriptor().provider_id: astrology_provider,
            ddgs_provider.descriptor().provider_id: ddgs_provider,
            requests_provider.descriptor().provider_id: requests_provider,
        }
        if providers:
            self.providers.update(providers)
        self.domain_plugins = {
            self.synthetic_plugin.domain_id: self.synthetic_plugin,
            self.vedic_astrology_plugin.domain_id: self.vedic_astrology_plugin,
        }
        if domain_plugins:
            self.domain_plugins.update(domain_plugins)
        self._astrology_promotion_materializer = VedicAstrologyPromotionMaterializer()
        self.store.recover_stale_runs()
        self._bootstrap_defaults()

    def _bootstrap_defaults(self) -> None:
        for plugin in self.domain_plugins.values():
            self.store.upsert_domain(plugin.domain_record())
            for record in plugin.seed_core_knowledge():
                self.store.upsert_core_knowledge(record)

    def list_domains(self) -> list[ResearchDomainRecord]:
        return self.store.list_domains()

    def provider_capability_matrix(self) -> list[dict[str, Any]]:
        matrix: list[dict[str, Any]] = []
        for provider_id, provider in self.providers.items():
            descriptor = provider.descriptor()
            state = self.store.get_provider_state(provider_id) or {}
            status = state.get("status") or (descriptor.status.value if hasattr(descriptor.status, "value") else str(descriptor.status))
            provider_type = self._provider_type_name(provider_id) or "UNKNOWN"
            enabled = bool(state.get("enabled", True))
            healthy = status in {ProviderStatus.HEALTHY.value, "ACTIVE"}
            suitable = enabled and provider.is_available() and provider_type in {"WEB_SEARCH", "DIRECT_WEB", "LOCAL_DOCUMENTS", "INTERNAL_KNOWLEDGE"}
            matrix.append(
                {
                    "provider": provider_id,
                    "search": bool(descriptor.supports_search),
                    "fetch": bool(descriptor.supports_fetch),
                    "auth": bool(descriptor.auth_required),
                    "enabled": enabled,
                    "healthy": healthy,
                    "suitable": suitable,
                    "implemented": True,
                    "configured": provider.is_available(),
                    "validated": bool(state.get("last_success")),
                    "status": status,
                    "provider_type": provider_type,
                }
            )
        matrix.sort(key=lambda item: item["provider"])
        return matrix

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

    def seed_vedic_astrology_external_program(self, *, actor_id: str = "admin") -> dict[str, Any]:
        provider_matrix = self.provider_capability_matrix()
        search_ready = any(
            item["provider"] == "ddgs-search"
            and item["search"]
            and item["enabled"]
            and item["configured"]
            and item["suitable"]
            for item in provider_matrix
        )
        retrieval_ready = any(
            item["provider"] == "requests-fetch"
            and item["fetch"]
            and item["enabled"]
            and item["configured"]
            and item["suitable"]
            for item in provider_matrix
        )
        activate = search_ready and retrieval_ready
        payloads = self.vedic_astrology_plugin.build_external_activation_program(
            search_provider_id="ddgs-search",
            retrieval_provider_id="requests-fetch",
            fallback_provider_ids=["vedic-astrology-local"],
            activate=activate,
        )
        missions: list[ResearchMissionRecord] = []
        schedules: list[ResearchScheduleRecord] = []
        for entry in payloads:
            mission_payload = dict(entry["mission"])
            schedule_payload = dict(entry["schedule"])
            existing_mission = self._find_mission_by_title(mission_payload["domain_id"], mission_payload["title"])
            if existing_mission is None:
                mission = self.create_mission(mission_payload)
            else:
                mission = existing_mission
                if activate and mission.status == MissionStatus.PAUSED:
                    mission = self.resume_mission(mission.mission_id, actor_id=actor_id)
                elif not activate and mission.status == MissionStatus.ACTIVE:
                    mission = self.pause_mission(mission.mission_id, actor_id=actor_id)
            missions.append(mission)

            existing_schedule = next((item for item in self.store.list_schedules() if item.mission_id == mission.mission_id), None)
            schedule_payload.update(
                {
                    "domain_id": mission.domain_id,
                    "mission_id": mission.mission_id,
                    "enabled": bool(schedule_payload.get("enabled", activate)),
                }
            )
            if existing_schedule is None:
                schedules.append(self.create_schedule(schedule_payload))
            else:
                schedules.append(
                    self.update_schedule(
                        existing_schedule.schedule_id,
                        {
                            "enabled": schedule_payload["enabled"],
                            "cadence_type": schedule_payload.get("cadence_type"),
                            "timezone": schedule_payload.get("timezone"),
                            "misfire_policy": schedule_payload.get("misfire_policy"),
                            "overlap_policy": schedule_payload.get("overlap_policy"),
                            "priority": schedule_payload.get("priority"),
                        },
                    )
                )

        return {
            "domain_id": self.vedic_astrology_plugin.domain_id,
            "external_ready": activate,
            "provider_matrix": provider_matrix,
            "missions": [item.model_dump(mode="json") for item in missions],
            "schedules": [item.model_dump(mode="json") for item in schedules],
        }

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

    def resume_mission(
        self,
        mission_id: str,
        *,
        actor_id: str = "admin",
        priority: MissionPriority | str | None = None,
        notes: str | None = None,
    ) -> ResearchMissionRecord:
        mission = self._require_mission(mission_id)
        updates: dict[str, Any] = {"updated_at": utc_now()}
        if mission.status == MissionStatus.PAUSED:
            updates["status"] = MissionStatus.ACTIVE
        if priority is not None:
            updates["priority"] = priority if isinstance(priority, MissionPriority) else MissionPriority(priority)
        if notes:
            updates["notes"] = notes
        updated = mission.model_copy(update=updates)
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
        cadence_type = CadenceType(payload.get("cadence_type", "MANUAL_ONLY"))
        timezone_name = payload.get("timezone", "Asia/Calcutta")
        record = ResearchScheduleRecord(
            schedule_id=self.store.next_id("schedule", "VEDA-RSCH-"),
            domain_id=payload["domain_id"],
            mission_id=payload["mission_id"],
            cadence_type=cadence_type,
            timezone=timezone_name,
            enabled=bool(payload.get("enabled", True)),
            next_run_at=payload.get("next_run_at") or self._next_schedule_time(now, cadence_type, timezone_name),
            last_run_at=payload.get("last_run_at"),
            misfire_policy=payload.get("misfire_policy", "RUN_ONCE"),
            overlap_policy=payload.get("overlap_policy", "COALESCE" if cadence_type != CadenceType.MANUAL_ONLY else "SKIP"),
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
        cadence_type = CadenceType(updates.get("cadence_type", schedule.cadence_type))
        timezone_name = updates.get("timezone", schedule.timezone)
        next_run_at = updates.get("next_run_at", schedule.next_run_at)
        if updates.get("enabled", schedule.enabled) and cadence_type != CadenceType.MANUAL_ONLY and not next_run_at:
            next_run_at = self._next_schedule_time(utc_now(), cadence_type, timezone_name)
        updated = ResearchScheduleRecord.model_validate(
            {
                **schedule.model_dump(mode="json"),
                "enabled": bool(updates.get("enabled", schedule.enabled)),
                "cadence_type": cadence_type,
                "timezone": timezone_name,
                "next_run_at": next_run_at,
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
        schedule = self.store.get_schedule(mission.schedule_id) if mission.schedule_id else None
        return self._execute_run(mission, actor_id=actor_id, trigger_type=trigger_type, schedule=schedule)

    def _execute_run(
        self,
        mission: ResearchMissionRecord,
        *,
        actor_id: str,
        trigger_type: TriggerType,
        schedule: ResearchScheduleRecord | None = None,
        as_of: str | None = None,
    ) -> ResearchRunRecord:
        domain = self._require_domain(mission.domain_id)
        search_providers, retrieval_provider = self._resolve_provider_chain(mission, domain)
        prior_runs = self.store.list_runs_for_mission(mission.mission_id)
        now = as_of or utc_now()

        run = ResearchRunRecord(
            run_id=self.store.next_id("run", "VEDA-RUN-"),
            mission_id=mission.mission_id,
            domain_id=mission.domain_id,
            trigger_type=trigger_type,
            started_at=now,
            status=RunStatus.RUNNING,
            model_metadata={
                "cycle": self._cycle_label_for_trigger(trigger_type, schedule),
                "backlog_state": self.backlog_state(),
                "budget_clock_at": now,
            },
        )
        self.store.insert_run(run)
        if trigger_type != TriggerType.MANUAL:
            self._append_ledger(
                event_type=LedgerEventType.SCHEDULE_TRIGGERED,
                actor_type=ActorType.SCHEDULER,
                actor_id=actor_id,
                action="schedule_triggered",
                domain_id=run.domain_id,
                mission_id=run.mission_id,
                run_id=run.run_id,
                metadata={
                    "schedule_id": schedule.schedule_id if schedule else None,
                    "trigger_type": trigger_type.value,
                },
            )
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
            provider, batch = self._search_with_fallback(
                mission,
                run,
                search_providers=search_providers,
                prior_run_count=len(prior_runs),
            )
            run.provider_calls += 1
            if batch.query:
                run.queries_executed += 1
            if batch.query or batch.search_metadata:
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

            documents = list(batch.documents)
            if len(documents) > mission.research_budget.max_sources:
                run.errors.append("budget_exhausted")
            accepted_any = False
            for document in documents[: mission.research_budget.max_sources]:
                if self._run_budget_exhausted(run, mission):
                    run.errors.append("budget_exhausted")
                    break
                try:
                    self._process_document(provider, retrieval_provider or provider, mission, run, document)
                    accepted_any = True
                except ResearchProviderAuthError as exc:
                    run.errors.append(str(exc))
                    self._mark_provider_failure((retrieval_provider or provider).descriptor().provider_id, error=str(exc), hard=True)
                    self._record_document_failure(
                        mission=mission,
                        run=run,
                        document=document,
                        reason=str(exc),
                        provider_id=(retrieval_provider or provider).descriptor().provider_id,
                    )
                except ResearchProviderTemporaryError as exc:
                    run.errors.append(str(exc))
                    self._mark_provider_failure((retrieval_provider or provider).descriptor().provider_id, error=str(exc), hard=False)
                    self._record_document_failure(
                        mission=mission,
                        run=run,
                        document=document,
                        reason=str(exc),
                        provider_id=(retrieval_provider or provider).descriptor().provider_id,
                    )
                except Exception as exc:
                    run.errors.append(str(exc))
                    self._record_document_failure(
                        mission=mission,
                        run=run,
                        document=document,
                        reason=str(exc),
                        provider_id=(retrieval_provider or provider).descriptor().provider_id,
                    )

            run.continuation_required = bool(batch.continuation_hint)
            run.continuation_hint = batch.continuation_hint
            if run.status == RunStatus.RUNNING:
                if run.errors and not accepted_any and run.sources_accepted == 0 and run.evidence_created == 0 and run.candidates_created == 0:
                    run.status = RunStatus.FAILED
                else:
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
            run = run.model_copy(
                update={
                    "completed_at": finished_at,
                    "cost_metrics": {
                        **dict(run.cost_metrics),
                        "sources_processed": run.sources_discovered,
                        "queries_executed": run.queries_executed,
                    },
                }
            )
            self.store.update_run(run)
            mission_update = mission.model_copy(
                update={
                    "status": MissionStatus.ACTIVE if mission.status != MissionStatus.PAUSED else mission.status,
                    "updated_at": finished_at,
                    "last_run_at": finished_at,
                }
            )
            self.store.update_mission(mission_update)
            if schedule:
                self._finalize_schedule_after_run(schedule, finished_at)
            self._append_ledger(
                event_type=LedgerEventType.RUN_COMPLETED if run.status != RunStatus.FAILED else LedgerEventType.RUN_FAILED,
                actor_type=ActorType.SYSTEM,
                actor_id=actor_id,
                action="complete_run" if run.status != RunStatus.FAILED else "run_failed",
                domain_id=run.domain_id,
                mission_id=run.mission_id,
                run_id=run.run_id,
                after_state=run.model_dump(mode="json"),
                metadata={"status": run.status.value},
            )
        return run

    def _process_document(
        self,
        search_provider: BasePlatformResearchProvider,
        retrieval_provider: BasePlatformResearchProvider,
        mission: ResearchMissionRecord,
        run: ResearchRunRecord,
        document,
    ) -> None:
        search_descriptor = search_provider.descriptor()
        provider_for_document = retrieval_provider
        descriptor = provider_for_document.descriptor()
        safe, unsafe_reason = is_safe_uri(document.source_uri, allowed_schemes=set(descriptor.allowed_uri_schemes))
        if not safe and search_descriptor.supports_fetch:
            fallback_safe, _ = is_safe_uri(document.source_uri, allowed_schemes=set(search_descriptor.allowed_uri_schemes))
            if fallback_safe:
                provider_for_document = search_provider
                descriptor = search_descriptor
                safe, unsafe_reason = fallback_safe, None
        plugin = self.domain_plugins[mission.domain_id]
        retrieved_at = utc_now()
        canonical_uri = normalize_uri(document.source_uri)
        raw_content = "" if not safe else provider_for_document.retrieve(document)
        raw_reference = provider_for_document.fetch_metadata(document)
        refined_metadata = plugin.refine_observation_metadata(
            mission=mission,
            document_metadata=dict(document.metadata),
            fetched_content=raw_content,
            canonical_uri=canonical_uri,
            raw_reference=dict(raw_reference),
        )
        document.metadata = dict(refined_metadata)
        prompt_injection = detect_prompt_injection(raw_content)
        previous_observation = self.store.find_latest_observation(canonical_uri)
        change_status = "NEW"
        if previous_observation is not None:
            change_status = "UNCHANGED" if previous_observation.content_hash == content_hash(raw_content) else "UPDATED"
        if safe:
            self._append_ledger(
                event_type=LedgerEventType.SOURCE_RETRIEVED,
                actor_type=ActorType.PROVIDER,
                actor_id=descriptor.provider_id,
                action="retrieve_source",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                metadata={
                    "source_uri": document.source_uri,
                    "discovery_provider": search_descriptor.provider_id,
                    "change_status": change_status,
                },
            )
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
            author=refined_metadata.get("author") or document.author,
            publisher=refined_metadata.get("publisher") or document.publisher,
            content_hash=content_hash(raw_content),
            content_version=refined_metadata.get("content_version"),
            access_status=SourceAccessStatus.ACCEPTED if safe else SourceAccessStatus.UNSAFE,
            trust_metadata={
                "prompt_injection_detected": prompt_injection,
                "unsafe_reason": unsafe_reason,
                "authority_score": refined_metadata.get("authority_score", 0.5),
                "change_status": change_status,
            },
            raw_reference={
                **dict(raw_reference),
                "search_provider_id": search_descriptor.provider_id,
                "retrieval_provider_id": descriptor.provider_id,
            },
            domain_metadata={
                **dict(refined_metadata),
                "discovery_provider_id": search_descriptor.provider_id,
                "retrieval_provider_id": descriptor.provider_id,
                "change_status": change_status,
            },
        )

        accepted, reject_reason = plugin.validate_source(observation)
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
            actor_id=search_descriptor.provider_id,
            action="accept_source",
            domain_id=mission.domain_id,
            mission_id=mission.mission_id,
            run_id=run.run_id,
            metadata={"observation_id": observation.observation_id, "source_uri": observation.source_uri},
        )

        for hint in retrieval_provider.extract(document, content=raw_content):
            normalized_text = sanitize_external_text(hint.normalized_text or hint.passage or hint.claim_hint)
            evidence_metadata = {
                **hint.metadata,
                "authority_score": observation.domain_metadata.get("authority_score", document.metadata.get("authority_score", 0.5)),
                "prompt_injection_detected": prompt_injection,
                "change_status": change_status,
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

    def _record_document_failure(
        self,
        *,
        mission: ResearchMissionRecord,
        run: ResearchRunRecord,
        document,
        reason: str,
        provider_id: str,
    ) -> None:
        run.sources_discovered += 1
        run.sources_rejected += 1
        self._append_ledger(
            event_type=LedgerEventType.SOURCE_REJECTED,
            actor_type=ActorType.VALIDATOR,
            actor_id="source_gate",
            action="source_retrieval_failed",
            domain_id=mission.domain_id,
            mission_id=mission.mission_id,
            run_id=run.run_id,
            reason=reason,
            metadata={
                "source_uri": getattr(document, "source_uri", None),
                "provider_id": provider_id,
            },
        )

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
        acknowledged_high_stakes: bool = False,
        conflict_id: str | None = None,
        conflict_resolution: str | None = None,
        conflict_note: str | None = None,
    ) -> ResearchApprovalRecord:
        action = action if isinstance(action, AdminAction) else AdminAction(action)
        candidate = self._require_candidate(candidate_id)
        before = candidate.model_dump(mode="json")

        if conflict_resolution and not conflict_id:
            candidate_conflicts = self.store.list_conflicts_for_candidate(candidate_id)
            if len(candidate_conflicts) == 1:
                conflict_id = candidate_conflicts[0].conflict_id
            elif len(candidate_conflicts) > 1:
                raise RuntimeError("Conflict resolution requires an explicit conflict selection when multiple conflicts exist")

        if (
            candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL}
            and action in {AdminAction.APPROVE, AdminAction.APPROVE_WITH_CONDITIONS}
            and not acknowledged_high_stakes
        ):
            raise RuntimeError("High-stakes candidate approval requires explicit acknowledgement")

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
            metadata={
                "approval_id": approval.approval_id,
                "conflict_id": conflict_id,
                "conflict_resolution": conflict_resolution,
            },
        )

        if conflict_id and conflict_resolution:
            self._apply_conflict_resolution(
                conflict_id,
                resolution_status=conflict_resolution,
                note=conflict_note or reason,
            )

        if action == AdminAction.REQUEST_MORE_RESEARCH:
            self._create_follow_up_mission(updated, reason=reason, actor_id=actor_id)

        return approval

    def run_promotion_preflight(
        self,
        candidate_id: str,
        *,
        actor_id: str,
        promotion_id: str | None = None,
    ) -> ResearchPromotionPreflightRecord:
        context = self._promotion_context(candidate_id)
        preflight = self._build_promotion_preflight(
            candidate=context["candidate"],
            approval=context["approval"],
            evidence_rows=context["evidence_rows"],
            observations=context["observations"],
            conflicts=context["conflicts"],
            existing_core_matches=context["existing_core_matches"],
            promotion_id=promotion_id,
        )
        self.store.insert_promotion_preflight(preflight)

        candidate = context["candidate"]
        next_state = PromotionState.BLOCKED if preflight.status == PromotionPreflightStatus.BLOCKED else PromotionState.PROMOTION_READY
        if candidate.promotion_state != next_state:
            updated_candidate = candidate.model_copy(
                update={
                    "promotion_state": next_state,
                    "updated_at": utc_now(),
                }
            )
            self.store.upsert_candidate(updated_candidate)
        else:
            updated_candidate = candidate

        self._append_ledger(
            event_type=LedgerEventType.PROMOTION_PREFLIGHT,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="promotion_preflight",
            domain_id=updated_candidate.domain_id,
            mission_id=updated_candidate.mission_id,
            run_id=updated_candidate.run_id,
            candidate_id=updated_candidate.candidate_id,
            metadata={
                "preflight_id": preflight.preflight_id,
                "promotion_id": promotion_id,
                "status": preflight.status.value,
                "blocking_reasons": list(preflight.blocking_reasons),
                "warnings": list(preflight.warnings),
            },
        )
        return preflight

    def promote_candidate(
        self,
        candidate_id: str,
        *,
        actor_id: str,
        promotion_notes: str | None = None,
    ) -> dict[str, Any]:
        context = self._promotion_context(candidate_id)
        promotion_id = self.store.next_id("promotion", "VEDA-RPRM-")
        preflight = self.run_promotion_preflight(candidate_id, actor_id=actor_id, promotion_id=promotion_id)
        context = self._promotion_context(candidate_id)
        candidate = context["candidate"]
        approval = context["approval"]

        if preflight.status == PromotionPreflightStatus.BLOCKED:
            promotion = ResearchPromotionRecord(
                promotion_id=promotion_id,
                candidate_id=candidate.candidate_id,
                domain_id=candidate.domain_id,
                approval_id=approval.approval_id,
                promotion_status=PromotionStatus.BLOCKED,
                preflight_result=preflight.status,
                source_ids=[],
                passage_ids=[],
                claim_ids=[],
                rule_ids=[],
                conflict_ids=[],
                core_ids=[],
                previous_version_ids=[],
                created_at=utc_now(),
                completed_at=utc_now(),
                promoted_by=actor_id,
                promotion_notes=promotion_notes,
                index_sync_status=IndexSyncStatus.PENDING,
            )
            self.store.insert_promotion(promotion)
            self._append_ledger(
                event_type=LedgerEventType.PROMOTION_BLOCKED,
                actor_type=ActorType.ADMIN,
                actor_id=actor_id,
                action="promote_candidate",
                domain_id=candidate.domain_id,
                mission_id=candidate.mission_id,
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                reason=promotion_notes,
                metadata={
                    "promotion_id": promotion_id,
                    "preflight_id": preflight.preflight_id,
                    "blocking_reasons": list(preflight.blocking_reasons),
                },
            )
            return {
                "preflight": preflight.model_dump(mode="json"),
                "promotion": promotion.model_dump(mode="json"),
                "index_sync": None,
                "core_records": [],
            }

        promotion = ResearchPromotionRecord(
            promotion_id=promotion_id,
            candidate_id=candidate.candidate_id,
            domain_id=candidate.domain_id,
            approval_id=approval.approval_id,
            promotion_status=PromotionStatus.PROMOTING,
            preflight_result=preflight.status,
            source_ids=[],
            passage_ids=[],
            claim_ids=[],
            rule_ids=[],
            conflict_ids=[],
            core_ids=[],
            previous_version_ids=[],
            created_at=utc_now(),
            completed_at=None,
            promoted_by=actor_id,
            promotion_notes=promotion_notes,
            index_sync_status=IndexSyncStatus.PENDING,
        )
        self.store.insert_promotion(promotion)
        self._append_ledger(
            event_type=LedgerEventType.PROMOTION_STARTED,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="promote_candidate",
            domain_id=candidate.domain_id,
            mission_id=candidate.mission_id,
            run_id=candidate.run_id,
            candidate_id=candidate.candidate_id,
            metadata={
                "promotion_id": promotion_id,
                "preflight_id": preflight.preflight_id,
                "proposed_operation": preflight.proposed_operation,
            },
        )

        materialization_result: PromotionMaterializationResult | None = None
        generic_docs_snapshot = self._read_text_if_exists(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS)
        try:
            if candidate.domain_id == self.vedic_astrology_plugin.domain_id:
                materialization_result = self._astrology_promotion_materializer.materialize(
                    candidate=candidate,
                    approval=approval,
                    evidence_rows=context["evidence_rows"],
                    observations=context["observations"],
                    conflicts=context["conflicts"],
                    existing_core_matches=context["existing_core_matches"],
                    promotion_id=promotion_id,
                    core_id=self._next_core_id(),
                    actor_id=actor_id,
                    promotion_notes=promotion_notes,
                )
                core_records = materialization_result.core_records
            else:
                core_records = [
                    self._create_generic_core_record(
                        core_id=self._next_core_id(),
                        candidate=candidate,
                        approval=approval,
                        promotion_id=promotion_id,
                        existing_core_matches=context["existing_core_matches"],
                        actor_id=actor_id,
                        promotion_notes=promotion_notes,
                    )
                ]
                self._write_generic_core_docs(
                    candidate=candidate,
                    new_core_record=core_records[0],
                    existing_core_matches=context["existing_core_matches"],
                )

            for previous in context["existing_core_matches"]:
                updated_previous = previous.model_copy(
                    update={
                        "version_state": CoreVersionState.SUPERSEDED,
                        "superseded_by_core_id": core_records[0].core_id,
                        "updated_at": utc_now(),
                        "updated_by": actor_id,
                        "change_reason": f"Superseded by promotion {promotion_id}.",
                    }
                )
                self.store.upsert_core_knowledge(updated_previous)

            for core_record in core_records:
                self.store.upsert_core_knowledge(core_record)

            index_sync = self._sync_promoted_core_index(
                promotion_id=promotion_id,
                domain_id=candidate.domain_id,
                source_doc_id=f"core:{core_records[0].core_id}",
                actor_id=actor_id,
            )
            final_status = (
                PromotionStatus.PROMOTED_WITH_CONDITIONS
                if candidate.approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS
                else PromotionStatus.PROMOTED
            )
            promotion = promotion.model_copy(
                update={
                    "promotion_status": final_status,
                    "source_ids": materialization_result.source_ids if materialization_result else [],
                    "passage_ids": materialization_result.passage_ids if materialization_result else [],
                    "claim_ids": materialization_result.claim_ids if materialization_result else [],
                    "rule_ids": materialization_result.rule_ids if materialization_result else [],
                    "conflict_ids": materialization_result.conflict_ids if materialization_result else [],
                    "core_ids": [item.core_id for item in core_records],
                    "previous_version_ids": [item.core_id for item in context["existing_core_matches"]],
                    "completed_at": utc_now(),
                    "index_sync_status": index_sync.status,
                }
            )
            self.store.update_promotion(promotion)

            promoted_state = (
                PromotionState.PROMOTED_WITH_CONDITIONS
                if final_status == PromotionStatus.PROMOTED_WITH_CONDITIONS
                else PromotionState.PROMOTED
            )
            updated_candidate = candidate.model_copy(
                update={
                    "promotion_state": promoted_state,
                    "updated_at": utc_now(),
                }
            )
            self.store.upsert_candidate(updated_candidate)

            self._append_ledger(
                event_type=LedgerEventType.PROMOTION_COMPLETED,
                actor_type=ActorType.ADMIN,
                actor_id=actor_id,
                action="promote_candidate",
                domain_id=updated_candidate.domain_id,
                mission_id=updated_candidate.mission_id,
                run_id=updated_candidate.run_id,
                candidate_id=updated_candidate.candidate_id,
                reason=promotion_notes,
                metadata={
                    "promotion_id": promotion_id,
                    "core_ids": [item.core_id for item in core_records],
                    "previous_version_ids": [item.core_id for item in context["existing_core_matches"]],
                    "index_sync_status": index_sync.status.value,
                },
            )
            return {
                "preflight": preflight.model_dump(mode="json"),
                "promotion": promotion.model_dump(mode="json"),
                "index_sync": index_sync.model_dump(mode="json"),
                "core_records": [item.model_dump(mode="json") for item in core_records],
            }
        except Exception as exc:
            if materialization_result is not None:
                self._astrology_promotion_materializer.rollback(materialization_result)
            else:
                self._restore_text(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS, generic_docs_snapshot)
            failed_candidate = candidate.model_copy(update={"promotion_state": PromotionState.BLOCKED, "updated_at": utc_now()})
            self.store.upsert_candidate(failed_candidate)
            failed_promotion = promotion.model_copy(
                update={
                    "promotion_status": PromotionStatus.FAILED,
                    "completed_at": utc_now(),
                }
            )
            self.store.update_promotion(failed_promotion)
            self._append_ledger(
                event_type=LedgerEventType.PROMOTION_FAILED,
                actor_type=ActorType.ADMIN,
                actor_id=actor_id,
                action="promote_candidate",
                domain_id=candidate.domain_id,
                mission_id=candidate.mission_id,
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                reason=str(exc),
                metadata={"promotion_id": promotion_id},
            )
            raise

    def rollback_promotion(
        self,
        promotion_id: str,
        *,
        actor_id: str,
        reason: str,
    ) -> dict[str, Any]:
        promotion = self.store.get_promotion(promotion_id)
        if promotion is None:
            raise KeyError(f"Unknown promotion: {promotion_id}")
        if promotion.promotion_status not in {PromotionStatus.PROMOTED, PromotionStatus.PROMOTED_WITH_CONDITIONS}:
            raise RuntimeError("Only promoted records can be rolled back")

        affected_core_ids = list(promotion.core_ids)
        restored_core_ids = list(promotion.previous_version_ids)
        for core_id in affected_core_ids:
            core = self.store.get_core_knowledge(core_id)
            if core is None:
                continue
            self.store.upsert_core_knowledge(
                core.model_copy(
                    update={
                        "version_state": CoreVersionState.WITHDRAWN,
                        "updated_at": utc_now(),
                        "updated_by": actor_id,
                        "change_reason": reason,
                    }
                )
            )
        for core_id in restored_core_ids:
            core = self.store.get_core_knowledge(core_id)
            if core is None:
                continue
            self.store.upsert_core_knowledge(
                core.model_copy(
                    update={
                        "version_state": CoreVersionState.CURRENT,
                        "superseded_by_core_id": None,
                        "updated_at": utc_now(),
                        "updated_by": actor_id,
                        "change_reason": f"Restored by rollback {promotion_id}.",
                    }
                )
            )

        self._rewrite_approved_core_docs_from_store()
        index_sync = self._sync_promoted_core_index(
            promotion_id=promotion_id,
            domain_id=promotion.domain_id,
            source_doc_id=f"rollback:{promotion_id}",
            actor_id=actor_id,
        )
        rollback = ResearchRollbackRecord(
            rollback_id=self.store.next_id("rollback", "VEDA-RRBK-"),
            promotion_id=promotion_id,
            domain_id=promotion.domain_id,
            affected_core_ids=affected_core_ids,
            restored_core_ids=restored_core_ids,
            rolled_back_by=actor_id,
            rolled_back_at=utc_now(),
            reason=reason,
        )
        self.store.insert_rollback(rollback)
        self.store.update_promotion(
            promotion.model_copy(
                update={
                    "promotion_status": PromotionStatus.ROLLED_BACK,
                    "completed_at": utc_now(),
                    "index_sync_status": index_sync.status,
                }
            )
        )
        candidate = self._require_candidate(promotion.candidate_id)
        restored_state = PromotionState.PROMOTION_READY if restored_core_ids else PromotionState.BLOCKED
        self.store.upsert_candidate(
            candidate.model_copy(update={"promotion_state": restored_state, "updated_at": utc_now()})
        )
        self._append_ledger(
            event_type=LedgerEventType.PROMOTION_ROLLED_BACK,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="rollback_promotion",
            domain_id=promotion.domain_id,
            candidate_id=promotion.candidate_id,
            reason=reason,
            metadata={
                "promotion_id": promotion_id,
                "rollback_id": rollback.rollback_id,
                "affected_core_ids": affected_core_ids,
                "restored_core_ids": restored_core_ids,
            },
        )
        return {
            "rollback": rollback.model_dump(mode="json"),
            "index_sync": index_sync.model_dump(mode="json"),
        }

    def _promotion_context(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        approval = self._latest_valid_admin_approval(candidate)
        evidence_rows = [self.store.get_evidence(item) for item in candidate.evidence_ids]
        evidence_rows = [item for item in evidence_rows if item is not None]
        observations = []
        seen_observation_ids: set[str] = set()
        for evidence in evidence_rows:
            observation = self.store.get_observation(evidence.observation_id)
            if observation is None or observation.observation_id in seen_observation_ids:
                continue
            seen_observation_ids.add(observation.observation_id)
            observations.append(observation)
        return {
            "candidate": candidate,
            "approval": approval,
            "evidence_rows": evidence_rows,
            "observations": observations,
            "conflicts": self.store.list_conflicts_for_candidate(candidate_id),
            "existing_core_matches": self._find_existing_core_matches(candidate),
        }

    def _latest_valid_admin_approval(self, candidate: ResearchCandidateRecord) -> ResearchApprovalRecord:
        approvals = self.store.list_approvals_for_candidate(candidate.candidate_id)
        approved_statuses = {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS}
        for approval in reversed(approvals):
            if approval.actor_type != ActorType.ADMIN:
                continue
            if approval.status not in approved_statuses:
                continue
            return approval
        raise RuntimeError(f"Candidate {candidate.candidate_id} does not have a valid admin approval for promotion")

    def _find_existing_core_matches(self, candidate: ResearchCandidateRecord) -> list[ResearchCoreKnowledgeRecord]:
        current_records = self.store.list_core_knowledge(candidate.domain_id)
        matched: list[ResearchCoreKnowledgeRecord] = []
        matched_ids: set[str] = set()
        for core_id in candidate.existing_knowledge_matches:
            record = self.store.get_core_knowledge(core_id)
            if record is None or record.domain_id != candidate.domain_id:
                continue
            if record.core_id not in matched_ids:
                matched.append(record)
                matched_ids.add(record.core_id)
        for record in current_records:
            if record.core_id in matched_ids:
                continue
            if record.normalized_claim == candidate.normalized_claim or record.topic_key == candidate.topic_key:
                matched.append(record)
                matched_ids.add(record.core_id)
        return matched

    def _build_promotion_preflight(
        self,
        *,
        candidate: ResearchCandidateRecord,
        approval: ResearchApprovalRecord,
        evidence_rows: list[ResearchEvidenceRecord],
        observations: list[SourceObservationRecord],
        conflicts: list[ResearchConflictRecord],
        existing_core_matches: list[ResearchCoreKnowledgeRecord],
        promotion_id: str | None,
    ) -> ResearchPromotionPreflightRecord:
        approved_states = {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS}
        checks: list[dict[str, Any]] = []
        blocking_reasons: list[str] = []
        warnings: list[str] = []
        required_actions: list[str] = []
        status = PromotionPreflightStatus.PASS

        def add_check(code: str, passed: bool, message: str, *, conditional: bool = False, blocking: bool = False) -> None:
            nonlocal status
            check_status = "PASS"
            if blocking and not passed:
                check_status = "BLOCKED"
                status = PromotionPreflightStatus.BLOCKED
                blocking_reasons.append(message)
            elif conditional or not passed:
                check_status = "PASS_WITH_CONDITIONS"
                if status != PromotionPreflightStatus.BLOCKED:
                    status = PromotionPreflightStatus.PASS_WITH_CONDITIONS
                warnings.append(message)
            checks.append({"code": code, "status": check_status, "message": message})

        eligible_state = candidate.promotion_state in {PromotionState.PROMOTION_READY, PromotionState.BLOCKED}
        add_check(
            "P1",
            candidate.approval_status in approved_states and eligible_state,
            "Candidate must be admin-approved and in PROMOTION_READY before promotion.",
            blocking=True,
        )
        add_check(
            "P2",
            approval.actor_type == ActorType.ADMIN and approval.status in approved_states,
            "Promotion requires a valid human Admin approval record.",
            blocking=True,
        )

        evidence_complete = len(evidence_rows) == len(candidate.evidence_ids) and bool(evidence_rows)
        add_check(
            "P3",
            evidence_complete,
            "Promotion requires intact evidence linkage for every referenced evidence record.",
            blocking=True,
        )

        accepted_observations = [item for item in observations if item.access_status == SourceAccessStatus.ACCEPTED]
        evidentiary_observations = [item for item in accepted_observations if not bool(item.domain_metadata.get("discovery_only"))]
        add_check(
            "P4",
            bool(evidentiary_observations),
            "Promotion requires at least one accepted evidentiary source; discovery-only sources cannot independently justify promotion.",
            blocking=True,
        )
        if any(bool(item.domain_metadata.get("discovery_only")) for item in observations):
            required_actions.append("Retain discovery-only sources as lineage, but ensure they are not the sole evidentiary basis for promotion.")

        evidence_observation_ids = {item.observation_id for item in evidence_rows}
        add_check(
            "P5",
            evidence_observation_ids.issubset({item.observation_id for item in observations}),
            "Each evidence record must resolve to an observed source.",
            blocking=True,
        )

        normalized_live = re.sub(r"[^a-z0-9]+", " ", candidate.normalized_claim.strip().lower())
        normalized_live = re.sub(r"\s+", " ", normalized_live).strip()
        normalized_expected = re.sub(r"[^a-z0-9]+", " ", candidate.claim.strip().lower())
        normalized_expected = re.sub(r"\s+", " ", normalized_expected).strip()
        add_check(
            "P6",
            normalized_live == normalized_expected,
            "Normalized claim differs from the raw claim text normalization and should be reviewed.",
            conditional=normalized_live != normalized_expected,
        )

        plugin = self.domain_plugins.get(candidate.domain_id)
        ontology_mapping = plugin.map_ontology(candidate.claim, candidate.metadata) if hasattr(plugin, "map_ontology") else {"ontology_matches": [], "ontology_gaps": []}
        ontology_gaps = list(ontology_mapping.get("ontology_gaps", []))
        add_check(
            "P7",
            not ontology_gaps,
            "Ontology gaps remain and must be preserved during promotion.",
            conditional=bool(ontology_gaps),
        )
        if ontology_gaps:
            required_actions.append(f"Preserve ontology gaps: {', '.join(ontology_gaps[:6])}")

        unresolved_conflicts = [item for item in conflicts if item.resolution_status == ConflictResolutionStatus.UNRESOLVED]
        high_stakes = candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL}
        conflict_blocking = high_stakes and bool(unresolved_conflicts)
        add_check(
            "P8",
            not unresolved_conflicts or not conflict_blocking,
            "Unresolved conflicts remain attached to this candidate.",
            conditional=bool(unresolved_conflicts) and not conflict_blocking,
            blocking=conflict_blocking,
        )

        add_check(
            "P9",
            True,
            "Existing core overlap evaluated for merge/version impact.",
            conditional=bool(existing_core_matches),
        )
        add_check(
            "P10",
            True,
            "Version impact assessed for non-destructive supersession.",
            conditional=bool(existing_core_matches),
        )

        add_check(
            "P11",
            not high_stakes or approval.status == ApprovalStatus.APPROVED_WITH_CONDITIONS,
            "High-stakes promotions should remain conditional and preserve output safety limits.",
            conditional=high_stakes and approval.status != ApprovalStatus.APPROVED_WITH_CONDITIONS,
        )
        add_check("P12", True, "Schema validation uses the existing governed platform and P002/P003 models.")

        proposed_operation = "ADD_CORE_KNOWLEDGE"
        if existing_core_matches:
            proposed_operation = "MERGE_VERSION_UPDATE"
        elif approval.status == ApprovalStatus.APPROVED_WITH_CONDITIONS or unresolved_conflicts:
            proposed_operation = "PROMOTE_WITH_CONDITIONS"

        return ResearchPromotionPreflightRecord(
            preflight_id=self.store.next_id("preflight", "VEDA-RPFL-"),
            candidate_id=candidate.candidate_id,
            domain_id=candidate.domain_id,
            approval_id=approval.approval_id,
            promotion_id=promotion_id,
            status=status,
            proposed_operation=proposed_operation,
            checks=checks,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            required_actions=required_actions,
            source_ids=list(candidate.source_ids),
            evidence_ids=list(candidate.evidence_ids),
            existing_core_ids=[item.core_id for item in existing_core_matches],
            high_stakes=high_stakes,
            created_at=utc_now(),
        )

    def _create_generic_core_record(
        self,
        *,
        core_id: str,
        candidate: ResearchCandidateRecord,
        approval: ResearchApprovalRecord,
        promotion_id: str,
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
            approval_status=approval.status,
            confidence=candidate.confidence,
            candidate_id=candidate.candidate_id,
            approval_id=approval.approval_id,
            promotion_id=promotion_id,
            version=self._increment_semver(previous.version if previous else None),
            version_state=CoreVersionState.CURRENT,
            supersedes_core_id=previous.core_id if previous else None,
            retrieval_classification="APPROVED_CORE",
            high_stakes=candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL},
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
                "predecessor_core_ids": [item.core_id for item in existing_core_matches],
            },
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    def _write_generic_core_docs(
        self,
        *,
        candidate: ResearchCandidateRecord,
        new_core_record: ResearchCoreKnowledgeRecord,
        existing_core_matches: list[ResearchCoreKnowledgeRecord],
    ) -> None:
        docs = self._load_core_docs()
        superseded = {item.core_id for item in existing_core_matches}
        survivors = []
        for doc in docs:
            meta = doc.get("meta", {}) if isinstance(doc.get("meta"), dict) else {}
            core_id = str(meta.get("core_id") or "").strip()
            if core_id and core_id in superseded:
                continue
            if core_id == new_core_record.core_id:
                continue
            survivors.append(doc)
        survivors.append(self._generic_core_doc_from_record(new_core_record, candidate))
        self._write_jsonl_docs(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS, survivors)

    def _sync_promoted_core_index(
        self,
        *,
        promotion_id: str,
        domain_id: str,
        source_doc_id: str,
        actor_id: str,
    ) -> ResearchIndexSyncRecord:
        result = refresh_unified_retrieval_assets(reason="approved_core_promotion", source_doc_id=source_doc_id)
        status = IndexSyncStatus.SUCCESS if result.get("ok") else IndexSyncStatus.FAILED
        index_sync = ResearchIndexSyncRecord(
            index_sync_id=self.store.next_id("index_sync", "VEDA-RIDX-"),
            promotion_id=promotion_id,
            domain_id=domain_id,
            status=status,
            created_at=utc_now(),
            completed_at=utc_now(),
            result=result,
        )
        self.store.insert_index_sync(index_sync)
        self._append_ledger(
            event_type=LedgerEventType.INDEX_SYNC_COMPLETED if status == IndexSyncStatus.SUCCESS else LedgerEventType.INDEX_SYNC_PENDING,
            actor_type=ActorType.SYSTEM,
            actor_id="unified_runtime_sync",
            action="sync_promoted_core_index",
            domain_id=domain_id,
            metadata={
                "promotion_id": promotion_id,
                "index_sync_id": index_sync.index_sync_id,
                "status": status.value,
                "result": result,
            },
        )
        return index_sync

    def _rewrite_approved_core_docs_from_store(self) -> None:
        docs = []
        for domain in self.store.list_domains():
            for record in self.store.list_core_knowledge(domain.domain_id):
                docs.append(self._core_doc_from_record(record))
        docs.sort(key=lambda item: str((item.get("meta") or {}).get("saved_at") or ""))
        self._write_jsonl_docs(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS, docs)

    def _load_core_docs(self) -> list[dict[str, Any]]:
        path = Path(cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS)
        if not path.exists():
            return []
        docs = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                docs.append(json.loads(line))
        return docs

    def _write_jsonl_docs(self, path_like: Path | str, docs: list[dict[str, Any]]) -> None:
        path = Path(path_like)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            for item in docs:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _core_doc_from_record(self, record: ResearchCoreKnowledgeRecord) -> dict[str, Any]:
        if record.domain_id == self.vedic_astrology_plugin.domain_id:
            source_map = self._load_astrology_source_map()
            sources = []
            for source_id in record.source_ids:
                source = source_map.get(source_id)
                if source is None:
                    continue
                sources.append(
                    {
                        "title": source.get("title_normalized"),
                        "url": source.get("digital_source"),
                        "published_at": source.get("publication_year"),
                        "source_class": source.get("source_class"),
                        "verification_status": source.get("verification_status"),
                    }
                )
            return {
                "doc_id": f"veda_core_{record.core_id.lower().replace('-', '_')}",
                "domain": "ASTROLOGY",
                "entity": record.title,
                "text": record.claim,
                "meta": {
                    "memory_type": "approved_core",
                    "governance_zone": "APPROVED_CORE",
                    "saved_at": record.updated_at,
                    "promoted_at": record.updated_at,
                    "summary": record.claim,
                    "intent": "ASTROLOGY",
                    "topic_key": record.topic_key,
                    "core_id": record.core_id,
                    "candidate_id": record.candidate_id,
                    "approval_id": record.approval_id,
                    "promotion_id": record.promotion_id,
                    "source_ids": record.source_ids,
                    "passage_ids": record.passage_ids,
                    "claim_ids": record.claim_ids,
                    "rule_ids": record.rule_ids,
                    "conflict_ids": record.conflict_ids,
                    "research_sources": sources,
                    "version": record.version,
                    "version_state": record.version_state.value,
                    "high_stakes": record.high_stakes,
                    "tags": ["astrology", "approved_core"],
                },
            }
        return {
            "doc_id": f"veda_core_{record.core_id.lower().replace('-', '_')}",
            "domain": record.domain_id,
            "entity": record.title,
            "text": record.claim,
            "meta": {
                "memory_type": "approved_core",
                "governance_zone": "APPROVED_CORE",
                "saved_at": record.updated_at,
                "promoted_at": record.updated_at,
                "summary": record.claim,
                "intent": record.domain_id,
                "topic_key": record.topic_key,
                "core_id": record.core_id,
                "candidate_id": record.candidate_id,
                "approval_id": record.approval_id,
                "promotion_id": record.promotion_id,
                "source_ids": record.source_ids,
                "passage_ids": record.passage_ids,
                "claim_ids": record.claim_ids,
                "rule_ids": record.rule_ids,
                "conflict_ids": record.conflict_ids,
                "version": record.version,
                "version_state": record.version_state.value,
                "high_stakes": record.high_stakes,
                "tags": [record.domain_id.lower(), "approved_core"],
            },
        }

    def _load_astrology_source_map(self) -> dict[str, dict[str, Any]]:
        path = Path(cfg.VEDA_ASTROLOGY_SOURCE_DIR)
        if not path.exists():
            return {}
        records: dict[str, dict[str, Any]] = {}
        for file_path in sorted(path.glob("*.json")):
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            source_id = str(payload.get("source_id") or "").strip()
            if source_id:
                records[source_id] = payload
        return records

    def _read_text_if_exists(self, path_like: Path | str) -> str | None:
        path = Path(path_like)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _restore_text(self, path_like: Path | str, content: str | None) -> None:
        path = Path(path_like)
        if content is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _increment_semver(self, value: str | None) -> str:
        raw = str(value or "1.0.0").strip() or "1.0.0"
        try:
            major, minor, patch = [int(part) for part in raw.split(".", 2)]
        except Exception:
            return "1.0.0"
        return f"{major}.{minor}.{patch + 1}"

    def _next_core_id(self) -> str:
        highest = 0
        for record in self.store.list_all_core_knowledge():
            try:
                highest = max(highest, int(str(record.core_id).rsplit("-", 1)[-1]))
            except Exception:
                continue
        return f"VEDA-RCORE-{highest + 1:06d}"

    def _generic_core_doc_from_record(self, record: ResearchCoreKnowledgeRecord, candidate: ResearchCandidateRecord) -> dict[str, Any]:
        return {
            "doc_id": f"veda_core_{record.core_id.lower().replace('-', '_')}",
            "domain": candidate.domain_id,
            "entity": record.title,
            "text": record.claim,
            "meta": {
                "memory_type": "approved_core",
                "governance_zone": "APPROVED_CORE",
                "saved_at": record.updated_at,
                "promoted_at": record.updated_at,
                "summary": record.claim,
                "intent": candidate.domain_id,
                "topic_key": record.topic_key,
                "core_id": record.core_id,
                "candidate_id": record.candidate_id,
                "approval_id": record.approval_id,
                "promotion_id": record.promotion_id,
                "source_ids": record.source_ids,
                "passage_ids": record.passage_ids,
                "claim_ids": record.claim_ids,
                "rule_ids": record.rule_ids,
                "conflict_ids": record.conflict_ids,
                "version": record.version,
                "version_state": record.version_state.value,
                "high_stakes": record.high_stakes,
                "tags": [candidate.domain_id.lower(), "approved_core"],
            },
        }

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

    def archive_mission(self, mission_id: str, *, actor_id: str = "admin", notes: str | None = None) -> ResearchMissionRecord:
        mission = self._require_mission(mission_id)
        updated = mission.model_copy(
            update={
                "status": MissionStatus.ARCHIVED,
                "updated_at": utc_now(),
                "notes": notes or mission.notes,
            }
        )
        self.store.update_mission(updated)
        self._append_ledger(
            event_type=LedgerEventType.MISSION_PAUSED,
            actor_type=ActorType.ADMIN,
            actor_id=actor_id,
            action="archive_mission",
            domain_id=updated.domain_id,
            mission_id=updated.mission_id,
            before_state=mission.model_dump(mode="json"),
            after_state=updated.model_dump(mode="json"),
            reason=notes,
        )
        return updated

    def dashboard_bundle(self, *, domain_id: str | None = None) -> dict[str, Any]:
        dashboard = self.dashboard().model_dump(mode="json")
        domains = [item for item in self.list_domains() if domain_id in {None, item.domain_id}]
        missions = [item for item in self.list_missions() if domain_id in {None, item.domain_id}]
        runs = [item for item in self.list_runs() if domain_id in {None, item.domain_id}]
        observations = [item for item in self.store.list_observations() if domain_id in {None, self._domain_for_run(item.run_id)}]
        evidence = [item for item in self.store.list_evidence() if domain_id in {None, item.domain_id}]
        candidates = [item for item in self.store.list_candidates() if domain_id in {None, item.domain_id}]
        conflicts = [item for item in self.store.list_conflicts() if any(candidate.candidate_id == item.candidate_id for candidate in candidates)]
        dashboard["engine_status"] = self._engine_status()
        dashboard["active_domains"] = sum(1 for item in domains if item.status.value == "ACTIVE")
        dashboard["active_missions"] = sum(1 for item in missions if item.status == MissionStatus.ACTIVE)
        dashboard["runs_today"] = sum(1 for item in runs if item.started_at.startswith(utc_now()[:10]))
        dashboard["successful_runs"] = sum(1 for item in runs if item.status == RunStatus.SUCCESS)
        dashboard["failed_runs"] = sum(1 for item in runs if item.status == RunStatus.FAILED)
        dashboard["sources_today"] = sum(1 for item in observations if item.retrieved_at.startswith(utc_now()[:10]))
        dashboard["new_candidates"] = sum(1 for item in candidates if item.created_at.startswith(utc_now()[:10]))
        dashboard["pending_approvals"] = sum(1 for item in candidates if item.approval_status == ApprovalStatus.PENDING)
        dashboard["approved_today"] = self._count_today_approvals(
            {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS},
            domain_id=domain_id,
        )
        dashboard["rejected_today"] = self._count_today_approvals(
            {ApprovalStatus.REJECTED, ApprovalStatus.ARCHIVED},
            domain_id=domain_id,
        )
        dashboard["needs_more_research"] = sum(
            1
            for item in candidates
            if item.approval_status == ApprovalStatus.NEEDS_MORE_RESEARCH
        )
        dashboard["high_priority_conflicts"] = sum(
            1
            for item in candidates
            if item.priority in {MissionPriority.P0, MissionPriority.P1}
            and item.contradiction_status != ContradictionStatus.NONE
        )
        dashboard["last_research_run"] = self._latest_run_timestamp(domain_id=domain_id)
        dashboard["next_expected_run"] = self._next_expected_run(domain_id=domain_id)
        dashboard["backlog_state"] = self.backlog_state()
        dashboard["runtime_controls"] = self.platform_runtime_state()
        dashboard["metrics"] = {
            "missions_active": dashboard["active_missions"],
            "runs_total": len(runs),
            "runs_failed": dashboard["failed_runs"],
            "sources_discovered": len(observations),
            "sources_rejected": sum(1 for item in observations if item.access_status != SourceAccessStatus.ACCEPTED),
            "evidence_created": len(evidence),
            "candidates_created": len(candidates),
            "candidate_duplicates": sum(1 for item in candidates if item.support_count > 1),
            "contradictions_found": len(conflicts),
            "pending_reviews": dashboard["pending_approvals"],
            "approvals": self._count_approval_total(
                {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS},
                domain_id=domain_id,
            ),
            "rejections": self._count_approval_total({ApprovalStatus.REJECTED}, domain_id=domain_id),
            "follow_ups": sum(1 for item in missions if item.parent_candidate_id is not None),
        }
        return {
            **dashboard,
            "domains": [item.model_dump(mode="json") for item in domains],
            "provider_health": self._provider_health_rows(),
            "external_web_research_status": self._external_web_research_status(),
            "daily_digest": next((item for item in self.list_digests(digest_type="DAILY", limit=1)), None),
            "weekly_digest": next((item for item in self.list_digests(digest_type="WEEKLY", limit=1)), None),
            "knowledge_gaps": self.knowledge_gap_rows(domain_id=domain_id),
            "notifications": self.notification_rows(domain_id=domain_id),
            "analytics": self.analytics_bundle(domain_id=domain_id),
            "coverage": self.coverage_rows(domain_id=domain_id),
        }

    def list_mission_rows(
        self,
        *,
        domain_id: str | None = None,
        status: str | None = None,
        research_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        runs = self.store.list_runs()
        candidates = self.store.list_candidates()
        schedules = {item.schedule_id: item for item in self.store.list_schedules()}
        missions = []
        for mission in self.store.list_missions():
            if domain_id and mission.domain_id != domain_id:
                continue
            if status and mission.status.value != status:
                continue
            if research_type and mission.research_type.value != research_type:
                continue
            if search and search.lower() not in " ".join(
                filter(None, [mission.title, mission.objective, mission.notes or ""])
            ).lower():
                continue
            mission_runs = [item for item in runs if item.mission_id == mission.mission_id]
            mission_candidates = [item for item in candidates if item.mission_id == mission.mission_id]
            mission_schedule = schedules.get(mission.schedule_id) if mission.schedule_id else None
            missions.append(
                {
                    **mission.model_dump(mode="json"),
                    "last_run": mission.last_run_at,
                    "next_run": mission_schedule.next_run_at if mission_schedule else None,
                    "candidate_count": len(mission_candidates),
                    "open_conflicts": sum(
                        1 for item in mission_candidates if item.contradiction_status != ContradictionStatus.NONE
                    ),
                    "follow_up_mission_count": sum(
                        1 for item in self.store.list_missions() if item.parent_mission_id == mission.mission_id
                    ),
                }
            )
        missions.sort(key=lambda item: (item["priority"], item["updated_at"], item["mission_id"]))
        paged, total = self._paginate(missions, page=page, per_page=per_page)
        return {"missions": paged, "total": total, "page": page, "per_page": per_page, "returned": len(paged)}

    def get_mission_detail(self, mission_id: str) -> dict[str, Any]:
        mission = self._require_mission(mission_id)
        runs = [item.model_dump(mode="json") for item in self.store.list_runs_for_mission(mission_id)]
        candidates = [
            self._candidate_summary(item)
            for item in self.store.list_candidates()
            if item.mission_id == mission_id
        ]
        follow_up_missions = [
            item.model_dump(mode="json")
            for item in self.store.list_missions()
            if item.parent_mission_id == mission_id or item.parent_candidate_id in {row["candidate_id"] for row in candidates}
        ]
        schedule = self.store.get_schedule(mission.schedule_id) if mission.schedule_id else None
        ledger = [
            item.model_dump(mode="json")
            for item in self.store.list_ledger_events()
            if item.mission_id == mission_id
        ]
        return {
            "mission": mission.model_dump(mode="json"),
            "schedule": schedule.model_dump(mode="json") if schedule else None,
            "run_history": runs,
            "candidate_history": candidates,
            "follow_up_missions": follow_up_missions,
            "ledger": ledger,
            "open_conflicts": sum(1 for item in candidates if item["contradiction_status"] != ContradictionStatus.NONE.value),
        }

    def list_run_rows(
        self,
        *,
        domain_id: str | None = None,
        mission_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
        include_sources: bool = False,
    ) -> dict[str, Any]:
        mission_lookup = {item.mission_id: item for item in self.store.list_missions()}
        runs = []
        source_rows: list[dict[str, Any]] = []
        for run in self.store.list_runs():
            if domain_id and run.domain_id != domain_id:
                continue
            if mission_id and run.mission_id != mission_id:
                continue
            if status and run.status.value != status:
                continue
            mission = mission_lookup.get(run.mission_id)
            provider_id = str(mission.query_strategy.get("provider_id")) if mission else None
            run_rows = self.store.list_observations_for_run(run.run_id)
            run_scope = self._run_scope_for_run(run, mission=mission, observations=run_rows)
            if include_sources:
                source_rows.extend(self._source_summary(item) for item in run_rows)
            runs.append(
                {
                    **run.model_dump(mode="json"),
                    "mission_title": mission.title if mission else run.mission_id,
                    "provider_id": provider_id,
                    "retrieval_provider_id": str(mission.query_strategy.get("retrieval_provider_id")) if mission else None,
                    "run_scope": run_scope,
                    "duration_seconds": self._duration_seconds(run.started_at, run.completed_at),
                }
            )
        runs.sort(key=lambda item: (item["started_at"], item["run_id"]), reverse=True)
        paged, total = self._paginate(runs, page=page, per_page=per_page)
        payload = {"runs": paged, "total": total, "page": page, "per_page": per_page, "returned": len(paged)}
        if include_sources:
            payload["sources"] = source_rows
        return payload

    def get_run_detail(self, run_id: str) -> dict[str, Any]:
        run = self._require_run(run_id)
        mission = self._require_mission(run.mission_id)
        observations = self.store.list_observations_for_run(run_id)
        evidence = [item for item in self.store.list_evidence() if item.run_id == run_id]
        candidates = [item for item in self.store.list_candidates() if item.run_id == run_id]
        ledger = [item for item in self.store.list_ledger_events() if item.run_id == run_id]
        return {
            "run": {
                **run.model_dump(mode="json"),
                "provider_id": str(mission.query_strategy.get("provider_id") or ""),
                "retrieval_provider_id": str(mission.query_strategy.get("retrieval_provider_id") or ""),
                "run_scope": self._run_scope_for_run(run, mission=mission, observations=observations),
                "duration_seconds": self._duration_seconds(run.started_at, run.completed_at),
            },
            "mission": mission.model_dump(mode="json"),
            "observations": [self._source_summary(item) for item in observations],
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "candidates": [self._candidate_summary(item) for item in candidates],
            "timeline": [item.model_dump(mode="json") for item in ledger],
        }

    def list_candidate_rows(
        self,
        *,
        domain_id: str | None = None,
        approval_status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        contradiction_only: bool = False,
        high_stakes_only: bool = False,
        promotion_state: str | None = None,
        sort_by: str = "updated_at",
        sort_dir: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        candidates = []
        for candidate in self.store.list_candidates():
            if domain_id and candidate.domain_id != domain_id:
                continue
            if approval_status and candidate.approval_status.value != approval_status:
                continue
            if priority and candidate.priority.value != priority:
                continue
            if promotion_state and candidate.promotion_state.value != promotion_state:
                continue
            if contradiction_only and candidate.contradiction_status == ContradictionStatus.NONE:
                continue
            if high_stakes_only and candidate.safety_class not in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL}:
                continue
            if search and search.lower() not in " ".join(
                filter(None, [candidate.title, candidate.claim, candidate.topic_key])
            ).lower():
                continue
            candidates.append(self._candidate_summary(candidate))
        reverse = sort_dir.lower() != "asc"
        candidates.sort(key=lambda item: self._candidate_sort_key(item, sort_by), reverse=reverse)
        paged, total = self._paginate(candidates, page=page, per_page=per_page)
        return {"candidates": paged, "total": total, "page": page, "per_page": per_page, "returned": len(paged)}

    def get_candidate_review_bundle(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        mission = self._require_mission(candidate.mission_id)
        run = self._require_run(candidate.run_id)
        evidence_rows = [self.store.get_evidence(item) for item in candidate.evidence_ids]
        evidence_rows = [item for item in evidence_rows if item is not None]
        observations = [self.store.get_observation(item.observation_id) for item in evidence_rows]
        observations = [item for item in observations if item is not None]
        validations = self.store.list_validations_for_candidate(candidate_id)
        approvals = self.store.list_approvals_for_candidate(candidate_id)
        conflicts = self.store.list_conflicts_for_candidate(candidate_id)
        preflights = self.store.list_promotion_preflights_for_candidate(candidate_id)
        promotions = self.store.list_promotions_for_candidate(candidate_id)
        rollbacks = [
            rollback.model_dump(mode="json")
            for promotion in promotions
            for rollback in self.store.list_rollbacks_for_promotion(promotion.promotion_id)
        ]
        index_sync = [
            sync.model_dump(mode="json")
            for promotion in promotions
            for sync in self.store.list_index_sync_for_promotion(promotion.promotion_id)
        ]
        core_ids = []
        for promotion in promotions:
            core_ids.extend(promotion.core_ids)
            core_ids.extend(promotion.previous_version_ids)
        core_history = []
        for core_id in dict.fromkeys(core_ids):
            record = self.store.get_core_knowledge(core_id)
            if record is not None:
                core_history.append(record.model_dump(mode="json"))
        related_candidates = [
            self._candidate_summary(item)
            for item in self.store.find_candidates_by_topic(candidate.domain_id, candidate.topic_key)
            if item.candidate_id != candidate.candidate_id
        ]
        follow_up_missions = [
            item.model_dump(mode="json")
            for item in self.store.list_missions()
            if item.parent_candidate_id == candidate_id
        ]
        ledger = [item.model_dump(mode="json") for item in self.store.list_ledger_for_candidate(candidate_id)]
        source_index = {item.observation_id: item for item in observations}
        evidence_view = []
        for evidence in evidence_rows:
            observation = source_index.get(evidence.observation_id)
            evidence_view.append(
                {
                    **evidence.model_dump(mode="json"),
                    "source": self._source_summary(observation) if observation else None,
                    "presentation": {
                        "source_text": observation.raw_reference.get("original_text") if observation else None,
                        "translation": evidence.passage,
                        "model_summary": evidence.claim_hint,
                        "model_inference": bool(evidence.domain_metadata.get("inference")),
                    },
                }
            )
        return {
            "candidate": self._candidate_summary(candidate),
            "mission": mission.model_dump(mode="json"),
            "run": run.model_dump(mode="json"),
            "evidence_summary": evidence_view,
            "source_observations": [self._source_summary(item) for item in observations],
            "validation_summary": [item.model_dump(mode="json") for item in validations],
            "approval_history": [item.model_dump(mode="json") for item in approvals],
            "conflicts": [item.model_dump(mode="json") for item in conflicts],
            "promotion_preflights": [item.model_dump(mode="json") for item in preflights],
            "promotion_history": [item.model_dump(mode="json") for item in promotions],
            "rollback_history": rollbacks,
            "index_sync_history": index_sync,
            "core_history": core_history,
            "related_candidates": related_candidates,
            "follow_up_missions": follow_up_missions,
            "ledger": ledger,
            "novelty": candidate.novelty_status.value,
            "contradiction": candidate.contradiction_status.value,
            "confidence": candidate.confidence.model_dump(mode="json"),
            "current_knowledge_comparison": dict(candidate.metadata.get("current_knowledge_comparison", {})),
            "status": candidate.approval_status.value,
        }

    def list_ledger_rows(
        self,
        *,
        limit: int = 200,
        page: int = 1,
        domain_id: str | None = None,
        mission_id: str | None = None,
        run_id: str | None = None,
        candidate_id: str | None = None,
        event_type: str | None = None,
        actor_type: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        rows = []
        for event in self.store.list_ledger_events():
            if domain_id and event.domain_id != domain_id:
                continue
            if mission_id and event.mission_id != mission_id:
                continue
            if run_id and event.run_id != run_id:
                continue
            if candidate_id and event.candidate_id != candidate_id:
                continue
            if event_type and event.event_type.value != event_type:
                continue
            if actor_type and event.actor_type.value != actor_type:
                continue
            if search and search.lower() not in json.dumps(event.model_dump(mode="json")).lower():
                continue
            rows.append(event.model_dump(mode="json"))
        rows.sort(key=lambda item: (item["timestamp"], item["event_id"]), reverse=True)
        paged, total = self._paginate(rows, page=page, per_page=limit)
        return {"events": paged, "returned": len(paged), "total": total, "page": page, "per_page": limit}

    def list_schedule_rows(self, *, domain_id: str | None = None) -> dict[str, Any]:
        missions = {item.mission_id: item for item in self.store.list_missions()}
        schedules = []
        for schedule in self.store.list_schedules():
            if domain_id and schedule.domain_id != domain_id:
                continue
            mission = missions.get(schedule.mission_id)
            schedules.append(
                {
                    **schedule.model_dump(mode="json"),
                    "mission_title": mission.title if mission else schedule.mission_id,
                    "mission_status": mission.status.value if mission else None,
                }
            )
        return {"schedules": schedules, "returned": len(schedules)}

    def notification_rows(self, *, domain_id: str | None = None) -> list[dict[str, Any]]:
        candidates = [item for item in self.store.list_candidates() if domain_id in {None, item.domain_id}]
        missions = [item for item in self.store.list_missions() if domain_id in {None, item.domain_id}]
        runs = [item for item in self.store.list_runs() if domain_id in {None, item.domain_id}]
        notifications: list[dict[str, Any]] = []
        seen: set[str] = set()

        def push(kind: str, entity_id: str, message: str, priority: str, target: str) -> None:
            key = f"{kind}:{entity_id}:{message}"
            if key in seen:
                return
            seen.add(key)
            notifications.append(
                {
                    "id": key,
                    "kind": kind,
                    "entity_id": entity_id,
                    "message": message,
                    "priority": priority,
                    "target": target,
                }
            )

        for candidate in candidates:
            if candidate.approval_status == ApprovalStatus.PENDING and candidate.priority in {MissionPriority.P0, MissionPriority.P1}:
                push("NEW_HIGH_PRIORITY_CANDIDATE", candidate.candidate_id, f"{candidate.title} awaits review.", candidate.priority.value, "queue")
            if candidate.contradiction_status != ContradictionStatus.NONE:
                push("NEW_CONTRADICTION", candidate.candidate_id, f"{candidate.title} carries an unresolved contradiction.", candidate.priority.value, "contradictions")
            if candidate.support_count > 1:
                push("CANDIDATE_ENRICHED", candidate.candidate_id, f"{candidate.title} received additional evidence.", candidate.priority.value, "queue")
            if candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL}:
                push("HIGH_STAKES_CANDIDATE", candidate.candidate_id, f"{candidate.title} requires explicit high-stakes review.", candidate.priority.value, "queue")
        for run in runs:
            if run.status == RunStatus.FAILED:
                push("RUN_FAILED", run.run_id, f"Research run {run.run_id} failed.", "P1", "runs")
        mission_failures: dict[str, int] = {}
        for run in runs:
            if run.status == RunStatus.FAILED:
                mission_failures[run.mission_id] = mission_failures.get(run.mission_id, 0) + 1
        for mission in missions:
            if mission_failures.get(mission.mission_id, 0) >= 2:
                push("MISSION_REPEATED_FAILURE", mission.mission_id, f"{mission.title} has repeated run failures.", mission.priority.value, "missions")
        return notifications

    def analytics_bundle(self, *, domain_id: str | None = None) -> dict[str, Any]:
        candidates = [item for item in self.store.list_candidates() if domain_id in {None, item.domain_id}]
        missions = [item for item in self.store.list_missions() if domain_id in {None, item.domain_id}]
        runs = [item for item in self.store.list_runs() if domain_id in {None, item.domain_id}]
        approvals = self.store.list_approvals()
        source_rows = [item for item in self.store.list_observations() if domain_id in {None, self._domain_for_run(item.run_id)}]
        domain_candidate_ids = {item.candidate_id for item in candidates}
        filtered_approvals = [item for item in approvals if item.candidate_id in domain_candidate_ids]
        approved_count = sum(1 for item in filtered_approvals if item.status in {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS})
        rejected_count = sum(1 for item in filtered_approvals if item.status == ApprovalStatus.REJECTED)
        avg_review_age_days = round(
            sum(self._age_days(item.created_at) for item in candidates if item.approval_status == ApprovalStatus.PENDING) /
            max(1, sum(1 for item in candidates if item.approval_status == ApprovalStatus.PENDING)),
            2,
        )
        quality_buckets: dict[str, int] = {}
        for row in source_rows:
            label = str(row.domain_metadata.get("source_class") or row.source_type.value)
            quality_buckets[label] = quality_buckets.get(label, 0) + 1
        return {
            "research_volume": {
                "missions": len(missions),
                "runs": len(runs),
                "sources": len(source_rows),
                "candidates": len(candidates),
            },
            "approval_rate": approved_count,
            "rejection_rate": rejected_count,
            "contradiction_rate": sum(1 for item in candidates if item.contradiction_status != ContradictionStatus.NONE),
            "legacy_rule_provenance_progress": self._legacy_progress(domain_id=domain_id),
            "average_review_age_days": avg_review_age_days,
            "mission_success_failure": {
                "successful_runs": sum(1 for item in runs if item.status == RunStatus.SUCCESS),
                "failed_runs": sum(1 for item in runs if item.status == RunStatus.FAILED),
            },
            "source_quality": quality_buckets,
        }

    def coverage_rows(self, *, domain_id: str | None = None) -> list[dict[str, Any]]:
        if domain_id and domain_id != self.vedic_astrology_plugin.domain_id:
            return []
        if hasattr(self.vedic_astrology_plugin, "build_coverage_matrix"):
            return self.vedic_astrology_plugin.build_coverage_matrix()
        return []

    def knowledge_gap_rows(self, *, domain_id: str | None = None) -> list[dict[str, Any]]:
        if domain_id and domain_id != self.vedic_astrology_plugin.domain_id:
            return []
        if not hasattr(self.vedic_astrology_plugin, "generate_gap_missions"):
            return []
        existing_missions = self.store.list_missions()
        candidates = self.store.list_candidates()
        rows = []
        for item in self.vedic_astrology_plugin.generate_gap_missions(limit=16):
            gap_id = next(iter(item.get("known_gap_ids", [])), None)
            gap_missions = [mission for mission in existing_missions if gap_id and gap_id in mission.known_gap_ids]
            gap_candidates = [candidate for candidate in candidates if candidate.mission_id in {mission.mission_id for mission in gap_missions}]
            rows.append(
                {
                    "gap_id": gap_id,
                    "domain": item.get("query_strategy", {}).get("domain") or item.get("title"),
                    "gap": item.get("objective"),
                    "priority": item.get("priority"),
                    "legacy_rule_ids": item.get("known_gap_ids", []),
                    "mission_count": len(gap_missions),
                    "candidate_count": len(gap_candidates),
                    "status": gap_missions[0].status.value if gap_missions else item.get("status", "QUEUED"),
                }
            )
        return rows

    def _apply_conflict_resolution(self, conflict_id: str, *, resolution_status: str, note: str | None) -> ResearchConflictRecord:
        conflict = self.store.get_conflict(conflict_id)
        if conflict is None:
            raise KeyError(f"Unknown conflict: {conflict_id}")
        updated = conflict.model_copy(
            update={
                "resolution_status": ConflictResolutionStatus(resolution_status),
                "approved_resolution": note or conflict.approved_resolution,
            }
        )
        self.store.update_conflict(updated)
        return updated

    def _candidate_summary(self, candidate: ResearchCandidateRecord) -> dict[str, Any]:
        mission = self.store.get_mission(candidate.mission_id)
        approvals = self.store.list_approvals_for_candidate(candidate.candidate_id)
        conflicts = self.store.list_conflicts_for_candidate(candidate.candidate_id)
        source_quality = round(candidate.confidence.authority_confidence, 4)
        evidence_count = len(candidate.evidence_ids)
        source_count = len(candidate.source_ids)
        evolution = "NEW"
        if candidate.support_count > 1:
            evolution = "UPDATED - NEW EVIDENCE"
        elif conflicts:
            evolution = "UPDATED - CONFLICT FOUND"
        elif candidate.updated_at != candidate.created_at:
            evolution = "UPDATED - CONFIDENCE CHANGED"
        recommendation = "REVIEW"
        if candidate.approval_status == ApprovalStatus.APPROVED:
            recommendation = "PROMOTION_READY"
        elif candidate.approval_status == ApprovalStatus.NEEDS_MORE_RESEARCH:
            recommendation = "FOLLOW_UP_RESEARCH"
        elif candidate.contradiction_status != ContradictionStatus.NONE:
            recommendation = "REVIEW_CONTRADICTION"
        elif candidate.validation_status == ValidationStatus.PASS:
            recommendation = "APPROVE_CANDIDATE"
        elif candidate.validation_status == ValidationStatus.PASS_WITH_CONDITIONS:
            recommendation = "APPROVE_WITH_CONDITIONS"
        return {
            **candidate.model_dump(mode="json"),
            "mission_title": mission.title if mission else candidate.mission_id,
            "evidence_count": evidence_count,
            "source_count": source_count,
            "source_quality": source_quality,
            "cross_source_support": candidate.confidence.cross_source_confidence,
            "high_stakes": candidate.safety_class in {SafetyClass.HIGH, SafetyClass.HIGH_STAKES, SafetyClass.CRITICAL},
            "research_recommendation": recommendation,
            "age_days": self._age_days(candidate.created_at),
            "evolution_status": evolution,
            "approval_history_count": len(approvals),
            "conflict_count": len(conflicts),
        }

    def _candidate_sort_key(self, candidate: dict[str, Any], sort_by: str) -> Any:
        if sort_by == "priority":
            return candidate["priority"]
        if sort_by == "confidence":
            return candidate.get("confidence", {}).get("domain_confidence", 0)
        if sort_by == "evidence":
            return candidate.get("evidence_count", 0)
        if sort_by == "high_stakes":
            return 1 if candidate.get("high_stakes") else 0
        if sort_by == "contradictions":
            return candidate.get("conflict_count", 0)
        if sort_by == "newest":
            return candidate.get("created_at")
        if sort_by == "oldest":
            return candidate.get("created_at")
        return candidate.get("updated_at")

    def _source_summary(self, observation: SourceObservationRecord | None) -> dict[str, Any]:
        if observation is None:
            return {}
        evidence_rows = [item for item in self.store.list_evidence() if item.observation_id == observation.observation_id]
        candidate_ids = []
        for candidate in self.store.list_candidates():
            if set(candidate.evidence_ids) & {item.evidence_id for item in evidence_rows}:
                candidate_ids.append(candidate.candidate_id)
        metadata = dict(observation.domain_metadata)
        authority = metadata.get("authority_profile", {})
        state = "DISCOVERY_ONLY" if metadata.get("discovery_only") else (
            "REJECTED" if observation.access_status != SourceAccessStatus.ACCEPTED else "EVIDENTIARY"
        )
        if metadata.get("source_id") and not metadata.get("discovery_only"):
            state = "GOVERNED"
        provider_type = self._provider_type_name(observation.provider_id)
        return {
            **observation.model_dump(mode="json"),
            "claims_supported": metadata.get("claim_ids", []),
            "candidate_ids": candidate_ids,
            "authority_level": authority.get("authority_tier") or metadata.get("source_class"),
            "state": state,
            "discovery_only": bool(metadata.get("discovery_only")),
            "provider_type": provider_type,
        }

    def backlog_state(self) -> str:
        pending = sum(1 for item in self.store.list_candidates() if item.approval_status == ApprovalStatus.PENDING)
        contradictions = sum(1 for item in self.store.list_candidates() if item.contradiction_status != ContradictionStatus.NONE)
        weighted = pending + contradictions
        if weighted >= cfg.VEDA_RESEARCH_BACKLOG_SATURATED:
            return "SATURATED"
        if weighted >= cfg.VEDA_RESEARCH_BACKLOG_HIGH:
            return "HIGH"
        if weighted >= cfg.VEDA_RESEARCH_BACKLOG_ELEVATED:
            return "ELEVATED"
        return "NORMAL"

    def platform_runtime_state(self) -> dict[str, Any]:
        return self.store.get_runtime_state("platform_controls") or {
            "paused": False,
            "kill_switch": False,
            "updated_at": utc_now(),
        }

    def set_platform_runtime_state(
        self,
        *,
        paused: bool | None = None,
        kill_switch: bool | None = None,
        actor_id: str = "admin",
        reason: str | None = None,
    ) -> dict[str, Any]:
        existing = self.platform_runtime_state()
        updated = {
            **existing,
            "paused": existing.get("paused", False) if paused is None else bool(paused),
            "kill_switch": existing.get("kill_switch", False) if kill_switch is None else bool(kill_switch),
            "updated_at": utc_now(),
            "updated_by": actor_id,
        }
        self.store.set_runtime_state("platform_controls", updated, updated_at=updated["updated_at"])
        return updated

    def set_domain_status(self, domain_id: str, status: DomainStatus | str) -> ResearchDomainRecord:
        domain = self._require_domain(domain_id)
        updated = domain.model_copy(update={"status": DomainStatus(status), "updated_at": utc_now()})
        self.store.upsert_domain(updated)
        return updated

    def set_provider_enabled(self, provider_id: str, enabled: bool) -> dict[str, Any]:
        provider = self.providers.get(provider_id)
        if provider is None:
            raise KeyError(f"Unknown provider: {provider_id}")
        current = self.store.get_provider_state(provider_id) or {}
        state = {
            **current,
            "provider_id": provider_id,
            "status": ProviderStatus.DISABLED.value if not enabled else ProviderStatus.HEALTHY.value,
            "enabled": bool(enabled),
            "updated_at": utc_now(),
        }
        self.store.upsert_provider_state(provider_id, state, updated_at=state["updated_at"])
        return state

    def run_due_schedules(self, *, as_of: str | None = None, actor_id: str = "scheduler") -> dict[str, Any]:
        now = as_of or utc_now()
        controls = self.platform_runtime_state()
        if controls.get("kill_switch"):
            return {"status": "KILL_SWITCH", "as_of": now, "runs_started": 0, "schedule_ids": []}
        if controls.get("paused"):
            return {"status": "PAUSED", "as_of": now, "runs_started": 0, "schedule_ids": []}

        backlog_state = self.backlog_state()
        started: list[str] = []
        skipped: list[str] = []
        for schedule in self.store.list_due_schedules(now):
            mission = self.store.get_mission(schedule.mission_id)
            domain = self.store.get_domain(schedule.domain_id)
            if (
                mission is None
                or domain is None
                or domain.status not in {DomainStatus.ACTIVE, DomainStatus.TEST}
                or mission.status in {MissionStatus.PAUSED, MissionStatus.CANCELLED, MissionStatus.ARCHIVED}
            ):
                skipped.append(schedule.schedule_id)
                self._finalize_schedule_after_run(schedule, now)
                continue
            if backlog_state in {"HIGH", "SATURATED"} and mission.research_type in {ResearchType.DISCOVERY, ResearchType.NOVELTY_SEARCH}:
                skipped.append(schedule.schedule_id)
                self._finalize_schedule_after_run(schedule, now)
                continue
            self._execute_run(
                mission,
                actor_id=actor_id,
                trigger_type=self._trigger_for_schedule(schedule),
                schedule=schedule,
                as_of=now,
            )
            started.append(schedule.schedule_id)

        if started:
            self._update_digest_for_cycle(now, schedule_ids=started)
        return {
            "status": "SUCCESS" if started else "IDLE",
            "as_of": now,
            "runs_started": len(started),
            "schedule_ids": started,
            "skipped_schedule_ids": skipped,
            "backlog_state": backlog_state,
        }

    def list_digests(self, *, digest_type: str | None = None, domain_id: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
        return self.store.list_digests(digest_type=digest_type, domain_id=domain_id, limit=limit)

    def _resolve_provider_chain(
        self,
        mission: ResearchMissionRecord,
        domain: ResearchDomainRecord,
    ) -> tuple[list[BasePlatformResearchProvider], BasePlatformResearchProvider | None]:
        strategy = dict(mission.query_strategy or {})
        primary_id = strategy.get("search_provider_id") or strategy.get("provider_id") or domain.provider_policy.get("default_provider_id")
        fallback_ids = list(strategy.get("fallback_provider_ids") or domain.provider_policy.get("fallback_provider_ids") or [])
        provider_ids = [item for item in [primary_id, *fallback_ids] if item]
        providers: list[BasePlatformResearchProvider] = []
        for provider_id in provider_ids:
            provider = self.providers.get(str(provider_id))
            if provider is None:
                raise KeyError(f"Unknown research provider: {provider_id}")
            providers.append(provider)
        retrieval_id = strategy.get("retrieval_provider_id") or domain.provider_policy.get("default_retrieval_provider_id")
        retrieval_provider = self.providers.get(str(retrieval_id)) if retrieval_id else None
        return providers, retrieval_provider

    def _search_with_fallback(
        self,
        mission: ResearchMissionRecord,
        run: ResearchRunRecord,
        *,
        search_providers: list[BasePlatformResearchProvider],
        prior_run_count: int,
    ) -> tuple[BasePlatformResearchProvider, Any]:
        last_error: Exception | None = None
        now = utc_now()
        for provider in search_providers:
            descriptor = provider.descriptor()
            self._append_ledger(
                event_type=LedgerEventType.PROVIDER_SELECTED,
                actor_type=ActorType.SYSTEM,
                actor_id=descriptor.provider_id,
                action="provider_selected",
                domain_id=mission.domain_id,
                mission_id=mission.mission_id,
                run_id=run.run_id,
                metadata={"provider_id": descriptor.provider_id},
            )
            if not self._provider_available_for_run(descriptor.provider_id, provider, now):
                last_error = RuntimeError(f"provider_unavailable:{descriptor.provider_id}")
                continue
            try:
                batch = provider.search(mission, prior_run_count=prior_run_count)
                self._mark_provider_success(descriptor.provider_id)
                return provider, batch
            except ResearchProviderAuthError as exc:
                last_error = exc
                self._mark_provider_failure(descriptor.provider_id, error=str(exc), hard=True)
            except ResearchProviderTemporaryError as exc:
                last_error = exc
                self._mark_provider_failure(descriptor.provider_id, error=str(exc), hard=False)
            except Exception as exc:
                last_error = exc
                self._mark_provider_failure(descriptor.provider_id, error=str(exc), hard=False)
        if last_error is None:
            raise RuntimeError("no_provider_available")
        raise last_error

    def _provider_available_for_run(self, provider_id: str, provider: BasePlatformResearchProvider, now: str) -> bool:
        if not provider.is_available():
            return False
        state = self.store.get_provider_state(provider_id) or {}
        if state.get("enabled") is False:
            return False
        cooldown_until = str(state.get("cooldown_until") or "")
        if cooldown_until and cooldown_until > now:
            return False
        return True

    def _mark_provider_success(self, provider_id: str) -> None:
        state = self.store.get_provider_state(provider_id) or {"provider_id": provider_id, "enabled": True}
        now = utc_now()
        state.update(
            {
                "status": ProviderStatus.HEALTHY.value,
                "last_success": now,
                "last_failure": None,
                "cooldown_until": None,
                "consecutive_failures": 0,
                "updated_at": now,
            }
        )
        self.store.upsert_provider_state(provider_id, state, updated_at=now)

    def _mark_provider_failure(self, provider_id: str, *, error: str, hard: bool) -> None:
        state = self.store.get_provider_state(provider_id) or {"provider_id": provider_id, "enabled": True, "consecutive_failures": 0}
        now = utc_now()
        failures = int(state.get("consecutive_failures", 0)) + 1
        cooldown_seconds = cfg.VEDA_CHAT_PROVIDER_HARD_FAILURE_COOLDOWN_S if hard else max(60, cfg.VEDA_RESEARCH_TIMEOUT_S * failures)
        cooldown_until = self._shift_iso(now, seconds=cooldown_seconds)
        state.update(
            {
                "status": ProviderStatus.COOLDOWN.value if hard else ProviderStatus.DEGRADED.value,
                "last_failure": now,
                "last_error": error,
                "cooldown_until": cooldown_until if hard else state.get("cooldown_until"),
                "consecutive_failures": failures,
                "updated_at": now,
            }
        )
        self.store.upsert_provider_state(provider_id, state, updated_at=now)

    def _run_budget_exhausted(self, run: ResearchRunRecord, mission: ResearchMissionRecord) -> bool:
        if run.queries_executed > mission.research_budget.max_queries:
            return True
        if run.sources_discovered >= mission.research_budget.max_sources:
            return True
        if run.provider_calls > mission.research_budget.max_provider_calls:
            return True
        started = datetime.fromisoformat(run.started_at.replace("Z", "+00:00"))
        reference_time = str(run.model_metadata.get("budget_clock_at") or utc_now())
        elapsed = (
            datetime.fromisoformat(reference_time.replace("Z", "+00:00")) - started
        ).total_seconds()
        return elapsed > mission.research_budget.max_runtime_seconds

    def _trigger_for_schedule(self, schedule: ResearchScheduleRecord) -> TriggerType:
        mapping = {
            CadenceType.HOURLY: TriggerType.HOURLY,
            CadenceType.DAILY: TriggerType.DAILY,
            CadenceType.WEEKLY: TriggerType.WEEKLY,
            CadenceType.CUSTOM: TriggerType.SYSTEM_RETRY,
            CadenceType.MANUAL_ONLY: TriggerType.MANUAL,
        }
        return mapping[schedule.cadence_type]

    def _cycle_label_for_trigger(self, trigger_type: TriggerType, schedule: ResearchScheduleRecord | None) -> str:
        if schedule is not None:
            return schedule.cadence_type.value
        return trigger_type.value

    def _finalize_schedule_after_run(self, schedule: ResearchScheduleRecord, finished_at: str) -> ResearchScheduleRecord:
        next_run_at = self._next_schedule_time(finished_at, schedule.cadence_type, schedule.timezone)
        updated = schedule.model_copy(update={"last_run_at": finished_at, "next_run_at": next_run_at, "updated_at": utc_now()})
        self.store.upsert_schedule(updated)
        return updated

    def _next_schedule_time(self, base_iso: str, cadence_type: CadenceType, timezone_name: str) -> str | None:
        if cadence_type == CadenceType.MANUAL_ONLY:
            return None
        try:
            tz = ZoneInfo(timezone_name.replace("Calcutta", "Kolkata"))
        except Exception:
            tz = ZoneInfo("Asia/Kolkata")
        base = datetime.fromisoformat(base_iso.replace("Z", "+00:00")).astimezone(tz)
        if cadence_type == CadenceType.HOURLY:
            next_local = (base + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        elif cadence_type == CadenceType.DAILY:
            next_local = (base + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
        elif cadence_type == CadenceType.WEEKLY:
            next_local = (base + timedelta(days=7)).replace(hour=7, minute=0, second=0, microsecond=0)
        else:
            next_local = (base + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return next_local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _shift_iso(self, iso_value: str, *, seconds: int) -> str:
        base = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return (base + timedelta(seconds=seconds)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _update_digest_for_cycle(self, as_of: str, *, schedule_ids: list[str]) -> None:
        schedules = [self.store.get_schedule(item) for item in schedule_ids]
        schedules = [item for item in schedules if item is not None]
        cadences = {item.cadence_type for item in schedules}
        if CadenceType.DAILY in cadences:
            self._create_digest("DAILY", as_of)
        if CadenceType.WEEKLY in cadences:
            self._create_digest("WEEKLY", as_of)

    def _create_digest(self, digest_type: str, as_of: str) -> dict[str, Any]:
        dashboard = self.dashboard_bundle()
        payload = {
            "digest_id": self.store.next_id("digest", "VEDA-RDIG-"),
            "digest_type": digest_type,
            "created_at": as_of,
            "research_status": dashboard.get("research_status"),
            "runs_completed": dashboard.get("runs_today"),
            "runs_failed": dashboard.get("failed_runs"),
            "new_candidates": dashboard.get("new_candidates"),
            "pending_approvals": dashboard.get("pending_approvals"),
            "high_priority_conflicts": dashboard.get("high_priority_conflicts"),
            "knowledge_gaps": len(dashboard.get("knowledge_gaps", [])),
            "provider_health": dashboard.get("provider_health", []),
            "backlog_state": self.backlog_state(),
        }
        self.store.insert_digest(payload["digest_id"], digest_type, None, as_of, payload)
        self._append_ledger(
            event_type=LedgerEventType.DIGEST_UPDATED,
            actor_type=ActorType.SYSTEM,
            actor_id="digest_builder",
            action="create_digest",
            metadata={"digest_id": payload["digest_id"], "digest_type": digest_type},
        )
        return payload

    def _provider_health_rows(self) -> list[dict[str, Any]]:
        observations = self.store.list_observations()
        ledger_events = self.store.list_ledger_events()
        today = utc_now()[:10]
        rows = []
        for provider_id, provider in self.providers.items():
            descriptor = provider.descriptor()
            state = self.store.get_provider_state(provider_id) or {}
            last_use = max(
                (item.retrieved_at for item in observations if item.provider_id == provider_id),
                default=None,
            )
            if not last_use:
                last_use = state.get("last_success")
            provider_events_today = [
                item
                for item in ledger_events
                if item.actor_id == provider_id and item.timestamp.startswith(today)
            ]
            queries_today = sum(1 for item in provider_events_today if item.event_type == LedgerEventType.QUERY_EXECUTED)
            retrievals_today = sum(1 for item in provider_events_today if item.event_type == LedgerEventType.SOURCE_RETRIEVED)
            observations_today = sum(1 for item in observations if item.provider_id == provider_id and item.retrieved_at.startswith(today))
            rows.append(
                {
                    **provider.health_check(),
                    "provider_id": provider_id,
                    "provider_type": descriptor.provider_type.value,
                    "capabilities": descriptor.capabilities,
                    "last_successful_use": last_use,
                    "status": state.get("status") or (descriptor.status.value if hasattr(descriptor.status, "value") else str(descriptor.status)),
                    "cooldown_until": state.get("cooldown_until"),
                    "last_failure": state.get("last_failure"),
                    "last_error": state.get("last_error"),
                    "enabled": state.get("enabled", True),
                    "calls_today": queries_today + retrievals_today,
                    "budget_used": {
                        "queries_today": queries_today,
                        "retrievals_today": retrievals_today,
                        "observations_today": observations_today,
                    },
                }
            )
        return rows

    def _external_web_research_status(self) -> str:
        provider_rows = self._provider_health_rows()
        external_rows = [row for row in provider_rows if row.get("provider_type") in {"WEB_SEARCH", "DIRECT_WEB", "API", "CONNECTOR"}]
        if any(row.get("last_successful_use") for row in external_rows):
            return "ACTIVE"
        if any(row.get("enabled") and row.get("status") not in {"DISABLED", "UNAVAILABLE"} for row in external_rows):
            return "CONFIGURED"
        return "LOCAL_ONLY"

    def _engine_status(self) -> str:
        controls = self.platform_runtime_state()
        if controls.get("kill_switch") or controls.get("paused"):
            return "PAUSED"
        health = self.health()
        if health["status"] == PlatformHealth.DEGRADED.value:
            return "DEGRADED"
        if any(item.status == RunStatus.RUNNING for item in self.store.list_runs()):
            return "RUNNING"
        domains = self.store.list_domains()
        if domains and all(item.status.value in {"PAUSED", "DISABLED", "RETIRED"} for item in domains):
            return "PAUSED"
        if domains or self.store.list_runs():
            return "IDLE"
        return "PAUSED"

    def _legacy_progress(self, *, domain_id: str | None = None) -> dict[str, Any]:
        if domain_id not in {None, self.vedic_astrology_plugin.domain_id}:
            return {"total": 0, "source_validated": 0, "under_research": 0, "unsourced": 0, "unresolved": 0}
        legacy_rules = getattr(self.vedic_astrology_plugin, "p005_legacy_rules", [])
        missions = self.store.list_missions()
        candidates = self.store.list_candidates()
        source_validated = sum(1 for item in legacy_rules if item.get("source_status") == "SOURCE_VALIDATED")
        under_research = sum(1 for item in missions if item.parent_candidate_id is None and item.known_gap_ids)
        unresolved = sum(1 for item in candidates if item.approval_status == ApprovalStatus.NEEDS_MORE_RESEARCH)
        unsourced = sum(1 for item in legacy_rules if str(item.get("source_status", "")).startswith("LEGACY_"))
        return {
            "total": len(legacy_rules),
            "source_validated": source_validated,
            "under_research": under_research,
            "unsourced": unsourced,
            "unresolved": unresolved,
        }

    def _domain_for_run(self, run_id: str) -> str | None:
        run = self.store.get_run(run_id)
        return run.domain_id if run else None

    def _provider_type_name(self, provider_id: str | None) -> str | None:
        if not provider_id:
            return None
        provider = self.providers.get(str(provider_id))
        if provider is None:
            return None
        provider_type = provider.descriptor().provider_type
        return provider_type.value if hasattr(provider_type, "value") else str(provider_type)

    def _run_scope_for_run(
        self,
        run: ResearchRunRecord,
        *,
        mission: ResearchMissionRecord | None = None,
        observations: list[SourceObservationRecord] | None = None,
    ) -> str:
        provider_ids: set[str] = set()
        mission = mission or self.store.get_mission(run.mission_id)
        if mission is not None:
            strategy = dict(mission.query_strategy or {})
            for key in ("provider_id", "search_provider_id", "retrieval_provider_id"):
                value = strategy.get(key)
                if value:
                    provider_ids.add(str(value))
        for observation in observations or self.store.list_observations_for_run(run.run_id):
            provider_ids.add(observation.provider_id)
            for key in ("discovery_provider_id", "retrieval_provider_id"):
                value = observation.domain_metadata.get(key)
                if value:
                    provider_ids.add(str(value))

        types = {self._provider_type_name(provider_id) for provider_id in provider_ids if self._provider_type_name(provider_id)}
        external = any(item in {"WEB_SEARCH", "DIRECT_WEB", "API", "CONNECTOR"} for item in types)
        local = any(item in {"LOCAL_DOCUMENTS", "INTERNAL_KNOWLEDGE", "FIXTURE"} for item in types)
        if external and local:
            return "HYBRID"
        if external:
            return "EXTERNAL"
        return "LOCAL"

    def _find_mission_by_title(self, domain_id: str, title: str) -> ResearchMissionRecord | None:
        return next(
            (
                item
                for item in self.store.list_missions()
                if item.domain_id == domain_id and item.title == title
            ),
            None,
        )

    def _count_today_approvals(self, statuses: set[ApprovalStatus], *, domain_id: str | None = None) -> int:
        today = utc_now()[:10]
        candidate_lookup = {item.candidate_id: item for item in self.store.list_candidates()}
        return sum(
            1 for item in self.store.list_approvals()
            if item.decided_at.startswith(today)
            and item.status in statuses
            and domain_id in {
                None,
                candidate_lookup.get(item.candidate_id).domain_id if candidate_lookup.get(item.candidate_id) else None,
            }
        )

    def _count_approval_total(self, statuses: set[ApprovalStatus], *, domain_id: str | None = None) -> int:
        candidate_lookup = {item.candidate_id: item for item in self.store.list_candidates()}
        return sum(
            1
            for item in self.store.list_approvals()
            if item.status in statuses
            and domain_id in {
                None,
                candidate_lookup.get(item.candidate_id).domain_id if candidate_lookup.get(item.candidate_id) else None,
            }
        )

    def _latest_run_timestamp(self, *, domain_id: str | None = None) -> str | None:
        runs = [item for item in self.store.list_runs() if domain_id in {None, item.domain_id}]
        if not runs:
            return None
        return max(item.started_at for item in runs)

    def _next_expected_run(self, *, domain_id: str | None = None) -> str | None:
        schedules = [item for item in self.store.list_schedules() if domain_id in {None, item.domain_id} and item.enabled]
        next_values = [item.next_run_at for item in schedules if item.next_run_at]
        if not next_values:
            return None
        return min(next_values)

    def _paginate(self, rows: list[Any], *, page: int, per_page: int) -> tuple[list[Any], int]:
        total = len(rows)
        start = max(0, (page - 1) * per_page)
        end = start + per_page
        return rows[start:end], total

    def _age_days(self, iso_timestamp: str) -> int:
        try:
            current = datetime.now(timezone.utc)
            created = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0
        return max(0, int((current - created).days))

    def _duration_seconds(self, started_at: str, completed_at: str | None) -> float | None:
        if not completed_at:
            return None
        try:
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        return round((completed - started).total_seconds(), 2)

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
