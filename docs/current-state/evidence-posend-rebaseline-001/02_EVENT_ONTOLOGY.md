# POSITION_END Event Ontology

## Frozen future estimand

`FORMAL_EFFECTIVE_ROLE_END` is the primary future definition. It requires an
explicit effective cessation of a defined office, role or employment position.
Useful secondary definitions are `RETIREMENT_EFFECTIVE_DATE`,
`RESIGNATION_EFFECTIVE_DATE`, `TERM_COMPLETION` and `PUBLIC_OFFICE_END`.

The following are excluded from exact-day confirmatory use unless separately
defined and documented:

- inferred career completion;
- announcement date or decision date used as the effective end;
- last known activity or successor appointment used as a proxy;
- date of death used as a substitute for position end.

## Current cohort classification

All 20 raw labels are `RETIREMENT`, but all 20 source records currently support
only `CAREER_END_INFERRED` at YEAR precision. The cohort is therefore
`HETEROGENEOUS_EXPLORATORY_ONLY` for future inference: a shared broad theme is
present, but the current evidence does not establish one objective effective
event family.

Each subject receives one deterministic event ID. No subject has multiple
primary events in this frozen cohort. A future study must choose
`PRE_SPECIFIED_EVENT_TYPE` or `FIRST_ELIGIBLE_EVENT` before any feature result
is opened; repeated events must use clustered/repeated-event inference.

## Precision policy

DAY is eligible for a future confirmatory estimand only after all provenance,
risk-window, control and independence gates pass. MONTH is interval-censored
secondary evidence. YEAR is exploratory/acquisition evidence only. UNKNOWN is
not timing-study eligible. No synthetic January 1 or month-start dates are
allowed.
