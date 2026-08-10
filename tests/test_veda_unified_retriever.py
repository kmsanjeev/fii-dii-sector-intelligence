from __future__ import annotations

from engines.ai.knowledge.unified_retriever import UnifiedHybridRetriever


def test_unified_retriever_builds_source_aware_context(monkeypatch):
    bm25_docs = [
        {
            "doc_id": "platform_market",
            "source_type": "platform_intelligence",
            "domain": "MARKET",
            "entity": "MARKET_REGIME",
            "text": "Market regime is ACCUMULATION with positive FII support.",
            "summary": "Market regime is ACCUMULATION.",
            "effective_date": "2026-08-04",
            "saved_at": None,
            "freshness_class": "dated_snapshot",
        },
        {
            "doc_id": "memory_book",
            "source_type": "attachment_chunk",
            "domain": "RESEARCH",
            "entity": "Astro timing notes",
            "text": "Jupiter transit rules help time expansion cycles from the uploaded book.",
            "summary": "Jupiter timing notes from the uploaded book.",
            "effective_date": None,
            "saved_at": "2026-08-04T10:00:00Z",
            "freshness_class": "durable_memory",
        },
    ]
    faiss_docs = [
        {
            "doc_id": "memory_book",
            "source_type": "attachment_chunk",
            "domain": "RESEARCH",
            "entity": "Astro timing notes",
            "text": "Jupiter transit rules help time expansion cycles from the uploaded book.",
            "summary": "Jupiter timing notes from the uploaded book.",
            "effective_date": None,
            "saved_at": "2026-08-04T10:00:00Z",
            "freshness_class": "durable_memory",
        }
    ]

    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._bm25_query",
        lambda query, top_k: bm25_docs[:top_k],
    )
    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._faiss_query",
        lambda query, top_k: faiss_docs[:top_k],
    )

    retriever = UnifiedHybridRetriever(top_k=4)
    context = retriever.build_context("Study this uploaded book and remember the Jupiter rules.", top_k=2)

    assert "Unified evidence below blends local platform intelligence" in context
    assert "attachment memory" in context
    assert "platform intelligence" in context
    assert "Jupiter transit rules" in context


def test_unified_retriever_marks_predictive_ml_signals_clearly(monkeypatch):
    bm25_docs = [
        {
            "doc_id": "stock_ethosltd",
            "source_type": "platform_intelligence",
            "evidence_kind": "predictive_ml_signal",
            "domain": "STOCK",
            "entity": "ETHOSLTD",
            "text": "ML bull run score is 80.78 and accumulation score is 99.70 for ETHOSLTD.",
            "summary": "ETHOSLTD remains a high-scoring bullish continuation candidate.",
            "effective_date": "2026-08-04",
            "saved_at": None,
            "freshness_class": "dated_snapshot",
            "model_name": "bull_run_score_pipeline",
            "model_version": "2026-08-04",
            "score_meaning": "Higher model scores indicate a stronger local bullish continuation signal.",
            "reliability_note": "Treat this as predictive scored evidence, not guaranteed fact.",
        },
    ]
    faiss_docs = list(bm25_docs)

    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._bm25_query",
        lambda query, top_k: bm25_docs[:top_k],
    )
    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._faiss_query",
        lambda query, top_k: faiss_docs[:top_k],
    )

    retriever = UnifiedHybridRetriever(top_k=4)
    bundle = retriever.build_context_bundle("What are the top local ML signals in stocks today?", top_k=1)
    context = bundle["context"]

    assert "predictive ML signal" in context
    assert "model=bull_run_score_pipeline@2026-08-04" in context
    assert "meaning:" in context
    assert bundle["summary"]["predictive_ml_count"] == 1
    assert bundle["summary"]["sources"][0]["title"] == "ETHOSLTD"
    assert bundle["summary"]["sources"][0]["model_name"] == "bull_run_score_pipeline"


