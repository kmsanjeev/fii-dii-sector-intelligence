# Final Acceptance

- Activity: `VEDA-CALC-SHADBALA-COMPONENT-REMEDIATION-R1-001`
- Starting commit: `bae998b6457399649e09519d4b785336000860f9`
- Final decision: `SHADBALA_R1_NAISARGIKA_DIG_REMEDIATED_WITH_LEGACY_COMPATIBILITY`
- Failures: `[]`
- Independent corpus: `100 charts / 700 records / 700 matches`
- Focused/regression suite: `151 passed`
- Full repository suite: `TIMEOUT after 604 seconds; not treated as pass`
- Aggregate source-component promotion: `NO`
- Approved Core promotion: `NO`

| ID | Criterion | Status |
|---|---|---|
| AC01 | predecessor contract IDs and hashes verified | PASS |
| AC02 | runtime to work lineage is complete | PASS |
| AC03 | canonical unit is Virupa with explicit Rupa conversion | PASS |
| AC04 | Naisargika independent oracle is 7/7 | PASS |
| AC05 | Dig independent synthetic oracle is 700/700 | PASS |
| AC06 | legacy component routes remain callable | PASS |
| AC07 | aggregate remains legacy and unvalidated | PASS |
| AC08 | Sthana/Kala/Cheshta/Drik remain outside remediation | PASS |
| AC09 | no partial aggregate promotion | PASS |
| AC10 | no interpretation, prediction, ML or provider work | PASS |
| AC11 | RAG and Approved Core remain unchanged | PASS_WITH_CONDITION |
| AC12 | full suite outcome is reported as timeout, not pass | PASS_WITH_CONDITION |
