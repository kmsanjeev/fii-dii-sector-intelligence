# VEDA-EMP-MARRIAGE-025 — Marriage signal replication

Status: `REPLICATION_COMPLETED_25_CASES`
Date: 2026-08-16
Parent: `VEDA-EMP-050-SIGNAL-SEARCH-001`

## Scope and frozen signal

The replication reuses `VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001`, version `1.0.0`,
hash `b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080`.
The only scored condition is the frozen Mahadasha-lord relationship to the
natal seventh house. Antardasha, Jupiter/Venus transits, D9, weights, dignity
and new houses were not added. EMP-025 remains sealed.

## Acquisition

The expanded [OGDB timed-data feed](https://opengauquelin.org/download/ogdb-time.csv.zip)
provided 24,540 birth rows. Twenty-six marriage candidates were assembled by
birth/event provenance only; chart fit was not used. Twenty-five were eligible
and chart-ready. One candidate, Tina Di Lorenzo, was excluded because the
available birth record did not contain a time. The machine artifact retains all
source URLs and precision limitations: 20 strong-referenced and 5
single-referenced eligible cases, with 15 exact-day, 1 month-level and 9
year-level events.

## Replication design

The 25 eligible rows are split deterministically into Design 10, Validation 5
and Holdout 10. Each case receives two matched subject controls at event year
minus/plus five, using the same frozen Mahadasha/seventh-house evaluator.
Uniform adult observation is age 18 through 70 for the base-time comparison.

| Split | Cases | Event rate | Control rate | Base-time prevalence | Event-control |
|---|---:|---:|---:|---:|---:|
| Design | 10 | 60.00% | 35.00% | 43.02% | +25.00 pp |
| Validation | 5 | 60.00% | 30.00% | 46.04% | +30.00 pp |
| Holdout | 10 | 30.00% | 30.00% | 31.51% | 0.00 pp |
| Combined | 25 | 48.00% | 32.00% | 39.02% | +16.00 pp |

The holdout does not reproduce the design/validation separation. The combined
result is descriptive and insufficient for a predictive-maturity upgrade or
signal doctrine change. Prospective use remains `RESEARCH_RESTRICTED`.

## Independent review and determinism

Focused marriage and signal tests pass (`13 passed`). The replication script
was run twice; the output SHA-256 was identical on both runs:
`AD0826B7D4BF11E6BE5F8D667FD374CFD92290E7DCEE5B3E76EF3183CB417F63`.
The replication corpus hash is
`cf2a6bf3a5212ebc6a19b8a61c3099f2b9f88549ca758866ecb673e498e84952`.

## Governance decision

- `PRED-M4`: remains `INSUFFICIENT_SAMPLE`.
- EMP-050: remains at 25/50 general cases; this marriage lane is separate.
- Production runtime: unchanged; provider calls added: 0.
- Approved Core: unchanged; no autonomous promotion.
- RAG: unchanged.
- EMP-001: remains active longitudinal.
- COMM-002 and GROUP-001 human validation: unchanged/pending.
- The marriage signal remains research-only and does not authorize personal
  outcome certainty.
