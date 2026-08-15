# VEDA-RM-002 Open Gauquelin Database Empirical Pilot

Status: `PASS_WITH_CONDITION`  
Activity: `VEDA-EMP-OGDB-001`  
Date: 2026-08-16

## Source and licence

The official Open Gauquelin Database timed-data download was inspected at
`https://opengauquelin.org/download/ogdb-time.csv.zip`. The site documents
semicolon-delimited ISO CSV data with OGID, optional WDID, birth date/time,
timezone, place and geography fields. The project states that its content is
released under CC-BY-SA-4.0 (alongside GPL/FDL software/documentation).

## Pilot result

- Feed registry: `data/veda/research/empirical/feed_registry.json`
- Adapter: `scripts/veda_ogdb_pilot.py`
- Pilot snapshot: `data/veda/research/empirical/ogdb_pilot_25.json`
- Timed records profiled: 25
- Usable empirical cases: **0**
- High-quality cases: **0**

The adapter preserves source identifiers and birth-record fields, but marks
each row `RESEARCH_ONLY_NO_EVENT`. A birth record alone is not an empirical
prediction case: a dated event/outcome, source verification and leakage review
are still required by the shared `CaseRegistry` contract.

## Governance decision

No case was ingested into the empirical registry, no outcome was fabricated,
and no predictive or calibration count changed. OGDB source quality remains
record-level and mixed; the site itself notes that records require checking
against civil registries. Wikidata enrichment is registered as a separate
feed but no automatic identity join was performed.

## Next bounded activity

`VEDA-EMP-WD-001`: test conservative WDID/event enrichment against explicitly
matched records while preserving original references. Do not count a subject
until an event and leakage review pass.
