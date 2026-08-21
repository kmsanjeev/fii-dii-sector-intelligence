# Cross-layer model

The contract composes five evidence groups: Market, institutional, sector,
stock and fundamental/corporate context. It emits `ALIGNED`,
`PARTIAL_CONFIRMATION`, `CONFLICTING` or `INSUFFICIENT_EVIDENCE`.

Stock/sector states are deterministic: aligned strong leadership, stock
outperformance inside a weak sector, a weak stock inside a leading sector, or
aligned weakness. No universal aggregate score is created.

Candidate discovery is bounded to at most 10 sectors and 5 stocks per sector,
with defaults of 5 and 3. Selection uses upstream sector leaders/laggards and
existing stock relative-strength/trend/volume/evidence fields.
