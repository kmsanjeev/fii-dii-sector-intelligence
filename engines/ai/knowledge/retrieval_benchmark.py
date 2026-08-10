from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from engines.common import config as cfg

from .retrieval_rollout import (
    attribution_quality_score,
    build_legacy_bundle,
    duplicate_noise_score,
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class RetrievalBenchmarkCase:
    case_id: str
    category: str
    query: str
    expected_domains: list[str]
    expected_source_types: list[str]
    expected_terms: list[str]
    requires_freshness: bool = False


def load_benchmark_cases(path: Path | None = None) -> list[RetrievalBenchmarkCase]:
    benchmark_path = Path(path or cfg.VEDA_UNIFIED_RETRIEVAL_BENCHMARK_PATH)
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    return [RetrievalBenchmarkCase(**item) for item in payload]


def _source_matches_case(source: dict[str, Any], case: RetrievalBenchmarkCase) -> bool:
    haystack = " ".join(
        str(part or "")
        for part in [
            source.get("title"),
            source.get("entity"),
            source.get("summary"),
            source.get("domain"),
            source.get("source_type"),
        ]
    ).lower()
    domain_match = not case.expected_domains or str(source.get("domain") or "") in case.expected_domains
    source_type_match = not case.expected_source_types or str(source.get("source_type") or "") in case.expected_source_types
    term_match = not case.expected_terms or any(term.lower() in haystack for term in case.expected_terms)
    return domain_match or source_type_match or term_match


def evaluate_bundle(case: RetrievalBenchmarkCase, bundle: dict[str, Any], *, top_k: int = 4) -> dict[str, Any]:
    summary = (bundle or {}).get("summary") or {}
    raw_sources = list(summary.get("sources") or [])
    sources = raw_sources[:top_k]
    relevant_count = sum(1 for source in sources if _source_matches_case(source, case))
    freshness_hit = not case.requires_freshness or any(
        str(source.get("source_type") or "") == "platform_intelligence" and str(source.get("date") or "").strip()
        for source in sources
    )
    return {
        "case_id": case.case_id,
        "category": case.category,
        "query": case.query,
        "hit": relevant_count > 0,
        "top_k_relevance": round(relevant_count / max(len(sources), 1), 3) if sources else 0.0,
        "duplicate_noise": duplicate_noise_score(sources),
        "source_attribution_quality": attribution_quality_score(sources),
        "freshness_hit": freshness_hit,
        "source_count": len(sources),
    }


def summarize_case_metrics(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not metrics:
        return {
            "case_count": 0,
            "hit_rate": 0.0,
            "top_k_relevance": 0.0,
            "duplicate_noise": 0.0,
            "source_attribution_quality": 0.0,
            "freshness_hit_rate": 0.0,
            "cases": [],
        }
    case_count = len(metrics)
    return {
        "case_count": case_count,
        "hit_rate": round(sum(1.0 if item["hit"] else 0.0 for item in metrics) / case_count, 3),
        "top_k_relevance": round(sum(float(item["top_k_relevance"]) for item in metrics) / case_count, 3),
        "duplicate_noise": round(sum(float(item["duplicate_noise"]) for item in metrics) / case_count, 3),
        "source_attribution_quality": round(sum(float(item["source_attribution_quality"]) for item in metrics) / case_count, 3),
        "freshness_hit_rate": round(sum(1.0 if item["freshness_hit"] else 0.0 for item in metrics) / case_count, 3),
        "cases": metrics,
    }


def compare_bundles(
    cases: list[RetrievalBenchmarkCase],
    *,
    unified_bundle_for_query: Callable[[str], dict[str, Any]],
    legacy_bundle_for_query: Callable[[str], dict[str, Any]],
    top_k: int = 4,
) -> dict[str, Any]:
    unified_metrics = [evaluate_bundle(case, unified_bundle_for_query(case.query), top_k=top_k) for case in cases]
    legacy_metrics = [evaluate_bundle(case, legacy_bundle_for_query(case.query), top_k=top_k) for case in cases]
    unified_summary = summarize_case_metrics(unified_metrics)
    legacy_summary = summarize_case_metrics(legacy_metrics)
    return {
        "generated_at": _utc_now(),
        "top_k": top_k,
        "case_count": len(cases),
        "unified": unified_summary,
        "legacy": legacy_summary,
        "winner_summary": {
            "hit_rate": _winner(unified_summary["hit_rate"], legacy_summary["hit_rate"]),
            "top_k_relevance": _winner(unified_summary["top_k_relevance"], legacy_summary["top_k_relevance"]),
            "duplicate_noise": _lower_winner(unified_summary["duplicate_noise"], legacy_summary["duplicate_noise"]),
            "source_attribution_quality": _winner(unified_summary["source_attribution_quality"], legacy_summary["source_attribution_quality"]),
        },
    }


def _winner(left: float, right: float) -> str:
    if left > right:
        return "unified"
    if right > left:
        return "legacy"
    return "tie"


def _lower_winner(left: float, right: float) -> str:
    if left < right:
        return "unified"
    if right < left:
        return "legacy"
    return "tie"


def run_default_benchmark(*, top_k: int = 4) -> dict[str, Any]:
    from engines.ai.capabilities import get_repo_capability_service
    from engines.ai.knowledge.review_service import get_knowledge_review_service
    from engines.ai.knowledge.retriever import HybridRetriever
    from engines.ai.knowledge.unified_retriever import UnifiedHybridRetriever

    cases = load_benchmark_cases()
    unified_retriever = UnifiedHybridRetriever(top_k=cfg.VEDA_UNIFIED_RETRIEVAL_TOP_K)
    legacy_retriever = HybridRetriever(top_k=5)
    knowledge_service = get_knowledge_review_service()
    repo_service = get_repo_capability_service()

    def _unified_bundle(query: str) -> dict[str, Any]:
        return unified_retriever.build_context_bundle(query, top_k=top_k)

    def _legacy_bundle(query: str) -> dict[str, Any]:
        reviewed_results = knowledge_service.search(query, top_k=2)
        repo_results = repo_service.search(query, top_k=2)
        legacy_results = legacy_retriever.retrieve(query, domain=None)[:3]
        return build_legacy_bundle(
            reviewed_results=reviewed_results,
            repo_results=repo_results,
            legacy_results=legacy_results,
            reviewed_context="",
            repo_context="",
        )

    return compare_bundles(
        cases,
        unified_bundle_for_query=_unified_bundle,
        legacy_bundle_for_query=_legacy_bundle,
        top_k=top_k,
    )


def write_benchmark_report(report: dict[str, Any], path: Path | None = None) -> Path:
    output_path = Path(path or cfg.VEDA_UNIFIED_RETRIEVAL_BENCHMARK_REPORT_DIR / "latest_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    report = run_default_benchmark()
    output = write_benchmark_report(report)
    print(json.dumps({"report_path": str(output), **report}, ensure_ascii=False, indent=2, sort_keys=True))
