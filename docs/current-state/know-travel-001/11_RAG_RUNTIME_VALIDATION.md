# RAG and Runtime Validation

RAG changed: `NO`. No travel-specific retriever/store was created. `scripts/rebuild_unified_rag.py` was not run because no governed semantic corpus record changed.

Focused runtime evidence remains the frozen P030 test surface (`tests/test_veda_p030_travel.py`). The implementation preserves:

- travel vs relocation;
- foreign travel vs foreign residence;
- residence vs settlement;
- away-from-birthplace vs foreign mapping;
- D4 calculation metadata vs D4 interpretation gate;
- research-candidate authority labels;
- no immigration, legal, citizenship, financial or career-decision advice.

Sample-query governance passes conceptually and through the existing deterministic contract: answers must be conditional and source-aware. “Rahu”, “12th house”, or “strong 9th” cannot be rendered as permanent foreign settlement certainty.
