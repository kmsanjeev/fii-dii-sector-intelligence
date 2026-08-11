# VEDA-P009-R1 — Final Acceptance

Date: August 11, 2026

## Acceptance Summary

| Requirement | Result | Evidence |
| --- | --- | --- |
| real external search provider enabled | `PASS` | `ddgs-search` executed live queries |
| real safe retrieval provider enabled | `PASS` | `requests-fetch` persisted live observations |
| real evidence reached research pipeline | `PASS` | `36` accepted external observations, `10` pending candidates |
| P002/P007 authority governance applied | `PASS` | accepted sources classified `REFERENCE_EDITION` / `METADATA_VERIFIED` |
| three controlled Jyotisha pilots ran | `PASS` | pilots A/B/C completed as governed partial-budget runs |
| candidate deduplication and enrichment work | `PASS` | repeated candidate merge events recorded |
| Admin approval does not block research | `PASS` | later runs executed with pending candidates still unresolved |
| provider failure, cooldown, fallback, recovery work | `PASS` | forced search cooldown, hybrid fallback, retrieval cooldown, recovery validation |
| controlled real missions seeded | `PASS` | four active real missions persisted |
| hourly/daily/weekly schedules persisted | `PASS` | one hourly, two daily, one weekly schedule remained visible after restart |
| runtime remains explicitly opt-in | `PASS` | activation still depends on explicit environment flags |
| Admin can kill / pause autonomous research | `PASS` | kill-switch block returned without starting due runs |
| full ledger lineage exists | `PASS` | query → source → evidence → candidate → validation → queue trace remained reconstructable |
| Approved Core remained untouched | `PASS` | no auto-promotion or production mutation occurred |
| regressions remained green | `PASS` | `422` Python tests passed; frontend and smoke passed |

## Final Verdict

`PASS`

External research is now genuinely active under controlled governance rather than local-only simulation.

