# VEDA-P006 Synthetic Pilot Report

Date baseline: `2026-08-10`

The tracked synthetic pilot demonstrates the complete P006 lifecycle without enabling live autonomous astrology research.

## Synthetic Domain

- domain: `VEDA-DOMAIN-SYNTHETIC`
- status: `TEST`
- provider: `synthetic-fixture`
- evidence source: `data/research/fixtures/synthetic_research_fixture.json`

## Pilot Sequence

1. Create `VEDA-RM-000001` synthetic pilot mission.
2. Run `initial` batch.
3. Run `continuation` batch while review is still pending.
4. Approve `alpha`.
5. Reject `beta`.
6. Mark `delta` as `NEEDS_MORE_RESEARCH`.
7. Create follow-up mission `VEDA-RM-000002`.
8. Run follow-up mission.
9. Export tracked snapshot.

## Required Pilot Cases Covered

- one genuinely new claim
- one duplicate-strengthening claim
- one conflicting claim
- one rejected source
- one approved candidate
- one rejected candidate
- one `NEEDS_MORE_RESEARCH` candidate
- one follow-up mission
- research continuation while approval is pending
- restart-safe persistence
- full ledger reconstruction

## Snapshot Counts

- domains: `1`
- approved core records: `2`
- missions: `2`
- schedules: `1`
- runs: `3`
- observations: `7`
- evidence: `6`
- candidates: `4`
- validations: `60`
- conflicts: `1`
- approvals: `3`
- ledger events: `92`

Tracked export location:

- `data/research/synthetic_pilot/`
