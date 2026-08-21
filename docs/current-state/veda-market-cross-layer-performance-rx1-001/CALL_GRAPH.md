# Call graph and execution audit

## Stock confirmation

`market router`
→ `build_cross_layer_intelligence`
→ market snapshot
→ institutional snapshot
→ sector snapshot
→ explicit-symbol stock contract
→ alignment/conflict/freshness/evidence-quality composition
→ JSON response.

The stock-confirmation branch does not call `_build_candidates`; it does not
evaluate the whole market or perform leadership discovery. The FII service does
not issue self-HTTP calls. VEDA invokes one bounded FII provider endpoint over
its persistent HTTP client and does not recalculate the Market result.

## Findings

- Before remediation, `build_institutional_contract` built the same F&O
  participant snapshots for the primary participant result, divergence, and
  quality calculation, and rebuilt cash snapshots for the primary result and
  quality calculation.
- The rolling helper processed the complete historical series even though only
  the current largest requested window can affect the returned snapshot.
- Fundamental evidence performed symbol lookup over provider-local frames and
  retained source/provenance semantics; it was measured at approximately
  `0.16s` in the local profile and was not the primary cost center.
- Corporate summary/stock corporate context was measured as non-material.

## Request reads

On a cold symbol-contract path after clearing identity/evidence memoization,
one cross-layer request observed four CSV reads and one symbol price-parquet
read. The CSVs were the equity master, provider fundamentals master (identity),
provider fundamentals master (evidence lookup), and reference fundamentals
master (conflict comparison). The shared data loader already held the large
intelligence datasets in memory. No whole-market candidate loop or RAG read
was observed.
