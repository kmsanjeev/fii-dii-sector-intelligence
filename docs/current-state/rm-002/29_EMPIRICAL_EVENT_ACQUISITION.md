# VEDA-EMP-EVENT-001 Event Acquisition Checkpoint

Status: `IN IMPLEMENTATION`
Date: 2026-08-16

## Material progress

The official OGDB cohort was expanded from the 25-record pilot to 250 timed
records. The expanded file contained no embedded Wikidata identifiers, so the
workflow switched to a bounded public-figure discovery pass. Identity
selection was completed before any chart inspection.

| Measure | Result |
| --- | ---: |
| OGDB records profiled | 250 |
| Identity-resolved candidates | 2 |
| Event-enriched subjects | 2 |
| CaseRegistry empirical-eligible cases | 1 |
| Excluded after enrichment | 1 |

## Accepted first case

`VEDA-EMP-CASE-001` is Joseph Alioto. The case uses the OGDB timed birth
record, exact identity agreement with Wikidata Q6280974, public San Francisco
corroboration, and a referenced exact death-date event. The case was ingested
into the existing shared `CaseRegistry` as `HISTORICAL_VERIFIED` with complete
retrospective cutoffs and `leakage_status=VALID`.

This is a pipeline-validation case, not a predictive accuracy result. No chart
agreement was used for subject selection, and no prediction was generated.

## Enriched but excluded

Ernst Abbe was identity-resolved and has an independently referenced death
event, but the OGDB record has no usable historical timezone. It is recorded in
the exclusion register with `TIMEZONE_UNRESOLVED`; the event is not silently
treated as a non-event.

## Governance

- Event claims preserve identifiers, precision, verification state, discovery
  source, verification source, and public/private status.
- Year-only appointment facts are retained as enrichment context but are not
  used as the first case event.
- BAV/SAV remain `IMPLEMENTED_UNVALIDATED` and are not used as validated
  empirical features.
- The shared CaseRegistry remains the only case-ingestion path.
- No Astro-Databank scraping, name-only join, chart-based selection, or
  fabricated outcome was used.

## Next work

Continue public-event enrichment on the expanded cohort, prioritize subjects
with multiple independently sourced exact/month events, and resolve timezone
provenance before admitting further cases. Do not claim predictive accuracy
until the first-10-case sanity gate is reached.
