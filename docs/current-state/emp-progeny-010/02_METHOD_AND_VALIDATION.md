# Method and Validation Register

## Predeclared scoring

- Signal: `VEDA-SIGNAL-PROGENY-OCCURRENCE-001` v1.0.0, hash frozen before
  outcome inspection.
- D1 only: fifth-lord structural gate plus the Jupiter Mahadasha/Sun
  Antardasha lane. No D7, no other Dashas, no transits, weights or empirical
  tuning.
- Event windows respect precision: exact day, month, or year. No false day
  precision is manufactured for year-only events.
- Controls are the same subject and same event precision at minus/plus five
  years. Base prevalence is measured over ages 18 through 70, frozen before
  scoring.
- Primary metric is event rate minus matched-control rate, with event rate
  minus base-time prevalence reported alongside it.

## Ordering and determinism

Each case contains a deterministic case hash and
`evaluation_lock=FROZEN_BEFORE_SIGNAL_EVALUATION`. The holdout split was
protected during the primary design/validation calculation and has a one-time
unseal record with signal hash, corpus hash, scoring-spec hash and baseline
commit. Two independent artifact generations were byte-identical.

Focused validation: `7 passed`. The pilot result is `NO_SEPARATION` with all
three reported primary rates equal to zero. This is retained as
`NO_SEPARATION`, not relabeled as proof, failure of the source text, or a
production decision.

## Governance

`APPROVED_CORE` is unchanged; no RAG rebuild occurred; provider calls added
are zero; PRED-M4 and EMP-001 statuses are unchanged. Marriage v1 remains
retired after its separate replicated no-separation result. P031/P032,
Muhurta, Prashna, LANG-002+ and human-validation statuses were not changed.
