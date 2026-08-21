# Fundamental contract

Contract: `fundamental-evidence-1.0`.

The additive payload is nested at
`stock_intelligence.facts.fundamental_evidence` and is passed through to the
cross-layer stock summary. Existing `facts.fundamentals`, endpoint fields and
`stock-intelligence-1.1` version are preserved for compatibility. VEDA remains
a read-only consumer; it does not calculate, score, or reinterpret the
provider evidence.
