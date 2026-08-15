# VEDA-EMP-025-R1 Diversity and Corroboration Recovery

Status: `IN IMPLEMENTATION`
Parent: `VEDA-EMP-025`
Date: 2026-08-16

## Progress checkpoint

- Eligible cases: `12 / 25`
- Chart-ready cases: `12 / 20`
- Event classes: `3` (`DEATH`, `POSITION_START`, `POSITION_END`)
- Death share: `10 / 12` (`83.3%`), above the directional 40% target
- Multi-event subjects: `1` subject with 3 events; `9` subjects with 1 event
- Indian documentary cases: `0`; no Indian timed case is counted
- BAV/SAV: `RESEARCH_ONLY`, inactive
- Method pilot: `NOT AUTHORISED`

## Material progress

The ingestion adapter now preserves all independently documented events for a
subject instead of discarding events after the first one. Joseph Alioto's
officially documented mayoral service added `POSITION_START` and
`POSITION_END` as year-precision conditional events. Twelve cases now pass the
existing registry gate, and all twelve have D1 chart snapshots using governed
coordinates and historical timezone inputs.

The new ranking adapter (`scripts/veda_emp_025_r1_ranking.py`) uses only
identity, source-likelihood, birth-data completeness, timezone and coordinate
fields. Chart features are explicitly excluded from acquisition selection.

## Ranking checkpoint

The 1,000-record screen produced these non-astrological lane counts:

| Lane | Screened | High priority |
|---|---:|---:|
| Leadership / public-event candidates | 91 | 51 |
| Science / awards candidates | 20 | 14 |
| Indian documentary lane in current OGDB slice | 0 | 0 |
| Other | 889 | 0 |

The Indian zero is a property of this source slice, not an existence claim.
The dedicated Indian lane remains `NOT_ESTABLISHED` and requires a separate
timed-source discovery pass.

## Recovery decision

The diversity bottleneck is improved but not closed. Continue acquisition in
leadership, science/awards and a dedicated Indian discovery lane. Death-only
expansion is deprioritized unless it materially improves provenance or balance.
