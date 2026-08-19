# Remediation plan

1. Bound existing-logic inventories to governed source, test, documentation,
   and small research/validation roots. Keep recursive fallback for synthetic
   roots.
2. Add a deterministic catalog/runner for Fast Core, Domain Regression, Full
   Deterministic, and External/Integration gates.
3. Keep scientific permutation counts and source/XML processing unchanged;
   optimize them only in a separately authorized empirical/calculation phase.
4. Do not add xdist yet. The suite contains mutable files, generated RAG
   artifacts, subprocesses, provider clients, and global state; parallelism
   requires a later isolation proof.
