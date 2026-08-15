# VEDA-MUH-R1 — Governed Muhurta Foundation Master Prompt

## Authorization

Implement the next activity after `VEDA-MUH-FND-001`: a deterministic,
source-aware Panchanga/electional foundation. This phase may add reusable
astronomical facts and contracts, but it must not become a recommendation
engine.

## Scope

- Add a date/location/timezone request contract.
- Compute deterministic approximate local sunrise and sunset with explicit
  method/version metadata and polar-day missing states.
- Preserve birth-time Tithi, Vara, Nakshatra, Yoga and Karana as reused context,
  not as electional results.
- Add a governed event taxonomy without event-specific rules.
- Return explicit gates for Tarabala, Chandrabala, event rules and scoring.
- Keep activation `INACTIVE` and recommendation `NOT_IMPLEMENTED`.
- Add focused fixtures, documentation and capability-registry metadata.

## Prohibited

- No auspiciousness score, date ranking, muhurta recommendation or automatic
  electional window.
- No Tarabala/Chandrabala implementation without passage-level validation.
- No Rahu Kalam/Yamaganda/Gulika/Abhijit/Durmuhurta rule engine in this phase.
- No Prashna, query-time horary chart, P032, LANG-002+, D20 remediation or RAG
  store.
- No changes to P031, P030, EMP-001, predictive maturity or human-validation
  statuses.

## Required validation

Run the new foundation tests, affected Panchanga/P016/P030/P031/D20 tests,
`git diff --check`, an independent staged-diff review, and post-commit status.
Full repository testing is optional only if practical; do not call a timeout a
pass.
