# VEDA-P001-05 Preservation Registry

## Purpose

This registry identifies components that later phases must not casually rewrite. The category indicates how tightly future work should be controlled.

| Component | Classification | Why Preserve | Primary Evidence | Risk if Changed Carelessly |
| --- | --- | --- | --- | --- |
| Deterministic ephemeris-backed kundli calculations | `PROTECTED` | strongest current astrology asset; now golden-fixture protected | `tests/test_veda_astrology_golden.py` | silent astrology drift |
| Personal kundli chat path | `PROTECTED` | user-facing astrology flow with its own output surface and deeper dasha detail | `engines/ai/chatbot/tools/kundli_calculator.py` + golden fixtures | behaviour loss hidden behind chat |
| REST human kundli path | `PROTECTED` | operational backend kundli contract surfaced through `/api/kundli/human` | `backend/routers/kundli.py` + smoke + fixtures | API regression |
| Stock kundli path and cache usage | `PROTECTED` | operational AstroFinance-facing stock chart path with cached corpus | `/api/stocks/{symbol}/kundli` baseline test | stock report regression |
| Authentication and session layer | `CONTROLLED_CHANGE` | security-sensitive and now explicitly environment-governed | `backend/auth/*` + M001 tests | lockout or unsafe exposure |
| Broker credential flow | `CONTROLLED_CHANGE` | touches live trading credentials and local persistence | `engines/broker/sync_engine.py` + broker tests | token leakage or broken reconnects |
| Data loader startup path | `CONTROLLED_CHANGE` | backend runtime health depends on it; smoke currently shows `41 / 43` datasets loaded | `backend/services/data_loader.py` via `/health` | runtime degradation |
| Scheduler / pipeline control surface | `CONTROLLED_CHANGE` | background orchestration is mounted and active | `/api/pipeline/status` smoke | data freshness failures |
| Retrieval substrate / reviewed-memory workflow | `CONTROLLED_CHANGE` | present but not source-ready; tests exist beyond current chat integration | `engines/ai/knowledge/*` | evidence drift and hidden knowledge regressions |
| AstroFinance report integration | `CONTROLLED_CHANGE` | stock kundli is already tied into report surfaces | `frontend/src/pages/ReportPage.tsx` + stock kundli contract | degraded stock interpretation UX |
| Chat-engine retrieval-shadow expectations | `EXPERIMENTAL` | current test block shows drift between intended and wired behavior | `tests/test_veda_chat_engine.py` failures | false confidence if treated as stable |

## Handling Rule

For `PROTECTED` components:

- validate first;
- freeze with fixtures or contract tests;
- extend only behind explicit regression coverage.

For `CONTROLLED_CHANGE` components:

- changes are allowed only with targeted tests and smoke validation.

For `EXPERIMENTAL` components:

- do not treat them as stable product contracts until the implementation and tests are reconciled in a later authorised phase.
