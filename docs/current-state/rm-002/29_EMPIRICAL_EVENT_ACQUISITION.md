# VEDA-EMP-EVENT-001 Event Acquisition Checkpoint

Status: `IN IMPLEMENTATION`
Date: 2026-08-16

## Material progress

The official OGDB cohort was expanded from the 25-record pilot to 1,000 timed
records. The expanded file contained no embedded Wikidata identifiers, so the
workflow switched to a bounded public-figure discovery pass. Identity
selection was completed before any chart inspection.

| Measure | Result |
| --- | ---: |
| OGDB records profiled | 1,000 |
| Identity-resolved candidates | 11 |
| Event-enriched subjects | 12 |
| CaseRegistry empirical-eligible cases | 10 |
| Excluded after enrichment | 2 |

## Accepted first case

`VEDA-EMP-CASE-001` through `VEDA-EMP-CASE-010` are now present in the shared
`CaseRegistry` as `HISTORICAL_VERIFIED` with retrospective cutoffs and
`leakage_status=VALID`. Joseph Alioto remains the first case and has the
strongest event-source record because San Francisco official material
corroborates the Wikidata event year. The other cases preserve lower
confidence where Wikidata references are the only event source.

This is a pipeline-validation case, not a predictive accuracy result. No chart
agreement was used for subject selection, and no prediction was generated.

## Enriched but excluded

Ernst Abbe is identity-resolved and event-enriched but remains excluded because
the OGDB record has no usable historical timezone. Maurice Barrès is excluded
because the OGDB identifier date conflicts with the Wikidata birth date. Both
are recorded in the exclusion register; neither is silently treated as a
non-event.

## EMP-010 sanity gate

`VEDA-EMP-010-SANITY` is `PASS_WITH_CONDITION`: all ten registry cases pass
eligibility, provenance, leakage and no-chart-selection checks. The corpus is
not suitable for predictive accuracy claims yet: all ten events are `DEATH`,
nine event records are referenced-Wikidata-only, and governed chart-fact
generation awaits latitude/longitude resolution without place-name guessing.

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
- Historical timezone resolution is reusable through the IANA-based helper;
  Berlin and Réunion offsets are stored as bounded solutions rather than
  assumed current offsets.

## Next work

Continue public-event enrichment toward the 25-case method-pilot threshold,
prioritize independent event corroboration and non-death event classes, and
resolve governed chart inputs before feature generation. Do not claim
predictive accuracy or tune rules against the first ten cases.
