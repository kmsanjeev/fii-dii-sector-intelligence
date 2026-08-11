from __future__ import annotations

from engines.ai.research.domains.vedic_astrology.plugin import VedicAstrologyResearchDomain
from engines.ai.research.platform.contracts import (
    ConfidenceDimensions,
    ContradictionStatus,
    KnowledgeZone,
    MissionPriority,
    NoveltyStatus,
    PromotionState,
    ResearchCandidateRecord,
    SafetyClass,
    ValidationStatus,
)


def _candidate(plugin: VedicAstrologyResearchDomain, **updates) -> ResearchCandidateRecord:
    payload = {
        "candidate_id": "VEDA-RCND-000001",
        "domain_id": plugin.domain_id,
        "mission_id": "VEDA-RM-000001",
        "run_id": "VEDA-RUN-000001",
        "title": "DASHA - Vimshottari Dasha Foundations",
        "candidate_type": "CLAIM_UPDATE",
        "claim": "The birth balance of a Vimshottari period is derived from the elapsed Moon portion in the Janma Nakshatra.",
        "normalized_claim": "the birth balance of a vimshottari period is derived from the elapsed moon portion in the janma nakshatra",
        "topic_key": "DASHA::VIMSHOTTARI_DASHA_FOUNDATIONS",
        "stance": "BIRTH_BALANCE_FROM_JANMA_NAKSHATRA",
        "evidence_ids": ["VEDA-EVD-000001"],
        "source_ids": ["VEDA-SRC-000001"],
        "existing_knowledge_matches": ["VEDA-RCORE-100002"],
        "novelty_status": NoveltyStatus.KNOWN,
        "contradiction_status": ContradictionStatus.CONTEXTUAL,
        "validation_status": ValidationStatus.PASS_WITH_CONDITIONS,
        "confidence": ConfidenceDimensions(
            source_confidence=0.9,
            authority_confidence=0.9,
            cross_source_confidence=0.5,
            provenance_confidence=0.95,
            novelty_confidence=0.8,
            contradiction_confidence=0.7,
            domain_confidence=0.8,
        ),
        "priority": MissionPriority.P1,
        "safety_class": SafetyClass.LOW,
        "approval_status": "PENDING",
        "knowledge_zone": KnowledgeZone.RESEARCH_CANDIDATE,
        "promotion_state": PromotionState.NONE,
        "created_at": "2026-08-11T00:00:00Z",
        "updated_at": "2026-08-11T00:00:00Z",
        "metadata": {
            "claim_ids": ["VEDA-CLM-000005"],
            "conflict_ids": ["VEDA-CNF-000001"],
            "domain": "DASHA",
            "subdomain": "VIMSHOTTARI_DASHA_FOUNDATIONS",
            "search_terms": ["vimshottari dasha order janma nakshatra balance"],
        },
    }
    payload.update(updates)
    return ResearchCandidateRecord.model_validate(payload)


def test_astrology_domain_record_and_mission_catalog_are_bootstrap_ready():
    plugin = VedicAstrologyResearchDomain()

    domain = plugin.domain_record()
    templates = plugin.mission_templates()
    gaps = plugin.generate_gap_missions(limit=5)
    coverage = plugin.build_coverage_matrix()

    assert domain.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"
    assert domain.status.value == "ACTIVE"
    assert domain.approval_policy["auto_promotion"] is False
    assert any(item["research_type"] == "LEGACY_RULE_PROVENANCE" for item in templates)
    assert len(templates) == 10
    assert len(gaps) == 5
    assert all(item["title"].startswith("Knowledge Gap - ") for item in gaps)
    assert len(coverage) == 15


