from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge.retrieval_benchmark import evaluate_bundle, load_benchmark_cases


def test_p011_benchmark_fixture_loads_extended_case_fields():
    fixture_path = Path(__file__).resolve().parents[1] / "docs" / "governance" / "fixtures" / "veda_p011_rag_benchmark.json"

    cases = load_benchmark_cases(fixture_path)

    assert len(cases) >= 20
    assert any(case.requires_approved_core for case in cases)
    assert any(case.requires_citation for case in cases)
    assert any(case.requires_conflict for case in cases)
    assert any("APPROVED_CORE" in case.expected_knowledge_classes for case in cases)


def test_p011_benchmark_evaluates_approved_core_citation_and_conflict_hits():
    case_payload = {
        "case_id": "p011-approved-core-01",
        "category": "approved_core",
        "query": "What supports the Vimshottari starting Dasha rule?",
        "expected_domains": ["DASHA"],
        "expected_source_types": ["approved_core"],
        "expected_terms": ["vimshottari", "dasha"],
        "expected_knowledge_classes": ["APPROVED_CORE"],
        "requires_freshness": False,
        "requires_approved_core": True,
        "requires_citation": True,
        "requires_conflict": True,
    }
    case = load_benchmark_cases(Path(__file__).resolve().parents[1] / "docs" / "governance" / "fixtures" / "veda_p011_rag_benchmark.json")[0]
    case = case.__class__(**case_payload)

    bundle = {
        "summary": {
            "conflict_note": "Sources differ on scope for alternate dasha usage.",
            "sources": [
                {
                    "source_id": "core_vimshottari_current",
                    "source_type": "approved_core",
                    "knowledge_class": "APPROVED_CORE",
                    "domain": "DASHA",
                    "title": "Vimshottari Dasha Foundations",
                    "summary": "Approved core Vimshottari baseline.",
                    "citation_labels": ["BPHS ch.46 v.12"],
                    "conflict_details": [{"conflict_id": "VEDA-CNF-000111"}],
                }
            ],
        }
    }

    metrics = evaluate_bundle(case, bundle, top_k=4)

    assert metrics["hit"] is True
    assert metrics["knowledge_class_hit"] is True
    assert metrics["approved_core_hit"] is True
    assert metrics["citation_hit"] is True
    assert metrics["conflict_hit"] is True
