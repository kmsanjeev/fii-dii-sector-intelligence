# VEDA-RM-002 Ashtakavarga Defect Closure

Status: `CALCULATION_DEFECT_CLOSED` / `METHOD_VALIDATION_PENDING`
Date: 2026-08-16

## Scope

This record closes the narrow deterministic defect identified in
`calculate_bav()`. The prior implementation computed qualifying contributors
but copied the resulting count into every target sign. The corrected path
assigns a qualifying bindu to the contributor's occupied sign, then emits the
twelve target-sign columns. `calculate_sav()` continues to aggregate those
columns.

## Evidence

- A deterministic chart with contributors in signs 4 and 7 produces bindus in
  those occupied target columns and zero in an unoccupied control column.
- The focused P018 and empirical-input suites pass: `63 passed`.
- The added test checks target-sign sensitivity and prevents regression to a
  repeated aggregate across all signs.

## Governance boundary

This is an engineering correction, not passage-level classical validation.
`VEDA-R2-CLM-000008` and `VEDA-R2-CLM-000009` remain research leads because
exact passage locators, edition details, school variance, and an independently
reviewed numerical witness are still unresolved. BAV/SAV remain
`IMPLEMENTED_UNVALIDATED` / `RESEARCH_REQUIRED`; predictive, empirical,
prospective, production, and Approved Core use remain unauthorized.

## Next admissible activity

Continue the bounded passage audit for contributor semantics and method
variants. Do not widen Ashtakavarga interpretation or use it for empirical
case selection until that audit is independently reviewed.
