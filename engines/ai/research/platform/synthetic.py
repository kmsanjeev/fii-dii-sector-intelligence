from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engines.ai.research.platform.contracts import (
    ConfidenceDimensions,
    ContradictionStatus,
    DomainStatus,
    EvidenceType,
    KnowledgeZone,
    MissionPriority,
    ResearchCandidateRecord,
    ResearchCoreKnowledgeRecord,
    ResearchDomainPlugin,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchMissionRecord,
    SafetyClass,
    SourceObservationRecord,
)
from engines.common import config as cfg


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SyntheticResearchDomainPlugin(ResearchDomainPlugin):
    def __init__(self, fixture_path: Path | None = None):
        self.fixture_path = Path(fixture_path or (cfg.VEDA_RESEARCH_PLATFORM_FIXTURE_DIR / "synthetic_research_fixture.json"))
        self.fixture = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        self.domain_id = "VEDA-DOMAIN-SYNTHETIC"
        self.ontology_namespace = "veda.synthetic"
        self.source_policy = {
            "allowed_source_types": [item.value for item in EvidenceType],
            "unsafe_uri_schemes_rejected": True,
        }
        self.authority_policy = {
            "mode": "fixture",
            "authority_dimensions": ["textual", "publisher", "cross_source"],
        }
        self.validation_policy = {
            "minimum_independent_sources": 2,
            "supports_follow_up": True,
        }
        self.safety_policy = {
            "high_stakes_topics": ["synthetic.delta"],
        }

    def domain_record(self) -> ResearchDomainRecord:
        now = utc_now()
        return ResearchDomainRecord(
            domain_id=self.domain_id,
            name="Synthetic Research Domain",
            version="1.0.0",
            status=DomainStatus.TEST,
            description="Controlled synthetic domain used to validate the autonomous research platform lifecycle.",
            ontology_namespace=self.ontology_namespace,
            source_policy=self.source_policy,
            validation_policy=self.validation_policy,
            safety_policy=self.safety_policy,
            approval_policy={
                "admin_required": True,
                "auto_promotion": False,
                "promotion_state": "PROMOTION_READY",
            },
            provider_policy={
                "default_provider_id": "synthetic-fixture",
                "allowed_provider_types": ["FIXTURE"],
            },
            schedule_policy={
                "default_cadence_type": "MANUAL_ONLY",
                "default_overlap_policy": "SKIP",
                "default_misfire_policy": "RUN_ONCE",
            },
            plugin_entrypoint="engines.ai.research.platform.synthetic:SyntheticResearchDomainPlugin",
            created_at=now,
            updated_at=now,
        )

    def seed_core_knowledge(self) -> list[ResearchCoreKnowledgeRecord]:
        now = utc_now()
        records: list[ResearchCoreKnowledgeRecord] = []
        for item in self.fixture.get("approved_core", []):
            records.append(
                ResearchCoreKnowledgeRecord(
                    core_id=item["core_id"],
                    domain_id=self.domain_id,
                    title=item["title"],
                    claim=item["claim"],
                    normalized_claim=item["normalized_claim"],
                    topic_key=item["topic_key"],
                    stance=item.get("stance", "NEUTRAL"),
                    source_ids=list(item.get("source_ids", [])),
                    knowledge_zone=KnowledgeZone.APPROVED_CORE,
                    confidence=ConfidenceDimensions(
                        source_confidence=float(item.get("source_confidence", 1.0)),
                        authority_confidence=float(item.get("authority_confidence", 1.0)),
                        cross_source_confidence=float(item.get("cross_source_confidence", 1.0)),
                        provenance_confidence=float(item.get("provenance_confidence", 1.0)),
                        novelty_confidence=float(item.get("novelty_confidence", 1.0)),
                        contradiction_confidence=float(item.get("contradiction_confidence", 1.0)),
                        domain_confidence=float(item.get("domain_confidence", 1.0)),
                    ),
                    created_at=now,
                    updated_at=now,
                )
            )
        return records

    def normalize_candidate(
        self,
        evidence: ResearchEvidenceRecord,
        observation: SourceObservationRecord,
        mission: ResearchMissionRecord,
    ) -> dict[str, Any]:
        metadata = dict(evidence.domain_metadata)
        title = metadata.get("title") or evidence.claim_hint
        topic_key = metadata.get("topic_key") or evidence.claim_hint.lower().replace(" ", ".")
        stance = metadata.get("stance", "NEUTRAL")
        candidate_type = metadata.get("candidate_type", "NEW_CLAIM")
        return {
            "title": title,
            "claim": evidence.claim_hint,
            "normalized_claim": metadata.get("normalized_claim", evidence.normalized_text),
            "topic_key": topic_key,
            "stance": stance,
            "candidate_type": candidate_type,
            "priority": metadata.get("priority", MissionPriority.P2.value),
            "safety_class": metadata.get("safety_class"),
            "metadata": metadata,
        }

    def validate_source(self, observation: SourceObservationRecord) -> tuple[bool, str | None]:
        if observation.domain_metadata.get("reject_reason"):
            return False, str(observation.domain_metadata["reject_reason"])
        return True, None

    def compare_to_core(self, candidate_payload: dict[str, Any], core_records: list[ResearchCoreKnowledgeRecord]) -> dict[str, Any]:
        normalized_claim = candidate_payload["normalized_claim"]
        topic_key = candidate_payload["topic_key"]
        stance = candidate_payload["stance"]

        exact_matches = [record for record in core_records if record.normalized_claim == normalized_claim]
        topic_matches = [record for record in core_records if record.topic_key == topic_key]

        if exact_matches:
            return {
                "novelty_status": "KNOWN",
                "existing_knowledge_matches": [record.core_id for record in exact_matches],
                "topic_matches": [record.core_id for record in topic_matches],
            }
        if topic_matches and any(record.stance != stance for record in topic_matches):
            return {
                "novelty_status": "POSSIBLE_UPDATE",
                "existing_knowledge_matches": [record.core_id for record in topic_matches],
                "topic_matches": [record.core_id for record in topic_matches],
            }
        return {
            "novelty_status": "NEW",
            "existing_knowledge_matches": [],
            "topic_matches": [],
        }

    def detect_domain_conflict(
        self,
        candidate_payload: dict[str, Any],
        core_records: list[ResearchCoreKnowledgeRecord],
        pending_candidates: list[ResearchCandidateRecord],
    ) -> dict[str, Any]:
        topic_key = candidate_payload["topic_key"]
        stance = candidate_payload["stance"]

        for record in core_records:
            if record.topic_key == topic_key and record.stance != stance:
                return {
                    "contradiction_status": ContradictionStatus.DIRECT.value,
                    "conflicting_core_id": record.core_id,
                    "analysis": f"Candidate stance {stance} conflicts with approved core stance {record.stance}.",
                }

        for candidate in pending_candidates:
            if candidate.topic_key == topic_key and candidate.stance != stance:
                return {
                    "contradiction_status": ContradictionStatus.DIRECT.value,
                    "conflicting_candidate_id": candidate.candidate_id,
                    "analysis": f"Candidate stance {stance} conflicts with pending candidate stance {candidate.stance}.",
                }

        return {
            "contradiction_status": ContradictionStatus.NONE.value,
            "analysis": "No domain conflict detected.",
        }

    def classify_safety(self, candidate_payload: dict[str, Any]) -> SafetyClass:
        override = candidate_payload.get("safety_class")
        if override:
            return SafetyClass(override)
        if candidate_payload.get("topic_key") in self.safety_policy["high_stakes_topics"]:
            return SafetyClass.HIGH
        return SafetyClass.MODERATE

    def create_follow_up(self, candidate: ResearchCandidateRecord, reason: str) -> dict[str, Any] | None:
        follow_up_sequence = candidate.metadata.get("follow_up_batch_sequence")
        if not follow_up_sequence:
            return None
        return {
            "domain_id": self.domain_id,
            "title": f"Follow-up: {candidate.title}",
            "objective": f"Gather additional evidence for {candidate.claim}",
            "research_type": "CLAIM_VALIDATION",
            "priority": candidate.priority.value,
            "status": "QUEUED",
            "created_by": "system",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": follow_up_sequence,
                "parent_candidate_id": candidate.candidate_id,
            },
            "required_source_classes": ["WEB_REFERENCE"],
            "minimum_independent_sources": 1,
            "known_claim_ids": [candidate.candidate_id],
            "known_conflict_ids": [],
            "known_gap_ids": [],
            "safety_class": candidate.safety_class.value,
            "completion_policy": {"auto_complete": False},
            "research_budget": {
                "max_queries": 1,
                "max_sources": 4,
                "max_provider_calls": 1,
                "max_runtime_seconds": 60,
                "max_model_calls": 0,
                "max_cost": 0,
                "max_follow_up_depth": 2,
                "max_retries": 1,
                "cooldown_seconds": 0,
            },
            "notes": reason,
            "follow_up_depth": candidate.metadata.get("follow_up_depth", 0) + 1,
            "parent_candidate_id": candidate.candidate_id,
            "parent_mission_id": candidate.mission_id,
        }
