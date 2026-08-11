# VEDA-P010 Transactional Promotion

Promotion is implemented as an atomic service workflow.

Service stages:
1. create preflight record;
2. insert promotion record in `PROMOTING`;
3. materialize governed artifacts;
4. upsert core knowledge;
5. run approved-core index sync;
6. finalize promotion state and ledger events.

Failure behavior:
- astrology file writes are wrapped in a reversible file snapshot;
- generic approved-core docs writes are reversible;
- failed promotions mark the candidate `BLOCKED`;
- failed promotions emit `PROMOTION_FAILED`;
- index sync is tracked separately from the authoritative core write.

This design prevents partial "source saved but claim missing" states from being reported as successful promotions.
