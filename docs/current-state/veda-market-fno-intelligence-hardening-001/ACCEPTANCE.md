# Acceptance register

| Gate | Final status |
|---|---|
| A - source/schema | PASS_WITH_CONDITION: observed local NSE schemas mapped; formal source documentation remains source-conditioned |
| B - contract/expiry | PASS: nearest, most-active, expiry and roll are distinct and tested |
| C - OI/positioning | PASS_WITH_CONDITION: source-reported OI change; roll and missing evidence suppress false state |
| D - options/PCR | PASS: stock/index scope and denominator behavior explicit |
| E - participant safety | PASS: ordinary bhavcopy never becomes participant stock attribution |
| F - integration | PASS: stock, cross-layer and portfolio context additive; VEDA provider query passed |
| G - performance/freshness | PASS_WITH_CONDITION: bounded reads and cache; cold 16.840 s, warm p50 0.122 s, p95 0.193 s |
| H - engineering/governance | PASS_WITH_CONDITION: full suites passed after API baseline synchronization; selective Git acceptance remains |

Full validation evidence:

- FII full suite: 1,359 passed before the expected API baseline synchronization; the affected 3-test contract suite passed after the four new governed F&O operations were recorded.
- VEDA platform full suite: all collected tests passed, with dependency deprecation warnings only.
- New F&O service, routes, engine and tests: Ruff clean.
- Direct-service deterministic digest: `2b6f562d15ca447732c0701c1ef2ec6ec3edee80257149f17f9c4ef61573279f` on repeated builds.
- Real HTTP FII and VEDA provider probes: PASS.

No Approved Core, RAG, PRED, EMP, ML, Jyotish, intraday, Theme-history or BEBOS change is authorized by this activity.
