# VEDA-MARKET-CROSS-LAYER-PERFORMANCE-RX1-001

Status: `VEDA_MARKET_CROSS_LAYER_PERFORMANCE_RX1_OPERATIONAL_WITH_CONDITIONS`

This bounded remediation investigated the cross-layer Market latency observed
after the fundamentals acquisition remediation. The result is a small,
semantics-preserving optimization in the existing institutional contract. No
new service, database, cache, provider, RAG store, or Market capability was
created.

The controlled post-remediation FII `STOCK_CONFIRMATION` path measured p50
`443.61 ms` and p90 `546.99 ms` over 20 warm requests. The formal VEDA path
measured p50 `431.13 ms` and p90 `615.28 ms`. The earlier approximately 4.1s
cross-layer observation was not reproduced as a steady-state condition on the
controlled host; a real request-scoped duplicate-computation defect was found
and removed.

Detailed evidence is in the benchmark, call graph, root-cause, remediation,
post-benchmark, validation, and acceptance records in this directory.

Boundaries preserved: Market ownership remains in FII-DII; institutional data
remains market-level context; fundamentals remain slower-frequency structural
evidence; FACT/SIGNAL/INTERPRETATION/PREDICTION remain distinct; RAG, ML,
PRED, EMP, Jyotish, identity, subscriptions, Personal Vault, BEBOS, and the
direct institutional-source decision were unchanged.
