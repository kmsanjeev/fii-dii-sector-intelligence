# Chandra Bala source audit

## Finding

The repeated operational candidate counts the event Moon sign inclusively from
the natal Moon sign over twelve signs. The commonly repeated standard table is
supportive at positions 1, 3, 6, 7, 10 and 11; neutral at 2, 5 and 9; and caution
at 4, 8 and 12.

This is retained as a diagnostic candidate only. Accessible modern witnesses
agree on the standard house set, but the primary Muhurta passage, exceptions and
the status of Paksha-dependent alternatives were not verified at passage level.

## Variant governance

The `PAKSHA_CONDITIONAL` variant records a later/practitioner convention that may
upgrade some otherwise neutral or caution positions under Shukla/Krishna Paksha.
It is isolated, never combined with the standard table, and is not used by any
production code.

No Chandra condition is a hard exclusion. Missing natal Moon sign, unresolved
birth data, or an uncertain derivation makes the personal factor
`NOT_EVALUABLE`; general Muhurta remains available.

## Decision

`CHANDRA_BALA_SOURCE_PARTIAL`; no production evaluator or API activation.
