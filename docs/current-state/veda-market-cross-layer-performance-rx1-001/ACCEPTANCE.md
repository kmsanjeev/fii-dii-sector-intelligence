# Acceptance register

| Gate | Result | Evidence |
|---|---|---|
| A. Controlled reproduction | PASS_WITH_CONDITION | Pre-remediation 1.58s p50 reproduced; 4.1s historical sample not reproduced |
| B. Root cause measured | PASS | cProfile and call/read traces identify duplicate institutional rolling work |
| C. Bounded remediation | PASS | Request-scoped snapshot reuse and tail-bounded windows only |
| D. Semantic equivalence | PASS | Canonical hash unchanged |
| E. Freshness/invalidation | PASS | No process cache introduced; existing loader remains authoritative |
| F. Provider performance | PASS | FII p50 443.61ms; VEDA p50 431.13ms |
| G. Governance | PASS | Boundaries and contract versions unchanged |
| H. Engineering quality | PASS_WITH_CONDITION | FII focused suite 32 passed; full suite 1337 passed in 597.03s; VEDA unrelated Ruff/mypy baseline findings recorded |

Final decision: `VEDA_MARKET_CROSS_LAYER_PERFORMANCE_RX1_OPERATIONAL_WITH_CONDITIONS`.

The next programme is authorized but not started:
`VEDA-MARKET-CORPORATE-INTELLIGENCE-HARDENING-001`.
