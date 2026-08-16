# VEDA-EMP-050 — Replication Signal 002 Final

Date: 2026-08-16
Status: `IMPLEMENTED / FROZEN` for the bounded replication activity
Activity: `VEDA-EMP-050-REPLICATION-SIGNAL-002`

## Decision

The immutable marriage signal `VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001` was
replicated with a separately acquired 25-case extension. The original and
extension cohorts are reported separately and were not pooled to conceal
cohort disagreement.

Final empirical status: `NO_SEPARATION_AT_EMP025`,
`NON_REPLICATING_PILOT_SIGNAL`. This is not a claim that the signal is false,
disproved, or validated. It is a bounded replication result.

No production astrology logic, PRED-M4, Approved Core, RAG, prospective
prediction status, or EMP-025 sealed corpus was changed.

## Cohort and metric results

| Cohort | Eligible | Chart-ready | Event rate | Matched control rate | Base prevalence | Event-control | Event-base |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original EMP-025 cohort | 25 | 25 | 0.48 | 0.32 | 0.3902 | +0.16 | +0.0898 |
| New independent extension | 25 | 25 | 0.28 | 0.26 | 0.3615 | +0.02 | -0.0815 |
| Combined descriptive view | 50 | 50 | 0.38 | 0.29 | 0.3758 | +0.09 | +0.0042 |

The extension split was also scored descriptively: design 10, validation 5,
and holdout 10. Their event-control differences were 0.00, 0.00, and +0.05
respectively. These are not predictive-validity claims.

One additional candidate, `MARRIAGE-046`, was excluded because the source
record has no birth time. Jacques Bardoux (`MARRIAGE-052`) was added from the
full OGDB feed to complete the authorized 25-case extension; the event source
records a 7 February 1899 marriage date. No chart-fit selection was used.

## Signal governance

- Signal version: `1.0.0`
- Immutable signal hash: `b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080`
- Original status preserved: `NO_SEPARATION_AT_EMP025`
- New status: `NO_REPLICATION_OF_SEPARATION`
- Pilot disposition: `NON_REPLICATING_PILOT_SIGNAL`
- General EMP-050 remains a separate `25/50` acquisition programme; the
  marriage lane is now a completed 50-case replication lane.
- Current scoring is a research artifact only; no signal activation occurred.

## Second source-governable signal search

The priority families were audited without freezing a second signal:

| Candidate | Status | Blocking issue |
|---|---|---|
| Progeny | `SOURCE_PARTIAL` | D7 interpretation and dated event timing are not validated; historical and gendered rules need context. |
| Education | `SOURCE_PARTIAL` | Start/completion/higher-study taxonomy is not source-governed; D24 remains cross-domain context. |
| Career commencement | `SOURCE_PARTIAL` | No deterministic event-specific commencement signal is frozen; the public-role signal search found none. |
| Relocation | `SOURCE_PARTIAL` | Existing travel/residence sources do not define a validated dated relocation event method. |
| Property acquisition | `SOURCE_PARTIAL` | D4 interpretation remains gated and property timing is not frozen as a deterministic signal. |

Decision: `NO_SECOND_SOURCE_GOVERNABLE_SIGNAL`. No second signal was frozen,
and no v2 or production implementation was started.

## Source and acquisition boundaries

The extension uses OGDB chart records plus individually recorded event sources.
Several events are year-precision or single-reference records, so the result
is deliberately a replication artifact rather than a claim of classical or
predictive validity. Event-first and India-specific acquisition were not
represented in this lane: candidates searched 0, event-first verified 0,
India-specific eligible 0.

The original EMP-025 holdout remains sealed. EMP-001 remains active
longitudinal. `PRED-M4` remains `INSUFFICIENT_SAMPLE` and predictive maturity
remains `PRED-M3_OPERATIONAL_PLUS`.

## Engineering and governance outcome

Engineering completion: complete for the authorized bounded replication and
second-signal audit. Evidence completion: partial; the marriage separation did
not replicate. Predictive validation completion: insufficient.

No P031-R1, P015-RX2, P032, Muhurta, Prashna, LANG-002+, RAG rebuild, Approved
Core promotion, COMM-002 status change, or GROUP-001 status change occurred.

Focused tests cover the immutable signal, cohort isolation, 50-case threshold,
the missing-time exclusion, and deterministic second-signal disposition.
The generated artifacts are:

- `data/veda/research/empirical/veda_emp_marriage_050_replication.json`
- `data/veda/research/empirical/veda_emp_050_second_signal_audit.json`

The next authorized activity is not another signal implementation. It is a
future source-governance decision on one of the five partial families, or
legitimate prospective/empirical intake under the existing contracts.