def test_unified_retriever_reports_conflict_and_freshness_notes(monkeypatch):
    bm25_docs = [
        {
            "doc_id": "platform_stock_positive",
            "source_type": "platform_intelligence",
            "evidence_kind": "predictive_ml_signal",
            "domain": "STOCK",
            "entity": "ETHOSLTD",
            "entity_keys": {"symbol": "ETHOSLTD"},
            "text": "ETHOSLTD still looks bullish with strong accumulation and breakout support.",
            "summary": "ETHOSLTD still looks bullish with strong accumulation support.",
            "effective_date": "2026-08-04",
            "saved_at": None,
            "freshness_class": "dated_snapshot",
            "reliability_note": "Treat this as predictive scored evidence, not guaranteed fact.",
        },
        {
            "doc_id": "memory_stock_negative",
            "source_type": "user_reviewed",
            "evidence_kind": "approved_memory",
            "domain": "STOCK",
            "entity": "ETHOSLTD",
            "entity_keys": {"symbol": "ETHOSLTD"},
            "text": "Older saved note warns that ETHOSLTD looked weak and should be avoided.",
            "summary": "Older note warns ETHOSLTD looked weak.",
            "effective_date": None,
            "saved_at": "2026-07-20T10:00:00Z",
            "freshness_class": "durable_memory",
            "provenance": {"source_title": "ETHOSLTD prior note"},
        },
    ]
    faiss_docs = list(bm25_docs)

    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._bm25_query",
        lambda query, top_k: bm25_docs[:top_k],
    )
    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._faiss_query",
        lambda query, top_k: faiss_docs[:top_k],
    )

    retriever = UnifiedHybridRetriever(top_k=4)
    bundle = retriever.build_context_bundle("What is the latest ETHOSLTD view?", top_k=2)

    assert "Conflict note:" in bundle["context"]
    assert "Freshness note:" in bundle["context"]
    assert "Local sources disagree on ETHOSLTD" in bundle["summary"]["conflict_note"]
    assert "newest dated item here is 2026-08-04" in bundle["summary"]["freshness_note"]
    assert len(bundle["summary"]["sources"]) == 2


def test_unified_retriever_boosts_repo_results_for_repo_queries(monkeypatch):
    bm25_docs = [
        {
            "doc_id": "platform_market",
            "source_type": "platform_intelligence",
            "domain": "MARKET",
            "entity": "MARKET_REGIME",
            "text": "Market regime is ACCUMULATION.",
            "summary": "Market regime is ACCUMULATION.",
            "effective_date": "2026-08-04",
            "saved_at": None,
            "freshness_class": "dated_snapshot",
        },
        {
            "doc_id": "mit_repo_1",
            "source_type": "mit_repo_capability",
            "domain": "MIT_REPO_CAPABILITY",
            "entity": "MIT repo capability: Agent Lab",
            "text": "Workflow guide shows reusable memory and prompt patterns.",
            "summary": "Reusable workflow guide.",
            "effective_date": None,
            "saved_at": "2026-08-04T10:00:00Z",
            "freshness_class": "reference",
        },
    ]
    faiss_docs = [
        {
            "doc_id": "platform_market",
            "source_type": "platform_intelligence",
            "domain": "MARKET",
            "entity": "MARKET_REGIME",
            "text": "Market regime is ACCUMULATION.",
            "summary": "Market regime is ACCUMULATION.",
            "effective_date": "2026-08-04",
            "saved_at": None,
            "freshness_class": "dated_snapshot",
        },
        {
            "doc_id": "mit_repo_1",
            "source_type": "mit_repo_capability",
            "domain": "MIT_REPO_CAPABILITY",
            "entity": "MIT repo capability: Agent Lab",
            "text": "Workflow guide shows reusable memory and prompt patterns.",
            "summary": "Reusable workflow guide.",
            "effective_date": None,
            "saved_at": "2026-08-04T10:00:00Z",
            "freshness_class": "reference",
        },
    ]

    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._bm25_query",
        lambda query, top_k: bm25_docs[:top_k],
    )
    monkeypatch.setattr(
        "engines.ai.knowledge.unified_retriever._faiss_query",
        lambda query, top_k: faiss_docs[:top_k],
    )

    retriever = UnifiedHybridRetriever(top_k=4)
    results = retriever.retrieve("Which MIT repo workflow or prompt should improve memory capability?")

    assert results[0]["source_type"] == "mit_repo_capability"
