# Focused Threat Review

| Risk | Control | Status |
|---|---|---|
| PII disclosure | identity-vault separation, minimization | external review required |
| Document leakage | encrypted restricted storage, source hashes | external review required |
| ID enumeration | pseudonymous non-sequential external IDs | design required |
| Authorization bypass | least-privilege role policy | implementation review required |
| Withdrawal failure | immutable audit plus deletion workflow | unimplemented |
| Backup leakage | encrypted backups/key management | external review required |
| Export leakage | deidentified default export | synthetic test passed |
| Cross-participant access | subject-scoped authorization | implementation review required |

Threat review: `CONDITIONAL_EXTERNAL_REVIEW_REQUIRED`.
