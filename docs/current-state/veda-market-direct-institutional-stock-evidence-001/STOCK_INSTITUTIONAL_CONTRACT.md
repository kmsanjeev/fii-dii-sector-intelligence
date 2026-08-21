# Stock institutional evidence contract

Contract version: `stock-institutional-evidence-1.0`.

The contract contains `symbol`, `isin`, `identity`, `scope`, component-wise
`as_of`, `data_status`, `direct_transactions`, `bulk_deals`, `block_deals`,
`ownership.latest`, `ownership.prior`, `ownership.change`,
`participant_classes`, `derived_signals`, `evidence_quality`, `facts`,
`signals`, `interpretation`, `limitations` and `provenance`.

Missing sections remain missing. The contract is exposed inside the existing
`stock-intelligence-1.1` result and is consumed by cross-layer stock summaries.
No new endpoint or duplicated stock calculation was created.
