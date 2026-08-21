# Acceptance register

| Gate | Result | Evidence |
|---|---|---|
| Existing acquisition reused | PASS | same provider-local engine and output |
| Official source transport repaired | PASS | HTTP 200 with identity encoding |
| Dynamic recent windows | PASS | Q4FY26/Q3FY26 derived at runtime |
| Missing issuers not suppressed by label | PASS | focused regression |
| Filing-date precision | PASS | full-year parser regression |
| Statement/restatement retention | PASS | canonical-key regression |
| Negative values and missingness | PASS | normalization regression and predecessor contracts |
| Idempotency | PASS | second live SHA-256/mtime unchanged |
| Current-quarter source freshness | PASS_WITH_CONDITION | upstream representative 2026-06-30 rows unavailable |
| Daily scheduler redesign | NOT IN SCOPE | results remains existing manual/backfill operation |
| No prediction/ML/EMP/RAG/Jyotish change | PASS | diff scope review |
| Approved Core change | PASS | count unchanged; no autonomous promotion |

Decision: `VEDA_MARKET_FUNDAMENTALS_ACQUISITION_RX1_OPERATIONAL_WITH_CONDITIONS`.

Next authorized activity: `VEDA-MARKET-CORPORATE-INTELLIGENCE-HARDENING-001`,
not started automatically.
