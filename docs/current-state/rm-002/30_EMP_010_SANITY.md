# VEDA-EMP-010 First-Ten Sanity Gate

Status: `PASS_WITH_CONDITION`
Date: 2026-08-16

## Result

The shared CaseRegistry contains 10 `HISTORICAL_VERIFIED` cases with
`leakage_status=VALID`. The deterministic sanity runner reports:

- Case count: `10 / 10`
- Quality: `10 MODERATE`
- Timezone: `8 RESOLVED`, `2 BOUNDED`
- Event precision: `10 EXACT`
- Event classes: `DEATH=10`
- Identity confidence: `7 HIGH`, `3 MODERATE`
- Chart-based selection: `FALSE`
- Predictive accuracy claim: `FALSE`

## Conditions

Nine event records are currently referenced-Wikidata-only and therefore remain
lower-confidence until independently corroborated. The corpus has only one
event class, so it is a pipeline sanity corpus rather than a method-comparison
corpus. Governed chart facts are not generated from guessed coordinates;
latitude/longitude resolution remains a data dependency.

## Decision

EMP-010 sanity passes its acquisition, provenance, leakage and reproducibility
checks with conditions. No rule tuning, predictive accuracy, calibration, or
astrological outcome claim is authorized. The next target is EMP-025, with
independent event-source expansion and event-class diversity prioritized.
