# Institutional-context decision

Final state: `MARKET_LEVEL_CONTEXT_ONLY`
Evidence type: `WEIGHT_ALLOCATED_MARKET_PARTICIPANT_CONTEXT`

Phase 6A allocates broad participant/F&O values by sector turnover weight. The
input is not a stock-level institutional transaction tape and therefore does
not establish that FII, DII, PRO or CLIENT money entered or exited a named
sector. The hardening preserves the legacy numeric fields for consumers but
adds an explicit scope and limitations block so the formal provider cannot
make that unsupported claim.

Valid statement: a sector can be a price/breadth leader while broad
institutional positioning is cautious. Invalid statement: FIIs are buying the
sector, unless a future governed stock-level source supports that attribution.

The feasible future lane, if source access changes, is a separately audited
`DERIVED_STOCK_LEVEL_CONFIRMATION` phase. This programme does not activate it.
