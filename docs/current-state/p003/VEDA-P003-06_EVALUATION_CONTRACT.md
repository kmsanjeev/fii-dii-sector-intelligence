# VEDA-P003-06 Evaluation Contract

## Chart Fact Contract

P003 defines a normalized chart-fact envelope in:

- `schemas/astrology/chart_facts.schema.json`
- `data/veda/rules/contracts/chart_facts_contract.sample.json`

Current top-level sections:

- `lagna`
- `planets`
- `houses`
- `vargas`
- `dashas`
- `relationships`
- `metadata`

## Evaluation Result Contract

P003 defines the future rule-evaluation response shape in:

- `schemas/astrology/evaluation_result.schema.json`
- `data/veda/rules/contracts/evaluation_result_contract.sample.json`

Fields include:

- `rule_id`
- `matched`
- `conditions_met`
- `conditions_failed`
- `modifiers_applied`
- `exceptions_triggered`
- `activation`
- `confidence`
- `evidence`
- `outputs`

## Explainability Chain

The intended explainability chain is now representable as:

`OUTPUT -> RULE RESULT -> MATCHED CONDITIONS -> CHART FACTS -> RULE -> CLAIM -> PASSAGE -> SOURCE`

## Production Boundary

These contracts are not wired into the live kundli engines yet.

P003 defines the interface only.

Adapters and runtime rule evaluation remain future work.
