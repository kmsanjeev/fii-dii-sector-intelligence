# VEDA-EMP-MARRIAGE-010 — First ten marriage cases

Status: `PILOT_COMPLETED_HOLDOUT_SCORED`
Date: 2026-08-16
Parent: `VEDA-SIGNAL-BREAKTHROUGH-001`

## Frozen signal

`VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001`, version `1.0.0`, remains frozen with
hash `b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080`.
The pilot used only the D1 seventh-house relationship and Vimshottari
Mahadasha lord. Jupiter transit and Antardasha were not added.

## Acquisition result

Ten distinct subjects were selected from the existing timed OGDB population.
Selection used birth quality, identity, event provenance, date precision,
coordinates and historical timezone usability only. No chart feature was used
for selection. All ten produced deterministic D1 chart snapshots after the
case ledger was frozen.

| Metric | Result |
|---|---:|
| candidates screened | 10 |
| birth-first | 10 |
| event-first | 0 |
| identity verified | 10 |
| marriage events | 10 |
| exact-day | 5 |
| month | 0 |
| year | 5 |
| primary sources | 0 |
| strong referenced | 6 |
| single referenced | 4 |
| chart-ready | 10 |
| Indian candidates / eligible | 0 / 0 |

The birth feed is the [OGDB timed-data download](https://opengauquelin.org/download/ogdb-time.csv.zip).
Event-source examples remain recorded in the machine artifact and include
public biographies for Brigitte Bardot, Arthur Ashe, Buzz Aldrin, Herb Alpert,
Charles Aznavour, James Arness, Don Ameche, Gaston Bachelard, Raymond Barre and
Konrad Adenauer.

## Freeze, controls and split

The deterministic split is Design: 4, Validation: 3, Holdout: 3. Each frozen
case contains a case hash, birth record, coordinate/timezone inputs, event
record, signal identity/hash, engine revision, chart snapshot and evaluation
lock. Controls were constructed before scoring as two matched subject windows
per case, excluding known marriage years. The artifact records 100
deterministic rotation-null values.

## Pilot state

The primary design-plus-validation view contains 7 cases: event-side signal
rate `3/7 = 42.86%`, matched controls `5/14 = 35.71%`, visible base-time
prevalence `46.63%`, event-minus-control `+7.14 percentage points`, and
event-minus-base `-3.77 percentage points`. Exact-day visible cases are `2/3`
and year-only visible cases are `1/4`. The primary result is
`NO_SEPARATION`.

The holdout was unsealed once under an explicit audit record after the signal,
cases, controls, observation rule and scoring specification were frozen. The
holdout is `3/3` signal present versus `2/6` controls; the all-ten combined
view is `6/10` versus `7/20` controls. These views are descriptive only and do
not establish predictive validity.

A prior artifact incorrectly included the unsealed holdout in the visible
rate. The scoring boundary was repaired and covered by focused tests. No
signal doctrine was changed, and no production prediction or confidence
calibration was performed.

## Governance preserved

- EMP-025 remains sealed and unchanged.
- EMP-050 general corpus remains 25/50.
- Public-role signal remains `PUBLIC_ROLE_SIGNAL_UNGOVERNABLE` and frozen.
- PRED-M4 remains `INSUFFICIENT_SAMPLE`.
- Approved Core and RAG are unchanged.
- Prospective personal marriage prediction remains `RESEARCH_RESTRICTED`.

Next automatic action: retain this result as descriptive evidence and continue
the independent `VEDA-EMP-MARRIAGE-025` replication ledger.

## Determinism review

The first post-commit rerun exposed nondeterministic ordering in the engine's
presentation-only yoga list. The acquisition artifact canonicalizes that list
before case hashing; the two-run artifact hash comparison passes. No chart
facts, signal doctrine or scoring result changed.
