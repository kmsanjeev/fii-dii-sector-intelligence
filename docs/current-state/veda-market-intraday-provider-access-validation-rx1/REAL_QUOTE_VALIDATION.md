# Real quote validation

A single bounded batch quote request for exact RELIANCE and NIFTY identities
was attempted through the Dhan adapter. It was blocked by the known inactive
Data API plan. No N+1 loop, quote polling or fallback was used.

Result: `DATA_ENTITLEMENT_REQUIRED`; no quote freshness or market-depth result
is claimed.
