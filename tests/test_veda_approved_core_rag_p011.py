from __future__ import annotations

from engines.ai.knowledge import approved_core_rag as rag
from engines.ai.research.platform.contracts import ConfidenceDimensions, CoreVersionState, ResearchCoreKnowledgeRecord


def _confidence() -> ConfidenceDimensions:
    return ConfidenceDimensions(
        source_confidence=0.93,
        authority_confidence=0.96,
        cross_source_confidence=0.91,
        provenance_confidence=0.94,
        novelty_confidence=0.55,
        contradiction_confidence=0.82,
        domain_confidence=0.95,
    )


def _core_record(
    *,
    core_id: str,
    title: str,
    claim: str,
    version_state: CoreVersionState = CoreVersionState.CURRENT,
) -> ResearchCoreKnowledgeRecord:
    return ResearchCoreKnowledgeRecord.model_validate(
        {
            "core_id": core_id,
            "domain_id": "VEDA-DOMAIN-VEDIC-ASTROLOGY",
            "title": title,
            "claim": claim,
            "normalized_claim": claim.lower(),
            "topic_key": "DASHA::VIMSHOTTARI",
            "stance": "SUPPORTED",
            "source_ids": ["VEDA-SRC-000111"],
            "passage_ids": ["VEDA-PSG-000111"],
            "claim_ids": ["VEDA-CLM-000111"],
            "conflict_ids": ["VEDA-CNF-000111"],
            "rule_ids": ["VEDA-RUL-DASHA-000111"],
            "confidence": _confidence().model_dump(),
            "candidate_id": "VEDA-RCND-000111",
            "approval_id": "VEDA-RAPR-000111",
            "promotion_id": "VEDA-RPRM-000111",
            "version": "1.0.0",
            "version_state": version_state.value,
            "retrieval_classification": "APPROVED_CORE",
            "high_stakes": False,
            "created_at": "2026-08-11T05:00:00Z",
            "updated_at": "2026-08-11T05:10:00Z",
        }
    )


class _FakeStore:
    def __init__(self, records):
        self._records = list(records)

    def list_all_core_knowledge(self):
        return list(self._records)


class _FakeService:
    def __init__(self, records):
        self.store = _FakeStore(records)


def test_p011_ontology_query_resolves_aliases(monkeypatch):
    monkeypatch.setattr(
        rag,
        "_load_ontology_aliases",
        lambda _root: (
            {
                "VEDA-GRAHA-JUPITER": {
                    "entity_id": "VEDA-GRAHA-JUPITER",
                    "canonical_name": "Jupiter",
                    "entity_type": "GRAHA",
                },
                "VEDA-BHAVA-07": {
                    "entity_id": "VEDA-BHAVA-07",
                    "canonical_name": "Seventh House",
                    "entity_type": "BHAVA",
                },
            },
            [
                ("seventh house", "VEDA-BHAVA-07"),
                ("guru", "VEDA-GRAHA-JUPITER"),
            ],
        ),
    )

    result = rag._query_ontology("Guru in seventh house")

    assert [item["entity_id"] for item in result["ontology_matches"]] == [
        "VEDA-BHAVA-07",
        "VEDA-GRAHA-JUPITER",
    ]
    assert "guru" in result["expanded_tokens"]
    assert "seventh" in result["expanded_tokens"]


def test_p011_approved_core_retrieval_returns_current_cited_conflict_aware_results(monkeypatch):
    current = _core_record(
        core_id="VEDA-RCORE-000111",
        title="Vimshottari Mahadasha sequence",
        claim="Vimshottari runs Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, and Venus.",
    )
    withdrawn = _core_record(
        core_id="VEDA-RCORE-000112",
        title="Withdrawn Vimshottari note",
        claim="Withdrawn sequence should never be active.",
        version_state=CoreVersionState.WITHDRAWN,
    )
    monkeypatch.setattr(rag, "get_research_platform_service", lambda: _FakeService([current, withdrawn]))
    monkeypatch.setattr(
        rag,
        "_source_map",
        lambda: {
            "VEDA-SRC-000111": {
                "source_id": "VEDA-SRC-000111",
                "title_normalized": "Brihat Parashara Hora Shastra",
                "author": "Parashara",
                "source_class": "CLASSICAL_PRIMARY",
                "verification_status": "VERIFIED",
                "authority_profile": {"authority_tier": "HIGH", "authority_score": 0.96},
            }
        },
    )
    monkeypatch.setattr(
        rag,
        "_passage_map",
        lambda: {
            "VEDA-PSG-000111": {
                "passage_id": "VEDA-PSG-000111",
                "source_id": "VEDA-SRC-000111",
                "chapter": "46",
                "section": "Dasha",
                "verse_start": "12",
                "verification_status": "VERIFIED",
                "translation": "Vimshottari dasha proceeds through the classical nine-graha order.",
            }
        },
    )
    monkeypatch.setattr(rag, "_claim_map", lambda: {})
    monkeypatch.setattr(rag, "_rule_map", lambda: {})
    monkeypatch.setattr(rag, "_claim_to_conflicts", lambda: {})
    monkeypatch.setattr(
        rag,
        "_conflict_map",
        lambda: {
            "VEDA-CNF-000111": {
                "conflict_id": "VEDA-CNF-000111",
                "topic": "Alternate dasha scope",
                "conflict_type": "DIFFERENT_SCOPE",
                "resolution_status": "CONTEXT_DEPENDENT",
                "analysis": "Some texts preserve other dasha systems for narrower scopes.",
            }
        },
    )

    diagnostics = rag.diagnose_approved_core_query("What does Vimshottari dasha say?", top_k=4)

    assert diagnostics.get("reason") is None
    assert len(diagnostics["results"]) == 1
    result = diagnostics["results"][0]
    assert result["knowledge_class"] == "APPROVED_CORE"
    assert result["version_state"] == "CURRENT"
    assert result["source_ids"] == ["VEDA-SRC-000111"]
    assert result["passage_ids"] == ["VEDA-PSG-000111"]
    assert result["citations"][0]["citation_type"] == "PRIMARY_TEXT_CITATION"
    assert result["citations"][0]["passage_id"] == "VEDA-PSG-000111"
    assert result["conflict_details"][0]["resolution_status"] == "CONTEXT_DEPENDENT"
    assert diagnostics["source_class_diversity"]["CLASSICAL_PRIMARY"] == 1


def test_p011_approved_core_retrieval_skips_non_astrology_queries(monkeypatch):
    monkeypatch.setattr(
        rag,
        "get_research_platform_service",
        lambda: _FakeService(
            [
                _core_record(
                    core_id="VEDA-RCORE-000211",
                    title="Vimshottari baseline",
                    claim="Vimshottari remains the governed baseline for this topic.",
                )
            ]
        ),
    )
    monkeypatch.setattr(rag, "_load_ontology_aliases", lambda _root: ({}, []))

    diagnostics = rag.diagnose_approved_core_query("Should I buy ETHOSLTD today?", top_k=4)

    assert diagnostics["results"] == []
    assert diagnostics["reason"] == "non_astrology_query"
