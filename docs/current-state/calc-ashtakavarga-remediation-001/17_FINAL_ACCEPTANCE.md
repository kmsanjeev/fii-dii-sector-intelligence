# VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001 — Final Acceptance

Overall status: `BLOCKED`

Decision: `ASHTAKAVARGA_CANONICAL_CONTRACT_INCONSISTENT`

The contract ID and contract hash were verified. The 768-cell source matrix,
its 8 × 8 × 12 coverage, and its recorded row hash were independently
verified. Its target totals are:

| Target | Total |
|---|---:|
| Sun | 49 |
| Moon | 49 |
| Mars | 39 |
| Mercury | 54 |
| Jupiter | 54 |
| Venus | 52 |
| Saturn | 39 |
| Lagna | 49 |

The seven planetary total is 336, not the contract's 337. The optional
Lagna-combined total is 385, not the contract's 386. The programme explicitly
requires stopping rather than changing source cells from code assumptions.

Production implementation, canonical conformance, synthetic comparison,
legacy migration, reduction work and release tagging are therefore not
authorized by this run. The diagnostic script and this governed blocked-state
record are the only new implementation artifacts.
