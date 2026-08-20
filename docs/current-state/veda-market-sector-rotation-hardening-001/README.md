# VEDA-MARKET-SECTOR-ROTATION-HARDENING-001

Status: `OPERATIONAL_WITH_CONDITIONS`
Implementation owner: `FII-DII-Sector-Intelligence`
Formal capability: `market.sector.intelligence`
Contract: `sector-rotation-1.1`
Endpoint: `GET /api/sectors`

This phase extends the existing Phase 6C sector rotation engine. It adds
bounded current-constituent returns, breadth coverage, relative strength,
leadership/persistence/rotation states, acceleration, date alignment and
evidence-quality fields. Legacy flow and price fields remain for compatible
consumers.

The result is deterministic market intelligence, not a forecast. The current
weighted participant allocation is explicitly exposed as
`MARKET_LEVEL_CONTEXT_ONLY`; it must not be described as sector-specific FII or
DII buying/selling.

## Scope and boundaries

- Sector and theme remain separate. This phase does not solve theme ontology.
- The canonical stock taxonomy is `company_classification_v4` and the current
  platform sector universe contains 27 sectors with classified symbols.
- Returns and breadth use an equal-weight current constituent universe.
- Historical constituent membership snapshots are unavailable, so historical
  breadth is survivorship-limited and labelled `CURRENT_CONSTITUENT_UNIVERSE`.
- Official NSE index files remain a legacy compatibility source and are date
  labelled; stale index output is not allowed to masquerade as current breadth.
- No Market data moved to VEDA, and no ML, prediction, RAG, EMP, Jyotish or
  BEBOS state changed.

See the companion inventory, taxonomy, constituent, contract, institutional
context, implementation and validation records in this directory.
