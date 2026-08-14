"""Deterministic structural response benchmark; never exact-matches prose."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


BENCHMARK_DOMAINS = ("GENERAL", "CAREER", "WEALTH", "EDUCATION", "MARRIAGE", "PROGENY", "HEALTH", "TIMING", "ASTROFINANCE")


@dataclass(frozen=True, slots=True)
class ResponseBenchmarkCase:
    case_id: str
    domain: str
    question: str
    chart_fixture: str


@dataclass(frozen=True, slots=True)
class ResponseMetrics:
    case_id: str
    chart_facts: int
    domain_facts: int
    unique_evidence: int
    timing_evidence: int
    conflict_evidence: int
    prediction_specificity: int
    timing_specificity: int
    generic_sentence_ratio: float
    duplicate_sentence_ratio: float
    disclaimer_count: int
    retrieval_diversity: int


@dataclass(frozen=True, slots=True)
class ProviderBenchmarkRecord:
    benchmark_id: str
    provider: str
    model: str
    prompt_version: str
    retrieval_mode: str
    chart_fixture: str
    question: str
    answer: str
    evidence_ids: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def capture_provider_response(case: ResponseBenchmarkCase, *, provider: str, model: str, prompt_version: str, retrieval_mode: str, responder: Any, configuration: dict[str, Any] | None = None, evidence_ids: list[str] | None = None) -> ProviderBenchmarkRecord:
    """Capture actual provider output; callers must not substitute a stub as proof."""
    answer = str(responder(case.question))
    return ProviderBenchmarkRecord(case.case_id, provider, model, prompt_version, retrieval_mode, case.chart_fixture, case.question, answer, tuple(evidence_ids or ()), dict(configuration or {}))


def default_cases() -> list[ResponseBenchmarkCase]:
    return [ResponseBenchmarkCase(f"STD002-{domain}", domain, f"What should VEDA analyze for {domain.lower()}?", "FIXTURE-STD002-1") for domain in BENCHMARK_DOMAINS]


def evaluate_response(case: ResponseBenchmarkCase, answer: str, *, evidence: list[dict[str, Any]] | None = None, chart_fact_terms: tuple[str, ...] = ("lagna", "dasha", "planet", "house", "chart")) -> ResponseMetrics:
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", answer or "") if item.strip()]
    normalized = [" ".join(item.lower().split()) for item in sentences]
    duplicates = len(normalized) - len(set(normalized))
    evidence = evidence or []
    text = (answer or "").lower()
    generic_terms = ("veda can", "it depends", "various factors", "as an ai", "consult")
    timing_terms = ("window", "period", "dasha", "transit", "timing")
    prediction_terms = ("likely", "hypothesis", "outlook", "probability", "scenario")
    return ResponseMetrics(case.case_id, sum(term in text for term in chart_fact_terms), sum(term in text for term in (case.domain.lower(),)), len({item.get("doc_id") or item.get("evidence_id") for item in evidence}), sum(term in text for term in timing_terms), sum("conflict" in str(item).lower() for item in evidence), sum(term in text for term in prediction_terms), sum(term in text for term in timing_terms), round(sum(any(term in sentence for term in generic_terms) for sentence in normalized) / max(len(sentences), 1), 3), round(duplicates / max(len(sentences), 1), 3), text.count("not a") + text.count("not medical"), len({str(item.get("trust_zone") or "") for item in evidence}))


def compare_metrics(before: list[ResponseMetrics], after: list[ResponseMetrics]) -> dict[str, Any]:
    before_map = {item.case_id: asdict(item) for item in before}
    after_map = {item.case_id: asdict(item) for item in after}
    results = []
    for case_id in sorted(set(before_map) | set(after_map)):
        left, right = before_map.get(case_id, {}), after_map.get(case_id, {})
        results.append({"case_id": case_id, "verdict": "NO_REGRESSION" if right.get("generic_sentence_ratio", 0) <= left.get("generic_sentence_ratio", 0) and right.get("duplicate_sentence_ratio", 0) <= left.get("duplicate_sentence_ratio", 0) else "REGRESSED", "before": left, "after": right})
    return {"case_count": len(results), "results": results, "human_validated": False, "model_level_improvement": False}


__all__ = ["BENCHMARK_DOMAINS", "ResponseBenchmarkCase", "ResponseMetrics", "ProviderBenchmarkRecord", "capture_provider_response", "compare_metrics", "default_cases", "evaluate_response"]
