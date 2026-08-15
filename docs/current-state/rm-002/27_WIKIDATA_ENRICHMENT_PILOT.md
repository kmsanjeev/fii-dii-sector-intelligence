# VEDA-RM-002 Wikidata Enrichment Pilot

Status: `PASS_WITH_CONDITION`  
Activity: `VEDA-EMP-WD-001`  
Date: 2026-08-16

## Findings

The planned WDQS route was tested against an exact-name/year query and timed
out at the public endpoint. The Wikidata MediaWiki search API responded for a
sample OGDB name, but name search alone is ambiguous and is not an accepted
identity join.

No WDID was assigned during the live timeout test, no event was imported, and
no empirical case count changed. A replayable conservative adapter is now
available at `scripts/veda_wikidata_enrichment.py`. It accepts externally
retrieved candidate claims and accepts an identity only when birth date, place,
and occupation all agree exactly; it preserves both OGDB and Wikidata
references.

## Governance decision

The adapter is input preparation only. It does not perform name-only joins,
does not submit records to `CaseRegistry`, and does not create dated outcomes.
The OGDB pilot therefore remains source-preserving birth-record research and
its usable empirical case count remains `0` until event verification and
leakage review are separately completed.
