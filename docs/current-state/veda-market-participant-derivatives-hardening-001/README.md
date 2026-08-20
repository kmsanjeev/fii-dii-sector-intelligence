# VEDA-MARKET-PARTICIPANT-DERIVATIVES-HARDENING-001

Status: `OPERATIONAL_WITH_CONDITIONS` (2026-08-21)

This activity hardens the existing provider-local participant-flow contract.
It does not create a derivatives prediction engine and does not move Market
data, calculations, ML, RAG, EMP or Jyotisha logic into VEDA.

The source audit establishes that NSE participant files expose index-futures,
stock-futures and option buckets. The persisted history used by the current
runtime intentionally retains only aggregate futures participant net OI and
volume. The public contract now states that boundary explicitly, separates
position level from position change, reports persistence/acceleration/reversal,
adds same-basis participant divergence, and reports F&O/cash date alignment.

Options, long/short ratios, gross long/short breakdowns and cash-versus-
derivatives normalization remain unsupported. The change is additive minor
version `institutional-flow-1.1`; the legacy `/api/participant/latest` and the
formal `/api/participant/institutional` endpoint remain available.

Decision: `VEDA_MARKET_PARTICIPANT_DERIVATIVES_HARDENING_OPERATIONAL_WITH_CONDITIONS`.

See the accompanying inventory, semantics, contract, validation and acceptance
records in this directory.
