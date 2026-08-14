# Regression

{
  "focused_tests": "tests/test_veda_p024_marriage.py",
  "python_suite": "py -3.11 -m pytest -q",
  "frontend_tests": "existing frontend tests",
  "frontend_build": "production build",
  "runtime_smoke": "existing runtime smoke",
  "rag_determinism": "py -3.11 scripts/rebuild_unified_rag.py twice when semantic RAG changes"
}
