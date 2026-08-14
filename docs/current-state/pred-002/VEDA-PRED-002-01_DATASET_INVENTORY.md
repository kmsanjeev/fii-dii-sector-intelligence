# Dataset Inventory

Existing `data/` contains approximately 40,773 files, dominated by runtime, validation, research, market, cache, and platform artifacts. `tests/fixtures/` contains three governed fixture files. The repository contains astrology research observations and comparison records, but those are not automatically historical prediction cases: many are source/research comparisons and do not establish that an outcome was unknown at prediction time.

Classification:

| Class | Available use | Empirical proof |
|---|---|---|
| REAL_VERIFIED | No qualifying cohort identified | Not claimed |
| REAL_USER_REPORTED | Contract supported; no production record | Not claimed |
| HISTORICAL_DOCUMENTED | Research artifacts exist | Cutoff review required |
| WORKED_CASE | Ingestion contract and pilot runner exist | Not proof without outcome verification |
| SYNTHETIC / TEST_FIXTURE | Pipeline tests only | Excluded |
| UNVERIFIED / UNUSABLE | Research or runtime context | Excluded |

No synthetic record is included in production performance statistics.
