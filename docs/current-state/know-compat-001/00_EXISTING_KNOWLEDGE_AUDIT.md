# VEDA-KNOW-COMPAT-001 Existing Knowledge Audit

Date: 2026-08-15

The existing P028-R1 engine is `ASHTAKOOTA_NORTH_INDIAN_RESEARCH_CANDIDATE`, version 1.0. It is deterministic, but its source is `REFERENCE_NOT_VERIFIED`. Existing P017/P024 records contain Manglik/Kuja research and unresolved scope, not a governed executable cancellation method. Existing chart calculations supply Moon sign and Nakshatra inputs; no separate astronomy was introduced.

Decision: retain the current implementation and trust boundary. This activity adds source-validation records only; it does not silently change scoring tables.

| Area | Existing | Reuse | Gap |
|---|---|---|---|
| Chart inputs | Deterministic chart pipeline | P015/P028 inputs | Boundary sensitivity remains explicit |
| Kuta calculation | `p028r1_traditional.py` | P028 traditional evidence seam | Several simplified tables differ from inspected reference tables |
| Provenance | P028-R1 metadata | STD-001 zones | No passage-level classical source confirmed |
| Manglik | P017/P024 research | Existing audit records | Method variants and cancellation unresolved |
| RAG | Unified 7-zone corpus | Existing rebuild pipeline | No semantic promotion in this activity |

