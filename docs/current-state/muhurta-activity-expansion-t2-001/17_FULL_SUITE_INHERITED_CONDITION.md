# Inherited full-suite condition

The predecessor T1 repository-wide pytest attempt reached the approximately
604-second command timeout. A timeout is not a pass and is not treated as a
T2 blocker by itself.

T2 changes are source contracts, machine-partial metadata, tests and
documentation; no shared production engine code is changed. Focused,
governance, contract, source-witness and current-production regressions are
the required validation lane. A separate repository test-performance
investigation remains recommended if the full-suite condition persists.
