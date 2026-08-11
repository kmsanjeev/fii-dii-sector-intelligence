from __future__ import annotations

from pathlib import Path

from engines.ai.research.platform.contracts import EvidenceType, ProviderStatus, ProviderType, ResearchMissionRecord, ResearchProviderDescriptor
from engines.ai.research.platform.providers import BasePlatformResearchProvider, ProviderDocument, ProviderEvidenceHint, ProviderSearchBatch
from engines.ai.research.platform.contracts import AdminAction, ApprovalStatus
from engines.ai.research.platform.service import ResearchPlatformService


def _service(tmp_dir, *, providers: dict[str, BasePlatformResearchProvider] | None = None) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        providers=providers,
    )


class ExternalAuthoritySearchProvider(BasePlatformResearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        return ResearchProviderDescriptor(
            provider_id="ddgs-search",
            provider_type=ProviderType.WEB_SEARCH,
            capabilities=["search"],
            supports_search=True,
            supports_fetch=False,
            supports_documents=True,
            status=ProviderStatus.HEALTHY,
            allowed_uri_schemes=["https", "http"],
        )

    def is_available(self) -> bool:
        return True

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        context = dict(mission.query_strategy)
        context.pop("queries", None)
        context.pop("fallback_provider_ids", None)
        blog_doc = ProviderDocument(
            source_uri="https://astro.example.com/gaja-kesari-buy",
            source_title="Gaja Kesari buy signal blog",
            source_type=EvidenceType.WEB_REFERENCE,
            content="A modern astrology blog claims Gaja Kesari is a strong buy setup.",
            metadata={**context, "snippet": "Modern blog summary"},
        )
        wisdom_doc = ProviderDocument(
            source_uri="https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621574.html",
            source_title="Phaladeepika chapter extract",
            source_type=EvidenceType.WEB_REFERENCE,
            content="Phaladeepika translated passage concerning Jupiter and the Moon.",
            metadata={**context, "snippet": "Reference edition excerpt"},
        )
        return ProviderSearchBatch(
            documents=[blog_doc, wisdom_doc],
            query="gaja kesari classical definition",
            search_metadata={"provider": "ddgs-search", "result_count": 2},
        )

    def retrieve(self, document: ProviderDocument) -> str:
        return document.content

    def fetch_metadata(self, document: ProviderDocument) -> dict:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str):
        metadata = dict(document.metadata)
        claim_text = str(metadata.get("claim_text") or "Gaja Kesari Yoga requires provenance review.")
        return [
            ProviderEvidenceHint(
                passage=content[:220],
                claim_hint=claim_text,
                normalized_text=claim_text.lower(),
                confidence=float(metadata.get("authority_score", 0.45)),
                location=document.source_uri,
                metadata=metadata,
            )
        ]

    def health_check(self) -> dict:
        return {"provider_id": "ddgs-search", "status": "HEALTHY", "available": True}


class ExternalAuthorityFetchProvider(BasePlatformResearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        return ResearchProviderDescriptor(
            provider_id="requests-fetch",
            provider_type=ProviderType.DIRECT_WEB,
            capabilities=["retrieve", "fetch_metadata", "extract"],
            supports_search=False,
            supports_fetch=True,
            supports_documents=True,
            status=ProviderStatus.HEALTHY,
            allowed_uri_schemes=["https", "http"],
        )

    def is_available(self) -> bool:
        return True

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        raise RuntimeError("not used")

    def retrieve(self, document: ProviderDocument) -> str:
        document.metadata.update(
            {
                "http_status": 200,
                "content_type": "text/html",
                "content_length": len(document.content),
                "final_url": document.source_uri,
                "redirect_count": 0,
                "retrieved_at": "2026-08-11T00:00:00Z",
                "original_text": document.content[:600],
            }
        )
        return document.content

    def fetch_metadata(self, document: ProviderDocument) -> dict:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str):
        metadata = dict(document.metadata)
        claim_text = str(metadata.get("claim_text") or "Gaja Kesari Yoga requires provenance review.")
        return [
            ProviderEvidenceHint(
                passage=content[:220],
                claim_hint=claim_text,
                normalized_text=claim_text.lower(),
                confidence=max(0.45, float(metadata.get("authority_score", 0.45))),
                location=document.source_uri,
                metadata=metadata,
            )
        ]

    def health_check(self) -> dict:
        return {"provider_id": "requests-fetch", "status": "HEALTHY", "available": True}


