# Implemented remediations

- Added `engines/common/repository_inventory.py` with deterministic governed
  roots and a synthetic-root fallback.
- Reused that iterator in the P024, P025, and P026 existing-logic inventories.
- Added `scripts/veda_engineering_test_suite_performance_rx1_001.py` for
  disjoint cataloging and bounded gate execution.
- Added three infrastructure regression tests covering scope exclusion,
  fixture fallback, and catalog disjointness.

The P024/P025/P026 focused path improved from approximately 295.5 seconds
before the change to 42.21 seconds after it, with 26/26 passing. No product
engine, source rule, RAG semantic record, prediction state, or Approved Core
record changed.
