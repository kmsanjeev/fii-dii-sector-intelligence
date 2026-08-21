# Acceptance Register

| AC | Result |
|---|---|
| Existing structured sources audited first | PASS |
| Primary exchange lineage preserved | PASS |
| Corporate contract versioned and bounded | PASS |
| Announcement/effective/record/completion/freshness separated | PASS |
| Scheduled is not completed | PASS |
| Order/MOU/approval/fundraising/acquisition semantics preserved | PASS |
| Unknown categories preserved | PASS |
| Deterministic IDs and bounded deduplication | PASS |
| Canonical identity gate | PASS |
| Financial metrics remain fundamental-owned | PASS |
| Institutional deal tape not duplicated | PASS |
| Materiality is non-predictive | PASS |
| Stock/cross-layer integration remains contextual | PASS |
| Global normalization bounded before event construction | PASS |
| Live five-symbol HTTP 200 sample | PASS |
| FII focused tests/lint | PASS |
| VEDA focused tests/lint | PASS |
| RAG/PRED/EMP/ML unchanged | PASS |
| Raw provider files excluded from staging | PASS — no raw provider files in programme scope |
| Full repository suites | PASS — FII 1340 passed; VEDA platform suite exit 0 |
| Remote push/tag | PENDING ACCEPTANCE |

Decision target: `VEDA_MARKET_CORPORATE_INTELLIGENCE_HARDENING_OPERATIONAL_WITH_CONDITIONS`.
Conditions are source freshness/coverage, row-level retrieval metadata not
being present in legacy CSVs, and inherited repository-wide quality findings.
