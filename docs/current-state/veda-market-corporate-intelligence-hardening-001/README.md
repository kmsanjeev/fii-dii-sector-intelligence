# VEDA-MARKET-CORPORATE-INTELLIGENCE-HARDENING-001

Status: IN IMPLEMENTATION pending final acceptance

This activity hardens the existing provider-owned Corporate Intelligence
surface. It introduces no new data provider, scheduler, retriever, predictive
model, LLM classifier, or source-ownership transfer.

Starting FII-DII commit: `ebcc058e1bcbb8bb2fcdb49b76758db6ad14f300`

Starting VEDA commit: `004b7618991a158e7bb0ad54be9cffb0e18b6cd3`

The authoritative endpoint remains `GET /api/corporate/summary`. The additive
contract is `corporate-intelligence-1.0`; legacy KPI fields remain available in
`legacy_summary` and at the top level for compatibility.

Hard boundaries:

- disclosure is not completion, revenue, price direction, or a recommendation;
- announcement, effective, record, completion, period-end, filing and
  retrieval dates remain distinct;
- scheduled events are not treated as completed events;
- an order, MOU/LOI, board approval, fundraising approval or acquisition
  announcement is not treated as execution or receipt of funds;
- corporate evidence is factual context, not predictive evidence;
- institutional deal tape, financial metrics and AI sentiment remain owned by
  their existing contracts and are not duplicated here.

The detailed source, lifecycle, contract, integration and validation records
are in the files in this directory.
