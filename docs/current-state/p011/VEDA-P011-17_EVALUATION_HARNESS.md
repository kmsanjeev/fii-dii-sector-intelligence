# Evaluation Harness

P011 extends the existing retrieval benchmark contract to track:
- approved-core hit rate
- knowledge-class correctness
- citation hit rate
- conflict hit rate
- freshness hit rate
- attribution quality
- duplicate noise

Artifacts:
- benchmark engine: `engines/ai/knowledge/retrieval_benchmark.py`
- P011 query pack: `docs/governance/fixtures/veda_p011_rag_benchmark.json`
- tests: `tests/test_veda_retrieval_benchmark_p011.py`

The committed P011 query pack currently contains 20 cases spanning approved core, conflicts, aliases, high-stakes, temporary research separation, and unsupported queries.
