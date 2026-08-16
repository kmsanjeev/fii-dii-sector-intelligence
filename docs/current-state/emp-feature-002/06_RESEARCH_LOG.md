# VEDA-EMP-FEATURE-002 - Research Log

Acquisition was birth-first from the existing 1,000-record outcome-free
population. The 20 selected source records were frozen in
`01_REPLICATION_COHORT_SOURCE.json` before feature calculation. The listed
URLs were retrieved on 2026-08-16 for identity/event verification; no feature
values were queried during selection.

Event precision in the frozen cohort: 8 `DAY`, 1 `MONTH`, 11 `YEAR`.
The event definition permits the source-recorded precision and does not
manufacture day dates. The primary unit is one qualifying event per subject.

The validation partition contains 14 subjects and the subject-level holdout
contains 6. Two controls are assigned per event at fixed offsets of 365 and
730 days. Event-shuffled and subject-event permutation nulls use deterministic
seeds and 2,000 iterations each; no iteration count was tuned after results.

