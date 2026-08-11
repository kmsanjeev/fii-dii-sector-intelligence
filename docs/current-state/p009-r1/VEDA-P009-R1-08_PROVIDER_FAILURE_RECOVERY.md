# VEDA-P009-R1 — Provider Failure & Recovery

Date: August 11, 2026

## Search Failure / Fallback

`ddgs-search` was forced into cooldown during live validation.

Result:

- cooldown state was recorded;
- a later due cycle still ran successfully;
- the affected run degraded to `HYBRID` by falling back into the governed local astrology corpus;
- duplicate-worker or retry-storm behaviour was not observed.

## Retrieval Failure Containment

`requests-fetch` encountered a live `403` during validation.

Result:

- the failed source was contained as a source-level runtime rejection;
- the run remained `PARTIAL` instead of becoming a false total failure;
- previously accepted evidence in the same run was preserved.

## Recovery

Both providers were returned to healthy operational state by the end of validation:

- `ddgs-search`: `HEALTHY`
- `requests-fetch`: `HEALTHY`

A follow-up real fetch against the archived WisdomLib monitor source succeeded after the recovery step.

