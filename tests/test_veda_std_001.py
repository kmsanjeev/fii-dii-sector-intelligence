from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge.knowledge_lifecycle import DocumentLearningService
from engines.ai.knowledge.response_quality import deduplicate_safety_messages, response_quality_metrics
from engines.ai.knowledge.unified_retriever import RetrievalMode, _filter_by_mode, _trust_zone
from engines.ai.knowledge.unified_corpus_builder import UnifiedCorpusBuilder
from engines.ai.knowledge.contracts import normalize_knowledge_record


def test_trust_zones_are_normalized_without_promoting_research() -> None:
    record = normalize_knowledge_record({
        "doc_id": "RCND-1",
        "trust_zone": "RESEARCH_CANDIDATE",
        "domain": "HEALTH",
        "entity": "Health hypothesis",
        "claim": "A research hypothesis.",
        "validation_status": "RESEARCH_REQUIRED",
    })
    assert record.trust_zone == "RESEARCH_CANDIDATE"
    assert record.knowledge_class != "APPROVED_CORE"
    assert record.provenance.details["validation_state"] == "RESEARCH_REQUIRED"


def test_corpus_builder_connects_existing_research_tiers() -> None:
    summary = UnifiedCorpusBuilder().run()
    counts = summary["trust_zone_counts"]
    assert counts["APPROVED_CORE"] > 0
    assert counts["RESEARCH_CANDIDATE"] > 0
    assert counts["RESEARCH_ARCHIVE"] > 0
    assert counts["EXPERIMENTAL"] > 0


def test_retrieval_modes_preserve_trust_boundaries() -> None:
    docs = [
        {"knowledge_class": "APPROVED_CORE"},
        {"trust_zone": "RESEARCH_CANDIDATE"},
        {"trust_zone": "EXPERIMENTAL"},
        {"trust_zone": "RESEARCH_ARCHIVE"},
        {"trust_zone": "PLATFORM_EVIDENCE"},
    ]
    safe = _filter_by_mode(docs, RetrievalMode.PRODUCTION_SAFE)
    research = _filter_by_mode(docs, RetrievalMode.RESEARCH)
    assert all(_trust_zone(item) not in {"RESEARCH_CANDIDATE", "EXPERIMENTAL", "RESEARCH_ARCHIVE"} for item in safe)
    assert {"RESEARCH_CANDIDATE", "EXPERIMENTAL", "RESEARCH_ARCHIVE"}.issubset({_trust_zone(item) for item in research})


def test_document_learning_compares_before_candidate_creation(tmp_path: Path) -> None:
    path = tmp_path / "source.md"
    path.write_text("# Health Research\n\nLagna vitality is a research hypothesis.", encoding="utf-8")
    service = DocumentLearningService()
    learned = service.register_document(path, domain="HEALTH")
    candidate = service.create_research_candidate(learned.candidate_claims[0]["claim"], document_id=learned.document_id, domain="HEALTH")
    assert learned.passages
    assert candidate["trust_zone"] == "RESEARCH_CANDIDATE"
    assert candidate["promotion_requires_admin"] is True


def test_response_quality_metrics_and_safety_deduplication() -> None:
    bundle = {"results": [{"doc_id": "1", "domain": "HEALTH", "trust_zone": "RESEARCH_CANDIDATE", "text": "specific"}]}
    metrics = response_quality_metrics(bundle)
    assert metrics["trust_zone_diversity"] == 1
    text = deduplicate_safety_messages("Not a diagnosis.\nUseful answer.\nNot a diagnosis.")
    assert text.count("Not a diagnosis.") == 1
