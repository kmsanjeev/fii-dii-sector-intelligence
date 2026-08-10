# VEDA-P004 Calculation Issue Register

| Issue ID | Severity | Title | Impact |
| --- | --- | --- | --- |
| `VEDA-CALC-ISSUE-0001` | `HIGH` | Ephemeris mode is implicit and currently resolves to Moshier fallback | Core planetary calculations are deterministic but not pinned to Swiss ephemeris files on this environment. |
| `VEDA-CALC-ISSUE-0002` | `HIGH` | Non-India stock exchange mappings ignore DST and historical zone transitions | Sampled Lagna shifts are roughly 10.5 to 12.4 degrees; Moon shifts are roughly 0.53 degrees. |
| `VEDA-CALC-ISSUE-0003` | `MEDIUM` | Country chart timezone provenance remains weak for pre-standard historical charts | Country chart behavior can be frozen and reproduced, but not every country inception time can yet be treated as research-grade chronology. |
| `VEDA-CALC-ISSUE-0004` | `MEDIUM` | Sidereal Ascendant derivation diverges slightly from swisseph sidereal-house reference | Most charts stay stable, but boundary births can change Lagna sign. |
| `VEDA-CALC-ISSUE-0005` | `MEDIUM` | Swiss Ephemeris sidereal mode remains shared process state across multiple modules | No direct numeric regression was reproduced in P004, but the cross-request risk is foundational. |

These issues were documented, not corrected, in accordance with the P004 change boundary.
