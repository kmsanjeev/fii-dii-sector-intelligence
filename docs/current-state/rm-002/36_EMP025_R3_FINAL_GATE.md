# VEDA-EMP-025-R3 Final Gate Closure

Status: `IMPLEMENTED / FROZEN` for the acquisition gate and pilot handoff
Date: 2026-08-16
Parent: `VEDA-EMP-025-R2`

## Deterministic gate register

| Gate | Requirement | Result | Status |
|---|---:|---:|---|
| eligible cases | >=25 | 25 | PASS |
| new accepted cases | >=4 | 4 | PASS |
| chart-ready cases | >=20 | 25 | PASS |
| event classes | >=4 | 5 | PASS |
| official/primary or strong corroboration | >=50% | 16/25 (64.0%) | PASS |
| leakage | 100% valid | 25/25 | PASS |
| subject splits | frozen | 5/4/4 | PASS |
| controls | frozen | yes | PASS |
| Indian lane | continue, non-blocking | 0 | PASS_WITH_CONDITION |
| prospective lane | continue, non-blocking | 0 | PASS_WITH_CONDITION |

## Corpus composition

The final corpus has 13 subjects and 25 eligible, chart-ready historical
cases. Event classes are `DEATH` 10, `POSITION_START` 6, `POSITION_END` 7,
`ELECTION_WIN` 1 and `PUBLIC_APPOINTMENT` 1. The four R3 additions are
year-precision public-office transitions for George Ariyoshi and Cecil Andrus,
retaining the source's year precision. Existing multi-event subjects remain
isolated at subject level for the frozen design/validation/holdout split.

The deterministic corpus manifest is
`data/veda/research/empirical/veda_emp_025_corpus_snapshot.json` with hash
`3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f`.
The manifest includes source/event identity, D1 chart readiness, the frozen
split, the no-leakage controls, knowledge cutoff and pilot scope. BAV/SAV are
excluded.

## Gate decision

All blocking acquisition gates pass. The corpus is frozen for the next
activity. No candidate was selected using chart agreement, no prediction
result was computed, and no empirical maturity upgrade is claimed.
