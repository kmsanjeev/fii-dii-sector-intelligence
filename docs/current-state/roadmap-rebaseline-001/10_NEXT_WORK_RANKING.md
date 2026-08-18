# Next Work Ranking

## Top three candidates (not started)

1. **VEDA-EVIDENCE-POSEND-REBASELINE-001** - Reconcile the acquired
   POSITION_END cohort with the evidence-rebaseline source/date/risk-set
   requirements before any scoring. It has the best immediate dependency
   unlock and remains feature-blind.
2. **VEDA-CALC-ASHTAKAVARGA-DECISION-001** - Resolve the source-to-code BAV/SAV
   implementation contract or explicitly split methods. It addresses a real
   calculation trust gap but has higher method risk.
3. **VEDA-EVIDENCE-ADB-FORMAL-ACCESS-001** - Execute the prepared formal ADB
   access path after human/provider/legal review. It has the highest evidence
   value but is not autonomous.

## Primary next programme recommendation

**ID:** `VEDA-EVIDENCE-POSEND-REBASELINE-001`

**Title:** Feature-blind POSITION_END evidence redesign

**Mission:** Make the acquired POSITION_END cohort compatible with the
evidence-rebaseline requirements for provenance, date precision, risk sets,
controls and multiple-testing before authorizing `EMP-FEATURE-003-R1` scoring.

**Why now:** The cohort is frozen and chart-ready, but the evidence lane
explicitly blocks scoring until the redesign is complete. This is a bounded
governance dependency, not a new prediction feature.

**Prerequisites:** `VEDA-EVIDENCE-REBASELINE-001`,
`VEDA-EMP-POSEND-ACQ-001`, frozen cohort and feature-family hashes.

**Success criteria:** deterministic redesign register; provenance/date-risk
classification for every subject/event; protected holdout and controls;
explicit go/no-go; no feature scoring, outcome leakage, ML, production or
PRED-M4 change.

No next programme was started automatically.
