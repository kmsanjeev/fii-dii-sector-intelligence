# D20 Implementation Comparison

## Independent diagnostic reconstruction

For a longitude within a sign, the source division index is `floor(degree / 1.5)`, with 20 one-degree-thirty-minute divisions. The inspected BPHS passage gives category starts: movable → Aries, fixed → Sagittarius, dual → Leo. VEDA’s current fallback instead uses zero-based sign parity: even index → same sign, odd index → sixth sign from it.

| Input sign | Source category | Source start | VEDA generic start | Result |
|---|---|---|---|---|
| Aries | movable | Aries | Aries | Match for this case only |
| Taurus | fixed | Sagittarius | Scorpio | Material mismatch |
| Gemini | dual | Leo | Gemini | Material mismatch |

The source also provides deity sequences for the Vimshamsha parts. VEDA currently returns a sign, not a source-verified deity assignment. Therefore the current implementation is `MATERIAL_MISMATCH` for source-specific D20 calculation, not merely a minor variant.

## Decision

`D20_METHOD_VARIANTS_REQUIRE_SPLIT` and `D20_ENGINEERING_REMEDIATION_REQUIRED` are recommended for future P015-RX2. No repair is made here. P031 remains D1-first and interpretive D20 use remains disabled.
