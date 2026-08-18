# Roadmap Drift and Reconciliation

## Corrected current references

1. The future registry contained a duplicate/stale `P030 | Next Jyotisha
   capability | NOT STARTED` row, conflicting with the frozen P030 row above it.
2. `docs/PROJECT_MASTER_STATE.md` had older P029/P030 `not started` lines
   immediately before later lines saying P029/P030 were implemented.
3. `VEDA-RM-001-11_NEXT_PHASE_RECOMMENDATION.md` was the historical RM-001
   recommendation to populate ADM-EMP-001, but ADM-EMP-001 is now implemented.
   It now points to this rebaseline while preserving the old recommendation.

## Preserved history

Historical acceptance records, old RM-001 baselines, and prior programme reports
were not rewritten. No stale reference justified changing calculation semantics,
prediction maturity, ML, RAG or production authorization.

The completed Hindi source-review activity and this rebaseline are now
represented in the current registry without authorizing another locale or
feature.

The tracked `docs/roadmap/veda/LOOP_STATE.json` is an idle controller checkpoint
whose last activity predates the later governed programmes. It has no active
activity and was not rewritten here because its schema is controller-runtime
history; the current roadmap decision is recorded in the rebaseline artifacts.
