# VEDA-P003-04 Condition Language

## Supported Structure

Rule conditions support:

- `all`
- `any`
- `none`

Nested condition groups are supported recursively through `ConditionNode`.

## Atomic Condition Shape

An atomic condition can contain:

- `subject`
- `operator`
- `object` or literal `value`
- `value_entity_id` or `value_entity_ids`

## Operand Kinds

- `ENTITY`
- `FACT_PATH`
- `RULE`
- `CLAIM`
- `PASSAGE`
- `SOURCE`
- `CONFLICT`
- `LITERAL`

`FACT_PATH` operands are constrained to `chart.*` references.

## Controlled Operators

- `EQUALS`
- `NOT_EQUALS`
- `IN`
- `NOT_IN`
- `GREATER_THAN`
- `LESS_THAN`
- `BETWEEN`
- `OCCUPIES`
- `RULES`
- `ASPECTS`
- `CONJUNCT`
- `EXCHANGES`
- `RECEIVES_ASPECT`
- `EXALTED`
- `DEBILITATED`
- `OWN_SIGN`
- `MOOLATRIKONA`
- `PRESENT`
- `ABSENT`

## Modifiers

Supported modifier effects:

- `AMPLIFY`
- `REDUCE`
- `SUPPRESS`
- `CANCEL`
- `ACTIVATE`
- `CONFIRM`
- `ANNOTATE`

Live pilot usage:

- `VEDA-RUL-DIGNITY-000001` uses a modifier for the current `exalted_exact` degree window
- `VEDA-RUL-YOGA-000001` uses a modifier to mark conjunction-distance Gaja Kesari as stronger

## Exceptions

`VEDA-RUL-DASHA-000002` demonstrates explicit exception support:

- if alternate dasha scope is flagged in chart context
- the rule is suppressed instead of being treated as universally exclusive

## Cancellation / Confirmation

The schema supports:

- `cancelled_by_rule_ids`
- `confirmations`

No production rule execution uses these fields yet.
