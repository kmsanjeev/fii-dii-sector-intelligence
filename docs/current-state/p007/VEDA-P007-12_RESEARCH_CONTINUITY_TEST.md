# VEDA-P007 Research Continuity Test

P007 explicitly proves that Admin latency does not block later research work.

## Verified Behaviors

- a pending astrology candidate remains pending while later runs continue
- later runs enrich the same candidate instead of creating duplicate queue items
- a rejected provenance candidate remains comparable on later rediscovery
- `NEEDS_MORE_RESEARCH` creates exactly one follow-up mission
- follow-up work preserves candidate identity
- candidate merge events now record before/after state in the ledger

## Snapshot Evidence

- pending claim candidate support count after rerun: `2`
- rejected provenance candidate support count after rediscovery: `4`
- rejected provenance candidate evidence ids after rediscovery: `8`
- follow-up missions: `1`
