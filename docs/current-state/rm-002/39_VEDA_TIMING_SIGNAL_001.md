# VEDA-TIMING-SIGNAL-001 — Public-Role Dasha Signal Governance

Status: `COMPLETED_WITH_NO_GOVERNABLE_SIGNAL`
Date: 2026-08-16
Parent: `VEDA-EMP-025-METHOD-PILOT`

## Decision

`NO_SOURCE_GOVERNABLE_PUBLIC_ROLE_SIGNAL`

The source audit found classical material about profession, authority,
government/king favor, loss of position and conditional Dasha/Antardasha
results. It did not establish a reproducible event-label contract for modern
`POSITION_START`, `POSITION_END`, `PUBLIC_APPOINTMENT` or `ELECTION_WIN`.
Those event classes therefore remain `NOT_GOVERNABLE` for the first EMP-025
pilot. No rule was selected by inspecting chart timing or by optimizing to the
25-case corpus.

## Evidence matrix

| Rule | Source evidence | Status | Event scope | Implementation |
|---|---|---|---|---|
| TS-001 | BPHS translated PDF, pp. 106-107, conditional authority/government results in named Antardasha conditions | SOURCE_PARTIAL | Possible authority/appointment context; not a general detector | Not implemented |
| TS-002 | BPHS translated PDF, p. 106, conditional loss of reputation/position | SOURCE_PARTIAL | Possible position-end theme; not a termination detector | Not implemented |
| TS-003 | Phaladeepika Ch. 5, profession/livelihood and tenth-lord/navamsha material | SOURCE_PARTIAL | Structural profession context; not event timing | Not implemented |
| TS-004 | VEDA P016 canonical timing governance | SOURCE_VALIDATED | Calculation facts only | Implemented calculation-only |
| TS-005 | Generic modern/legacy career combinations without verified passage | REJECTED | All event classes | Prohibited |

Sources inspected included the existing P016/P020/RM-002 corpus, the [BPHS
translated PDF](https://www.iswaryajyotisha.com/pages/library.php?book=Brihat+parspara+hora+sastra)
containing the Dasha/Antardasha passages, and the [Wisdomlib Phaladeepika
Chapter 5 translation](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621577.html).
The BPHS material is retained as
translation-dependent partial evidence; it does not justify flattening
historical authority language into modern elections or appointments. The
Phaladeepika material describes profession, not a dated public-role outcome.

## Signal contract outcome

No `signal_id` or `signal_version` was activated. A future contract may use
`SIGNAL_PRESENT`, `SIGNAL_ABSENT` and `SIGNAL_INDETERMINATE`, but no planet,
house, lordship, aspect, dignity, Sun/Saturn/Jupiter condition or reverse
position-end rule is admitted until separately source-governed.

The frozen method facts remain `VEDA-DASHA-VIMSHOTTARI`,
`P016_CANONICAL_TIMING`, Mahadasha and Antardasha, D1/Lahiri. Exact dates may
support narrow windows in a future pilot; year-level dates may only support
year-compatible overlap and must not be scored as exact-day timing.

## Impact

- EMP-025 rerun: `NOT_READY`.
- Holdout: sealed and not accessed.
- EMP-050 acquisition: continues in parallel.
- Prospective candidates: 0; no PRED-005 creation.
- RAG: unchanged; no new validated semantic claim was promoted.
- Approved Core: unchanged.
- Predictive validation completion: unchanged.

Next automatic action: select the next source-governable event/method pairing;
do not manufacture a public-role signal.
