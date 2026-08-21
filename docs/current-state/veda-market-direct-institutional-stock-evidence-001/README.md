# VEDA-MARKET-DIRECT-INSTITUTIONAL-STOCK-EVIDENCE-001

Status: `IMPLEMENTED_WITH_CONDITIONS`

This activity establishes the provider-owned `stock-institutional-evidence-1.0`
contract. It exposes disclosed NSE bulk/block activity and periodic ownership
snapshots through the existing stock-intelligence and cross-layer surfaces.

The direct daily stock-level FII/DII flow gate is:
`NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE`.
The direct sector-level FII/DII flow gate is:
`NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE`.

The implementation does not create a new provider, retriever, score, model,
prediction, recommendation, or data owner. Existing market-level participant
flows remain market context only.

See the companion decision, contract, source, validation and acceptance files
in this directory.
