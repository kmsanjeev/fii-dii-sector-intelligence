# Classical Source Expansion — Loop 14

Status: `PASS_WITH_CONDITION`  
Activity: `CLASSICAL_SOURCE_EXPANSION`  
Date: 2026-08-16

## Scope

This bounded activity audits the existing P002 source registry and identifies
the next passage-level expansion targets. It does not add quotations, create
new source records, promote Approved Core knowledge, alter runtime semantics,
or infer empirical or prospective evidence.

## Verified registry baseline

`scripts/validate_p002_astrology_registry.py` passed with 10 sources, 13
passages, 13 claims, 2 conflicts, 3 approvals, 6 policies, and 1 legacy
record. The source-to-passage join is internally consistent for all existing
passages.

| Source group | Records | Passage records | Current boundary |
|---|---:|---:|---|
| BPHS | 1 | 3 | Passage-verified pilot evidence |
| Hora Sara | 1 | 2 | Passage-verified; translation limitations retained |
| Brihat Jataka | 1 | 1 | Passage-verified scoped evidence |
| Predictive Astrology editions | 2 | 6 | Passage-verified, edition-specific evidence |
| Phaladeepika | 1 | 0 | Metadata-only; no rule extraction |
| Saravali | 1 | 0 | Metadata-only; no rule extraction |
| Jataka Parijata | 1 | 0 | Metadata-only; no rule extraction |
| Internal / modern pilot records | 2 | 1 | Lower-authority or metadata-qualified evidence |

## Expansion decision

The next safe research slice is a passage-level audit of **Phaladeepika** and
**Jataka Parijata**, followed by **Saravali** and **Uttara Kalamrita** only if a
governed source record is first established. The work must capture edition,
chapter/verse or page locator, translation status, legal-access status, and
source-to-passage-to-claim lineage. A discovered web page is not sufficient
authority, and a translation or commentary must not be represented as root
Sanskrit.

No passage-level promotion is justified in this activity: the four target
families remain `METADATA_VERIFIED`/candidate-level or absent from the current
passage join. Existing approvals and Approved Core counts are unchanged.

## Validation boundary

- Registry validator: **PASS**.
- Full `pytest` run: **270 passed before an unrelated failure** in
  `tests/test_api_contract_baseline.py::test_api_contract_baseline_snapshot`;
  the generated API contract reports 140 paths/153 operations while the
  fixture expects 129/141. This activity did not modify API code or fixtures.
- Empirical cases: **0**; prospective subjects/predictions/outcomes: **0**.

## Resumable next action

Loop 15 should perform one governed edition/passages audit for Phaladeepika or
Jataka Parijata, using only directly inspectable material and recording any
bounded access or verification failure. Do not add a passage from memory or
secondary web summaries, and do not rebuild or promote runtime knowledge from
metadata-only records.
