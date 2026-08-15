# VEDA-EMP-025-R2 Corpus Completion Checkpoint

Status: `IN IMPLEMENTATION`
Parent: `VEDA-EMP-025-R1`
Date: 2026-08-16

## Gate state

| Gate | Requirement | Current | Status |
|---|---:|---:|---|
| eligible cases | >=25 | 21 | FAIL |
| chart-ready cases | >=20 | 21 | PASS |
| event classes | >=4 | 5 | PASS |
| official/primary or strong corroboration | >=50% | 12/21 (57.1%) | PASS |
| leakage | 100% valid | 21/21 | PASS |
| subject splits | frozen | 5/4/4 | PASS |
| controls | frozen | yes | PASS |

## New evidence

R2 converted existing high-priority leadership candidates into documented
multi-event subjects. George Ariyoshi, Cecil Andrus and Walter Annenberg add
officially sourced public-office transitions; Ariyoshi also adds an
officially documented election win. The U.S. Department of State Office of the
Historian provides primary appointment and mission dates for Annenberg, while
National Governors Association biographies provide institutional term records
for Ariyoshi and Andrus.

The adapter now retains every eligible event for a subject, uses distinct case
families for distinct events, and preserves year precision as year-level
evidence rather than falsely upgrading it to exact timing.

## Decision

EMP-025 method comparison remains `NOT READY` solely because the eligible-case
count is 21/25. Acquisition should continue with the remaining high-priority
leadership/science pools. No method result, accuracy claim, BAV/SAV activation,
or chart-based candidate selection is authorized.
