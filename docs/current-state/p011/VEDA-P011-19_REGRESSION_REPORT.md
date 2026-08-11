# Regression Report

Validated during P011 work:
- targeted P011 Python slice for approved-core retrieval, unified retrieval, chat integration, and admin diagnostics
- retrieval benchmark tests, including the extended P011 benchmark contract
- full Python regression suite
- frontend single-worker Vitest run
- frontend production build
- official P001 smoke runner

Commands executed:
- `py -3.11 -m pytest tests/test_veda_approved_core_rag_p011.py tests/test_veda_unified_retriever.py tests/test_veda_chat_engine.py tests/test_veda_research_admin_api.py -q`
- `py -3.11 -m pytest tests/test_veda_retrieval_benchmark.py tests/test_veda_retrieval_benchmark_p011.py -q`
- `py -3.11 -m pytest -q`
- `frontend: npx vitest run --pool=threads --maxWorkers=1`
- `frontend: npm run build`
- `py -3.11 scripts/run_p001_smoke.py`

Recorded outcomes on August 11, 2026:
- full Python suite: `438 passed, 0 failed, 1 warning`
- frontend tests: `7 files passed, 27 tests passed`
- frontend build: `PASS`
- runtime smoke: `PASS`
- P011 golden-query benchmark fixture: `21` cases
- P011 unified benchmark summary:
  - hit rate: `0.952`
  - top-k relevance: `0.940`
  - approved-core hit rate: `0.952`
  - citation hit rate: `0.952`
  - conflict hit rate: `1.000`
- P011 legacy benchmark summary:
  - hit rate: `0.048`
  - top-k relevance: `0.024`

Benchmark conclusion:
- the unified approved-core retrieval path materially outperformed the legacy path across the P011 query set
- duplicate noise remained `0.000` in both paths

Retained non-blocking condition:
- frontend build still emits the inherited large-chunk warning for the main JavaScript bundle
