# VEDA-MARKET-INSTITUTIONAL-FLOW-HARDENING-001

Status: `OPERATIONAL_WITH_CONDITIONS` (2026-08-21)

This activity hardens the existing FII/DII participant-flow surface. It is a
deterministic market-data contract, not a prediction or ML capability.

Current bounded scope:

- F&O participant OI and volume for FII, DII, PRO and CLIENT.
- FII futures-statistics field where the existing source provides it.
- Cash category flows for FPI, MF, INSURANCE and RETAIL where present.
- 1D, 3D, 5D, 10D and 20D rolling windows with explicit completeness.
- Persistence, acceleration and reversal as derived descriptive metrics.
- Existing FII/DII and smart/retail divergences.
- Provider-local freshness and evidence quality, distinct from prediction confidence.

Explicit non-claims: options and cash-vs-derivatives comparability are not
supported by the current source contract. No market prediction, PRED, EMP, ML,
RAG, astrology or VEDA data migration is included.

The additive contract passed focused and full FII regression validation,
72-test VEDA validation, live FII-to-VEDA HTTP validation, and local latency
checks. The remaining conditions are source coverage/freshness, unsupported
options/cash-vs-derivatives normalization, and preservation of unrelated
pre-existing generated/data changes during selective Git synchronization.
