# VEDA-EMP-025 Method Pilot Gate Audit

Status: `COMPLETED_WITH_PRIMARY_SCORING_STOP`
Date: 2026-08-16
Parent: `VEDA-EMP-025-R3`

## Corpus and primary sample

The corpus hash was verified as
`3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f`.
The public-role primary family contains 15 eligible events across 4 subjects:
`POSITION_START` 6, `POSITION_END` 7, `PUBLIC_APPOINTMENT` 1 and
`ELECTION_WIN` 1. Date precision is 2 `EXACT` and 13 `YEAR`; no year-level
record was treated as an exact-day event. Event membership is DESIGN 5,
VALIDATION 6 and HOLDOUT 4. Subject-level isolation remains frozen at 5/4/4
because several subjects contribute multiple events.

The frozen method facts contract is `VEDA-DASHA-VIMSHOTTARI`, version
`P016_CANONICAL_TIMING`, using the existing Lahiri D1 runtime, Moon Janma
Nakshatra remainder, Mahadasha and Antardasha facts. Pratyantardasha was not
used.

## Mandatory scoring gate

`P016` governs deterministic Dasha timing facts, but the repository has no
source-governed event-specific public-role Dasha signal definition. Therefore:

- Signal governance: `FAIL`
- Method result state: `INSUFFICIENT_SIGNAL_GOVERNANCE`
- Primary scoring: `STOPPED`
- Design run: `NOT_RUN`
- Validation run: `NOT_RUN`
- Holdout: `SEALED_NOT_RUN`
- Rule invented after inspection: `NO`

No event-window or control-window signal counts, rates, differences, null
comparison or empirical separation claim are reported. Controls are retained
as a specification only: matched time windows, event-date shuffles,
subject/event permutations, bounded time perturbation and a random baseline.
None was generated from Dasha output.

## Holdout audit

Holdout outcomes were not accessed. The holdout remains sealed because the
signal, windows and scoring rule were not governed and validation did not
complete. No unseal event exists.

## Decision and next activity

This is a valid bounded negative result, not a corpus failure and not evidence
against Vimshottari. Classical authority and empirical performance remain
separate. The next activity is `TIMING_VALIDATION_SOURCE_SIGNAL`: establish a
source-governed, reproducible event-specific signal before any scoring run.
No production behavior, Approved Core, RAG authority, ML weight or predictive
maturity changed. `PRED-M4` remains `INSUFFICIENT_SAMPLE`.