def test_astrology_source_authority_and_exact_core_comparison_are_structured():
    plugin = VedicAstrologyResearchDomain()
    source = plugin.sources["VEDA-SRC-000001"].model_dump(mode="json")
    authority = plugin.evaluate_authority(source)
    classified = plugin.classify_source(source)
    core_records = plugin.seed_core_knowledge()
    comparison = plugin.compare_to_core(
        {
            "normalized_claim": plugin.normalize_claim_text(plugin.claims["VEDA-CLM-000001"].claim_text),
            "topic_key": "DASHA::VIMSHOTTARI_DASHA_FOUNDATIONS",
            "stance": "SEQUENCE_DEFINED",
            "metadata": {},
        },
        core_records,
    )

    assert classified["source_class"] == "CLASSICAL_PRIMARY"
    assert authority["textual_authority"] == 1.0
    assert authority["authority_score"] >= 0.85
    assert comparison["comparison_outcome"] == "EXACT_MATCH"
    assert comparison["novelty_status"] == "KNOWN"
    assert comparison["existing_knowledge_matches"]


def test_astrology_ontology_mapping_and_safety_classification_cover_high_stakes_and_gaps():
    plugin = VedicAstrologyResearchDomain()

    mapped = plugin.map_ontology("Guru Vimshottari Dasha and Pancha Mahapurusha review", {"domain": "FINANCE"})
    high_stakes = plugin.classify_safety({"metadata": {"domain": "FINANCE"}})
    discovery_only = plugin.classify_safety(
        {
            "metadata": {
                "domain": "YOGA",
                "candidate_type": "PROVENANCE_CANDIDATE",
                "discovery_only": True,
            }
        }
    )

    assert "VEDA-GRAHA-JUPITER" in mapped["ontology_matches"]
    assert "VEDA-DASHA-VIMSHOTTARI" in mapped["ontology_matches"]
    assert "PANCHA_MAHAPURUSHA_FAMILY" in mapped["ontology_gaps"]
    assert "DOMAIN::FINANCE" in mapped["ontology_gaps"]
    assert high_stakes == SafetyClass.HIGH_STAKES
    assert discovery_only == SafetyClass.MODERATE


def test_astrology_follow_up_preserves_candidate_identity_and_upload_policy():
    plugin = VedicAstrologyResearchDomain()

    governed_candidate = _candidate(plugin)
    governed_follow_up = plugin.create_follow_up(governed_candidate, "Need contradiction context.")

    provenance_candidate = _candidate(
        plugin,
        candidate_id="VEDA-RCND-000002",
        title="VEDA-P005-LGC-0001",
        candidate_type="PROVENANCE_CANDIDATE",
        claim="Pancha Mahapurusha-family detections in VEDA currently depend on kendra placement and dignity heuristics and require governed provenance recovery before migration.",
        normalized_claim="pancha mahapurusha family detections in veda currently depend on kendra placement and dignity heuristics and require governed provenance recovery before migration",
        topic_key="YOGA::PANCHA_MAHAPURUSHA_SIMPLIFIED",
        stance="PROVENANCE_RECOVERY",
        contradiction_status=ContradictionStatus.NONE,
        metadata={
            "legacy_rule_id": "VEDA-P005-LGC-0001",
            "domain": "YOGA",
            "subdomain": "PANCHA_MAHAPURUSHA",
            "search_terms": ["predictive astrology", "pancha mahapurusha", "mooltrikona", "kendra"],
            "discovery_only": True,
        },
    )
    provenance_follow_up = plugin.create_follow_up(provenance_candidate, "Need stronger primary evidence.")

    assert governed_follow_up is not None
    assert governed_follow_up["research_type"] == "CONTRADICTION_RESOLUTION"
    assert governed_follow_up["query_strategy"]["title"] == governed_candidate.title
    assert governed_follow_up["query_strategy"]["claim_text"] == governed_candidate.claim
    assert governed_follow_up["query_strategy"]["stance"] == governed_candidate.stance
    assert governed_follow_up["query_strategy"]["search_rounds"][0]["include_uploads"] is False

    assert provenance_follow_up is not None
    assert provenance_follow_up["research_type"] == "CROSS_SOURCE_VALIDATION"
    assert provenance_follow_up["query_strategy"]["search_rounds"][0]["include_uploads"] is True
    assert provenance_follow_up["parent_candidate_id"] == provenance_candidate.candidate_id
