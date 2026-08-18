# VEDA-EVIDENCE-POSEND-ACQ-R1 — Research Log

## Scope

This log records the bounded, feature-blind acquisition performed for exact-day
`POSITION_END` evidence. It does not record chart calculations, feature values,
predictive outcomes or model results. The frozen birth frame was the governed
114-subject ADB source-diversity pool; raw ADB XML remained local and ignored.

## Search policy

- Search one subject at a time for an objective formal public-role end.
- Accept an event only when the public source states an exact calendar day and
  the role interval can be represented without inference.
- Prefer official government, parliamentary or institutional sources.
- Separate birth-source provenance from event-source provenance.
- Exclude inferred career endings, approximate dates, death endpoints and
  source-only discovery leads from the target event cohort.
- Do not scrape or redistribute provider pages; no formal ADB access request was
  submitted.

## Accepted evidence

The event register contains the passage-level metadata, retrieval dates, source
URLs, exact dates, role labels and source clusters for the four accepted events:

| Subject | Event | Exact interval | Source family |
|---|---|---|---|
| ADB-51916 | Nicole Catala, French National Assembly term completion | 1997-06-01 to 2002-06-18 | Assemblée nationale official |
| ADB-53387 | Willy de Clercq, European Commission term completion | 1985-01-06 to 1989-01-05 | European Commission / Vlaams Parlement |
| ADB-53441 | Vittorino Colombo, Italian Senate presidency completion | 1983-05-12 to 1983-07-11 | Senato della Repubblica official |
| ADB-53866 | Pierre Cardo, French National Assembly term completion | 2002-06-19 to 2007-06-19 | Assemblée nationale official |

The official pages accessed for these records were:

- [Assemblée nationale — Nicole Catala](https://www.assemblee-nationale.fr/11/tribun/fiches_id/764.asp)
- [European Commission — Belgium in the EU](https://belgium.representation.ec.europa.eu/about-us/la-belgique-dans-lue_fr?prefLang=bg)
- [Vlaams Parlement — Willy de Clercq](https://www.vlaamsparlement.be/nl/vlaamse-volksvertegenwoordigers-het-vlaams-parlement/willy-de-clercq)
- [Senato della Repubblica — Vittorino Colombo](https://www.senato.it/legislature/8/composizione/senatori/elenco-alfabetico/scheda-attivita?did=00000640)
- [Assemblée nationale — Pierre Cardo](https://www.assemblee-nationale.fr/13/tribun/xml/xml/acteurs/734.asp)

## Rejected or downgraded leads

- A Chiyonofuji retirement lead was retained as `EVENT_FOUND_BUT_INSUFFICIENT_PRECISION`; the available public evidence did not meet the exact-day acceptance rule.
- Charles II and Hugo Chávez death endpoints were marked not applicable to the
  formal public-role-end family.
- Search snippets, Wikipedia-only leads, generic biography pages and
  practitioner/SEO material were discovery-only and were not accepted as event
  evidence.

## Result

The candidate register has 114 screened subjects: 4 exact-day eligible events,
1 insufficient-precision event lead, 2 not-applicable endpoints and 107
search-exhausted candidates. The next authorized activity is a design-freeze
review, not feature scoring or production activation.
