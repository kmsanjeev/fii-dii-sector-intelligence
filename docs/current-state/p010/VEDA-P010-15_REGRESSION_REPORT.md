# VEDA-P010 Regression Report

Validation executed on August 11, 2026.

Targeted P010 coverage:
- `py -3.11 -m pytest tests/test_veda_knowledge_contract.py tests/test_veda_unified_corpus_builder.py tests/test_veda_research_admin_api.py tests/test_veda_research_promotion_p010.py -q`
- result: `19 passed, 1 warning`

Frontend P010 control-centre slice:
- `npm test -- --run src/test/AdminResearchControlCentre.test.tsx`
- result: `4 passed`

Full frontend suite:
- `npm test`
- result: `7 files, 26 tests passed`

Frontend build:
- `npm run build`
- result: `PASS`
- note: inherited Vite large-chunk warning remains

Runtime smoke:
- `py -3.11 scripts/run_p001_smoke.py`
- result: `PASS`

Full Python suite:
- `py -3.11 -m pytest -q`
- result: `430 passed, 1 warning`

Schema reconciliation completed:
- tracked `schemas/research/*.schema.json` now include promotion, preflight, rollback, and index-sync schemas.
