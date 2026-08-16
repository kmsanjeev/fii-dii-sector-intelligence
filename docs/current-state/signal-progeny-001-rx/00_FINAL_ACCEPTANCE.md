# VEDA-SIGNAL-PROGENY-001-RX — Empirical Viability Audit

Status: `PASS_WITH_CONDITION`

## Decision

The frozen signal is computationally reachable, but its event-time activation
prevalence is near zero. The ten-case result is therefore more precisely
classified as:

`SIGNAL_TOO_SPARSE_TO_TEST_AT_EMP010`

The raw EMP-PROGENY-010 result `NO_SEPARATION` is preserved. No childbirth
outcomes were read or joined during this audit.

## Signal verification

| Field | Result |
|---|---|
| Signal | `VEDA-SIGNAL-PROGENY-OCCURRENCE-001 v1.0.0` |
| Hash | `564bec942c8361ad1f3292093c9b067d72ebf17aea07fc7f69bd6740e1c4a8db` |
| Positive fixture | `SIGNAL_PRESENT` |
| Negative fixture | `CONDITIONAL_BLOCKED` |
| Missing-input fixture | `INDETERMINATE` |
| D7 / extra timing methods | Not used |
| Signal changed | `NO` |

The independent audit reconstructs D1 fifth-lord ownership, exaltation,
Jupiter conjunction/aspect, Vimshottari Mahadasha/Antardasha intervals and
the ages 18–70 observation window. A deterministic positive fixture proves the
contract is reachable; zero prevalence is not an implementation-unreachable
artifact.

## Outcome-blind population

The deterministic OGDB timed-birth sample requested 1,000 rows and produced
999 usable subjects after ordinary chart/timezone readiness filtering. No
childbirth labels, family fields or event corpus were joined.

| Metric | Value |
|---|---:|
| Subjects analyzed | 999 |
| Subjects with any signal | 64 |
| Subject activation rate | 6.4064% |
| Total observation years | 52,946.7488 |
| Signal-present years | 51.2 |
| Time-weighted prevalence | 0.0967% |
| Mean subject prevalence | 0.0967% |
| Median subject prevalence | 0% |
| Zero-signal subjects | 935 |
| Indeterminate subjects | 0 |

Subject-level reachability is `LOW_PREVALENCE`; event-time reachability is
`NEAR_ZERO_PREVALENCE`. The latter governs childbirth sample feasibility.

## Bottleneck decomposition

- Structural condition rate: `62.4625%`
- Jupiter Mahadasha rate: `70.8709%`
- Jupiter Mahadasha + Sun Antardasha rate: `55.6557%`
- Structural + timing candidate rate: `35.4354%`
- Final combined signal rate: `6.4064%`
- Primary sparsity cause: `COMBINED_FILTER`

The observed signal duration is too short for a 25-case childbirth pilot to
expect meaningful activation.

## Sample feasibility

Expected signal-positive events using the measured time-weighted prevalence:

| Childbirth cases | Expected signal-positive cases |
|---:|---:|
| 10 | 0.00967 |
| 25 | 0.024175 |
| 50 | 0.04835 |
| 100 | 0.096701 |
| 250 | 0.241752 |

`EMPIRICAL_VIABILITY = INSUFFICIENT_PREVALENCE`.

Do not blindly acquire EMP-PROGENY-025 for this v1 signal. Freeze the
empirical feasibility finding and pursue separate, independently sourced
signal research only. Source status remains `SOURCE_GOVERNABLE`.

## Governance

PRED-M4, production behavior, Approved Core, RAG, EMP-001, marriage v1,
human-validation states and the frozen signal are unchanged. No v2 was
created. The audit artifact is
`data/veda/research/empirical/veda_signal_progeny_001_rx.json`.
