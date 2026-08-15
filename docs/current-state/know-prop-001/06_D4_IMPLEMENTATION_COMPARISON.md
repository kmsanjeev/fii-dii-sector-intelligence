# D4 Implementation Comparison

Current state: `CALCULATION_ONLY` / `IMPLEMENTED_WITH_CONDITIONS`, not interpretively validated.

The inspected reference method divides each sign into four 7°30' portions and assigns the portions to the sign itself and the 4th, 7th and 10th signs. VEDA's generic branch uses same-sign for odd signs and 7th-sign start for even signs across unsupported methods. It therefore cannot be labeled a match to the inspected D4 method.

| Item | Result |
|---|---|
| D4 output exists | YES |
| Source-specific calculation match | MATERIAL_MISMATCH / UNVERIFIED |
| Interpretive property validation | NOT_IMPLEMENTED |
| Birth-time sensitivity | HIGH near 7°30', 15° and 22°30' boundaries; house/Lagna sensitivity also applies |
| D1-first fallback | PRESERVE |
| Production enablement | NO |

Engineering ownership: `P015-RX_REQUIRED` for source-selected D4 calculation remediation; `P029-R1_REQUIRED` only for later P029 interpretation integration.