def _astrology_candidates(service: ResearchPlatformService):
    return [item for item in service.list_candidates() if item.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"]


def test_astrology_pilot_runs_create_governed_claim_and_legacy_provenance_candidates(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    run_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
    run_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")
    run_c = service.trigger_manual_run(missions[2].mission_id, actor_id="admin@example.com")
    candidates = _astrology_candidates(service)

    assert run_a.status.value == "SUCCESS"
    assert run_a.sources_discovered == 2
    assert run_a.candidates_created == 2
    assert run_a.conflicts_created == 2

    assert run_b.status.value == "SUCCESS"
    assert run_b.sources_discovered == 4
    assert run_b.candidates_created == 1
    assert run_b.duplicates_detected == 3

    assert run_c.status.value == "SUCCESS"
    assert run_c.sources_discovered == 2
    assert run_c.candidates_created == 3
    assert run_c.duplicates_detected == 1
    assert run_c.conflicts_created == 3

    provenance = next(item for item in candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE")
    contextual = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000005"])
    cross_supported = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000006"])

    assert len(candidates) == 6
    assert provenance.title == "VEDA-P005-LGC-0001"
    assert provenance.support_count == 4
    assert provenance.validation_status.value == "PASS_WITH_CONDITIONS"
    assert provenance.metadata["legacy_rule_id"] == "VEDA-P005-LGC-0001"
    assert contextual.contradiction_status.value == "CONTEXTUAL"
    assert contextual.metadata["conflict_ids"] == ["VEDA-CNF-000001"]
    assert cross_supported.support_count == 2
    assert service.store.list_conflicts()


def test_astrology_research_continues_while_review_is_pending_and_rejections_are_rediscovered_not_duplicated(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    for mission in missions:
        service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")

    initial_candidates = _astrology_candidates(service)
    approved = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000002"])
    pending = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000001"])
    more_research = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000005"])
    rejected = next(item for item in initial_candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE")

    service.decide_candidate(approved.candidate_id, action=AdminAction.APPROVE, actor_id="admin@example.com", reason="Known governed foundation.")
    service.decide_candidate(rejected.candidate_id, action=AdminAction.REJECT, actor_id="admin@example.com", reason="Discovery-only provenance is not sufficient.")
    service.decide_candidate(more_research.candidate_id, action=AdminAction.REQUEST_MORE_RESEARCH, actor_id="admin@example.com", reason="Need more contradiction context.")

    follow_up = next(item for item in service.list_missions() if item.parent_candidate_id == more_research.candidate_id)
    follow_up_run = service.trigger_manual_run(follow_up.mission_id, actor_id="admin@example.com")
    rerun_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
    rerun_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")
    final_candidates = _astrology_candidates(service)

    approved_after = next(item for item in final_candidates if item.candidate_id == approved.candidate_id)
    pending_after = next(item for item in final_candidates if item.candidate_id == pending.candidate_id)
    more_after = next(item for item in final_candidates if item.candidate_id == more_research.candidate_id)
    rejected_after = next(item for item in final_candidates if item.candidate_id == rejected.candidate_id)
    provenance_candidates = [item for item in final_candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE"]

    assert follow_up_run.status.value == "SUCCESS"
    assert follow_up_run.candidates_created == 0
    assert follow_up_run.duplicates_detected == 2

    assert rerun_a.status.value == "SUCCESS"
    assert rerun_a.candidates_created == 0
    assert rerun_a.duplicates_detected == 3

    assert rerun_b.status.value == "SUCCESS"
    assert rerun_b.candidates_created == 0
    assert rerun_b.duplicates_detected == 4

    assert len(final_candidates) == 6
    assert approved_after.approval_status == ApprovalStatus.APPROVED
    assert pending_after.candidate_id == pending.candidate_id
    assert pending_after.support_count == 2
    assert len(pending_after.evidence_ids) == 2
    assert more_after.approval_status == ApprovalStatus.NEEDS_MORE_RESEARCH
    assert len(more_after.evidence_ids) == 2
    assert rejected_after.approval_status == ApprovalStatus.REJECTED
    assert rejected_after.knowledge_zone.value == "RESEARCH_ARCHIVE"
    assert rejected_after.support_count == 4
    assert len(rejected_after.evidence_ids) == 8
    assert len(provenance_candidates) == 1


def test_astrology_candidate_ledger_reconstructs_creation_merge_and_admin_decision(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    for mission in missions:
        service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")

    candidates = _astrology_candidates(service)
    approved = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000002"])
    pending = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000001"])

    service.decide_candidate(approved.candidate_id, action=AdminAction.APPROVE, actor_id="admin@example.com", reason="Known governed foundation.")
    service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")

    approved_events = {item.event_type.value for item in service.store.list_ledger_for_candidate(approved.candidate_id)}
    pending_events = {item.event_type.value for item in service.store.list_ledger_for_candidate(pending.candidate_id)}

    assert "CANDIDATE_CREATED" in approved_events
    assert "VALIDATION_COMPLETED" in approved_events
    assert "ADMIN_APPROVED" in approved_events
    assert "CANDIDATE_CREATED" in pending_events
    assert "CANDIDATE_MERGED" in pending_events
    assert "VALIDATION_COMPLETED" in pending_events


def test_astrology_external_research_refines_authority_and_marks_run_scope_external(tmp_dir):
    providers = {
        "ddgs-search": ExternalAuthoritySearchProvider(),
        "requests-fetch": ExternalAuthorityFetchProvider(),
    }
    service = _service(tmp_dir, providers=providers)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-VEDIC-ASTROLOGY",
            "title": "External authority mission",
            "objective": "Validate external authority refinement for live Jyotisha research.",
            "research_type": "LEGACY_RULE_PROVENANCE",
            "priority": "P2",
            "status": "ACTIVE",
            "query_strategy": {
                "provider_id": "ddgs-search",
                "retrieval_provider_id": "requests-fetch",
                "fallback_provider_ids": ["vedic-astrology-local"],
                "queries": ["gaja kesari classical definition"],
                "title": "VEDA-P005-LGC-0002",
                "claim_text": "Gaja Kesari Yoga requires governed provenance review.",
                "topic_key": "YOGA::GAJA_KESARI",
                "stance": "PROVENANCE_REVIEW",
                "candidate_type": "PROVENANCE_CANDIDATE",
                "priority": "P2",
                "legacy_rule_id": "VEDA-P005-LGC-0002",
                "domain": "YOGA",
                "subdomain": "GAJA_KESARI",
                "search_terms": ["Gaja Kesari", "Phaladeepika", "Wisdom Library"],
                "requires_primary_source": True,
            },
            "required_source_classes": ["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY", "REFERENCE_EDITION"],
            "minimum_independent_sources": 2,
        }
    )

    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    observations = service.store.list_observations_for_run(run.run_id)
    run_detail = service.get_run_detail(run.run_id)
    candidates = _astrology_candidates(service)

    blog = next(item for item in observations if "astro.example.com" in item.source_uri)
    reference = next(item for item in observations if "wisdomlib.org" in item.source_uri)
    candidate = next(item for item in candidates if item.metadata.get("legacy_rule_id") == "VEDA-P005-LGC-0002")

    assert run.status.value == "SUCCESS"
    assert run.sources_discovered == 2
    assert run.candidates_created == 1
    assert run.duplicates_detected == 1
    assert blog.domain_metadata["discovery_only"] is True
    assert blog.domain_metadata["source_class"] in {"FOLKLORE_OR_UNVERIFIED", "MODERN_PRACTITIONER"}
    assert reference.domain_metadata["discovery_only"] is False
    assert reference.domain_metadata["source_class"] == "REFERENCE_EDITION"
    assert reference.domain_metadata["verification_status"] == "METADATA_VERIFIED"
    assert candidate.support_count == 2
    assert run_detail["run"]["run_scope"] == "EXTERNAL"
