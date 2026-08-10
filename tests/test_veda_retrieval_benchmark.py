from __future__ import annotations

from engines.ai.knowledge.retrieval_benchmark import (
    RetrievalBenchmarkCase,
    compare_bundles,
)
from engines.ai.knowledge.retrieval_rollout import build_legacy_bundle


def test_legacy_bundle_preserves_source_summary():
    bundle = build_legacy_bundle(
        reviewed_results=[
            {
                "doc_id": "reviewed_bank_note",
                "source_type": "user_reviewed",
                "domain": "RESEARCH",
                "entity": "Banking note",
                "text": "Approved note says banking looked strong earlier.",
                "summary": "Approved banking note.",
                "saved_at": "2026-08-03T10:00:00Z",
            }
        ],
        repo_results=[
            {
                "doc_id": "mit_memory_prompt",
                "source_type": "mit_repo_capability",
                "domain": "MIT_REPO_CAPABILITY",
                "entity": "MIT memory prompt",
                "text": "Reusable MIT prompt for memory review.",
                "summary": "MIT memory prompt.",
                "saved_at": "2026-08-04T08:00:00Z",
                "meta": {
                    "repo_label": "Agent Lab",
                    "license_name": "MIT",
                },
            }
        ],
        legacy_results=[
            {
                "doc_id": "platform_ethosltd",
                "domain": "STOCK",
                "entity": "ETHOSLTD",
                "text": "Local platform snapshot says ETHOSLTD remains supportive.",
                "summary": "ETHOSLTD remains supportive.",
                "effective_date": "2026-08-04",
            }
        ],
        reviewed_context="Reviewed context",
        repo_context="Repo context",
    )

    assert bundle["summary"]["approved_memory_count"] == 1
    assert bundle["summary"]["repo_count"] == 1
    assert bundle["summary"]["platform_snapshot_count"] == 1
    assert bundle["summary"]["sources"][1]["repo_label"] == "Agent Lab"
    assert "Reviewed context" in bundle["context"]
    assert "Relevant intelligence context" in bundle["context"]


def test_compare_bundles_reports_unified_as_cleaner_winner():
    cases = [
        RetrievalBenchmarkCase(
            case_id="mit-1",
            category="mit_capability_reuse",
            query="Which MIT repo capability should Veda reuse for memory?",
            expected_domains=["MIT_REPO_CAPABILITY"],
            expected_source_types=["mit_repo_capability"],
            expected_terms=["mit", "repo", "memory"],
            requires_freshness=False,
        )
    ]

    unified_bundle = {
        "summary": {
            "sources": [
                {
                    "source_id": "mit_memory_prompt",
                    "source_type": "mit_repo_capability",
                    "domain": "MIT_REPO_CAPABILITY",
                    "title": "Agent Lab",
                    "summary": "MIT memory workflow with review gates.",
                    "date": "2026-08-04",
                }
            ]
        }
    }
    legacy_bundle = {
        "summary": {
            "sources": [
                {
                    "source_id": "platform_market_1",
                    "source_type": "platform_intelligence",
                    "domain": "MARKET",
                    "title": "Market regime",
                    "summary": "General market note.",
                    "date": "",
                },
                {
                    "source_id": "platform_market_1",
                    "source_type": "platform_intelligence",
                    "domain": "MARKET",
                    "title": "Market regime",
                    "summary": "General market note.",
                    "date": "",
                },
            ]
        }
    }

    report = compare_bundles(
        cases,
        unified_bundle_for_query=lambda query: unified_bundle,
        legacy_bundle_for_query=lambda query: legacy_bundle,
        top_k=4,
    )

    assert report["case_count"] == 1
    assert report["winner_summary"]["hit_rate"] == "unified"
    assert report["winner_summary"]["top_k_relevance"] == "unified"
    assert report["winner_summary"]["duplicate_noise"] == "unified"
    assert report["winner_summary"]["source_attribution_quality"] == "unified"
