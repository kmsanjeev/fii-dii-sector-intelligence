# Determinism

- Collection is deterministic: 1,266 baseline tests, 1,269 after the three
  new infrastructure tests.
- Full after-remediation run: 1,266 passed; final run including the three
  infrastructure tests: 1,269 passed.
- Existing deterministic artifact tests passed.
- Inventory traversal is sorted by repository-relative POSIX path.
- No RAG rebuild or semantic content change was authorized by this activity.
- Generated RAG working-tree markers were refreshed and reconciled; no semantic
  diff remains.
